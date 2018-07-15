# -*- coding: utf-8 -*
import json

import django_filters
import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django_tables2 import RequestConfig
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from accounts.models import Customer
from emanage.permissions import IsStaff
from express.utils import toTZDatetime
from waybills.permissions import IsOwnerOrReadOnly, IsOwner
from waybills.serializers import (UserSerializer, WaybillSerializer, GoodSerializer, WaybillStatusEntrySerializer,
                                  WaybillStatusSerializer, LocationSerializer, WaybillCreateSerializer,
                                  WaybillBulkCreateResponseSerializer)
from .forms import *
from .forms import WaybillSearchForm
from .pdf_template import *
from .tables import WaybillTable
from addresses.tasks import *
from pallets.tasks import *


class NotCreateModelViewSet(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    pass;


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class WaybillFilterSet(django_filters.rest_framework.FilterSet):
    tracking_no = django_filters.CharFilter(name="tracking_no", lookup_expr="icontains")
    start_date = django_filters.DateFilter(name='create_dt', lookup_expr=('gte'))
    end_date = django_filters.DateFilter(name='create_dt', lookup_expr=('lte'))
    status_name = django_filters.CharFilter(name='status_set__status__name', lookup_expr="icontains")

    class Meta:
        model = Waybill
        fields = ['tracking_no', 'start_date', 'end_date', 'status_name']


class WaybillViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Waybill.objects.all().order_by('-id')
    serializer_class = WaybillSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly, IsStaff)
    filter_class = WaybillFilterSet

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        waybill_status = Waybill.objects.get(pk=instance.id).status_set.order_by("-create_dt").first()
        if instance.can_delete():
            if instance.cn_tracking:
                QFTracking.revert_tracking(instance.cn_tracking)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN,
                            data={"detail": "订单状态为\"%s\"， 不允许删除" % str(waybill_status)})

            # @list_route(methods=['post'], permission_classes=[permissions.IsAuthenticated])
            # def bulk_create(self, request):
            #     listSerializer = WaybillSerializer(data=request.data, many=True, context={'request': request})
            #     trackings = []
            #     if listSerializer.is_valid():
            #         for waybill_data in listSerializer.validated_data:
            #             waybill_data['user'] = self.request.user
            #             serializer = WaybillSerializer(data=waybill_data)
            #             waybill = serializer.create(waybill_data)
            #             trackings.append(waybill.tracking_no)
            #
            #     return Response(trackings)


