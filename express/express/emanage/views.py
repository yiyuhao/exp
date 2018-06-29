# -*- coding: utf-8 -*
from __future__ import unicode_literals

from collections import OrderedDict
from distutils.util import strtobool

from base64 import b64decode
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Max, Count, Sum, Q
from django.db.models.functions import Lower, Upper
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib.auth import views as auth_views
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django_tables2 import RequestConfig
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from emanage.excels import *
from emanage.tables import WaybillTable, BulkPrintTable, ExceptionRecordTable
from express.yunda_api import auto_create
from pallets.excels import update_usps_excel, overload_bc_excel
from waybills.pdf_template import multi_pdf_response
from waybills.tasks import wms_order_send_out, push_weight_to_wms
from .forms import *
from rest_framework.response import Response
from waybills.serializers import WaybillAuditSerializer, WaybillRevertErrorSerializer, WaybillDetailSerializer
from waybills.models import Waybill, WaybillStatus, WaybillStatusEntry
from accounts.models import Employee
from addresses.models import People
from .permissions import *
from django.utils import timezone
import pytz
from waybills.models import QFTracking
import django_excel as excel
from addresses.tasks import notify_user_upload_person_info2, notfiy_user_up_id_finish_packing
from addresses.utils import id_card_images_to_one_paper


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_index_view(request):
    return render(request, 'manage/index.html', context={'username': request.user.username})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def performacne_view(request):
    form = ManagePerformanceSearchForm(request.GET or None)
    user_names = ['vicky', 'huang', 'qian']
    qs_chudan = None
    if form.is_valid():
        q = Q()
        if form.cleaned_data["dt_st"]:
            dt_st = pytz.timezone(settings.TIME_ZONE).localize(
                datetime.strptime(form.cleaned_data["dt_st"], '%m/%d/%Y'))
            q.add(Q(create_dt__gte=dt_st), AND)
        if form.cleaned_data["dt_ed"]:
            dt_ed = pytz.timezone(settings.TIME_ZONE).localize(
                datetime.strptime(form.cleaned_data["dt_ed"], '%m/%d/%Y')) + timezone.timedelta(days=1)
            q.add(Q(create_dt__lte=dt_ed), AND)
        q.add(Q(user__username__in=user_names), AND)
        q.add(Q(status__name='已发往集运仓'), AND)
        qs_chudan = WaybillStatus.objects.filter(q).extra(
            {'day': "date(waybills_waybillstatus.create_dt AT TIME ZONE '{0}') ".format(settings.TIME_ZONE)}).values(
            'day', 'user__username').annotate(
            cnt=Count('status__name')).order_by('day')
        qs_chudan = table_helper_chudan(qs_chudan)
    return render(request, 'manage/performance.html', context={"form": form, "qs_chudan": qs_chudan})


def table_helper_chudan(qs):
    last_dt = None
    result = []
    rowspans = []
    rs = 0
    for o in qs:
        if o['day'] != last_dt:
            result.append({'day': o['day'],
                           'user__username': o['user__username'],
                           'cnt': o['cnt']})
            if last_dt:
                rowspans.append(rs)
            rs = 0
            rs += 1
        else:
            rs += 1
            result.append({'day': None,
                           'user__username': o['user__username'],
                           'cnt': o['cnt']})
        last_dt = o['day']
    rowspans.append(rs)
    for n in result:
        if n['day']:
            rowspan = rowspans.pop(0)
            n['rowspan'] = rowspan
    return result


def get_overview(qs):
    result = OrderedDict()
    for status in ['待出单', '美国在途', '已审核', '打板', '国内在途', '海关查验', '国内派送']:
        result[status] = 0
    for o in qs:
        order_index = o['status__order_index']
        if order_index >= 1 and order_index <= 2:
            result['待出单'] = result.get('待出单', 0) + o['cnt']
        elif order_index >= 10 and order_index < 30:
            result['美国在途'] = result.get('美国在途', 0) + o['cnt']
        elif order_index == 30:
            result['已审核'] = result.get('已审核', 0) + o['cnt']
        elif order_index >= 40 and order_index <= 50:
            result['打板'] = result.get('打板', 0) + o['cnt']
        elif order_index >= 60 and order_index <= 100:
            result['国内在途'] = result.get('国内在途', 0) + o['cnt']
        elif order_index == 105:
            result['海关查验'] = result.get('海关查验', 0) + o['cnt']
        elif order_index == 110:
            result['国内派送'] = result.get('国内派送', 0) + o['cnt']
    return result


def get_today_over_view(qs):
    result = OrderedDict()
    for status in ['新增单数', '打包数', '打板数', '出库数', '国内派送', '已完成']:
        result[status] = 0
    for o in qs:
        order_index = o['status__order_index']
        if order_index == 1:
            result['新增单数'] += o['cnt']
        elif order_index == 30:
            result['打包数'] += o['cnt']
        elif order_index == 50:
            result['打板数'] += o['cnt']
        elif order_index == 70:
            result['出库数'] += o['cnt']
        elif order_index == 110:
            result['国内派送'] += o['cnt']
        elif order_index == 120:
            result['已完成'] += o['cnt']
    return result


@never_cache
def manage_login_view(request):
    next = request.GET.get('next', reverse("manage-index"))

    if request.user.is_active and request.user.is_staff:
        return HttpResponseRedirect(reverse("manage-index"))

    else:
        if request.method == "POST":
            from accounts.views import set_user_timezone
            set_user_timezone(request)

        defaults = {
            'extra_context': {"next": next},
            'authentication_form': AdminAuthenticationForm,
            'template_name': 'manage/login.html',
        }
        # authentication_form not working with given template
        return auth_views.login(request, **defaults)


