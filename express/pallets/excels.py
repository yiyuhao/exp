# -*- coding: utf-8 -*
from __future__ import unicode_literals
from decimal import Decimal

import django_excel as excel

from addresses.constants import PROV_CITY_CODE, get_prov_city_code
from express.utils import *
from pypinyin import lazy_pinyin

from pallets.models import CH6
from waybills.models import *
from django.db.models import Q, Min
import pyexcel


def bc_excel(air_waybill):
    waybills = Waybill.objects.filter(pallet__air_waybill=air_waybill).distinct()

    result = get_custom_data(air_waybill, waybills)
    sheet = excel.pe.Sheet(result, name="Sheet1")
    return sheet


def get_custom_data(air_waybill, waybills):
    result = []
    if air_waybill.channel.name == CH1:
        result = bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH3:
        result = yhc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH4:
        result = bdt_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH5:
        result = hm_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH6:
        result = qd_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH7:
        result = fj_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name in [CH8, CH14]:
        result = a_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH12:
        result = e_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH15:
        result = z_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name == CH16:
        result = h_bc_data(air_waybill.air_waybill_no, waybills)
    elif air_waybill.channel.name in [CH17, CH18, CH19, CH23]:
        result = k_bc_data(air_waybill.air_waybill_no, waybills)
    else:
        result = fj_bc_data(air_waybill.air_waybill_no, waybills)
    return result


def overload_bc_excel(waybills, channel_name):
    result = get_overload_custom_data(channel_name, waybills)
    sheet = excel.pe.Sheet(result)
    return sheet


def get_overload_custom_data(channel_name, waybills):
    result = []
    if channel_name == CH1:
        result = bc_data('', waybills)
    elif channel_name == CH3:
        result = yhc_data('', waybills)
    elif channel_name == CH4:
        result = bdt_data('', waybills)
    elif channel_name == CH5:
        result = hm_data('', waybills)
    elif channel_name == CH6:
        result = qd_bc_data('', waybills)
    elif channel_name == CH7:
        result = fj_bc_data('', waybills)
    elif channel_name in [CH8, CH14]:
        result = a_bc_data('', waybills)
    elif channel_name == CH12:
        result = e_bc_data('', waybills)
    elif channel_name == CH15:
        result = z_bc_data('', waybills)
    elif channel_name == CH16:
        result = h_bc_data('', waybills)
    elif channel_name == CH17:
        result = k_bc_data('', waybills)
    else:
        result = fj_bc_data('', waybills)
    return result


def bc_data(air_waybill_no, waybills):
    columnNames = [u'订单编号', u'物流电子运单号', u'支付交易号', u'净重', u'毛重', u'收货人地址', u'收货人电话', u'收货人名称', u'收货人身份证', u'运输工具名称',
                   u'进出境日期', u'发货人城市', u'发货人地址', u'发货人名称', u'发货人电话', u'主运单号', u'海关税号', u'商品名称', u'NAME', u'商品规格类型',
                   u'成交数量', u'成交单价', u'#'
                   ]
    result = [columnNames]
    for waybill in waybills:
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
        r.append(air_waybill_no)  # 主运单号

        for good in waybill.goods.all():
            g = []
            g.append("")  # 海关税号
            g.append(good.hs_type)  # 商品名称
            g.append(good.brand)  # NAME
            g.append(good.spec)  # 商品规格类型
            g.append(good.quantity)  # 成交数量
            g.append(good.unit_price)  # 成交单价
            g.append(waybill.pallet.pallet_no)  # 托盘号
            result.append(r + g)
    return result


def yhc_data(air_waybill_no, waybills):
    columnNames = [u'提单号', u'运单号', u'重量(磅)', u'收货人地址', u'收货人电话', u'收货人名称', u'商品品名', u'品牌', u'成交数量', u'成交单价(USD)']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(air_waybill_no)
        r.append(waybill.tracking_no)
        r.append('%.2f' % waybill.weight)
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_name)

        for good in waybill.goods.all():
            g = []
            g.append(good.hs_type)
            g.append(good.brand)
            g.append(good.quantity)
            g.append('%.2f' % (good.unit_price * Decimal(0.5)))
            result.append(r + g)
    return result