@api_view(["POST"])
@permission_classes([IsStaff])
@parser_classes((JSONParser,))
@transaction.atomic
def waybill_bulk_create(request):
    # d = request.data

    listSerializer = WaybillCreateSerializer(data=request.data, many=True, context={'request': request})

    if listSerializer.is_valid():
        data = []
        is_success = True

        with transaction.atomic():
            sid = transaction.savepoint()

            # 获取国内单号, 目前只有全峰单号可用
            # TODO 段号用完怎么办
            qftrackings = []
            for w in listSerializer.validated_data:
                if w.get("person_id"):
                    qftrackings.append(QFTracking.get_unused_trackings()[0])
                else:
                    qftrackings.append(None)

            i = 0
            succ_waybill = []
            for waybill_data in listSerializer.validated_data:
                waybillResponseData = {
                    "init_loc": waybill_data.get('init_loc').id,
                    "tracking_no": waybill_data.get('tracking_no', ''),
                    "order_no": waybill_data.get('order_no')
                }
                try:
                    waybill_data['user'] = request.user.id
                    waybill_data['init_loc'] = waybill_data.get('init_loc').id
                    waybill_data["cn_tracking"] = qftrackings[i]
                    waybill_data["is_self_define"] = not not waybill_data.get('tracking_no', '')

                    serializer = WaybillCreateSerializer(data=waybill_data)

                    if serializer.is_valid():
                        succ_waybill.append(serializer.save())
                        waybillResponseData.update({
                            "code": 0,
                            "msg": u'成功',
                        })
                    else:
                        waybillResponseData.update({
                            "code": 1,
                            "msg": serializer.errors,
                        })
                        is_success = False

                    data.append(waybillResponseData)
                except Exception as e:
                    waybillResponseData.update(
                        {
                            "code": 1,
                            "msg": "内部错误" if not settings.DEBUG else  e.message,
                        }
                    )
                    data.append(waybillResponseData)
                    is_success = False
                i += 1

            if is_success:
                transaction.savepoint_commit(sid)
                for waybill in succ_waybill:
                    waybill.transaction_no = uuid.uuid4()
                    waybill.save()
                    if waybill.cn_tracking:
                        qfobj = QFTracking.objects.filter(tracking_no=waybill.cn_tracking).first()
                        if qfobj:
                            qfobj.waybill = waybill
                            qfobj.save()

            else:
                transaction.savepoint_rollback(sid)

        responseData = WaybillBulkCreateResponseSerializer(data={
            "code": 0 if is_success else 1,
            'msg': u'成功' if is_success else u'建单数据有问题, 建单失败; 所有成功建单的数据已被撤销',
            'data': data
        })
        st = status.HTTP_200_OK if is_success else status.HTTP_400_BAD_REQUEST
        responseData.is_valid()
        if settings.DEBUG:
            print (JSONRenderer().render(responseData.data))
        return Response(data=responseData.data, status=st, content_type="application/json")
    else:
        err_response_data = []
        for (e, input) in zip(listSerializer.errors, listSerializer.initial_data):
            a = {}
            a["tracking_no"] = input.get("tracking_no", "")
            a["code"] = 0 if len(e.keys()) == 0 else 1
            a["msg"] = "" if len(e.keys()) == 0 else e
            a["order_no"] = input.get("order_no", "")
            err_response_data.append(a)
        responseData = WaybillBulkCreateResponseSerializer(data={
            "code": 1,
            'msg': u'建单数据检验未通过',
            'data': err_response_data
        })
        responseData.is_valid()
        if settings.DEBUG:
            print (JSONRenderer().render(responseData.data))
        return Response(data=responseData.data, status=status.HTTP_400_BAD_REQUEST, content_type="application/json")


@api_view(["POST"])
@permission_classes([IsStaff])
@parser_classes((JSONParser,))
@transaction.atomic
def waybill_bulk_create_new(request):
    # d = request.data

    listSerializer = WaybillCreateSerializer(data=request.data, many=True, context={'request': request})

    if listSerializer.is_valid():
        data = []
        is_success = True

        with transaction.atomic():
            sid = transaction.savepoint()

            i = 0
            succ_waybill = []
            for waybill_data in listSerializer.validated_data:
                waybillResponseData = {
                    "init_loc": waybill_data.get('init_loc').id,
                    "tracking_no": waybill_data.get('tracking_no', ''),
                    "order_no": waybill_data.get('order_no')
                }
                try:
                    waybill_data['user'] = request.user.id
                    waybill_data['init_loc'] = waybill_data.get('init_loc').id
                    waybill_data["is_self_define"] = not not waybill_data.get('tracking_no', '')
                    waybill_data['src_loc'] = waybill_data.get('src_loc').id if waybill_data.get('src_loc') else None
                    waybill_data['channel'] = waybill_data.get('channel').id if waybill_data.get('channel') else None

                    serializer = WaybillCreateSerializer(data=waybill_data)

                    if serializer.is_valid():
                        w = serializer.save()
                        succ_waybill.append(w)
                        waybillResponseData.update({
                            "code": 0,
                            "msg": u'成功',
                            "link": request.build_absolute_uri(reverse('customer_waybill_label', args=(w.id,)))
                        })
                    else:
                        waybillResponseData.update({
                            "code": 1,
                            "msg": serializer.errors,
                        })
                        is_success = False

                    data.append(waybillResponseData)
                except Exception as e:
                    waybillResponseData.update(
                        {
                            "code": 1,
                            "msg": "内部错误" if not settings.DEBUG else  e.message,
                        }
                    )
                    data.append(waybillResponseData)
                    is_success = False
                i += 1

            if is_success:
                transaction.savepoint_commit(sid)
                in_no = ''
                for waybill in succ_waybill:
                    waybill.transaction_no = uuid.uuid4()
                    waybill.save()
                    in_no = waybill.in_no
                try:
                    if len(succ_waybill) == 1:
                        w = succ_waybill[0]
                        if not w.person_id:
                            notify_user_upload_person_info2.delay(w.recv_mobile, w.recv_name, w.tracking_no)
                    elif len(succ_waybill) > 1 and in_no:
                        notify_user_upload_person_info2_batch2.delay(in_no)
                except Exception as e:
                    print e
            else:
                transaction.savepoint_rollback(sid)

        responseData = WaybillBulkCreateResponseSerializer(data={
            "code": 0 if is_success else 1,
            'msg': u'成功' if is_success else u'建单数据有问题, 建单失败; 所有成功建单的数据已被撤销',
            'data': data
        })
        st = status.HTTP_200_OK if is_success else status.HTTP_400_BAD_REQUEST
        responseData.is_valid()
        if settings.DEBUG:
            print (JSONRenderer().render(responseData.data))
        return Response(data=responseData.data, status=st, content_type="application/json")
    else:
        err_response_data = []
        for (e, input) in zip(listSerializer.errors, listSerializer.initial_data):
            a = {}
            a["tracking_no"] = input.get("tracking_no", "")
            a["code"] = 0 if len(e.keys()) == 0 else 1
            a["msg"] = "" if len(e.keys()) == 0 else e
            a["order_no"] = input.get("order_no", "")
            err_response_data.append(a)
        responseData = WaybillBulkCreateResponseSerializer(data={
            "code": 1,
            'msg': u'建单数据检验未通过',
            'data': err_response_data
        })
        responseData.is_valid()
        if settings.DEBUG:
            print (JSONRenderer().render(responseData.data))
        return Response(data=responseData.data, status=status.HTTP_400_BAD_REQUEST, content_type="application/json")


