# -*- coding: utf-8 -*
from __future__ import unicode_literals
from decimal import Decimal

import django_excel as excel
from django.db import transaction

from express.utils import *
from pallets.models import *
from waybills.models import *
from django.db.models import Q, Min
from django.utils.encoding import smart_unicode
from django.conf import settings
from xlwt import *


def waybill_excel_address_info(params):
    qs = get_waybills_from_query(params)
    columnNames = [u'国际单号', u'国内单号', u'收件人', u'收件人手机', u'省', u'市', u'区', u'地址', u'邮编']
    result = [columnNames]
    for waybill in qs:
        r = []
        r.append(waybill.tracking_no)
        r.append(waybill.cn_tracking)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_province)
        r.append(waybill.recv_city)
        r.append(waybill.recv_area)
        r.append(waybill.recv_address)
        r.append(waybill.recv_zipcode)
        result.append(r)
    sheet = excel.pe.Sheet(result)
    return sheet


def waybill_excel(params, loc):
    qs = get_waybills_from_query(params, loc)

    columnNames = [u'国际单号', u'国内单号', u'省', u'地点', u'渠道', u'状态', u'状态时间', u'有无身份证', u'建单批次', u'货架号',
                   u'收件人', u'收件人手机', u'重量', u'托盘', u'生成日期',
                   u'商品条码1', u'商品品牌1', u'类别1', u'商品描述1', u'商品件数1', u'单价(美金)',
                   u'商品条码2', u'商品品牌2', u'类别2', u'商品描述2', u'商品件数2', u'单价(美金)',
                   u'商品条码3', u'商品品牌3', u'类别3', u'商品描述3', u'商品件数3', u'单价(美金)']
    result = [columnNames]
    for waybill in qs:
        r = []
        r.append(waybill.tracking_no)
        r.append(waybill.cn_tracking)
        r.append(waybill.recv_province)
        r.append(waybill.src_loc.name)
        r.append(waybill.channel.name)
        r.append(waybill.status.name)
        r.append(waybill.get_most_recent_status().create_dt.strftime("%Y-%m-%d"))
        r.append(u'有' if waybill.person_id else u'无')
        r.append(waybill.in_no)
        r.append(waybill.shelf_no)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append("%.2f" % waybill.weight)
        r.append(waybill.pallet.pallet_no if waybill.pallet else '-')
        r.append(waybill.create_dt.strftime("%Y-%m-%d"))
        for g in waybill.goods.all():
            r.append(g.sku)
            r.append(g.brand)
            r.append(g.hs_type)
            r.append(g.description)
            r.append(g.quantity)
            r.append("%.2f" % g.unit_price)
        result.append(r)

    sheet = excel.pe.Sheet(result)
    return sheet