def hm_data(air_waybill_no, waybills):
    columnNames = [u'运单号', u'重量(磅)', u'收货人名称', u'收货人电话', u'收货人地址', u'品牌', u'商品品名', u'个数', u'申报价值(USD)']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)
        r.append('%.2f' % waybill.weight)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)  # 收货人地址

        for good in waybill.goods.all():
            g = []
            g.append(good.brand)
            g.append(good.hs_type)
            g.append(good.quantity)
            g.append('%.2f' % (good.unit_price * Decimal(0.5)))
            result.append(r + g)
    return result


def bdt_data(air_waybill_no, waybills):
    columnNames = [u'运单号', u'重量(磅)', u'收货人名称', u'收货人电话', u'收货人地址', u'提单号']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)
        r.append('%.2f' % waybill.weight)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)  # 收货人地址
        r.append(air_waybill_no)
        result.append(r)
    return result


def qd_bc_data(air_waybill_no, waybills):
    columnNames = [u'订单号', u'物流运单编号', u'毛重(KG)', u'订购人姓名', u'订购人证件号码(身份证号)', u'收货人电话', u'收货地址',
                   u'企业商品名称', u'规格型号', u'数量', u'单价', u'总价', u'商品描述', u'条码']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)  # 订单号
        r.append(waybill.cn_tracking)  # 物流号
        r.append('%.2f' % (waybill.weight * Decimal(0.453592)))  # 毛重
        r.append(waybill.recv_name)  # 收货人名称
        r.append(waybill.person_id)  # 收货人身份证
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)  # 收货人地址

        for good in waybill.goods.all():
            g = []
            g.append(good.brand + good.hs_type)  # 商品名称
            g.append(good.spec)  # 商品规格类型
            g.append(good.quantity)  # 成交数量
            g.append('%.2f' % good.unit_price)  # 成交单价
            g.append('%.2f' % (good.unit_price * good.quantity))  # 总价
            g.append(good.description)
            g.append(good.sku)
            result.append(r + g)
    return result


def fj_bc_data(air_waybill_no, waybills):
    columnNames = [u'订单号', u'物流运单编号', u'毛重(KG)', u'订购人姓名', u'订购人证件号码(身份证号)', u'收货人电话', u'收货地址',
                   u'企业商品名称', u'规格型号', u'数量', u'单价', u'总价', u'商品描述', u'sku', u'城市码']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)  # 订单号
        r.append(waybill.cn_tracking)  # 物流号
        r.append('%.2f' % (waybill.weight * Decimal(0.453592)))  # 毛重
        r.append(waybill.recv_name)  # 收货人名称
        r.append(waybill.person_id)  # 收货人身份证
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_province + waybill.recv_city + waybill.recv_area + waybill.recv_address)  # 收货人地址

        for good in waybill.goods.all():
            g = []
            g.append(good.brand + good.hs_type)  # 商品名称
            g.append(good.spec)  # 商品规格类型
            g.append(good.quantity)  # 成交数量
            g.append('%.2f' % good.unit_price)  # 成交单价
            g.append('%.2f' % (good.unit_price * good.quantity))  # 总价
            g.append(good.description)
            g.append(good.sku)
            g.append(get_prov_city_code(waybill))
            result.append(r + g)
    return result


def a_bc_data(air_waybill_no, waybills):
    columnNames = [u'订单号', u'物流运单编号', u'毛重(KG)', u'订购人姓名', u'订购人证件号码(身份证号)', u'收货人电话', u'省',
                   u'市', u'区', u'地址',
                   u'企业商品名称', u'规格型号', u'数量', u'单价', u'总价', u'商品描述', u'sku', u'城市码']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)  # 订单号
        r.append(waybill.cn_tracking)  # 物流号
        r.append('%.2f' % (waybill.weight * Decimal(0.453592)))  # 毛重
        r.append(waybill.recv_name)  # 收货人名称
        r.append(waybill.person_id)  # 收货人身份证
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_province)  # 省
        r.append(waybill.recv_city)  # 市
        r.append(waybill.recv_area)  # 区
        r.append(waybill.recv_address)  # 地址

        for good in waybill.goods.all():
            g = []
            g.append(good.brand + good.hs_type)  # 商品名称
            g.append(good.spec)  # 商品规格类型
            g.append(good.quantity)  # 成交数量
            g.append('%.2f' % good.unit_price)  # 成交单价
            g.append('%.2f' % (good.unit_price * good.quantity))  # 总价
            g.append(good.description)
            g.append(good.sku)
            g.append(get_prov_city_code(waybill))
            result.append(r + g)
    return result