class GoodViewSet(NotCreateModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Good.objects.all()
    serializer_class = GoodSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsStaff]


class WaybillStatusEntryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = WaybillStatusEntry.objects.all()
    serializer_class = WaybillStatusEntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsStaff]


class LocationViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsStaff]


@login_required()
def waybills(request):
    qs = Waybill.objects.filter(user=request.user).filter(status_set__create_dt__lte=timezone.now()).annotate(
        status_order_index=Max("status_set__status__order_index")).distinct()
    form = WaybillSearchForm(request.GET or None)
    form_action = WaybillBatchActionForm(request.POST or None)
    per_page = 10

    if form.is_valid():
        qs = form.addQuery(qs)
        per_page_data = form.cleaned_data["per_page"]
        if per_page_data:
            per_page = per_page_data

    table = WaybillTable(qs, order_by="-create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)

    return render(request, 'waybills/waybill_list.html', {'table': table, 'form': form, 'form_action': form_action})


@login_required()
def waybill(request, pk):
    waybill = get_object_or_404(Waybill, user=request.user, pk=pk)
    WaybillFormSet = inlineformset_factory(Waybill, Good, extra=1, can_delete=True,
                                           fields=['cat1', 'cat2', 'brand', 'description', 'quantity', 'unit_price',
                                                   'unit_weight', 'remark'])

    if request.method == "POST":
        form = WaybillForm(request.POST or None, instance=waybill)
        formset = WaybillFormSet(request.POST or None, instance=waybill)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, u'运单更新成功')
            return render(request, 'waybills/waybill_detail.html',
                          {"form": form, "formset": formset, 'tracking_no': waybill.tracking_no})
        else:
            messages.info(request, u'商品信息缺少必填信息')
            return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})

    else:
        form = WaybillForm(instance=waybill)
        formset = WaybillFormSet(instance=waybill)
        return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})


