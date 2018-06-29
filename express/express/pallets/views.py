# -*- coding: utf-8 -*
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, DecimalField
from django.http import HttpResponse, HttpResponseServerError
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django_tables2 import RequestConfig

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Employee
from emanage.permissions import staffCheck, IsStaff
from pallets.forms import PalletActionForm
from pallets.serializers import PalletSerializer
from rest_framework import permissions

from pallets.tasks import update_cn_tracking_by_air_waybill_no
from waybills.models import WaybillStatusEntry, Waybill, WaybillStatus
from waybills.permissions import IsOwnerOrReadOnly
from .models import *
from .tables import *
from .excels import *
from .forms import *
from addresses.utils import IdCardsZipper
import datetime


class PalletViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Pallet.objects.all()
    serializer_class = PalletSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsStaff,)

    def perform_create(self, serializer):
        serializer.save(create_user=self.request.user)


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_pallet_create_view(request):
    channels = Channel.objects.all()
    return render(request, "manage/pallet_create.html", {"channels": channels})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_pallet_create_view2(request):
    channels = Channel.objects.all()
    return render(request, "manage/pallet_create2.html", {"channels": channels})


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_waybill_package_to_pallet_view(request):
    '''
    code
    0 success
    1 not exist
    2 not valid to package to pallet
    3 already package to pallet
    4 channel not valid
    5 system error
    6 over limit per batch
    7 lux brand over limit
    8 lux brand
    '''
    data = request.data.get("tracking_no", '').strip()
    channel_id = request.data.get("channel_id", '')
    user = request.user
    force_add = request.data.get("force_add", False)

    code, id, goods_des = do_package_to_pallet(data, user, channel_id, force_add)
    return Response({"tracking_no": data, "code": code, "id": id, "goods_des": goods_des})


def do_package_to_pallet(tracking_no, user, channel_id, force_add):
    try:
        # 识别渠道
        ch = Channel.objects.get(id=channel_id)

        # 获取所在地
        employee = Employee.objects.get(user=user)
        loc = employee.loc
        status = WaybillStatusEntry.objects.get(name=u'打板中')  # 打板中 status

        if Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
            waybill = Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).first()
            if not waybill.channel or waybill.channel != ch:
                return 4, 0, ''

            if waybill.status.name == u"已审核":
                if force_add:
                    WaybillStatus.objects.create(waybill=waybill, status=status, location=loc, user=user)
                    return 0, waybill.id, ''
                elif waybill.is_lux_brand():
                    return 8, 0, waybill.get_goods_content_lux()
                elif waybill.is_lux_brand_over_limit():
                    return 7, 0, waybill.get_goods_content_lux()
                if waybill.is_over_limit_per_batch():
                    return 6, 0, waybill.get_goods_content_lux()
                else:
                    WaybillStatus.objects.create(waybill=waybill, status=status, location=loc, user=user)
                    return 0, waybill.id, ''
            elif waybill.status.name == u'打板中':
                return 3, 0, ''
            else:
                return 2, 0, ''
        else:
            return 1, 0, ''
    except Exception as e:
        return 5, 0, ''


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_waybill_package_to_pallet_view2(request):
    '''
    code
    0 success
    1 not exist
    2 not valid to package to pallet
    3 already package to pallet
    4 channel not valid
    5 system error
    6 over limit per batch
    7 lux brand over limit
    8 lux brand
    9 special
    10 not person_id
    11 same name
    '''
    data = request.data.get("tracking_no", '').strip()
    user = request.user
    force_add = request.data.get("force_add", False)

    code, id, goods_des, channel_id, channel_name, weight = do_package_to_pallet2(data, user, force_add)
    return Response({"waybill": {"tracking_no": data, "id": id, "channel_id": channel_id, "channel_name": channel_name,
                                 'weight': weight},
                     "code": code, "goods_des": goods_des})