def e_bc_data(air_waybill_no, waybills):
    columnNames = ['订单编号', '电商平台代码', '电商企业代码', '商品价格（订单商品总额）', '运杂费', '非现金抵扣金额', '代扣税款',
                   '订购人（买方）注册号', '订购人（买方）名称', '订购人（买方）证件类型', '订购人（买方）证件号', '订购人（买方）电话',
                   '收货人姓名', '收货人电话', '市', '收货人地址', '订单备注', '运单号', '贸易方式', '订单商品总重量',
                   '商品序号', '商品货号', '商品名称', '商品编码', '商品规格型号', '条形码', '商品单价', '商品数量',
                   '计量单位', '法定数量', '法定单位', '第二数量', '第二单位', '原产国']
    result = [columnNames]
    i = 1
    for waybill in waybills:
        r = []
        r.append(waybill.order_no)  # 订单号
        r.append('111198Z002')  #
        r.append('1111980076')  #
        r.append('')  #
        r.append('0.00')  #
        r.append('0.00')  #
        r.append('0.00')  #

        r.append('N')  #
        r.append(waybill.recv_name)  #
        r.append('1')  #
        r.append(waybill.person_id)  #
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_name)  #
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_city)  #
        r.append('%s%s%s%s' % (waybill.recv_province, waybill.recv_city, waybill.recv_area, waybill.recv_address))  # 地址
        r.append('')  #
        r.append(waybill.cn_tracking)  #
        r.append('9610')  #
        r.append('%.2f' % (waybill.weight * Decimal(0.453592)))  # 毛重

        for good in waybill.goods.all():
            g = [i]
            g.append('GX%s01' % good.sku)
            g.append(good.hs_type)  #
            g.append('')  #
            g.append(good.brand + good.hs_type + good.spec)  #
            g.append(good.sku)
            g.append('%.2f' % good.unit_price)  #
            g.append(good.quantity)  #
            g.append('')  #
            g.append('')  #
            g.append('')  #
            g.append('')  #
            g.append('')  #
            g.append('502')  #
            g.append(good.description)  #
            result.append(r + g)
            i += 1
    return result


def z_bc_data(air_waybill_no, waybills):
    columnNames = [u'订单号', u'国内单号', u'重量(磅)', u'收件人姓名', u'身份证号', u'收货人电话', u'省',
                   u'市', u'区', u'地址', u'品牌', u'商品描述', u'数量', u'单价', u'总价']
    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)  # 订单号
        r.append(waybill.cn_tracking)  # 物流号
        r.append('%.2f' % (waybill.weight))  # 毛重
        r.append(waybill.recv_name)  # 收货人名称
        r.append(waybill.person_id)  # 收货人身份证
        r.append(waybill.recv_mobile)  # 收货人电话
        r.append(waybill.recv_province)  # 省
        r.append(waybill.recv_city)  # 市
        r.append(waybill.recv_area)  # 区
        r.append(waybill.recv_address)  # 地址

        for good in waybill.goods.all():
            g = []
            g.append(good.brand)  # 商品名称
            g.append(good.description)  # 商品名称
            g.append(good.quantity)  # 成交数量
            g.append('%.2f' % good.unit_price)  # 成交单价
            g.append('%.2f' % (good.unit_price * good.quantity))  # 总价
            result.append(r + g)
    return result