@login_required()
def waybillCreate(request):
    WaybillFormSet = inlineformset_factory(Waybill, Good, can_delete=True, min_num=1, extra=0,
                                           fields=['cat1', 'cat2', 'brand', 'description', 'quantity', 'unit_price',
                                                   'unit_weight', 'remark'])
    customer = Customer.objects.get(user=request.user)

    if request.method == "POST":
        form = WaybillForm(request.POST or None)

        if form.is_valid():
            try:
                waybill = form.save(commit=False)
                waybill.tracking_no = Waybill.get_next_sys_tracking_no()
                waybill.user = request.user
                waybill.save()
            except Exception as e:
                messages.info(request, str(e) if settings.DEBUG else u'运单提交时有异常发生， 请尝试重新提交')
                return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": WaybillFormSet()})

            # TODO 没有商品时不允许提交 js 实现
            formset = WaybillFormSet(request.POST or None, instance=waybill)
            if formset.is_valid():
                try:
                    formset.save()
                    messages.success(request, u'新建订单成功， 单号：%s' % waybill.tracking_no)
                    return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})
                except Exception as e:
                    waybill.delete()
                    messages.info(request, str(e) if settings.DEBUG else u'商品提交时有异常发生， 请尝试重新提交')
                    return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})
            else:
                waybill.delete()
                messages.info(request, u'商品信息缺少必填信息， 请重新提交')
                return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})
        else:
            messages.info(request, u'商品信息缺少必填信息')
            return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": WaybillFormSet()})

    else:
        form = WaybillForm(
            initial={"send_name": customer.repr_name, "send_mobile": customer.mobile, "send_address": customer.address,
                     "weight": 2})
        formset = WaybillFormSet()
        return render(request, 'waybills/waybill_detail.html', {"form": form, "formset": formset})


@login_required()
def waybillBulkCreate(request):
    # Note: waybill status will be create automatically after waybill save

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            book = request.FILES['file'].get_book()
            customer = Customer.objects.get(user=request.user)

            is_valid, errors, waybill_valid_forms, good_valid_forms, g_tracking_nos = validate(book, customer)

            if is_valid:
                # 保存
                saved_waybill = {}
                try:
                    for form in waybill_valid_forms:
                        waybill = form.save(commit=False)
                        waybill.user = request.user
                        waybill.is_self_define = True
                        waybill.save()
                        saved_waybill[waybill.tracking_no] = waybill

                    g_i = 0
                    for g_from in good_valid_forms:
                        good = g_from.save(commit=False)
                        good.waybill = saved_waybill[g_tracking_nos[g_i]]
                        good.save()
                        g_i += 1

                    messages.success(request, u'导入成功')
                except Exception as e:
                    for k, v in saved_waybill:
                        v.delete()
                    messages.info(request, str(e) if settings.DEBUG else u'导入途中异常，请重新导入')

            else:
                for error in errors:
                    messages.error(request, error, extra_tags='danger')
        else:
            messages.error(request, u'导入失败，表单验证失败', extra_tags='danger')

    form = UploadFileForm()
    return render(request, 'waybills/waybill_buld_create.html', {'form': form, })


def validate(book, customer):
    '''
    self_defined tracking_nos should be:
       1 unique in waybill and  good tracking_no match waybill tracking_no
       2 tracking_no unique in database
       3 one waybill should has at least one good
    '''
    if book.number_of_sheets() < 2:
        return False, None, list(u'缺少必要表格，请使用模板文件')

    # create two sheet
    waybill_sheet = book[0]
    waybill_sheet.name_columns_by_row(0)
    waybill_sheet.colnames = ['tracking_no', 'recv_province', 'recv_city', 'recv_area', 'recv_address',
                              'recv_zipcode', 'recv_name', 'recv_mobile', 'send_name', 'send_mobile',
                              'send_address', 'remark', 'order_no']
    good_sheet = book[1]
    good_sheet.name_columns_by_row(0)
    good_sheet.colnames = ['tracking_no', 'cat1', 'cat2', 'brand', 'description', 'quantity',
                           'unit_price',
                           'unit_weight', 'remark']

    tracking_waybill = [x.strip() for x in waybill_sheet.column["tracking_no"]]
    tracking_good = [x.strip() for x in good_sheet.column["tracking_no"]]

    is_tracking_no_valid, tracking_no_error = tracking_no_validate(tracking_good, tracking_waybill)

    if not is_tracking_no_valid:
        return False, list(tracking_no_error), None, None, None

    records = waybill_sheet.to_records()
    is_waybill_valid, waybill_content_errors, waybill_valid_forms = waybill_content_validate(customer, records)

    if not is_waybill_valid:
        return False, waybill_content_errors, None, None, None

    g_records = good_sheet.to_records()
    g_tracking_nos = good_sheet.column_at(0)

    is_good_valid, good_content_errors, good_valid_forms = good_content_validate(g_records)

    if not is_good_valid:
        return False, good_content_errors, None, None, None

    return True, None, waybill_valid_forms, good_valid_forms, g_tracking_nos


