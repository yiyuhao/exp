# -*- coding: utf-8 -*

import requests

from express.crypto import md5
from express.utils import *
from waybills.models import Waybill


def notify_order_send_out(tracking_no, username):
    # 通知wms出库操作
    data = {
        "action": "send_out",
        "tracking_no": tracking_no,
        'sq_user': username
    }
    return post_req_wms(data, 'Order.ashx')


def push_person_id(tracking_no, name, person_id, mobile):
    data = {
        "action": "update_person_id_by_tracking",
        "tracking_no": tracking_no,
        "name": to_utf8(name),
        "person_id": person_id,
        "mobile": mobile
    }
    result = post_req_wms(data, 'Person.ashx')

    try:
        w = Waybill.objects.get(tracking_no=tracking_no)

        if 'shelf_no' in result and result['shelf_no']:
            w.shelf_no = result['shelf_no']
            w.save()
        if 'shelf_obj' in result and result['shelf_obj']:
            bind_shelf_no_to_goods(w, result['shelf_obj'])
    except Exception as e:
        result['error'] = e.message

    return result


def bind_shelf_no_to_goods(w, shelf_obj):
    for order_no in shelf_obj:
        if shelf_obj[order_no]:
            g = w.goods.filter(order_no=order_no).first()
            if g:
                g.shelf_no = shelf_obj[order_no]
                g.save()


def get_person_id_from_wms(tracking_no):
    data = {
        "action": "get_by_tracking",
        "tracking_no": tracking_no
    }
    return post_req_wms(data, 'Person.ashx')


def bind_shelf(tracking_no):
    data = {
        "action": "bind_shelf",
        "tracking_no": tracking_no
    }
    result = post_req_wms(data, 'Order.ashx')

    try:
        if result['shelf_no']:
            w = Waybill.objects.get(tracking_no=tracking_no)
            w.shelf_no = result['shelf_no']
            w.save()
    except Exception as e:
        result['error'] = e.message
    return result


def update_weight(goods_no, weight, fee, tracking_no, tax):
    data = {
        "action": "update_weight",
        "goods_no": goods_no,
        "weight": weight,
        'express_fee': fee,
        'tracking_no': tracking_no,
        'tax': tax
    }
    result = post_req_wms(data, 'Product.ashx')
    return result


def createSignWms(params_dict):
    api_key = '5BA7CFFBEF7D4'
    result = ""
    for k in sorted(params_dict):
        result += str(k) + str(params_dict[k])

    return md5(api_key + result + api_key)


def post_req_wms(params_dict, uri):
    url = ('http://wmstest.xunleiex.com/Admin/Api/' if settings.DEBUG else 'http://wms.xunleiex.com/Admin/Api/') + uri
    # url = 'http://wms.xunleiex.com/Admin/Api/'+ uri
    headers = {"Accept": "application/json"}
    params_dict["request_type"] = "app"
    params_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    params_dict['sign'] = createSignWms(params_dict)
    try:
        response = requests.request("POST", verify=False, url=url, data=params_dict, headers=headers)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print e
        return None


def update_currency(rate, create_dt):
    d = {
        "action": 'update',
        'rate': rate,
        "create_dt": create_dt}
    return post_req_wms(d, "Currency.ashx")