def h_bc_data(air_waybill_no, waybills):
    columnNames = [u'运单号', u'收件人', u'收件手机', u'收件人身份证', u'收件省份', u'收件城市', u'收件地址',
                   u'收件邮编', u'渠道', u'重量', u'货物分类', u'分类(英文)', u'品名', u'品牌', u'产品明细(备注)', u'数量']

    result = [columnNames]
    for waybill in waybills:
        r = []
        r.append(waybill.tracking_no)
        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.person_id)
        r.append(waybill.recv_province)  # 省
        r.append(waybill.recv_city)  # 市
        r.append(waybill.recv_area + waybill.recv_address)  # 地址
        r.append(waybill.recv_zipcode)
        r.append(u'特快渠道')
        r.append('%.2f' % (waybill.weight))

        is_first = True
        for good in waybill.goods.all():
            g = []
            g.append(good.hs_type)  # 货物分类
            g.append('')  # 分类(英文)
            g.append(good.cat2 if good.cat2 else good.description)  # 品名
            g.append(good.brand)  # 品牌
            g.append(good.description)  # 产品明细(备注)
            g.append(good.quantity)  # 数量
            if is_first:
                result.append(r + g)
                is_first = False
            else:
                r_ = [''] * 10
                result.append(r_ + g)
    return result


def k_bc_data(air_waybill_no, waybills):
    columnNames = [u'NO', u'第一次转单单号', u'发件人', u'发件人地址', u'发件人电话', u'收件人', u'收件人电话', u'省', u'城市', u'区',
                   u'邮编', u'收件人地址', u'总数量', u'包裹总价值（人民币）', u'申报毛重', u'实际毛重(KG)', u'预估海关费用（美金）',
                   u'预计国内派送费用', u'身份证件号码', u'条码', u'物品名称', u'单价（人民币)', u'物品数量', u'品牌', u'规格型号', u'单位', u'英文']

    result = [columnNames]
    cnt = 1
    for waybill in waybills:
        r = []
        r.append(cnt)
        r.append(waybill.cn_tracking)
        r.append('Darren zhang')
        r.append('77 Glandale Ave NJ 08817')
        r.append('8058681682')

        r.append(waybill.recv_name)
        r.append(waybill.recv_mobile)
        r.append(waybill.recv_province)  # 省
        r.append(waybill.recv_city)  # 市
        r.append(waybill.recv_area)
        r.append(waybill.recv_zipcode)
        r.append("{0}{1}{2}{3} ".format(waybill.recv_province, waybill.recv_city, waybill.recv_area,
                                        waybill.recv_address).replace(" ", ""))  # 地址
        r.append(waybill.get_goods_quantity())
        r.append(waybill.get_value_rmb())
        r.append('%.2f' % (waybill.get_goods_weight() * Decimal(0.45359)))
        r.append('%.2f' % (waybill.weight * Decimal(0.45359)))
        r.append(1)
        r.append(0)
        r.append(waybill.person_id)
        cnt += 1
        is_first = True
        for good in waybill.goods.all():
            g = []
            g.append(good.sku)
            g.append(good.cat2 if good.cat2 else good.description)  # 货物分类
            g.append('%.2f' % (good.unit_price * RMB_RATE))  # 货物分类
            g.append(good.quantity)  # 数量
            g.append(good.brand)  # 品牌
            g.append(good.spec)  # 产品明细(备注)
            g.append(u'个')  # 产品明细(备注)
            g.append(good.english_name)
            if is_first:
                result.append(r + g)
                is_first = False
            else:
                r_ = [''] * 19
                result.append(r_ + g)
    return result


def bc_goods_excel():
    colnames = [u'ID', u'商品名称中文', u'商品名称英文', u'品牌', u'HS编码', u'规格型号', u'单位', u'价格', u'原产国', u'商品描述参考']
    result = [[], [], colnames]

    qs = Good.objects.filter(~Q(waybill__person_id__iexact='') | ~Q(waybill__person_id__isnull=True)).values('sku') \
        .annotate(g_brand=Max('brand'), g_type=Max('hs_type'), g_spec=Max('spec'), g_unit=Max('unit'),
                  g_price=Min('unit_price'), g_desc=Max('description'))
    i = 1
    for g in qs:
        r = []
        r.append(i)
        r.append(g['g_type'])
        r.append(toEng(g['g_type']))
        r.append(g['g_brand'])
        r.append('')
        r.append(g['g_spec'])
        r.append(g['g_unit'])
        r.append(g['g_price'])
        r.append('')
        r.append(g['g_desc'])
        i += 1
        result.append(r)

    sheet = excel.pe.Sheet(result)
    return sheet