def good_content_validate(records):
    errors = []
    validForms = []
    for record in records:
        form = GoodForm(record)
        form.full_clean()
        if form.is_valid():
            validForms.append(form)

        else:
            errors.append(str(form.errors))
    errs = []
    is_valid = False
    if len(errors) > 0:
        i = 1
        for good_error in errors:
            errs.append(u'商品表第%d行: %s' % (i, (good_error.decode('utf-8') if settings.DEBUG else u'有必填项未填写')))
            i += 1
    else:
        is_valid = True
    return is_valid, errs, validForms


def waybill_content_validate(customer, records):
    errors = []
    validForms = []
    for record in records:
        if record.get("send_name").strip() == "":
            record["send_name"] = customer.repr_name
        if record.get("send_mobile").strip() == "":
            record["send_mobile"] = customer.mobile
        if record.get("send_address").strip() == "":
            record["send_address"] = customer.address
        record.update({"weight": 2})

        form = WaybillForm(record)
        form.full_clean()
        if form.is_valid():
            validForms.append(form)
        else:
            errors.append(str(form.errors))
    errs = []
    is_valid = False
    if len(errors) > 0:
        i = 1
        for waybill_error in errors:
            errs.append(u'运单:%s: %s' % (records[i - 1]['tracking_no'].decode('utf-8'),
                                        (waybill_error.decode('utf-8')) if settings.DEBUG else u'有必填项未填写'))
            i += 1
    else:
        is_valid = True
    return is_valid, errs, validForms


def tracking_no_validate(tracking_good, tracking_waybill):
    tracking_set_waybill = set(tracking_waybill)
    tracking_set_good = set(tracking_good)

    if "" in tracking_waybill:
        return False, u'表1第一列运单号有空单号情况， 请检查'
    if "" in tracking_good:
        return False, u'表2第一列运单号有空单号情况， 请检查'
    if len(tracking_waybill) != len(tracking_set_waybill):
        return False, u'表1第一列运单号有重复， 请检查'
    for good_tracing_no in tracking_set_good:
        if good_tracing_no not in tracking_set_waybill:
            return False, u'表2运单号为%s的行， 在表1中找不到对应运单号，请检查' % good_tracing_no
    for waybill_tracking_no in tracking_set_waybill:
        if waybill_tracking_no not in tracking_set_good:
            return False, u'每个订单，至少需要包含一件商品, 运单%s缺少商品 ' % waybill_tracking_no
    waybillObjs = Waybill.objects.filter(tracking_no__in=list(tracking_set_waybill)).values(
        "tracking_no")
    if waybillObjs.count() > 0:
        return False, u'以下运单号已在系统中存在：%s, 请更正' % (
            u','.join([x["tracking_no"] for x in waybillObjs]))  # .decode('utf-8')
    return True, ""