def manage_logout_view(request):
    return auth_views.logout(request, template_name="manage/logged_out.html")


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_check_in_view(request):
    return render(request, 'manage/waybill_check_in.html')


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_audit_view(request):
    return render(request, 'manage/waybill_audit.html')


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_error_view(request):
    return render(request, 'manage/waybill_error_report.html')


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_id_card_image_view(request):
    # 待审核
    if request.method == 'GET':
        search_key = request.GET.get('keywords')
        split_group = request.GET.get('split_group', 1)
        split_group = 1 if not split_group else int(split_group)
        start_index = request.GET.get('start_index', 1)
        start_index = 1 if not start_index else int(start_index)

        people = People.objects.filter(Q(status=1), ~Q(id_card_backside__isnull=True),
                                       ~Q(id_card_backside__exact=''))
        if search_key:
            people = people.filter(
                Q(name__contains=search_key) | Q(id_no__contains=search_key) | Q(mobile__contains=search_key))
        total = people.count()

        if total > 0:

            start = total / split_group * (start_index - 1)

            person = people[start:][0]
        else:
            person = None

        return render(request, 'manage/waybill_review_id_image.html', {'people': person, 'total': total})

    elif request.method == 'POST':
        try:
            people = People.objects.get(id=request.POST.get('person_id'))
            # 不通过审核
            is_reject = request.POST.get('reject') == 'true'
            if is_reject:
                people.status = 3
                people.save()
                return JsonResponse(dict(data={'succ': True, 'msg': '操作成功，审核不通过'}))

            # base64
            id_card_front = request.POST.get('id_card_front')
            id_card_backside = request.POST.get('id_card_backside')
            assert ';base64,' in id_card_front and ';base64,' in id_card_backside, '图片文件存在问题, 请审核不通过'

            # get base64 data
            id_card_front = id_card_front.split(';base64,')[-1]
            id_card_backside = id_card_backside.split(';base64,')[-1]

            id_card_front = b64decode(id_card_front)
            id_card_backside = b64decode(id_card_backside)

            # 更新人工裁剪后的照片
            people.id_card_front = ContentFile(id_card_front, '{}_id_card_font.jpg'.format(people.id))
            people.id_card_backside = ContentFile(id_card_backside, '{}_id_card_backside.jpg'.format(people.id))
            # 审核通过
            people.status = 2
            # 将正反面照粘贴至一张图片并保存至people.id_card
            id_card_images_to_one_paper(people)

            people.save()

            return JsonResponse(dict(data={'succ': True, 'msg': '裁剪成功，通过审核'}))

        except Exception as e:
            return JsonResponse(dict(data={'succ': False, 'msg': "保存失败: {}".format(e.message)}))


def do_check_in_package(tracking_no, user):
    try:
        # 获取所在地
        employee = Employee.objects.get(user=user)
        loc = employee.loc
        status = WaybillStatusEntry.objects.get(name='已入库')  # 已入库 status

        if Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
            waybill = Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).first()

            # 没有身份证不可以入库
            if not waybill.person_id:
                return 6, waybill.channel.name
            elif not waybill.cn_tracking and waybill.channel.name not in CH_LIST_NOT_REQUIRED_PERSON_ID:
                return 5, waybill.channel.name
            elif waybill.is_able_to_check_in():
                sent_to_warehouse = WaybillStatusEntry.objects.get(name='已发往集运仓')
                if waybill.status.order_index < sent_to_warehouse.order_index:
                    # 没有出单, 直接入库的情况
                    try:
                        wms_order_send_out.delay(waybill.tracking_no, user.username)
                    except:
                        pass
                WaybillStatus.objects.create(waybill=waybill, status=status, location=loc, user=user)
                return 0, waybill.channel.name
            elif waybill.status.name == u"已入库":
                return 3, waybill.channel.name
            else:
                return 2, waybill.channel.name

        else:
            return 1, ''
    except:
        return 4, ''


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_checkin_view(request):
    '''
    code
    0 success
    1 not exist
    2 not valid to checkin
    3 already checkin
    4 system error
    5 no cn_tracking
    6 no person_id
    '''

    data = request.data.get("tracking_no", '').strip().upper()
    user = request.user
    code, channel = do_check_in_package(data, user)

    return Response({"tracking_no": data, "code": code, "channel": channel})


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_check_form(request):
    '''
      code
      0 success
      1 not exist
      2 already audit
      3 not able to audit
      4 system error
    '''
    tracking_no = request.data.get("tracking_no", '').strip().upper()

    code, waybill_obj, msg = get_waybill_check_form(tracking_no)

    return Response({"waybill_obj": waybill_obj, "code": code, "msg": msg})


def get_waybill_check_form(tracking_no):
    try:
        if Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
            waybill = Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).first()
            serializer = WaybillAuditSerializer(waybill)
            able_to_audit, msg = waybill.is_able_to_audit()

            if able_to_audit:
                return 0, serializer.data, ''
            else:
                return 3, serializer.data, msg
        else:
            return 1, None, ''
    except Exception  as e:

        return 4, str(e), ''


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_detail_view(request):
    return render(request, 'manage/waybill_check_detail.html')


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_detail(request):
    tracking = request.data.get("tracking", '').strip().upper()

    succ, waybill_obj, msg = get_waybill_detail(tracking)

    return Response({"waybill_obj": waybill_obj, "succ": succ, "msg": msg})


def get_waybill_detail(tracking):
    try:
        if Waybill.objects.filter(Q(tracking_no=tracking) | Q(cn_tracking=tracking)).exists():
            waybill = Waybill.objects.filter(Q(tracking_no=tracking) | Q(cn_tracking=tracking)).first()
            serializer = WaybillDetailSerializer(waybill)
            return True, serializer.data, '获取成功'
        else:
            return False, None, '运单:{0}不存在'.format(tracking)
    except Exception  as e:
        return False, None, '发送异常:' + str(e)


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_error_report_form(request):
    '''
      code
      0 可以拦截
      1 不可拦截
    '''
    tracking_no = request.data.get("tracking_no", '').strip().upper()

    code, waybill_obj, msg = get_waybill_error_report_form(tracking_no)

    return Response({"waybill_obj": waybill_obj, "code": code, "msg": msg})


def get_waybill_error_report_form(tracking_no):
    if Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
        waybill = Waybill.objects.get(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no))
        audit_status = WaybillStatusEntry.objects.get(name='已审核')
        if waybill.status.order_index <= audit_status.order_index:
            serializer = WaybillAuditSerializer(waybill)
            return 0, serializer.data, '当前运单可以拦截'
        else:
            return 1, {}, '当前运单状态为:' + waybill.status.name + ', 不可以拦截'
    else:
        return 1, {}, "输入的运单号不存在"


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_waybill_weight(request):
    '''
        input: id, weight
        output:
            code
            0   success
            1   not exist
            2   waybill not able to do full check
            3   system error

    '''
    id = request.data.get("id")
    weight = request.data.get("weight")
    is_box = request.data.get("is_box", "false")
    is_box = True if is_box == "true" else False
    employee = Employee.objects.get(user=request.user)
    loc = employee.loc
    code = waybill_weight(id, weight, loc, request.user, is_box)
    return Response({"code": code})