def do_package_to_pallet2(tracking_no, user, force_add):
    try:
        # 获取所在地
        employee = Employee.objects.get(user=user)
        loc = employee.loc
        status = WaybillStatusEntry.objects.get(name=u'打板中')  # 打板中 status

        if Waybill.objects.filter(Q(tracking_no__iexact=tracking_no) | Q(cn_tracking__iexact=tracking_no)).exists():
            waybill = Waybill.objects.filter(
                Q(tracking_no__iexact=tracking_no) | Q(cn_tracking__iexact=tracking_no)).first()
            if not waybill.channel:
                return 4, 0, '', 0, '', 0

            if not waybill.person_id and waybill.channel.name in CH_LIST_REQUIRED_PERSON_ID:
                return 10, 0, '', waybill.channel.id, waybill.channel.name, waybill.weight

            if waybill.status.name == u"已审核":
                if force_add:
                    WaybillStatus.objects.create(waybill=waybill, status=status, location=loc, user=user)
                    return 0, waybill.id, '', waybill.channel.id, waybill.channel.name, waybill.weight
                # elif waybill.is_lux_brand():
                #     return 8, 0, waybill.get_goods_content_lux(),waybill.channel.id, waybill.channel.name, waybill.weight
                # elif waybill.is_lux_brand_over_limit():
                #     return 7, 0, waybill.get_goods_content_lux(),waybill.channel.id, waybill.channel.name, waybill.weight
                elif waybill.special_channel_check():
                    return 9, 0, waybill.get_goods_content_lux(), waybill.channel.id, waybill.channel.name, waybill.weight
                # elif waybill.is_over_limit_per_batch():
                #     return 6, 0, waybill.get_goods_content_lux(),waybill.channel.id, waybill.channel.name, waybill.weight
                elif waybill.is_k_over_limit_per_batch():
                    return 11, 0, waybill.recv_name, waybill.channel.id, waybill.channel.name, waybill.weight
                else:
                    WaybillStatus.objects.create(waybill=waybill, status=status, location=loc, user=user)
                    return 0, waybill.id, '', waybill.channel.id, waybill.channel.name, waybill.weight
            elif waybill.status.name == u'打板中':
                return 3, 0, '', waybill.channel.id, waybill.channel.name, waybill.weight
            else:
                return 2, 0, '', waybill.channel.id, waybill.channel.name, waybill.weight
        else:
            return 1, 0, '', 0, '', 0
    except Exception as e:
        return 5, 0, '', 0, '', 0


@api_view(['POST'])
@permission_classes([IsStaff])
def get_waybills_in_pallet_not_submit(request):  # 获取操作员上次打板还没提交的数据
    waybills = [status.get_pallet_waybill_format() for status in
                WaybillStatus.objects.filter(status__name="打板中")
                    .filter(waybill__status__name="打板中")
                    .filter(user=request.user)]
    data = {}
    data["code"] = 0 if len(waybills) > 0 else 1
    data["waybills"] = waybills
    return Response(data, content_type="application/json")


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_pallet_create(request):
    '''
       code
       0 success
       1 waybill id list not valid
       2 system error
       3 tracking_list empty
       '''
    try:
        track_id_list = [int(x) for x in request.data.get("track_id_list_str").split(u',') if x.strip()]
        p_w = request.data.get('pallet_weight', '').strip()
        pallet_weight = Decimal(p_w) if p_w != '' else 0
        user = request.user
        code, pallet_no, error_tracking_no_list, msg = create_pallet(track_id_list, user, pallet_weight)
        return Response(
            {"code": code, "pallet_no": pallet_no, "error_tracking_no_list": error_tracking_no_list, "msg": msg})
    except:
        return Response({"code": 2, "pallet_no": '', "error_tracking_no_list": ''})


def create_pallet(track_id_list, user, pallet_weight):
    if len(track_id_list) == 0:
        return 3, '', [], u'运单列表为空'
    employee = Employee.objects.get(user=user)
    loc = employee.loc
    shortname = loc.short_name
    pallet = None
    try:
        if Waybill.objects.filter(id__in=track_id_list).filter(pallet__isnull=False).exists():
            return 1, '', [x['tracking_no'] for x in
                           Waybill.objects.filter(id__in=track_id_list).filter(pallet__isnull=False).values(
                               "tracking_no")], u'部分运单已经有托盘, 请刷新打板页面后重试'

        else:
            pallet = Pallet.objects.create(pallet_no=Pallet.get_next_pallet_no(shortname), user=user,
                                           weight=0)
            statusEntry = WaybillStatusEntry.objects.get(name=u'已打板')
            pallet_weight_cal = 0
            for id in track_id_list:
                waybill = Waybill.objects.get(id=id)
                waybill.pallet = pallet
                pallet_weight_cal += waybill.weight
                waybill.save()
                WaybillStatus.objects.create(waybill=waybill, status=statusEntry, user=user, location=loc)
            pallet.weight = pallet_weight_cal if pallet_weight <= 0 else pallet_weight
            pallet.channel = waybill.channel
            pallet.save()
            if pallet_weight > 0:
                average_pallet_weight(pallet, pallet_weight, pallet_weight_cal)
            return 0, pallet.pallet_no, [], u'成功生成托盘, 共计%s单' % len(track_id_list)

    except Exception as e:
        if pallet is not None:
            pallet.delete()
        return 2, '', [], u'系统异常'