def add_time_helper(obj):
    if not obj:
        return ''

    if isinstance(obj, WaybillStatus):
        return obj.create_dt.astimezone(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d") if obj else ''
    elif isinstance(obj, datetime):
        return obj.astimezone(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d") if obj else ''
    else:
        return ''


def waybills_transist_excel(qs):
    columnNames = [u'国际单号', u'国内单号', u'提单号', u'建单时间', u'上传身份证时间', u'入库时间', u'审核时间', u'航班起飞时间',
                   u'国内派送时间', u'完成时间']
    result = [columnNames]
    for w in qs:
        status_set = w.status_set.filter(status__name__in=['已建单', '已入库', '已审核', '航班起飞', '国内派送', '已完成'])
        st_map = {}
        for st in status_set:
            st_map[st.status.name] = st.create_dt

        r = []
        r.append(w.tracking_no)
        r.append(w.cn_tracking)

        if w.pallet and w.pallet.air_waybill:
            r.append(w.pallet.air_waybill.air_waybill_no)
        else:
            r.append('')

        r.append(add_time_helper(st_map.get(u'已建单', '')))
        r.append(add_time_helper(w.upload_person_id_dt))
        r.append(add_time_helper(st_map.get(u'已入库', '')))
        r.append(add_time_helper(st_map.get(u'已审核', '')))
        r.append(add_time_helper(st_map.get(u'航班起飞', '')))
        r.append(add_time_helper(st_map.get(u'国内派送', '')))
        r.append(add_time_helper(st_map.get(u'已完成', '')))
        result.append(r)

    sheet = excel.pe.Sheet(result)
    return sheet


def waybills_send_days_excel(qs):
    cn_tz = pytz.timezone('Asia/Shanghai')
    columnNames = [u'国际单号', u'当前状态', u'发货时间']
    result = [columnNames]
    for o in qs:
        r = []
        r.append(o['waybill__tracking_no'])
        r.append(o['waybill__status__name'])
        r.append(o['create_dt'].astimezone(cn_tz).strftime("%Y-%m-%d %H:%M:%S"))
        result.append(r)
    sheet = excel.pe.Sheet(result)
    return sheet


def get_waybills_from_query(params, loc):
    search = params.get("search", '').strip()
    status_order_index = params.get("status_order_index", '').strip()
    src_loc = params.get("src_loc", '').strip()
    channel = params.get("channel", '')
    dt_start = params.get("dt_start", '').strip()
    dt_end = params.get("dt_end", '').strip()
    multi_search = params.get("multi_search", '').strip()
    has_person_id = params.get("has_person_id", '').strip()
    has_cn_tracking = params.get("has_cn_tracking", '').strip()
    in_no = params.get("in_no", '').strip()
    status_dt_start = params.get("status_dt_start", '').strip()
    status_dt_end = params.get("status_dt_end", '').strip()
    qty = params.get("qty", '').strip()

    return Waybill.query_filter(channel, dt_end, dt_start, has_cn_tracking, has_person_id, in_no, loc,
                                multi_search, qty, search, src_loc, status_dt_end, status_dt_start,
                                status_order_index)


def gen_cn_status_excel(f):
    sheet = f.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['tracking_no', 'company_name', 'cn_tracking']
    export_colnames = ['运单号', '快递公司', '国内单号', '状态']
    export_result = [export_colnames]
    i = 0
    total = sheet.number_of_rows()
    for x in sheet.to_records():
        tracking_no = str(x.get('tracking_no', '')).strip()
        company_name = x.get('company_name', '').strip()
        cn_tracking = str(x.get('cn_tracking', '')).strip()
        result = u''
        if cn_tracking:
            result = smart_unicode(check_waybill_cn_status(cn_tracking))
        r = []
        r.append(tracking_no)
        r.append(company_name)
        r.append(cn_tracking)
        r.append(result)
        export_result.append(r)

        i += 1
        sys.stdout.write("\r%d/%d" % (i, total))
        sys.stdout.flush()
    wb = Workbook(encoding='utf-8')
    ws = wb.add_sheet('sheet1')
    i = 0
    for row in export_result:
        j = 0
        for item in row:
            ws.write(i, j, export_result[i][j])
            j += 1
        i += 1
    wb.save(settings.MEDIA_ROOT + "/xls/x.xls")
    return settings.MEDIA_URL + "xls/x.xls"


@transaction.atomic()
def add_yunda_from_excel(filehandle):
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['index', 'yunda']
    cnt = 0
    for x in sheet.to_records():
        tracking_no = str(x.get('yunda', '')).strip()
        if tracking_no:
            QFTracking.objects.create(tracking_no=tracking_no)
            cnt += 1
    return cnt


def vriual_yundan_excel(query_params):
    in_no = query_params.get("search", '').strip()
    q = Q()
    if in_no:
        q.add(Q(in_no=in_no), Q.AND)
    else:
        raise Exception('无建单批次号')

    qs = Waybill.objects.filter(q).order_by('tracking_no')

    columnNames = [u'虚拟单号', u'省', u'市', u'区', u'地址', u'收件人', u'收件人手机', u'内容物品名', u'內物件数', u'重量(kg)']
    result = [columnNames]
    for waybill in qs:
        virtual_no = to_virtual_waybill_no(waybill.tracking_no)

        if waybill.cn_tracking:
            raise Exception('有国内单号')
        elif virtual_no == '':
            raise Exception('国际单号有误')

        r = []
        r.append(virtual_no)
        r.append(waybill.recv_province)
        r.append(waybill.recv_city)
        r.append(waybill.recv_area)
        r.append(waybill.recv_address)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.get_goods_content())
        r.append(waybill.get_goods_quantity())
        r.append("%.2f" % (waybill.get_goods_weight() * Decimal(0.453592)))

        result.append(r)

    sheet = excel.pe.Sheet(result)
    return sheet


def to_virtual_waybill_no(tracking_no):
    m = {
        "HH": "620",
        "HC": "621",
        "HF": "622"
    }

    if tracking_no.startswith('HH'):
        return tracking_no.replace('HH', m["HH"])
    elif tracking_no.startswith('HC'):
        return tracking_no.replace('HC', m["HC"])
    elif tracking_no.startswith('HF'):
        return tracking_no.replace('HF', m["HF"])
    else:
        return ""


def to_tracking_no(vitual_no):
    m = {
        "620": "HH",
        "621": "HC",
        "622": "HF"
    }
    if vitual_no.startswith('620'):
        return vitual_no.replace('620', m["620"], 1)
    elif vitual_no.startswith('621'):
        return vitual_no.replace('621', m["621"], 1)
    elif vitual_no.startswith('622'):
        return vitual_no.replace('622', m["622"], 1)
    else:
        return ""


@transaction.atomic()
def update_virtual_yunda_excel(filehandle):
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['virtual_no', 'yunda']
    cnt = 0
    for x in sheet.to_records():
        a = str(x.get('virtual_no', '')).strip()
        tracking_no = to_tracking_no(a)
        cn_tracking = str(x.get('yunda', '')).strip()

        if tracking_no and Waybill.objects.filter(tracking_no=tracking_no).exists():
            w = Waybill.objects.get(tracking_no=tracking_no)
            QFTracking.objects.create(tracking_no=cn_tracking, waybill=w, is_used=True)
            w.cn_tracking = cn_tracking
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 虚拟单号不存在对应运单,请更正后重新上传".format(x.get('virtual_no', '')).strip())
    return cnt


def bdt_yundan_excel(query_params):
    in_no = query_params.get("search", '').strip()
    q = Q()
    if in_no:
        q.add(Q(in_no=in_no), Q.AND)
    else:
        raise Exception('无建单批次号')
    q.add(Q(channel=Channel.objects.get(name=CH4)), Q.AND)
    qs = Waybill.objects.filter(q).order_by('tracking_no')

    columnNames = [u'序号', u'交货时间(文本格式)', u'运单号', u'寄件人', u'寄件人地址', u'寄件人电话', u'收件人', u'收件人地址', u'收件人电话', u'计费重量(磅)',
                   u'实际重量(磅)', u'数量(个)', u'运费(USD)', u'保价金额(USD)', u'保额(USD)', u'品名', u'品牌', u'总申报价值(USD)', u'渠道']

    result = [columnNames]
    i = 1
    for waybill in qs:
        r = []
        r.append(i)
        r.append(datetime.today().strftime('%Y-%m-%d'))
        r.append(waybill.tracking_no)
        r.append('Darren Zhang')
        r.append('US')
        r.append("805-868-1682")
        r.append(waybill.recv_name)
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)
        r.append(waybill.recv_mobile)
        r.append("%.2f" % waybill.weight)
        r.append("%.2f" % waybill.weight)
        r.append(waybill.get_goods_quantity())
        r.append('')
        r.append('')
        r.append('')
        r.append(waybill.get_goods_content_bdt())
        r.append(waybill.person_id)
        r.append(waybill.get_declare_value_bdt())
        r.append('standard')
        result.append(r)
        i += 1

    sheet = excel.pe.Sheet(result)
    return sheet