@transaction.atomic()
def waybill_weight(id, weight, loc, user, is_box):
    try:
        if Waybill.objects.select_for_update().filter(id=id).exists():
            waybill = Waybill.objects.get(id=id)
            if waybill.is_able_to_audit():
                waybill.package_fee = Decimal('1.5') if is_box else Decimal('0')
                checkin_status = WaybillStatusEntry.objects.get(name='已入库')
                audit_status = WaybillStatusEntry.objects.get(name='已审核')
                if waybill.status.name == '已建单' or waybill.status.name == '已传身份证':
                    # 通知wms出库
                    try:
                        wms_order_send_out.delay(waybill.tracking_no, user.username)
                    except:
                        pass
                if waybill.status.name == u'已发往集运仓':  # 补上已入库状态
                    WaybillStatus.objects.create(waybill=waybill, status=checkin_status, location=loc, user=user)
                if waybill.status != audit_status and waybill.status.order_index < audit_status.order_index:
                    WaybillStatus.objects.create(waybill=waybill, status=audit_status, location=loc, user=user)
                waybill.weight = Decimal(weight)
                waybill.save()

                try:

                    # 如果一单多货的情况, 则不更新商品重量, 只更新运单费用
                    sku = ''
                    if waybill.get_goods_quantity() == 1:
                        g = waybill.goods.all().first()
                        sku = g.sku if g else ''
                    if not waybill.is_billed:
                        push_weight_to_wms.delay(sku, Decimal(weight), waybill.get_fee_actual(), waybill.tracking_no,
                                                 waybill.get_tax_fee())
                        # waybill.gen_bill()

                except Exception as e:
                    pass
                return 0
            else:
                return 2
        else:
            return 1
    except Exception  as e:
        return 3


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_error_report(request):
    '''
        input: tracking_no, remark
        output:
            code
            0   success
            1   not exist
            2   is error status
            3   waybill not able to do report
            4   system error
        '''
    id = request.data.get("id")
    remark = request.data.get("remark")
    employee = Employee.objects.get(user=request.user)
    loc = employee.loc
    code = waybill_error_report(id, remark, loc, request.user)
    return Response({"code": code})