def waybill_search_view(request):
    if request.user.is_anonymous:
        timezone.activate(pytz.timezone("Asia/Shanghai"))

        # anonymous_tz = request.GET.get("anonymous_tz", '')
        # if anonymous_tz:
        #     try:
        #         timezone.activate(pytz.timezone(anonymous_tz))
        #     except:
        #         pass

    pre = request.GET.get('pre', '')
    is_staff = request.user.is_staff
    tracking_no_list = [x.strip().upper() for x in list(set(request.GET.get('tracking_no', '').split(',')))[:10]]

    data = {"waybills": []}
    if len(tracking_no_list) > 0:
        qs = Waybill.objects.filter(tracking_no__in=tracking_no_list).filter(~Q(channel__name=CH3))

        waybillMap = {}
        for waybill in qs:
            waybillObj = {"tracking_no": waybill.tracking_no,
                          "has_person_id": (not waybill.is_required_person_id()) or waybill.person_id != '',
                          "person_id_update_dt": waybill.upload_person_id_dt.astimezone(
                              pytz.timezone('Asia/Shanghai')) if waybill.upload_person_id_dt else None,
                          "is_error": waybill.status.name == u'运单异常',
                          "lack_person_id_pic": waybill.status.order_index < 109 and waybill.channel.name in [CH19,
                                                                                                              CH23] and (
                          not waybill.people or not waybill.people.id_card_front),
                          "status_set": []}

            has_cn_json = False
            if waybill.status_set.filter(status__name=u'国内派送').exists():
                cn_status = waybill.status_set.get(status__name=u'国内派送')

                last_update_date = cn_status.last_update.astimezone(pytz.timezone('Asia/Shanghai'))
                current_date = timezone.now().astimezone(pytz.timezone('Asia/Shanghai'))

                if waybill.status.name == u'国内派送' and cn_status.api_cnt < 40 and last_update_date.date() < current_date.date():
                    try:
                        update_waybill_cn_tracking.delay(waybill.id)
                    except Exception as e:
                        pass
                if cn_status.cn_status_json:
                    has_cn_json = True

            # 最近状态的更新时间
            now_dt = timezone.now().astimezone(pytz.timezone('Asia/Shanghai'))
            last_status_update_dt = now_dt

            for status in waybill.status_set.all().filter(Q(create_dt__lte=timezone.now())).order_by(
                    'status__order_index'):
                last_status_update_dt = status.create_dt.astimezone(pytz.timezone('Asia/Shanghai'))

                if not waybill.person_id and waybill.channel.name in CH_LIST_REQUIRED_PERSON_ID:
                    if status.status.order_index > 1 and status.status.order_index < 130:
                        continue

                if status.status.order_index >= 109 and status.status.order_index <= 110 and not has_cn_json:
                    continue

                waybillObj["status_set"].append(
                    {
                        "create_dt": status.create_dt,
                        "status__name": status.status.description,
                        'remark': status.remark
                    }
                )

                if status.status.name == u"已建单" and waybill.src_loc:
                    name = ''
                    if waybill.src_loc.name == 'NH':
                        name = 'New Hampshire'
                    elif waybill.src_loc.name == 'FL':
                        name = 'Florida'
                    elif waybill.src_loc.name == 'NJ':
                        name = 'New Jersey'

                    waybillObj["status_set"][-1]["status__name"] = name + waybillObj["status_set"][-1]["status__name"]

                if status.status.name == u"国内派送":
                    waybillObj["status_set"][-1]["create_dt"] = ''
                    # 区分邮政件和电商件
                    if waybill.channel.name != CH2:
                        waybillObj["status_set"][-1]["status__name"] += status.get_cn_tracking_info()
                    else:
                        waybillObj["status_set"][-1]["status__name"] = u"国际派送 " + status.get_cn_tracking_info()
                        if waybillObj["status_set"][-2]["status__name"] == u'已出库, 送往机场':
                            waybillObj["status_set"][-2]["status__name"] = u'已出库, 转交美国邮政'

                    waybillObj["status_set"] += status.get_cn_status_list()

            # 状态超期
            if waybill.status.order_index == 100:
                waybillObj["is_overtime"] = waybill.upload_person_id_dt and \
                                            now_dt - max(last_status_update_dt,
                                                         waybill.upload_person_id_dt) > timezone.timedelta(days=20)
            elif waybill.status.order_index < 100 or (
                            waybill.status.order_index > 100 and waybill.status.order_index <= 110):
                waybillObj["is_overtime"] = waybill.person_id \
                                            and waybill.upload_person_id_dt \
                                            and now_dt - max(last_status_update_dt,
                                                             waybill.upload_person_id_dt) > timezone.timedelta(days=7)
            else:
                waybillObj["is_overtime"] = False

            waybillMap[waybillObj['tracking_no']] = waybillObj

        for tracking_no in tracking_no_list:
            if tracking_no in waybillMap:
                data['waybills'].append(waybillMap[tracking_no])
            else:
                data['waybills'].append({"tracking_no": tracking_no, "status_set": []})

    return render(request, 'waybills/waybill_search.html',
                  {'data': data,
                   'current_timezone': timezone.get_current_timezone(),
                   "base_template": "manage/manage_base.html" if pre else "waybills/customer_base.html",
                   "manage": is_staff and pre})


