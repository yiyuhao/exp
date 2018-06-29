# -*- coding: utf-8 -*

import httplib
from datetime import datetime
import hashlib
import json
from waybills.serializers import YHCCreateResponseDataSerializer,YHCCreateResponseSerializer
from rest_framework.parsers import JSONParser

endpoint = "testapi.1hcang.com"

timestamp = int(datetime.now().strftime('%s'))

appid = 'testapi'

appkey = 'DC39AE3E28DC4FD3A3EB9331C4276C71'

headers = {"Content-type": "application/json", "Accept": "application/json"}
md5 = hashlib.md5()

md5.update(appkey + str(timestamp))
token = md5.hexdigest()

example_tracking_no = 'OCABZAU170266510'

example_data = [{"ReferenceOrderDetailNo": "AB17021700001", "DeliveryType": "SELF", "TrackingNoIn": "AB17021700001",
                 "WarehouseID": 2, "Consignee": "张三", "Phone": "13800001234", "Province": "广东省", "City": "深圳市",
                 "Postcode": "518000", "Address1": "大三擦灰姑娘大法师", "Commodity": "包", "UnitPrice": 50, "DeclaredValue": 20,
                 "Quantity": 2}]

example_data2 = [{"ReferenceOrderDetailNo": "AB17021700001", "ReferenceInboundGroup": "AB17021700001",
                  "ReferenceOutboundGroup": "AB17021700001", "DeliveryType": "SELF", "TrackingNoIn": "AB17021700001",
                  "WarehouseID": 2, "Consignee": "张三", "Phone": "13800001234", "Province": "广东省", "City": "深圳市",
                  "Postcode": "518000", "Address1": "大三擦灰姑娘大法师", "Commodity": "包", "UnitPrice": 50, "DeclaredValue": 20,
                  "Quantity": 2},
                 {"ReferenceOrderDetailNo": "AB17021700001", "ReferenceInboundGroup": "AB17021700001",
                  "ReferenceOutboundGroup": "AB17021700001", "DeliveryType": "SELF", "TrackingNoIn": "AB17021700001",
                  "WarehouseID": 2, "Consignee": "张三", "Phone": "13800001234", "Province": "广东省", "City": "深圳市",
                  "Postcode": "518000", "Address1": "大三擦灰姑娘大法师", "Commodity": "鞋子", "UnitPrice": 30,
                  "DeclaredValue": 10, "Quantity": 1}]


def get_conn(uri):
    return httplib.HTTPConnection(endpoint)


def create(input_data):
    conn = get_conn(endpoint)
    url = '/Shipment/Create?timestamp=%s&appid=%s&token=%s' % (timestamp, appid, token)

    conn.request("POST", url, json.dumps(input_data), headers)

    response = conn.getresponse()
    data = JSONParser().parse(response)

    print (response.status, response.reason)
    print (data)
    conn.close()

    # d = JSONParser().parse(response)
    yhcSe = YHCCreateResponseSerializer(data=data)
    print(yhcSe.is_valid())
    print(yhcSe.errors)
    print(yhcSe.error_messages)
    print (yhcSe.validated_data)


def check(tracking_no):
    md5 = hashlib.md5()
    md5.update(appkey + str(tracking_no))
    token = md5.hexdigest()

    conn = get_conn(endpoint)

    url_get = 'http://testapi.1hcang.com/ExpressTrack/Track?expressno=%s&appid=%s&token=%s' % (
        tracking_no, appid, token)

    conn.request("GET", url_get, headers=headers)

    response = conn.getresponse()
    data = response.read()

    print (response.status, response.reason)
    print (data)
    conn.close()

# params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})