def waybill_error_report(id, remark, loc, user):
    try:
        if Waybill.objects.filter(id=id).exists():
            waybill = Waybill.objects.get(id=id)
            send_out_status = WaybillStatusEntry.objects.get(name='打板中')
            error_status = WaybillStatusEntry.objects.get(name='运单异常')  # 异常
            if waybill.status == error_status:  # 是异常状态
                return 2
            elif waybill.status.order_index >= send_out_status.order_index:  # 已经装袋或打板
                return 3
            else:
                WaybillStatus.objects.create(waybill=waybill, status=error_status, location=loc, user=user,
                                             remark=remark)
                return 0
        else:
            return 1
    except Exception as e:
        return 4


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybills_view(request):
    form = ManageWaybillSearchForm(request.GET or None)
    form_action = WaybillActionForm()
    per_page = 20
    loc = Employee.objects.get(user=request.user).loc

    if form.is_valid():
        qs = form.addQuery(loc)
    else:
        qs = Waybill.objects.all()

    table = WaybillTable(qs, order_by="-create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)
    total = qs.count()

    return render(request, 'manage/waybill_list.html',
                  {'table': table, 'total': total, 'form': form, 'form_action': form_action})


'''
 Waybill.objects.annotate(status_id=Max("status_set__id")).annotate(status_order_index=Max("status_set__status__order_index"))
'''


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybills_bulk_print_view(request):
    form = BulkPrintSearchForm(request.GET or None)
    shelf_list = ''
    per_page = 10
    qs = Waybill.objects.none()
    total_waybill_cnt, total_a1, total_a2, total_a3, total_k2, total_q = 0, 0, 0, 0, 0, 0
    if form.is_valid():
        qs = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(Q(goods_num=1),
                                                                               Q(status__name__in=['已建单',
                                                                                                   '已传身份证']), ).exclude(
            channel__name__in=['Q']).distinct()

        channel = form.cleaned_data["channel"]
        src_loc = form.cleaned_data["src_loc"]
        in_no = form.cleaned_data["in_no"]
        dt = form.cleaned_data["dt"]

        total_a1, total_a2, total_a3, total_k2, total_q, total_waybill_cnt = cal_total_cnt(dt, qs, src_loc)

        qs = qs.filter(Waybill.get_able_to_print_query())

        shelf_list = get_shelf_list_str(qs, src_loc, in_no, channel, dt)

        qs = form.addQuery(qs)

    table = BulkPrintTable(qs, order_by="goods__sku, create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)
    waybill_cnt = qs[:per_page].count()

    goods_cnt = qs[:per_page].aggregate(goods_cnt=Sum('goods__quantity'))['goods_cnt']
    return render(request, 'manage/waybill_print_bulk_print.html',
                  {'table': table, 'waybill_cnt': waybill_cnt, 'goods_cnt': goods_cnt, 'form': form, 'form_action': '',
                   'shelf_list': shelf_list, 'total_waybill_cnt': total_waybill_cnt, 'total_a1': total_a1,
                   'total_a2': total_a2, 'total_a3': total_a3, 'total_k2': total_k2, 'total_q': total_q})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybills_bulk_print_multiple_view(request):
    form = BulkPrintMultiSearchForm(request.GET or None)
    shelf_list = ''
    per_page = 10
    qs = Waybill.objects.none()
    total_waybill_cnt, total_a1, total_a2, total_a3, total_k2, total_q = 0, 0, 0, 0, 0, 0

    if form.is_valid():
        qs = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(Q(goods_num__gt=1),
                                                                               Q(status__name__in=['已建单',
                                                                                                   '已传身份证']), ).exclude(
            channel__name__in=['Q']).distinct()
        src_loc = form.cleaned_data["src_loc"]
        channel = form.cleaned_data["channel"]
        dt = form.cleaned_data["dt"]

        total_a1, total_a2, total_a3, total_k2, total_q, total_waybill_cnt = cal_total_cnt(dt, qs, src_loc)

        qs = qs.filter(Waybill.get_able_to_print_query())

        shelf_list = get_shelf_list_str(qs, src_loc, '', channel, dt)

        qs = form.addQuery(qs)

    table = BulkPrintTable(qs, order_by="upload_person_id_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)
    waybill_cnt = qs[:per_page].count()

    goods_cnt = qs[:per_page].aggregate(goods_cnt=Sum('goods__quantity'))['goods_cnt']
    return render(request, 'manage/waybill_print_multiple_batch.html',
                  {'table': table, 'waybill_cnt': waybill_cnt, 'goods_cnt': goods_cnt, 'form': form, 'form_action': '',
                   'shelf_list': shelf_list, 'total_waybill_cnt': total_waybill_cnt, 'total_a1': total_a1,
                   'total_a2': total_a2, 'total_a3': total_a3, 'total_k2': total_k2, 'total_q': total_q})


def cal_total_cnt(dt, qs, src_loc):
    total_qs = qs.filter(
        Q(src_loc=src_loc), Q(channel__name__in=['A1', 'A2', 'A3', 'K2', 'Q']),
        ~Q(cn_tracking__exact=''), Q(cn_tracking__isnull=False),
        ~Q(person_id__exact=''), Q(person_id__isnull=False), (Q(in_no__istartswith='HH') | Q(in_no__istartswith='HC')))
    if dt:
        total_qs = total_qs.filter(Q(upload_person_id_dt__lt=toTZDatetime(dt) + timezone.timedelta(days=1)))

    total_waybill_cnt = total_qs.count()
    total_a1 = total_qs.filter(channel__name='A1').count()
    total_a2 = total_qs.filter(channel__name='A2').count()
    total_a3 = total_qs.filter(channel__name='A3').count()
    total_k2 = total_qs.filter(channel__name='K2').count()
    total_q = total_qs.filter(channel__name='Q').count()
    return total_a1, total_a2, total_a3, total_k2, total_q, total_waybill_cnt


def get_shelf_list_str(qs, src_loc, in_no, channel, dt):
    q = Q()
    q.add(~Q(shelf_no__iexact=''), Q.AND)
    if src_loc:
        q.add(Q(src_loc=src_loc), Q.AND)
    if in_no:
        q.add(Q(in_no__istartswith=in_no), Q.AND)
    else:
        q.add(Q(in_no__istartswith='HH') | Q(in_no__istartswith='HC'), Q.AND)
    if channel:
        q.add(Q(channel=channel), Q.AND)
    if dt:
        q.add(Q(upload_person_id_dt__lt=toTZDatetime(dt) + timezone.timedelta(days=1)), Q.AND)

    qs_shelf = qs.filter(q).annotate(shelf_no_upper=Upper("shelf_no")).values('shelf_no_upper').distinct().order_by(
        'shelf_no_upper')

    shelf_list = set([s['shelf_no_upper'] for s in qs_shelf])

    shelf_list = ', '.join(sorted(shelf_list))

    shelf_list = ', '.join(sorted(set([a.strip() for a in shelf_list.split(',')])))

    return shelf_list


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_print_single_good_view(request):
    '''
        输入运单号以后, 自动出面单的界面, 用于扫描单个sku商品出单
    '''
    return render(request, 'manage/waybill_print_single_good.html',
                  {'channels': Channel.objects.all().order_by('id')})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_print_multi_goods_view(request):
    '''
        输入运单号以后, 自动出面单的界面, 用于扫描多个sku商品出单
    '''
    return render(request, 'manage/waybill_print_multiple_goods.html',
                  {'channels': Channel.objects.all().order_by('id')})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_print_tracking_view(request):
    '''
        输入运单号以后, 自动出面单的界面, 用于扫描单号后出单
    '''
    return render(request, 'manage/waybill_print_with_tracking.html')


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_change_label_view(request):
    '''
        用于换单, 输入原国内单号, 返回新面单
    '''
    return render(request, 'manage/waybill_print_change_label.html')


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_exist_check(request, type):
    '''
        input: tracking_no
        output:
            code
            0   success
            1   waybill not exist
            2   no cn_tracking
            3   no person_id
            4   system error
            5   goods not in shelf

            link
            for waybill pdf
    '''
    code = 1
    link = ""
    goods = []
    tracking_no = ""
    if type == "a":
        code, link, tracking_no = check_waybill_with_tracking_no(request)
    elif type == "b":
        code, link, goods, tracking_no = check_waybill_with_sku(request)
    elif type == "c":
        code, link, tracking_no = get_change_label(request)
    elif type == "d":
        code, link, tracking_no = get_label(request)
    else:
        pass
    return Response({"code": code, "link": link, 'goods': goods, 'tracking_no': tracking_no})


def get_change_label(request):
    code = 1
    link = ""
    tracking_no = ""
    try:
        tracking_no = request.data.get("tracking_no", '').strip().upper()

        q_obj = Q()
        q_obj.add(Q(third_party_tracking_no=tracking_no), Q.OR)

        if Waybill.objects.filter(q_obj).exists():
            obj = Waybill.objects.filter(q_obj).order_by('-id').first()
            link = reverse('customer_waybill_label', kwargs={"pk": obj.id})
            code = 0
        else:
            code = 1
    except Exception as e:
        print(e)
        code = 1
    return code, link, tracking_no


def get_label(request):
    code = 1
    link = ""
    tracking_no = ""
    try:
        tracking_no = request.data.get("tracking_no", '').strip().upper()

        q_obj = Q()
        q_obj.add(Q(cn_tracking=tracking_no), Q.OR)

        if Waybill.objects.filter(q_obj).exists():
            obj = Waybill.objects.filter(q_obj).order_by('-id').first()
            link = reverse('customer_waybill_label', kwargs={"pk": obj.id})
            code = 0
        else:
            code = 1
    except Exception as e:
        print(e)
        code = 1
    return code, link, tracking_no


def check_waybill_with_sku(request):
    skus = [x.strip().replace('\n', '').replace('\r', '') for x in request.data.get("sku", '').split(',') if
            x.strip()]
    in_no = request.data.get('in_no', '')
    src_loc_id = request.data.get('in_warehouse', '')
    channel_id = request.data.get('channel', '')
    shelf_no = request.data.get('shelf_no', '')
    code = 1
    link = ""
    goods = []
    tracking_no = ""

    # TODO 按waybill 所有者筛选
    try:
        code, link, goods, tracking_no, obj = Waybill.get_waybill_with_skus(skus, in_no, src_loc_id, channel_id,
                                                                            shelf_no)
        if code == 0:
            able_to_print, code = obj.is_able_to_print_out()
            # if not obj.person_id and obj.channel.name not in CH_LIST_NOT_REQUIRED_PERSON_ID:
            #     code = 3
            # if not obj.cn_tracking and obj.channel.name not in CH_LIST_NOT_REQUIRED_PERSON_ID:
            #     code = 2

            # 通知没身份证的
            if not obj.person_id and obj.channel.name in CH_LIST_REQUIRED_PERSON_ID:
                try:
                    if obj.sms_notify_times < 3 and is_cn_day_time():
                        notify_user_upload_person_info2.delay(obj.recv_mobile, obj.recv_name, obj.tracking_no)
                        obj.sms_notify_times += 1
                        obj.save()
                except:
                    pass
            if able_to_print:
                obj.is_print_by_manage = True
                obj.set_package_sent_to_center(request.user)
                obj.save()
                # 通知wms出库
                try:
                    wms_order_send_out.delay(obj.tracking_no, request.user.username)
                except:
                    pass
    except Exception as e:
        code = 4

    return code, link, goods, tracking_no


def check_waybill_with_tracking_no(request):
    code = 1
    link = ""
    tracking_no = ""
    try:
        tracking_no = request.data.get("tracking_no", '').strip().upper()
        send_to_express = bool(strtobool(request.data.get("send_to_express", 'false')))
        sent_to_warhouse_status = WaybillStatusEntry.objects.get(name='已发往集运仓')

        q_obj = Q()
        q_obj.add(Q(tracking_no=tracking_no), Q.OR)
        q_obj.add(Q(cn_tracking=tracking_no), Q.OR)
        q_obj.add(Q(third_party_tracking_no=tracking_no), Q.OR)
        q_obj.add(Q(status__order_index__lt=sent_to_warhouse_status.order_index), Q.AND)

        if Waybill.objects.filter(q_obj).exists():

            obj = Waybill.objects.filter(q_obj).first()

            able_to_print, code = obj.is_able_to_print_out()

            if not obj.person_id and obj.channel.name in CH_LIST_REQUIRED_PERSON_ID:
                try:
                    if obj.sms_notify_times < 3 and is_cn_day_time():
                        notify_user_upload_person_info2.delay(obj.recv_mobile, obj.recv_name, obj.tracking_no)
                        obj.sms_notify_times += 1
                        obj.save()
                except:
                    pass

            if able_to_print:
                obj.is_print_by_manage = True
                if send_to_express:
                    obj.set_package_sent_to_center(request.user)
                    # 通知wms出库
                    try:
                        wms_order_send_out.delay(obj.tracking_no, request.user.username)
                    except:
                        pass
                obj.save()
                link = reverse('customer_waybill_label', kwargs={"pk": obj.id})
                code = 0
        else:
            code = 1
    except Exception as e:
        print(e)
        code = 4
    return code, link, tracking_no


@api_view(['POST'])
@permission_classes([IsStaff])
def test_api_post(request):
    foo = request.data.get("foo")
    return Response({"foo": foo + "_server_patch"})


@api_view(['POST'])
@permission_classes([IsStaff])
def update_waybill_usps(request):
    if request.FILES['file']:
        succ, total, succ_cnt, errors = update_usps_excel(request.FILES['file'])
        if succ:
            return Response(data={"succ": succ, "msg": "更新成功", "succ_cnt": succ_cnt, "total": total},
                            content_type="application/json")
        else:
            return Response(data={"succ": succ, "msg": errors, "succ_cnt": succ_cnt, "total": total},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, 'total': 0})


@api_view(['POST'])
@permission_classes([IsStaff])
def add_yunda_waybills(request):
    if request.FILES['file']:
        try:
            cnt = add_yunda_from_excel(request.FILES['file'])
            return Response(data={"succ": True, "msg": "更新成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_export_waybill(request):
    params = request.query_params
    loc = Employee.objects.get(user=request.user).loc

    sheet = waybill_excel(params, loc)
    return excel.make_response(sheet, "xls", file_name="导出运单信息")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_export_waybill_address_info(request):
    params = request.query_params
    sheet = waybill_excel_address_info(params)
    return excel.make_response(sheet, "xls", file_name="导出运单地址信息")


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_batch_export_view(request):
    form = BatchCheckForm(request.POST or None)
    return render(request, 'manage/batch_check_cn_status.html', {"form": form})


@api_view(['POST'])
@permission_classes([IsStaff])
def check_cn_status_excel(request):
    f = request.FILES['file']
    url = gen_cn_status_excel(f)
    return Response(data={"url": url})


@api_view(['GET'])
@permission_classes([IsStaff])
def get_virtual_yunda_excel(request):
    query_params = request.query_params
    sheet = vriual_yundan_excel(query_params)
    return excel.make_response(sheet, "xls", file_name="韵达虚拟单号")


@api_view(['POST'])
@permission_classes([IsStaff])
def update_virtual_yunda_excel_view(request):
    if request.FILES['file']:
        try:
            cnt = update_virtual_yunda_excel(request.FILES['file'])
            return Response(data={"succ": True, "msg": "更新虚拟单号成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
@parser_classes((JSONParser,))
def revert_waybill_error_view(request):
    serializer = WaybillRevertErrorSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        msg = ''
        succ = True
        waybill = Waybill.objects.filter(tracking_no=serializer.validated_data["tracking_no"]).first()
        if not waybill:
            succ = False
            msg = u'运单不存在'
        else:
            if waybill.status.name == '运单异常':
                waybill.get_most_recent_status().delete()

            goods_data = serializer.validated_data.pop('goods')
            for g in goods_data:
                Good.objects.create(waybill=waybill, **g)
            msg = u"成功"

        if settings.DEBUG:
            print (JSONRenderer().render({"succ": succ, "msg": msg}))
        return Response(data={"succ": succ, "msg": msg}, status=status.HTTP_200_OK, content_type="application/json")
    else:
        return Response(data={"succ": False, "msg": serializer.error_messages},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR, content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def mark_waybill_error_view(request):
    tracking_no = request.data.get('tracking_no', '').strip()
    goods_no = request.data.get('goods_no', '')
    quantity = 0
    try:
        q = request.data.get('quantity', 1)
        quantity = int(q)
    except:
        pass
    msg, succ = mark_waybill_error(request.user, tracking_no, goods_no, quantity)
    return Response(data={'succ': succ, 'msg': msg}, content_type='application/json')


def mark_waybill_error(user, tracking_no, goods_no, quantity):
    msg = u''
    succ = False
    if tracking_no:
        w = Waybill.objects.filter(tracking_no=tracking_no).first()
        if w:
            msg, succ = w.mark_error(user, goods_no, quantity)
        else:
            msg = u'运单不存在'
    else:
        msg = u'运单号不能为空'
    return msg, succ


@api_view(['GET'])
@permission_classes([IsStaff])
def get_export_q_excel(request):
    src_loc_name = request.GET.get('src_loc', '')
    sheet = export_Q(src_loc_name)
    return excel.make_response(sheet, "xls", file_name="Q渠道无国内单号导出")


@api_view(['GET'])
@permission_classes([IsStaff])
def get_bdt_yunda_excel(request):
    query_params = request.query_params
    sheet = bdt_yundan_excel(query_params)
    return excel.make_response(sheet, "xls", file_name="八达通导出")


@api_view(['GET'])
@permission_classes([IsStaff])
def get_qd_ems_excel(request):
    query_params = request.query_params
    sheet = qd_ems_excel(query_params)
    return excel.make_response(sheet, "xls", file_name="青岛电商导出", sheet_name='Order')


@api_view(['POST'])
@permission_classes([IsStaff])
def update_cn_tracking_from_excel_view(request):
    if request.FILES['file']:
        try:
            cnt = update_cn_tracking_excel(request.FILES['file'], request.POST['channel_name'])
            return Response(data={"succ": True, "msg": "更新国内单号成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def change_cn_tracking_from_excel_view(request):
    if request.FILES['file']:
        try:
            cnt = change_cn_tracking_excel(request.FILES['file'], request.POST['channel_name'])
            return Response(data={"succ": True, "msg": "换单成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def change_channel_from_excel_view(request):
    if request.FILES['file'] and request.POST['channel_name']:
        try:
            cnt = change_channel_excel(request.FILES['file'], request.POST['channel_name'])
            return Response(data={"succ": True, "msg": "换渠道成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件并选择渠道", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def change_name_from_excel_view(request):
    if request.FILES['file']:
        try:
            cnt = change_name_excel(request.FILES['file'])
            return Response(data={"succ": True, "msg": "换姓名成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def waybills_time(request):
    msg = ""
    link = ""
    if (request.POST['dt_start'] and request.POST['dt_end']) or request.POST['air_waybill_no']:
        dt_end = request.POST['dt_end']
        dt_start = request.POST['dt_start']
        air_waybill_no = request.POST['air_waybill_no']
        q = Q()

        if dt_start:
            q.add(Q(create_dt__gte=toTZDatetime(dt_start)), Q.AND)
        if dt_end:
            q.add(Q(create_dt__lt=toTZDatetime(dt_end)), Q.AND)
        if air_waybill_no:
            q.add(Q(pallet__air_waybill__air_waybill_no__iexact=air_waybill_no), Q.AND)

        qs = Waybill.objects.filter(q)

        sheet = waybills_transist_excel(qs)
        sheet.save_as(settings.MEDIA_ROOT + "/time.xlsx")
        msg = '成功生成, 请下载'
        link = settings.MEDIA_URL + "time.xlsx"
    else:
        msg = "请提供时间范围或提单号"

    return Response(data={'msg': msg, "link": link}, content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def waybills_send_days(request):
    msg = ""
    link = ""
    if request.POST['dt_start']:
        dt_start = request.POST['dt_start']
        q = Q()

        if dt_start:
            q.add(Q(create_dt__gte=toTZDatetime(dt_start)), Q.AND)
            q.add(Q(create_dt__lt=toTZDatetime(dt_start) + timezone.timedelta(days=1)), Q.AND)
        q.add(Q(status__name=u'已发往集运仓'), Q.AND)
        qs = WaybillStatus.objects.filter(q).values('waybill__tracking_no', 'waybill__status__name', 'create_dt')

        sheet = waybills_send_days_excel(qs)
        sheet.save_as(settings.MEDIA_ROOT + "/send_days.xlsx")
        msg = '成功生成, 请下载'
        link = settings.MEDIA_URL + "send_days.xlsx"
    else:
        msg = "请提供时间范围"
    return Response(data={'msg': msg, "link": link}, content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def auto_create_view(request):
    try:
        cnt = auto_create()
        return Response(data={"succ": True, "msg": "获取面单成功", "succ_cnt": cnt, "total": cnt},
                        content_type="application/json")
    except Exception as e:
        return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def update_package_weight_from_excel_view(request):
    if request.FILES['file']:
        try:
            cnt = update_package_weight_from_excel(request.FILES['file'])
            return Response(data={"succ": True, "msg": "更新运单重量成功", "succ_cnt": cnt, "total": cnt},
                            content_type="application/json")
        except Exception as e:
            return Response(data={"succ": False, "msg": e.message, "succ_cnt": 0, "total": 0},
                            content_type="application/json")
    else:
        return Response(data={'succ': False, 'msg': "请提供excel文件", "succ_cnt": 0, "total": 0},
                        content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_bulk_print_view(request):
    '''
        input: list of waybill id
        output:
            succ_list: list of succ waybill obj
            fail_list: list of fail waybill obj
                the obj: {
                    id: 0,
                    tracking_no: ''
                    url:'' # emtpy if not able to print
                }
            url: the pdf file path of waybills
            action_msg: action result
            next: next item
            {
                pic_url: '',
                sku : ''
            }
    '''
    succ_list = []
    fail_list = []
    url = ''  # file for multiple waybill
    objs = []
    action_msg = u'操作正常'
    next = {"img_url": "", "sku": "", 'des': "", "list": [], "total_qty": 0}
    try:
        id_list = [int(a) for a in request.data.get("id_list", '').split(',') if a.strip() != '']
        shelf_no = request.data.get("shelf_no", '').strip()
        loc = request.data.get("loc", '').strip()
        in_no = request.data.get('in_no', '').strip()
        channel_name = request.data.get('channel_name', '').strip()
        dt = request.data.get('dt', '').strip()

        qs = Waybill.objects.filter(id__in=id_list).filter(status__name__in=[u'已建单', u'已传身份证']).exclude(
            channel__name__in=['Q']).distinct()

        m = {}
        for w in qs:
            m[w.id] = w

        for id in id_list:
            if id in m.keys():
                w = m[id]
                succ_list.append(
                    {"id": id, "tracking_no": w.tracking_no,
                     "url": reverse('customer_waybill_label', kwargs={"pk": w.id}),
                     'msg': u'成功出单'})
                objs.append(w.get_wrap_pdf())

                # change waybill status
                w.is_print_by_manage = True
                w.set_package_sent_to_center(request.user)
                w.save()
                # 通知wms出库
                try:
                    wms_order_send_out.delay(w.tracking_no, request.user.username)
                except:
                    pass
            else:
                w = Waybill.objects.get(id=id)
                msg = ""
                if w:
                    msg = u'状态: {0}, 不允许出单'.format(w.status.name)
                else:
                    msg = u'不存在该运单'
                fail_list.append({"id": id, "tracking_no": w.tracking_no, "url": "", "msg": msg})

            if len(succ_list) > 0:
                if len(succ_list) == 1:
                    url = reverse('customer_waybill_label', kwargs={"pk": succ_list[0]['id']})
                else:
                    url = multi_pdf_response(objs)
        if loc:
            qs = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(Q(src_loc__name=loc),
                                                                                   Q(goods_num=1),
                                                                                   Q(status__name__in=['已建单',
                                                                                                       '已传身份证'])).exclude(
                channel__name__in=['Q']).distinct()

            q = Waybill.get_able_to_print_query()

            if dt and toTZDatetime(dt):
                q.add(Q(upload_person_id_dt__lt=toTZDatetime(dt) + timezone.timedelta(days=1)), Q.AND)

            if channel_name:
                q.add(Q(channel__name=channel_name), Q.AND)

            if shelf_no:
                q.add(Q(shelf_no__iexact=shelf_no), Q.AND)

            if in_no:
                q.add(Q(in_no__istartswith=in_no), Q.AND)

            is_first = True
            last_sku = ''

            qs = qs.filter(q).distinct()

            goods_cnt_map = get_goods_cnt_map_helper(qs)

            for w in qs:
                g = w.goods.all().first()
                if g and last_sku != g.sku:
                    next['list'].append({'img_url': g.img_url, 'sku': g.sku, 'des': g.brand + " " + g.description,
                                         'total_qty': goods_cnt_map[g.sku]})
                    if is_first:
                        next['img_url'] = g.img_url
                        next["sku"] = g.sku
                        next['des'] = g.brand + " " + g.description
                        next['total_qty'] = goods_cnt_map[g.sku]
                        is_first = False
                    last_sku = g.sku

    except Exception as e:
        action_msg = u'服务器异常, {0}'.format(e.message)
    return Response({"succ_list": succ_list, "fail_list": fail_list, "url": url, "msg": action_msg, "next": next})


def get_goods_cnt_map_helper(qs):
    m = {}
    for w in qs:
        g = w.goods.all().first()
        if g and g.sku in m.keys():
            m[g.sku] += g.quantity
        else:
            m[g.sku] = g.quantity
    return m


@api_view(['POST'])
@permission_classes([IsAdmin])
def manage_waybill_batch_print_view(request):
    '''
        input: list of waybill id
        output:
            url for the list of id
    '''
    url = ''  # file for multiple waybill
    msg = ''
    id_list = [int(a) for a in request.data.get("id_list", '').split(',') if a.strip() != '']

    msg, url = batch_print_by_ids(msg, id_list, url)

    return Response({'url': url, 'msg': msg})


def batch_print_by_ids(msg, id_list, url):
    objs = []

    try:
        qs = Waybill.objects.filter(id__in=id_list).distinct()

        m = {}
        not_exist_list = []

        for w in qs:
            m[w.id] = w

        for id in id_list:
            if id not in m:
                not_exist_list.append(id)
            else:
                print type(m[id])
                objs.append(m[id].get_wrap_pdf())

        if qs.count() == 1:
            url = reverse('customer_waybill_label', kwargs={"pk": qs.first().id})
        elif qs.count > 1:
            url = multi_pdf_response(objs)
        else:
            msg = "无单号可打印"

        if len(not_exist_list) > 0:
            msg = ', '.join(not_exist_list) + " 运单id 不存在"
        else:
            msg = '批量打印 {0} 单'.format(qs.count())

    except Exception as e:
        msg = e.message
    return msg, url


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_batch_print_sku(request):
    url = ''
    msg = ''
    succ = False
    sku = request.data.get('sku', '').strip()
    qty = request.data.get('qty', '').strip()

    if not sku:
        msg = "必须填写sku"
        return Response({'url': url, 'msg': msg})

    quantity = None
    try:
        quantity = int(qty)
    except:
        pass

    if not quantity:
        msg = "必须填写每单个数"
        return Response({'url': url, 'msg': msg})

    src_loc_name = request.data.get('src_loc', '').strip()
    if not src_loc_name:
        msg = "必须选地点"
        return Response({'url': url, 'msg': msg})

    channel_name = request.data.get('channel', '').strip()
    if not channel_name:
        msg = "必须选渠道"
        return Response({'url': url, 'msg': msg})

    try:
        msg, succ, url = batch_print_sku(sku, src_loc_name, channel_name, request.user, quantity)
        return Response({'succ': succ, 'url': url, 'msg': msg})
    except Exception as e:
        return Response({'succ': succ, 'url': url, 'msg': e.message})


@api_view(['GET'])
@permission_classes([IsStaff])
def custom_data(request):
    succ = False
    tracking_nos = [x.strip() for x in request.query_params.get("multi_search", '').strip().split(',') if
                    x.strip() != '']
    channel_name = request.query_params.get("channel", '')
    qs = Waybill.objects.filter(Q(tracking_no__in=tracking_nos) | Q(cn_tracking__in=tracking_nos))
    if qs.count() == 0:
        return Response({'succ': succ, 'msg': '无单可导出'})
    else:
        sheet = overload_bc_excel(qs, channel_name)
        return excel.make_response(sheet, "xls", file_name="导出清关数据")


@transaction.atomic()
def batch_print_sku(sku, src_loc_name, channel_name, user, quantity):
    url = ''
    msg = ''
    succ = False
    q = Q()
    q.add(Q(goods__sku=sku), Q.AND)
    q.add(Q(src_loc__name=src_loc_name), Q.AND)
    q.add(Q(channel__name=channel_name), Q.AND)
    q.add(Q(goods_num=quantity), Q.AND)
    q.add(Q(is_print_by_manage=False), Q.AND)
    # 有身份证
    q.add(~Q(person_id__iexact=''), Q.AND)
    q.add(~Q(person_id__isnull=True), Q.AND)
    # 有国内单号
    q.add(~Q(cn_tracking__iexact=''), Q.AND)
    q.add(~Q(cn_tracking__isnull=True), Q.AND)

    # 状态
    sent_to_warhouse_status = WaybillStatusEntry.objects.get(name='已发往集运仓')
    q.add(Q(status__order_index__lt=sent_to_warhouse_status.order_index), Q.AND)

    if Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(q).exists():
        qs = Waybill.objects.annotate(goods_num=Sum('goods__quantity')).filter(q).order_by('id')
        objs = [w.get_wrap_pdf() for w in qs]
        url = multi_pdf_response(objs)
        for w in qs:
            w.is_print_by_manage = True
            w.set_package_sent_to_center(user)
            w.save()
            # print w.tracking_no
            # 通知wms出库
            try:
                wms_order_send_out.delay(w.tracking_no, user.username)
            except:
                pass
        msg = "成功"
        succ = True
    else:
        msg = '无单可打印'
    return msg, succ, url


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_exception_list_view(request):
    form = ExceptionRecordSearchForm(request.GET or None)
    per_page = 20
    # loc = Employee.objects.get(user=request.user).loc
    if form.is_valid():
        qs = form.addQuery()
    else:
        qs = ExceptionRecord.objects.all()

    table = ExceptionRecordTable(qs, order_by="-create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)
    total = qs.count()

    return render(request, 'manage/Exception_list.html',
                  {'table': table, 'total': total, 'form': form})


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_delete_exception_record(request, pk):
    record = ExceptionRecord.objects.filter(pk=pk)
    if record:
        record.delete()
        return Response({'succ': True, 'msg': '成功提交'})
    return Response({'succ': False, 'msg': '问题件单号不存在， 请查证后再提交'})


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_add_exception_record(request):
    tracking_no = request.data.get('tracking_no', '')
    remark = request.data.get('remark', '')
    value = request.data.get('value', 0)
    description = request.data.get('description', '')
    qty = request.data.get('qty', 0)
    area = request.data.get('area', '')
    type = request.data.get('type', '')

    if Waybill.objects.filter(Q(tracking_no__iexact=tracking_no) | Q(cn_tracking__iexact=tracking_no)).exists():
        w = Waybill.objects.filter(Q(tracking_no__iexact=tracking_no) | Q(cn_tracking__iexact=tracking_no)).first()
        if ExceptionRecord.objects.filter(waybill=w).exists():
            return Response({'succ': False, 'msg': '运单号已经提交过问题单， 不允许重复提交'})
        else:
            e = ExceptionRecord.objects.create(waybill=w, remark=remark, value=value, description=description, qty=qty,
                                               area=area, user=request.user, type=type)
            for f in request.FILES:
                ExceptionRecordImage.objects.create(record=e, image=request.FILES.get(f))
            return Response({'succ': True, 'msg': '成功提交'})
    else:
        return Response({'succ': False, 'msg': '运单号不存在， 请查证后再提交'})


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_get_exception_record_images(request):
    id = request.data.get('id', 0)
    images = ExceptionRecordImage.objects.filter(record__id=id)
    if len(images) > 0:
        return Response({'succ': True, 'msg': '请求成功', 'urls': [i.image.url for i in images]})
    else:
        return Response({'succ': False, 'msg': '没有图片'})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_waybill_send_to_warehouse_view(request):
    return render(request, 'manage/waybill_send_to_warehouse.html')


@api_view(['POST'])
@transaction.atomic()
@permission_classes([IsStaff])
def waybill_send_to_warehouse(request):
    tracking = request.data.get("tracking", '')
    if Waybill.objects.filter(Q(tracking_no=tracking) | Q(cn_tracking=tracking)).exists():
        w = Waybill.objects.select_for_update().filter(Q(tracking_no=tracking) | Q(cn_tracking=tracking)).first()
        serializer = WaybillDetailSerializer(w)
        if w.channel.name != 'Q':
            succ = False
            msg = '仅允许Q渠道这样操作'
        elif w.status.name in ['已建单', '已传身份证']:
            if w.cn_tracking and w.person_id:
                w.is_print_by_manage = True
                w.set_package_sent_to_center(request.user)
                w.save()
                msg = '成功'
                succ = True
                try:
                    wms_order_send_out.delay(w.tracking_no, request.user.username)
                except:
                    pass
            elif not w.cn_tracking:
                succ = False
                msg = "缺少国内单号"
            elif not w.person_id:
                succ = False
                msg = '缺少身份证号'
        else:
            succ = False
            if w.status.name == '运单异常':
                status_detail = WaybillStatus.objects.filter(waybill=w).filter(status=w.status).first()
                msg = '运单原状态:{0}, 备注信息:{1}; 如果不是拼单拦截, 而是退款, 请重新入库'.format(w.status.name,
                                                                          status_detail.remark if status_detail else '')
            else:
                status_detail = WaybillStatus.objects.filter(waybill=w).filter(status=w.status).first()
                msg = '运单原状态:{0}, 备注信息:{1}; 如果已经发往集运仓, 请勿重复扫描'.format(w.status.name,
                                                                      status_detail.remark if status_detail else '')
    else:
        succ = False
        w = None
        msg = '运单{0}不存在'.format(tracking)

    return Response({'succ': succ, 'w': serializer.data if w else w, 'msg': msg})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def package_time_view(request):
    # TODO
    return render(request, 'manage/package-time.html')


@api_view(['GET'])
@permission_classes([IsStaff])
def get_k_no_pid_excel(request):
    air_waybill = request.data.get('air_waybill', '')
    q = Q(Q(status__order_index__lte=109),
          Q(status__order_index__gte=1),
          Q(channel__name='K2'),
          Q(Q(people__isnull=True) | Q(people__id_card_front__isnull=True) | Q(people__id_card_front__exact='') | Q(
              people__status=3)))
    if air_waybill:
        q.add(Q(pallet__air_waybill__air_waybill_no=air_waybill), Q.AND)

    qs = Waybill.objects.filter(q).values('tracking_no', 'pallet__air_waybill__air_waybill_no', 'create_dt',
                                          'status__name').distinct().order_by('src_loc', 'tracking_no')
    title = ['运单号', '建单日期', '提单号', '状态']
    results = [title]
    for w in qs:
        r = []
        r.append(w['tracking_no'])
        r.append(w['create_dt'])
        r.append(w['pallet__air_waybill__air_waybill_no'])
        r.append(w['status__name'])
        results.append(r)
    sheet = excel.pe.Sheet(results)
    return excel.make_response(sheet, "xls", file_name="K渠道无身份证图片导出")