'''
function base apiview has not obj or query set, so object level permission is not working
below funciton view not used
need to use class base api view
'''


@api_view(["GET"])
def waybill_print(request, pk):
    waybill = get_object_or_404(Waybill, pk=pk)
    return get_pdf_response(waybill.get_wrap_pdf())


class WaybillPDF(generics.RetrieveAPIView):
    queryset = Waybill.objects.all()
    permission_classes = (IsOwner,)  # staff can print all, user can only print it's own

    def get(self, request, *args, **kwargs):
        waybill = self.get_object()
        return get_pdf_response(waybill.get_wrap_pdf())


class WaybillSmallLabel(generics.RetrieveAPIView):
    queryset = Waybill.objects.all()
    permission_classes = (IsOwner,)  # staff can print all, user can only print it's own

    def get(self, request, *args, **kwargs):
        waybill = self.get_object()
        return get_small_label_response(waybill.get_wrap_pdf())


class WaybillLabel(generics.RetrieveAPIView):
    queryset = Waybill.objects.all()
    permission_classes = (IsOwner,)  # staff can print all, user can only print it's own

    def get(self, request, *args, **kwargs):
        waybill = self.get_object()
        pdf_wrap = waybill.get_wrap_pdf()
        return one_r4_pdf_response(pdf_wrap)


@api_view(['GET'])
@permission_classes([IsStaff])
@parser_classes([JSONParser])
def waybill_goods(request, waybill_id):
    w = get_object_or_404(Waybill, id=waybill_id)
    goods = []
    for g in w.goods.all():
        o = {}
        o["brand"] = g.brand
        o["description"] = g.description
        o["quantity"] = g.quantity
        o["sku"] = g.sku
        o["unit_weight"] = g.unit_weight
        o["img_url"] = g.img_url
        goods.append(o)

    return Response(data={"tracking_no": w.tracking_no, "goods": goods})


@api_view(['POST'])
@permission_classes([IsStaff])
@parser_classes([JSONParser])
def get_labels(request):
    tracking_list = [a.replace('\r', '').strip() for a in request.data.get("tracking_nos", "").split('\n') if
                     a.replace('\r', '').strip()]
    in_no = request.data.get('in_no', '').strip()

    if in_no:
        qs = Waybill.objects.filter(in_no=in_no)
    else:
        qs = Waybill.objects.all()

    not_exist = []
    objs = []

    for tracking_no in tracking_list:
        if not qs.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
            not_exist.append(tracking_no)
        else:
            w = Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).first()
            objs.append(w.get_wrap_pdf())

    if len(tracking_list) == 0:
        for w in Waybill.objects.filter(in_no=in_no):
            objs.append(w.get_wrap_pdf())

    succ = False
    succ_cnt = len(objs) - len(not_exist)
    total = len(objs)
    msg = ''
    url = ''
    if len(objs) == 0 and len(not_exist) == 0:
        succ = False
        msg = u"无运单"
    elif len(not_exist) > 0:
        succ = False
        msg = u"\n".join(not_exist) + u"\n 给定条件下搜不到以上单号"
    else:
        succ = True
        msg = u"面单将会在新窗口中打开, 请确保浏览器不会屏蔽新窗口"
        url = multi_pdf_response(objs)
    return Response(data={"succ": succ, "total": total, "succ_cnt": succ_cnt, "msg": msg, 'url': url})