def usps_excel(air_waybill):
    columnNames = ['Package ID', 'Sender First Name', 'Sender Last Name', 'Sender Business Name',
                   'Sender Address Line 1', 'Sender Address Line 2', 'Sender City', 'Sender Province',
                   'Sender Postal Code', 'Sender Country Code', 'Sender Phone Number', 'Recipient First Name',
                   'Recipient Last Name', 'Recipient Business Name', 'Recipient Address Line 1',
                   'Recipient Address Line 2', 'Recipient Address Line 3', 'RecipientInLineTranslationAddressLine1',
                   'RecipientInLineTranslationAddressLine2', 'Recipient City', 'Recipient Province',
                   'Recipient Postal Code', 'Recipient Country Code', 'Recipient Phone Number',
                   'Recipient E-mail Address', 'Package Weight', 'Weight Unit ', 'Service Type', 'Rate Type',
                   'Package Type', 'Package Physical Count', 'Value Loaded (USD)', 'PFC/EEL Code', 'Item ID',
                   'Item Description', 'Unit Value (USD)', 'Quantity', 'Country Of Origin'
                   ]
    result = [columnNames]
    for pallet in air_waybill.pallets.all():
        for waybill in pallet.waybills.all():

            cn_address = waybill.get_usps_cn_address()

            goods_qty = 0
            goods_price = 0.0
            goods_des_list = []
            for good in waybill.goods.all():
                goods_qty += good.quantity
                goods_price = good.get_usps_value()
                goods_des_list.append(good.hs_type)

            cnList = [waybill.recv_address, u";".join(goods_des_list)]
            enList = toEng(cnList)

            r = []
            r.append(waybill.tracking_no)
            r.append("Darren")
            r.append("Zheng")
            r.append("HEX")
            r.append("77 Glendale Ave")
            r.append("")
            r.append("Edison")
            r.append("NJ")
            r.append("08817")
            r.append("US")
            r.append("805-868-1682")
            r.append(waybill.get_eng_name())  # First Name
            r.append(".")  # Last Name
            r.append("")  # business name
            r.append(" ".join(lazy_pinyin(enList[0])))  # rec_add_1
            r.append("")  # rec_add_2
            r.append("")  # rec_add_3
            r.append(cn_address[0])
            r.append(cn_address[1])
            r.append("".join(lazy_pinyin(remove_sheng_shi_zizhiqu(waybill.recv_city))).upper())
            r.append("".join(lazy_pinyin(remove_sheng_shi_zizhiqu(waybill.recv_province))).upper())
            r.append(waybill.recv_zipcode)
            r.append("CN")  # cn code
            r.append(waybill.recv_mobile)
            r.append("")  # email
            r.append("%.2f" % waybill.weight)
            r.append("LB")
            r.append("LBL")
            r.append("EPMI")
            r.append("M")
            r.append("1")
            r.append("N")
            r.append("NOEEI 30.37(a)")
            r.append(".")
            r.append(enList[1])
            r.append("%.2f" % goods_price)
            r.append(goods_qty)
            r.append("US")
            result.append(r)
    sheet = excel.pe.Sheet(result)
    return sheet


def both_tracking_excel(air_waybill):
    columnNames = [u'运单号', u'国内运单号']
    result = [columnNames]
    for pallet in air_waybill.pallets.all():
        for waybill in pallet.waybills.all():
            r = []
            r.append(waybill.tracking_no)
            r.append(waybill.cn_tracking)
            result.append(r)

    sheet = excel.pe.Sheet(result)
    return sheet


