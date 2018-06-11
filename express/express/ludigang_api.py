# -*- coding: utf-8 -*
import httplib
import urllib

import requests
from express.crypto import md5
import datetime
import json

URL = 'http://121.196.245.34:8099/WMS'
Cusname = 'SAUIR'
APIKey = 'HC'
CREATE_ACTION = 'OrderService'
CHECK_ACTION = 'ExpressnoService'
secret = 'E0B8FE623C834351918FB24F50A476FA'
Version = '1.0'


def sign(params_dict, dt_str, secret):
    s = ''
    for k in sorted(params_dict):
        s += str(k) + str(params_dict[k])
    return md5(dt_str + s + secret).upper()


def getUrl(params):
    s = '&'.join(['%s=%s' % (key, value) for (key, value) in params.items()])
    return '%s?%s' % (URL, s)


def create(w):
    dt_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    params = {"Cusname": Cusname, "Action": CREATE_ACTION,
              "APIKey": APIKey, "Version": Version, "Time": dt_str,
              "OrderCode": w.tracking_no,
              "Sig": sign({"OrderCode": w.tracking_no}, dt_str, secret)}
    d = {
        "Request": {
            "orderno": w.tracking_no,
            "express": "yundaex",
            "ordertype": "S",
            "orderdate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "piece": 1,
            "weight": 1,
            "post": 0,
            "buytype": "zj01",
            "goodsValue": 0,
            "freight": 0,
            "taxAmount": 0,
            "insurance_fee": 0,
            "taxno": "",
            "currency": "142",
            "sendercusname": "",
            "sendername": "福建海豹跨境电子商务有限公司",
            "sendaddress": "福建省泉州市丰海路1号海岸带管理中心12楼",
            "sendtel": "17759252767",
            "sendcity": "泉州",
            "sendprovice": "福建",
            "sendcountry": "中国",
            "cosignee": w.recv_name,
            "consigneeAddress": w.recv_address,
            "consigneeTelephone": w.recv_mobile,
            "consigneedistrict": w.recv_area,
            "consigneecity": w.recv_city,
            "consigneeprovice": w.recv_province,
            "consigneeCountry": "中国",
            "pic1": "",
            "pic2": "",
            "idcard": w.person_id if w.person_id else '',
            "cusname": "sauir",
            "note": " ",
            "Item": [
                {
                    "itemNo": "",
                    "hsCode": "",
                    "skuname": "",
                    "goodsModel": "",
                    "brand": "",
                    "unit": "035",
                    "currency": "142",
                    "qty": w.get_goods_quantity(),
                    "price": 0,
                    "total": 0,
                    "originCountry": "",
                    "packageType": "",
                    "material": "",

                }
            ]
        }
    }

    try:
        r = requests.post(url=getUrl(params), json=d, headers={"Content-type": "application/x-www-form-urlencoded"})
        if r.status_code == requests.codes.ok:
            rj = json.loads(r.text.lower())
            code = rj['response']['code']
            msg = rj['response']['message']
            return code, msg
        else:
            return u'8888', u'返回状态有误, ' + r.text
    except Exception as e:
        return u'9999', e.message


def create2():
    dt_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    params = {"Cusname": Cusname, "Action": CREATE_ACTION,
              "APIKey": APIKey, "Version": Version, "Time": dt_str,
              "OrderCode": "ab003",
              "Sig": sign({"OrderCode": "ab003"}, dt_str, secret)}
    d = {
        "Request": {
            "orderno": "ab003",
            "express": "yundaex",
            "ordertype": "S",
            "orderdate": datetime.datetime.now().strftime("%Y-%m-%d"),
            "piece": 1,
            "weight": 1,
            "post": 0,
            "buytype": "zj01",
            "goodsValue": 0,
            "freight": 0,
            "taxAmount": 0,
            "insurance_fee": 0,
            "taxno": "",
            "currency": "142",
            "sendercusname": "",
            "sendername": "福建海豹跨境电子商务有限公司",
            "sendaddress": "福建省泉州市丰海路1号海岸带管理中心12楼",
            "sendtel": "17759252767",
            "sendcity": "泉州",
            "sendprovice": "福建",
            "sendcountry": "中国",
            "cosignee": "老大",
            "consigneeAddress": "地址",
            "consigneeTelephone": '13012345321',
            "consigneedistrict": "朝阳区",
            "consigneecity": "北京",
            "consigneeprovice": "北京",
            "consigneeCountry": "中国",
            "pic1": "",
            "pic2": "",
            "idcard": '',
            "cusname": "sauir",
            "note": " ",
            "Item": [
                {
                    "itemNo": "",
                    "hsCode": "",
                    "skuname": "",
                    "goodsModel": "",
                    "brand": "",
                    "unit": "035",
                    "currency": "142",
                    "qty": 1,
                    "price": 0,
                    "total": 0,
                    "originCountry": "",
                    "packageType": "",
                    "material": "",

                }
            ]
        }
    }
    try:
        r = requests.post(url=getUrl(params), json=d, headers={"Content-type": "application/x-www-form-urlencoded"})
        if r.status_code == requests.codes.ok:
            rj = json.loads(r.text.lower())
            code = rj['response']['code']
            msg = rj['response']['message']
            return code, msg
        else:
            return u'8888', u'回复状态有误, ' + r.text
    except Exception as e:
        return u'9999', e.message


def getYunda(tracking_no):
    dt_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    params = {"Cusname": Cusname, "Action": CHECK_ACTION,
              "APIKey": APIKey, "Version": Version, "Time": dt_str,
              "OrderCode": tracking_no,
              "Sig": sign({"OrderCode": tracking_no}, dt_str, secret)}
    try:
        r = requests.get(url=getUrl(params))
        if r.status_code == requests.codes.ok:
            rj = json.loads(r.text.lower())
            code = rj['response']['code']
            msg = rj['response']['message']
            expressno = rj['response']['data']['expressno']
            return code, msg, expressno
        else:
            return u'8888', u'返回状态有误, ' + r.text, ''
    except Exception as e:
        return u'9999', e.message, ''