def qd_ems_excel(query_params):
    in_no = query_params.get("search", '').strip()
    q = Q()
    if in_no:
        q.add(Q(in_no=in_no), Q.AND)
    else:
        raise Exception('无建单批次号')
    q.add(Q(channel=Channel.objects.get(name=CH6)), Q.AND)
    qs = Waybill.objects.filter(q).order_by('tracking_no')

    columnNames = [u'订单号', u'发件人姓名', u'发件人地址', u'收件人姓名', u'收件人手机', u'收件人所在省', u'收件人所在市', u'收件人所在区', u'收件人地址', u'快递单号',
                   u'重量', u'数量', u'备注']

    result = [columnNames]
    i = 1
    for waybill in qs:
        r = []
        r.append(waybill.tracking_no)
        r.append('HuskyEx')
        r.append('877 Glendale Ave, Edison, NJ')
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_province)
        r.append(waybill.recv_city)
        r.append(waybill.recv_area)
        r.append(waybill.recv_address)
        r.append('')
        r.append("%.2f" % (waybill.weight * Decimal('0.45359')))
        r.append(1)
        r.append('')
        result.append(r)
        i += 1

    sheet = excel.pe.Sheet(result)
    return sheet


@transaction.atomic()
def update_cn_tracking_excel(filehandle, channel_name):
    # 输入: 国际单号和国内单号
    c = None
    if channel_name:
        c = Channel.objects.get(name=channel_name)

    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['tracking_no', 'ems']
    cnt = 0
    # 处理重复行
    tracking_map = {}
    for x in sheet.to_records():
        tracking_no = str(x.get('tracking_no', '')).strip().upper()
        cn_tracking = str(x.get('ems', '')).strip().upper()
        tracking_map[tracking_no] = cn_tracking

    for tracking_no in tracking_map:
        cn_tracking = tracking_map[tracking_no]
        if tracking_no and Waybill.objects.filter(tracking_no=tracking_no).exists():
            w = Waybill.objects.get(tracking_no=tracking_no)
            QFTracking.objects.create(tracking_no=cn_tracking, waybill=w, is_used=True)
            w.cn_tracking = cn_tracking
            if c:
                w.channel = c
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 单号不存在对应运单,请更正后重新上传".format(x.get('tracking_no', '')).strip())
    return cnt