def agent_excel(air_waybill):
    pallet_cnt = air_waybill.pallets.all().count()
    columnNames = ['Number of Unit', 'Number of Packages', 'Total weight(LB)', 'Other Weight(LB)', 'Total weight(KG)']
    result = [columnNames]
    air_waybill_total_weight = air_waybill.get_weight()
    r = [pallet_cnt, air_waybill.get_waybills_count(), "%.2f" % air_waybill_total_weight,
         "%.2f" % (pallet_cnt * Decimal(0.55)),
         "%.2f" % (air_waybill_total_weight * Decimal(0.453592) + pallet_cnt * Decimal(0.55) * Decimal(0.453592))]
    result.append(r)
    columnNames = ['Pallet No', 'Package ID', 'Weight(LB)']
    result2 = [columnNames]
    for pallet in air_waybill.pallets.all():
        for waybill in pallet.waybills.all().order_by('pallet__pallet_no'):
            r = []
            r.append(waybill.pallet.pallet_no)
            r.append(waybill.tracking_no)
            r.append("%.2f" % waybill.weight)
            # r.append(waybill.get_goods_content())
            # r.append(waybill.get_goods_quantity())
            result2.append(r)
    book = excel.pe.Book({"Summary": result, "Detail": result2})
    return book


def update_waybill_usps(tracking_no, usps_tracking):
    '''
    :param tracking_no:
    :param usps_excel:
    :return:
     code
     0 success
     1 not exist
     2 status error
    '''
    code = 0
    msg = ''
    if Waybill.objects.filter(tracking_no=tracking_no).exists():
        w = Waybill.objects.filter(tracking_no=tracking_no).first()
        auditStatus = WaybillStatusEntry.objects.get(name=u'已审核')
        if w.get_most_recent_status().status.order_index >= auditStatus.order_index:
            if w.cn_tracking:
                QFTracking.revert_tracking(w.cn_tracking)
            w.cn_tracking = usps_tracking
            w.save()
            code = 0
            msg = ''
        else:
            code = 2
            msg = u'运单号:{0}, 状态:{1} 无法更新, 订单必须为已审核以及之后的状态' \
                .format(w.tracking_no, w.get_most_recent_status())
    else:
        code = 1
        msg = u'运单号:{0}, 不存在'.format(tracking_no)
    return code, msg


def update_usps_excel(filehandle):
    succ = True
    errors = []
    sheet = filehandle.get_sheet()
    sheet.name_columns_by_row(0)
    sheet.colnames = ['tracking_no', 'usps_tracking', 'weight', 'name', 'port']
    succ_cnt = 0
    i = 2
    for x in sheet.to_records():
        tracking_no = x.get('tracking_no', '').strip()
        usps_tracking = x.get('usps_tracking', '').strip()
        if tracking_no and usps_tracking:
            code, msg = update_waybill_usps(tracking_no, usps_tracking)
            if code == 0:
                succ_cnt += 1
            else:
                succ = False
                errors.append(u'第{0}行, {1}'.format(i, msg))
        i += 1
    return succ, i - 2, succ_cnt, errors


def air_waybill_fee_excel(qs):
    columnNames = ['国际单号', '国内单号', '重量(lb)', '重量(kg)', '渠道', '申报价(USD)', '运费(USD)', '税费(USD)', '打包费', '总计(USD)', '提单号']
    result = [columnNames]
    for o in qs:
        r = []
        r.append(o['tracking_no'])
        r.append(o['cn_tracking'])
        r.append(o['weight'])
        r.append(round(o['weight'] * Decimal('0.453592'), 2))
        r.append(o['channel__name'])
        r.append(round(o['price'], 2))
        weight = o['weight'] if o['weight'] >= 1 else 1
        yunfei = yunfei_helper(o['channel__name'], o['price'], weight)
        tax = tax_helper(o['channel__name'], o['price'])
        r.append(round(yunfei, 2))
        r.append(round(tax, 2))
        r.append(1)
        r.append(round(yunfei + tax + 1, 2))
        r.append(o['pallet__air_waybill__air_waybill_no'])
        result.append(r)
    sheet = excel.pe.Sheet(result, name="Sheet1")
    return sheet


def yunfei_helper(channel_name, price, weight):
    if channel_name == 'A1':
        return weight * Decimal('2.7')
    elif channel_name == 'K2':
        return weight * Decimal('2.5')
    else:
        return 0


def tax_helper(channel_name, price):
    if channel_name == 'A1':
        return Decimal('0.119') * price * Decimal('0.5')
    else:
        return 0