def average_pallet_weight(pallet, pallet_weight, pallet_weight_cal):
    if pallet_weight > 0 and pallet_weight_cal > 0:
        diff = pallet_weight - pallet_weight_cal
        for w in pallet.waybills.all():
            new_weight = w.weight / pallet_weight_cal * diff + w.weight
            if new_weight > 0:
                w.weight = new_weight
                w.save()


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_waybill_pallet_delete(request, pk):
    '''
       code
       0 success
       1 not exist
       2 system error
       '''
    user = request.user
    code, msg = waybill_pallet_delete(pk, user)
    return Response({"code": code, "msg": msg})


def waybill_pallet_delete(pk, user):
    try:
        if WaybillStatus.objects.filter(waybill__id=pk).filter(user=user).filter(status__name='打板中').exists():
            WaybillStatus.objects.filter(waybill__id=pk).filter(user=user).filter(
                status__name='打板中').first().delete()
            return 0, '成功'
        else:
            return 1, '要删除的运单不存在'
    except Exception as e:
        return 2, '服务器错误: ' + e.message


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def manage_pallets_view(request):
    qs = Pallet.objects.all()
    form = PalletSearchForm(request.GET or None)
    if form.is_valid():
        qs = form.addQuery(qs)
    per_page = 100
    table = PalletTable(qs, order_by="-create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)

    # form_action = PalletActionForm();
    return render(request, 'manage/pallet_list.html', {'table': table, 'form': form, 'channels': Channel.objects.all()})


@login_required(login_url='/manage/login/')
@user_passes_test(staffCheck, login_url='/')
def air_waybills_view(request):
    qs = AirWaybill.objects.all()
    form = AirWaybillSearchForm(request.GET or None)
    action_form = AirWaybillActionForm(request.GET or None)
    per_page = 20

    if form.is_valid():
        qs = form.addQuery(qs)

    table = AirWaybillTable(qs, order_by="-create_dt", template='table.html')
    RequestConfig(request).configure(table)
    RequestConfig(request, paginate={'per_page': per_page}).configure(table)

    return render(request, 'manage/air_waybill_list.html', {'table': table, 'form': form, 'action_form': action_form})


@api_view(['POST'])
@permission_classes([IsStaff])
def manage_air_waybill_create(request):
    '''
       code
       0 success
       1 invalid pallets
       2 system error
    '''
    pallet_nos = [a for a in request.data.get('pallets', '').split(',')]
    air_waybill_no = request.data.get("air_waybill_no", '').strip()
    channel_id = int(request.data.get('channel_id', '0'))
    code, msg = create_air_waybill(request, pallet_nos, air_waybill_no, channel_id)

    return Response({"code": code, "msg": msg})


def create_air_waybill(request, pallet_nos, air_waybill_no, channel_id):
    code = 0
    msg = ""
    pallets = []
    air_waybill = None
    status_list = []
    for pallet_no in pallet_nos:
        pallet = Pallet.objects.get(pallet_no=pallet_no)
        if not pallet:
            code = 1
            msg += pallet_no + u" 不存在"
            return code, msg
        elif pallet.air_waybill:
            code = 1
            msg += pallet_no + u" 已发出, 已经存在对应提单"
            return code, msg
        elif channel_id != pallet.channel.id:
            code = 1
            msg += pallet_no + u"托盘渠道为: {0}, 与所选渠道不同, 请选择正确的渠道和托盘".format(pallet.channel.name, )
            return code, msg
        else:
            pallets.append(pallet)
    try:
        user = request.user
        e = Employee.objects.get(user=user)
        loc = e.loc
        air_waybill = AirWaybill.get_next_auto_air_waybill(e, air_waybill_no, channel_id)

        for pallet in pallets:
            pallet.air_waybill = air_waybill
            pallet.save()
            # 运单状态变为等待航空公司取货
            for waybill in pallet.waybills.all():
                status = WaybillStatusEntry.objects.get(name=u'待航空公司取货')
                s = WaybillStatus.objects.create(user=user, waybill=waybill, status=status, location=loc)
                status_list.append(s)

    except Exception as e:
        if air_waybill:
            air_waybill.delete()
            for s in status_list:
                s.delete()
        code = 2
        msg = "系统错误, 创建失败" if not settings.DEBUG else e.message

    return code, msg


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_customs_files(request, pk):
    air_waybill = AirWaybill.objects.get(pk=pk)
    sheet = bc_excel(air_waybill)
    return excel.make_response(sheet, "xls", file_name="电商")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_customs_files2(request):
    waybills = Waybill.objects.filter(pallet__pallet_no__istartswith='MNJ170312').filter(
        pallet__pallet_no__lte='MNJ170312020')
    result = bc_data("", waybills)
    sheet = excel.pe.Sheet(result)
    return excel.make_response(sheet, "xls")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_customs_goods(request):
    sheet = bc_goods_excel()
    return excel.make_response(sheet, "xls", file_name="电商-商品")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_agent_files(request, pk):
    air_waybill = AirWaybill.objects.get(pk=pk)
    book = agent_excel(air_waybill)
    return excel.make_response(book, "xls", file_name="货代")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_usps_files(request, pk):
    air_waybill = AirWaybill.objects.get(pk=pk)
    sheet = usps_excel(air_waybill)
    return excel.make_response(sheet, "xls", file_name="usps")


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_id_cards_files(request, pk):
    zip_handler = IdCardsZipper(air_waybill_id=pk)
    with zip_handler:
        zip_file = zip_handler.zip_file
        if zip_file is None:
            return HttpResponseServerError(u'下载文件出错: {}'.format(zip_handler.exception.message))
        with open(zip_file, 'rb') as f:
            response = HttpResponse(f, content_type="application/zip")
            response['Content-Disposition'] = u'inline; filename=' + zip_handler.zip_file_name
            return response


@api_view(['GET'])
@permission_classes([IsStaff])
def manage_both_tracking_files(request, pk):
    air_waybill = AirWaybill.objects.get(pk=pk)
    sheet = both_tracking_excel(air_waybill)
    return excel.make_response(sheet, "xls", file_name="双边单号")


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_air_waybill_send_out(request, pk):
    '''
    :param request:
    :param pk:
    :return:
    code:
    0 success
    1 air_waybill already send out
    2 air_waybill not exist
    '''
    code = 1
    air_waybill = AirWaybill.objects.get(id=pk)
    send_out_time_str = request.data.get('send_out_time', '')
    if send_out_time_str:
        send_out_time = toTZDatetime(send_out_time_str, '%m-%d-%Y %H:%M', 'America/New_York')
    else:
        send_out_time = timezone.now()

    if air_waybill:
        if air_waybill.status >= 2:
            code = 1
        else:
            user = request.user
            employee = Employee.objects.get(user=user)
            loc = employee.loc
            status_send_out = WaybillStatusEntry.objects.get(name="已出库, 送往机场")
            status_wait_airline = WaybillStatusEntry.objects.get(name="等待航班起飞")

            wait_airline_time = send_out_time + timezone.timedelta(hours=3, minutes=random.randint(1, 60))

            for pallet in air_waybill.pallets.all():
                for waybill in pallet.waybills.all():
                    if waybill.status.name == u'待航空公司取货':
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill, status=status_send_out,
                                                     create_dt=send_out_time)
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill,
                                                     status=status_wait_airline, create_dt=wait_airline_time)
            air_waybill.is_send_out = True
            air_waybill.status = 2
            air_waybill.save()
            code = 0
    else:
        code = 2

    return Response({"code": code})


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_air_waybill_update_airline(request, pk):
    '''完成提单航空起降时间更新'''
    code = 1
    air_waybill = AirWaybill.objects.get(id=pk)
    take_off_time = toTZDatetime(request.data.get('take_off_time'), '%m-%d-%Y %H:%M', 'America/New_York')
    arrive_time = toTZDatetime(request.data.get('arrive_time'), '%m-%d-%Y %H:%M', 'Asia/Shanghai')
    custom_time = arrive_time + timezone.timedelta(hours=6, minutes=random.randint(1, 60))

    if air_waybill:
        if air_waybill.status != 2:
            code = 1
            msg = u'提单状态有误, 只有已出库提单可以执行操作'
        else:
            user = request.user
            employee = Employee.objects.get(user=user)
            loc = employee.loc
            status_take_off = WaybillStatusEntry.objects.get(name="航班起飞")
            status_arrive = WaybillStatusEntry.objects.get(name="航班到港")
            status_custom = WaybillStatusEntry.objects.get(name='国内清关')

            update_cnt = 0
            create_cnt = 0
            for pallet in air_waybill.pallets.all():
                for waybill in pallet.waybills.all():
                    if waybill.status.name == u'等待航班起飞':
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill, status=status_take_off,
                                                     create_dt=take_off_time)
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill,
                                                     status=status_arrive, create_dt=arrive_time)
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill,
                                                     status=status_custom, create_dt=custom_time)
                        create_cnt += 1
                    else:
                        if waybill.status_set.filter(status__name__in=['航班起飞', '航班到港', '国内清关']).exists():
                            update_cnt += 1
                            for st in waybill.status_set.filter(status__name__in=['航班起飞', '航班到港', '国内清关']):
                                if st.status.name == u'航班起飞':
                                    st.create_dt = take_off_time
                                elif st.status.name == u'航班到港':
                                    st.create_dt = arrive_time
                                elif st.status.name == u'国内清关':
                                    st.create_dt = custom_time
                                st.save()
            code = 0
            msg = u'操作无误, 更新: %d 单, 新建: %d 单' % (update_cnt, create_cnt)
    else:
        code = 2
        msg = u'提单不存在'

    return Response({"code": code, 'msg': msg})