@transaction.atomic()
def change_cn_tracking_excel(filehandle, channel_name):
    # 输入: 原国内单号,  新国内单号
    c = None
    if channel_name:
        c = Channel.objects.get(name=channel_name)

    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['pre_cn_tracking', 'new_cn_tracking']
    cnt = 0
    i = 2
    for x in sheet.to_records():
        pre_cn_tracking = str(x.get('pre_cn_tracking', '')).strip().upper()
        new_cn_tracking = str(x.get('new_cn_tracking', '')).strip().upper()

        if not new_cn_tracking or not pre_cn_tracking:
            raise Exception(u"第{0}行 数据有误, 第一列必须是原国内单号, 第二列必须是新单号".format(i))
        if pre_cn_tracking and Waybill.objects.filter(cn_tracking=pre_cn_tracking).exists():
            w = Waybill.objects.get(cn_tracking=pre_cn_tracking)

            if QFTracking.objects.filter(tracking_no=pre_cn_tracking).exists():
                old_qf = QFTracking.objects.get(tracking_no=pre_cn_tracking)
                old_qf.delete()

            QFTracking.objects.create(tracking_no=new_cn_tracking, waybill=w, is_used=True)
            w.third_party_tracking_no = w.cn_tracking
            w.cn_tracking = new_cn_tracking
            if c:
                w.channel = c
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 单号不存在对应运单,请更正后重新上传".format(x.get('pre_cn_tracking', '')).strip())
    return cnt


@transaction.atomic()
def change_channel_excel(filehandle, channel_name):
    # 输入: 国际单号及渠道
    c = Channel.objects.get(name=channel_name)

    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['us_tracking']
    cnt = 0
    for x in sheet.to_records():
        us_tracking = str(x.get('us_tracking', '')).strip().upper()

        if us_tracking and Waybill.objects.filter(tracking_no=us_tracking).exists():
            w = Waybill.objects.get(tracking_no=us_tracking)
            if w.cn_tracking:
                raise Exception(u"{0} 已经有国内单号, 不允许更换渠道".format(x.get('us_tracking', '')).strip())
            w.channel = c
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 单号不存在对应运单,请更正后重新上传".format(x.get('us_tracking', '')).strip())
    return cnt


@transaction.atomic()
def change_name_excel(filehandle):
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['tracking', 'name']
    cnt = 0
    for x in sheet.to_records():
        tracking = x.get('tracking', '').strip().upper()
        name = x.get('name', '').strip().upper()
        if not name:
            raise Exception(u"{0} 对应行姓名不存在".format(tracking))

        if tracking and Waybill.objects.filter(Q(tracking_no=tracking) | Q(cn_tracking=tracking)).exists():
            w = Waybill.objects.get(Q(tracking_no=tracking) | Q(cn_tracking=tracking))
            w.recv_name = name
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 单号不存在".format(x.get('tracking', '')).strip())
    return cnt


@transaction.atomic()
def update_package_weight_from_excel(filehandle):
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['tracking_no', 'weight']
    cnt = 0
    for x in sheet.to_records():
        tracking_no = str(x.get('tracking_no', '')).strip().upper()
        weight = Decimal(x.get('weight', 0))

        if weight <= 0:
            raise Exception(u"{0} 运单重量必须大于0".format(x.get('tracking_no', '')).strip())
        elif tracking_no and Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).exists():
            w = Waybill.objects.filter(Q(tracking_no=tracking_no) | Q(cn_tracking=tracking_no)).first()
            w.weight = weight
            w.save()
            cnt += 1
        else:
            raise Exception(u"{0} 单号不存在对应运单,请更正后重新上传".format(x.get('tracking_no', '')).strip())
    return cnt


def export_Q():
    qs = Waybill.objects.filter(Q(channel__name='Q'), Q(status__name__in=['已建单', '已传身份证']), Q(cn_tracking__isnull=True),
                                Q(person_id__isnull=False)).exclude(person_id__iexact='').order_by('shelf_no')
    results = []
    title = [u'业务单号', u'收件人姓名', u'收件人手机', u'收件省', u'收件市', u'收件区/县', u'收件人地址', u'品名', u'数量', u'备注']
    results.append(title)
    for w in qs:
        r = []
        r.append(w.tracking_no)
        r.append(w.recv_name)
        r.append(w.recv_mobile)
        r.append(w.recv_province)
        r.append(w.recv_city)
        r.append(w.recv_area)
        r.append(w.recv_address)
        for go in w.goods.all():
            g = []
            g.append(u'{0} {1} {2}'.format(go.sku if go.sku else '', go.hs_type if go.hs_type else '',
                                           go.shelf_no if go.shelf_no else ''))
            g.append(go.quantity)
            remark = u'{0} {1}'.format(w.tracking_no, w.shelf_no if w.shelf_no else '')
            results.append(r + g + [remark])
    sheet = excel.pe.Sheet(results)
    return sheet