@api_view(['POST'])
@permission_classes([IsStaff])
@parser_classes([JSONParser])
def get_waybills_cn_tracking(request):
    date = request.data.get('date', '').strip()
    warehouse = request.data.get('warehouse', '').strip()
    low = []
    not_check_in_cnt = 0
    status_sum_up = []
    qs = []
    if date and warehouse:
        start_dt = toTZDatetime(date, '%y%m%d')
        q = Q()
        q = q.add(Q(create_dt__gte=start_dt), Q.AND)
        q = q.add(Q(create_dt__lt=start_dt + timezone.timedelta(days=1)), Q.AND)
        q = q.add(Q(src_loc=warehouse), Q.AND)
        qs = Waybill.objects.filter(q).order_by('cn_tracking')
        for w in qs:
            style = ''
            check_in_status = WaybillStatusEntry.objects.get(name='已入库')

            if w.status.order_index < check_in_status.order_index:
                not_check_in_cnt += 1
                low.append(
                    {"id": w.id, "tracking_no": w.cn_tracking if w.cn_tracking else w.tracking_no,
                     "status": w.status.name, "style": ''})
                # elif w.status == check_in_status:
                #     style = 'success'
                # else:
                #     style = 'danger'
                # low.append(
                #     {"id": w.id, "tracking_no": w.cn_tracking if w.cn_tracking else w.tracking_no,
                #      "status": w.status.name, "style": style})
        status_sum_up = Waybill.get_status_sum_up(q)
    return Response(
        data={"result": low, "not_check_in_cnt": not_check_in_cnt, "total": qs.count(), "status_sum_up": status_sum_up})


@api_view(['POST', 'GET'])
@permission_classes([IsStaff])
def api_test(request):
    return render(request, "manage/api_test.html")


@api_view(['POST', 'GET'])
@permission_classes([IsStaff])
def hard_code(request):
    qs = Waybill.objects.filter(in_no='T171009')
    columnNames = [u'订单编号', u'物流电子运单号', u'支付交易号', u'净重', u'毛重', u'收货人地址', u'收货人电话', u'收货人名称', u'收货人身份证', u'运输工具名称',
                   u'进出境日期', u'发货人城市', u'发货人地址', u'发货人名称', u'发货人电话', u'主运单号', u'海关税号', u'商品名称', u'NAME', u'商品规格类型',
                   u'成交数量', u'成交单价'
                   ]
    result = [columnNames]
    for waybill in qs:
        r = []
        r.append(waybill.order_no)  # 订单号
        r.append(waybill.cn_tracking)  # 物流号
        r.append(waybill.transaction_no)  # 支付号
        r.append(waybill.weight * Decimal(0.453592))  # 净重
        r.append(waybill.weight * Decimal(0.453592))  # 毛重
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)  # 收货人地址
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_name)  # 收货人名称
        r.append(waybill.person_id)  # 收货人身份证
        r.append("")  # 运输工具名称
        r.append("")  # 进出境日期
        r.append("")  # 发货人城市
        r.append("")  # 发货人地址
        r.append("Mary Chang")  # 发货人名称
        r.append("8571421232")  # 发货人电话
        r.append('')  # 主运单号

        for good in waybill.goods.all():
            g = []
            g.append("")  # 海关税号
            g.append(good.hs_type)  # 商品名称
            g.append(good.brand)  # NAME
            g.append(good.spec)  # 商品规格类型
            g.append(good.quantity)  # 成交数量
            g.append(good.unit_price * DISCOUNT * RMB_RATE)  # 成交单价
            result.append(r + g)

    import django_excel as excel
    sheet = excel.pe.Sheet(result)
    return excel.make_response(sheet, "xls", file_name="电商")


@login_required()
def barcode_view(request):
    return render(request, 'manage/barcode.html')


@api_view(['POST', 'GET'])
@permission_classes([IsStaff])
def barcode(request, barcode):
    return get_barcode_label(barcode)


@api_view(['POST'])
@permission_classes([IsStaff])
@parser_classes((JSONParser,))
def get_sifang_pdf(request):
    try:

        url = multi_pdf_response(request.data, 'sifang.pdf')

        return Response(data={'succ': True, 'msg': "成功", 'url': url}, content_type="application/json")
    except Exception as e:
        return Response(data={'succ': False, 'msg': e.message, 'url': ''}, content_type="application/json")