@api_view(['POST'])
@permission_classes([IsStaff])
@transaction.atomic()
def manage_air_waybill_cn_deliver(request, pk):
    '''
    :param request:
    :param pk:
    :return:
    code
    0 success
    1 status not correct
    2 waybill not exist
    '''
    code = 1
    air_waybill = AirWaybill.objects.get(id=pk)
    cn_deliver_time_str = request.data.get('cn_deliver_time', '')
    if cn_deliver_time_str:
        cn_deliver_time = toTZDatetime(cn_deliver_time_str, '%m-%d-%Y %H:%M', 'Asia/Shanghai')
    else:
        cn_deliver_time = timezone.now()

    if air_waybill:
        if air_waybill.status == 2:
            user = request.user
            loc = Location.objects.get(name='国内在途')
            finish_custom = WaybillStatusEntry.objects.get(name="清关完毕")
            status_cn_deliver = WaybillStatusEntry.objects.get(name="国内派送")

            for pallet in air_waybill.pallets.all():
                for waybill in pallet.waybills.all():
                    if waybill.cn_tracking and waybill.status.name == u'国内清关':
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill, status=finish_custom,
                                                     create_dt=cn_deliver_time)
                        WaybillStatus.objects.create(user=user, location=loc, waybill=waybill, status=status_cn_deliver,
                                                     create_dt=cn_deliver_time)
            air_waybill.status = 3
            air_waybill.save()
            try:
                update_cn_tracking_by_air_waybill_no.delay(air_waybill.air_waybill_no)
            except:
                pass
            code = 0
        else:
            code = 1
    else:
        code = 2
    return Response({"code": code})