def waybill_excel(air_waybills):
    qs = Waybill.objects.filter(pallet__air_waybill__air_waybill_no__in=air_waybills)
    results = []
    for w in qs:
        r = []
        r.append(w.tracking_no)
        r.append(w.get_fee_actual())
        r.append(w.weight)
        results.append(r)
    import pyexcel
    pyexcel.save_as(array=results, dest_file_name=settings.MEDIA_ROOT + '/t.xlsx')


def yunfei_export(qs):
    results = []
    title = ['运单号', '状态', '渠道', '运费', '打包费', '税费', '重量']
    results.append(title)
    for w in qs:
        r = []
        r.append(w.tracking_no)
        r.append(w.status.name)
        r.append(w.channel.name)
        r.append(w.express_fee)
        r.append(w.package_fee)
        r.append(w.tax_fee)
        r.append(w.weight)
        results.append(r)
    import pyexcel
    pyexcel.save_as(array=results, dest_file_name=settings.MEDIA_ROOT + '/t2.xlsx')


def yunfei_export2(qs):
    results = []
    title = ['运单号', '状态', '渠道', '运费', '打包费', '税费', '重量']
    results.append(title)
    for w in qs:
        r = []
        r.append(w.tracking_no)
        r.append(w.status.name)
        r.append(w.channel.name)
        r.append(w.get_express_fee())
        r.append(1.5)
        r.append('')
        r.append(w.weight)
        results.append(r)
    pyexcel.save_as(array=results, dest_file_name=settings.MEDIA_ROOT + '/t2.xlsx')


#########

def get_status_time_diff(st_order_index, ed_order_index, w):
    day_in_seconds = 24 * 3600.0
    if st_order_index > ed_order_index:
        raise Exception('给定状态顺序有误')
    else:
        if w.status_set.filter(status__order_index=st_order_index).exists() and w.status_set.filter(
                status__order_index=ed_order_index).exists():
            s1 = w.status_set.filter(status__order_index=st_order_index).first()
            s2 = w.status_set.filter(status__order_index=ed_order_index).first()
            return (s2.create_dt - s1.create_dt).days + \
                   (s2.create_dt - s1.create_dt).seconds / day_in_seconds
        else:
            return 0


def effectiveness_excel():
    dt_1 = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("04/01/2018", '%m/%d/%Y'))
    dt_2 = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("05/01/2018", '%m/%d/%Y'))
    dt_3 = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("06/01/2018", '%m/%d/%Y'))
    qs_4 = Waybill.objects.filter(Q(create_dt__gte=dt_1), Q(create_dt__lte=dt_2), ~Q(status__name='运单异常'))
    qs_5 = Waybill.objects.filter(Q(create_dt__gte=dt_2), Q(create_dt__lte=dt_3), ~Q(status__name='运单异常'))

    o1 = 20  # 已入库
    o2 = 70  # 已出库
    o3 = 100  # 国内清关
    o4 = 110  # 国内派送
    o5 = 120  # 已完成

    book_obj = {}
    i = 0
    for qs in [qs_4, qs_5]:
        results = []
        title = ['运单号', '状态', '美国处理时效', '航空/货代时效', '清关时效', '国内派送时效', '总时效', '创建日期']
        results.append(title)
        for w in qs:
            r = [w.tracking_no, w.status.name]
            us_time = get_status_time_diff(o1, o2, w)
            air_time = get_status_time_diff(o2, o3, w)
            cn_custom_time = get_status_time_diff(o3, o4, w)
            cn_delivery_time = get_status_time_diff(o4, o5, w)
            r += [us_time, air_time, cn_custom_time, cn_delivery_time]
            if us_time > 0 and air_time > 0 and cn_custom_time > 0 and cn_delivery_time > 0:
                r.append(us_time + air_time + cn_custom_time + cn_delivery_time)
            else:
                r.append(0)
            r.append(w.create_dt.strftime('%m/%d/%Y'))
            results.append(r)
        if i == 0:
            book_obj['4月'] = results
        else:
            book_obj['5月'] = results
        i += 1

    book = excel.pe.Book(book_obj)

    book.save_as(settings.MEDIA_ROOT + '/time2.xlsx')