@api_view(['POST'])
@permission_classes([IsStaff])
def air_waybill_fee_excel_view(request):
    msg = ""
    link = ""
    dt_start = request.data.get('dt_start', None)
    dt_start = None if dt_start == None or dt_start == '' else toTZDatetime(dt_start)
    dt_end = request.data.get('dt_end', None)
    dt_end = timezone.now() if dt_end == None or dt_end == '' else toTZDatetime(dt_end)
    channel_id = request.data.get('channel_id', '')
    status_id = int(request.data.get('status_id', 0))
    air_waybill_no = request.data.get('air_waybill_no', '')

    if dt_start and dt_end and dt_end - dt_start <= timezone.timedelta(days=31):
        q = Q()

        q.add(Q(pallet__air_waybill__create_dt__gte=dt_start), Q.AND)
        q.add(Q(pallet__air_waybill__create_dt__lte=dt_end), Q.AND)

        if channel_id:
            q.add(Q(channel__id=channel_id), Q.AND)

        if status_id:
            q.add(Q(status=status_id), Q.AND)

        if air_waybill_no:
            q.add(Q(pallet__air_waybill__air_waybill_no=air_waybill_no), Q.AND)

        qs = Waybill.objects.filter(q).values('tracking_no', 'cn_tracking', 'weight', 'channel__name',
                                              'pallet__air_waybill__air_waybill_no').annotate(
            price=Sum(F('goods__unit_price') * F('goods__quantity'), output_field=DecimalField()))

        sheet = air_waybill_fee_excel(qs)
        sheet.save_as(settings.MEDIA_ROOT + "/air_waybll_yunfei_list.xlsx")
        msg = '成功生成, 共计%s单, 请下载' % qs.count()
        link = settings.MEDIA_URL + "air_waybll_yunfei_list.xlsx"
    else:
        msg = "请提供时间范围, 且跨度小于31天"
    return Response(data={'msg': msg, "link": link}, content_type="application/json")
