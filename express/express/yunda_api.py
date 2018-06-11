# -*- coding: utf-8 -*

from __future__ import unicode_literals
import json
import math
import xml.etree.ElementTree as ET
import dicttoxml
import requests
import xmltodict

from express import settings
from waybills.models import Waybill, CnTrackingCreateLog, QFTracking
from express.crypto import base64_encode, md5
from pallets.models import Channel, CH14

version = '1.0'
data = 'data'
my_item_func = lambda x: x[:-1]

got = 'got'  # 已揽收
transit = 'transit'  # 运输中
signed = 'signed'  # 正常签收
signfail = 'signfail'  # 异常签收

STATUS_MAP = {
    got: 2,
    transit: 3,
    signed: 4,
    signfail: 9
}

if settings.DEBUG:
    # debug
    host = 'http://orderdev.yundasys.com:10110/cus_order/order_interface/'
    partnerid = '7864641052'
    secect = 'KkPHQixh7wE2MeyRrAFv8qf4aScmJ3'
else:
    # pro
    host = 'http://order.yundasys.com:10235/cus_order/order_interface/'
    partnerid = '3149031009'
    secect = 'nIKAps9N4F8Zuk6SDXVQtJfiMwGecY'

create_url = host + 'interface_receive_order__mailno.php'
update_url = host + 'interface_modify_order.php'
cancel_url = host + 'interface_cancel_order.php'
lookup_url = host + 'interface_order_info.php'
cn_transist_url = host + 'interface_transite_search.php'


def upsert_one(w, is_update=False):
    url = update_url if is_update else create_url
    position = ''
    position_no = ''
    result_mail_no = ''
    result_msg = ''
    status = ''
    order_serial_no = w.tracking_no
    xml = dicttoxml.dicttoxml([w.get_yunda_obj()], attr_type=False, custom_root='orders', item_func=my_item_func)
    validation = md5(base64_encode(str(xml)) + partnerid + secect)
    post_data = {
        'partnerid': partnerid,
        'version': version,
        'xmldata': base64_encode(str(xml)),
        'validation': validation,
        'request': data
    }
    # print post_data

    r = requests.post(url, data=post_data)
    if r.status_code == requests.codes.ok:
        # print r.text

        root = ET.fromstring(r.text.encode('utf-8'))
        response_list = root.findall('response')
        for res_obj in response_list:
            try:
                status, position_no, order_serial_no, position, result_mail_no, result_msg = process_one(res_obj)
            except Exception as e:
                result_msg = e.message
    else:
        result_msg = "请求异常, 代码" + r.status_code
    return order_serial_no, result_mail_no, result_msg, status, position, position_no


def process_one(res_obj):
    order_serial_no = res_obj.find('order_serial_no').text
    mail_no = res_obj.find('mail_no').text
    status = res_obj.find('status').text
    msg = res_obj.find('msg').text
    pdf_info = json.loads(res_obj.find('pdf_info').text)
    position = pdf_info[0][0]['position']
    position_no = pdf_info[0][0]['position_no']
    return status, position_no, order_serial_no, position, mail_no, msg


def one_by_one_create(qs):
    succ_list = []
    fail_list = []
    for w in qs:
        flag = 5
        temp_tracking_no = ''
        o_tracking_no = w.tracking_no
        while not w.cn_tracking and flag > 0:
            w.tracking_no = w.tracking_no + '-1'
            temp_tracking_no = w.tracking_no
            w.save()
            request_result, succ_cnt, fails = bulk_create([w])
            print request_result, succ_cnt, fails
            w = Waybill.objects.get(tracking_no=temp_tracking_no)
            flag -= 1
        w.tracking_no = o_tracking_no
        w.save()
        if w.cn_tracking:
            print o_tracking_no, 'succ'
            succ_list.append(w.tracking_no)
        else:
            print o_tracking_no, 'fail'
            fail_list.append(w.tracking_no)
    return succ_list, fail_list


def bulk_create(ws, is_update=False):
    url = update_url if is_update else create_url

    request_result = "请求成功"
    results = []
    succ_cnt = 0

    xml = dicttoxml.dicttoxml([w.get_yunda_obj() for w in ws], attr_type=False, custom_root='orders',
                              item_func=my_item_func)

    validation = md5(base64_encode(str(xml)) + partnerid + secect)
    post_data = {'partnerid': partnerid,
                 'version': version,
                 'xmldata': base64_encode(str(xml)),
                 'validation': validation,
                 'request': data
                 }

    r = None
    i = 0
    while i < 3:
        try:
            r = requests.post(url, data=post_data)
            break
        except Exception as e:
            i += 1
            if i == 3:
                return '重试三次失败', results, succ_cnt

    fail_waybills = []

    if r and r.status_code == requests.codes.ok:
        # print r.text.encode('utf-8')
        root = ET.fromstring(r.text.encode('utf-8'))
        response_list = root.findall('response')
        for res_obj in response_list:
            order_serial_no = ''
            mail_no = ''
            position = ''
            position_no = ''

            try:
                status, position_no, order_serial_no, position, mail_no, msg = process_one(res_obj)

                results.append({
                    'order_serial_no': order_serial_no,
                    'mail_no': mail_no,
                    'status': status,
                    'position_no': position_no,
                    'position': position,
                    'msg': msg,
                })

            except Exception as e:
                results.append({
                    'order_serial_no': order_serial_no,
                    'mail_no': mail_no,
                    'status': '0',
                    'position_no': position_no,
                    'position': position,
                    'msg': e.message,
                })

        for r in results:
            c = Channel.objects.get(name=CH14)

            if r['status'] == '1':
                w = Waybill.objects.get(tracking_no=r['order_serial_no'])
                msg, is_succ = waybill_process(w, r['mail_no'], r['status'], r['position'], r['position_no'])

                if is_succ:
                    succ_cnt += 1
                else:
                    fail_waybills.append(w)

                CnTrackingCreateLog.objects.create(us_tracking=r['order_serial_no'], cn_tracking=r['mail_no'],
                                                   msg=r['msg'] + "|" + msg, status=r['status'], channel=c)
            else:
                CnTrackingCreateLog.objects.create(us_tracking=r['order_serial_no'], cn_tracking=r['mail_no'],
                                                   msg=r['msg'], status=r['status'], channel=c)
    else:
        request_result = "请求异常, 代码" + r.status_code
    return request_result, succ_cnt, fail_waybills


def cancel_cn_tracking(results):
    for result in results:
        tracking_no = result['order_serial_no']
        status = result['status']
        msg = result['msg']
        if status == '1' and tracking_no:
            w = Waybill.objects.get(tracking_no=tracking_no)
            if w:
                try:
                    qf = QFTracking.objects.get(tracking_no=w.cn_tracking)
                    qf.delete()
                except Exception as e:
                    print e
                w.cn_tracking = None
                w.save()


def cancel(ws):
    request_result = "请求发送成功"
    results = []
    succ_cnt = 0
    xml = dicttoxml.dicttoxml([{'order_serial_no': w.tracking_no, 'mailno': w.cn_tracking} for w in ws],
                              attr_type=False, custom_root='orders', item_func=my_item_func)
    validation = md5(base64_encode(str(xml)) + partnerid + secect)
    post_data = {'partnerid': partnerid,
                 'version': version,
                 'xmldata': base64_encode(str(xml)),
                 'validation': validation,
                 'request': 'cancel_order'
                 }

    r = requests.post(cancel_url, data=post_data)
    if r.status_code == requests.codes.ok:
        root = ET.fromstring(r.text.encode('utf-8'))
        response_list = root.findall('response')
        for res_obj in response_list:
            order_serial_no = ''
            status = ''
            try:
                order_serial_no = res_obj.find('order_serial_no').text
                status = res_obj.find('status').text
                msg = res_obj.find('msg').text
                results.append({
                    'order_serial_no': order_serial_no,
                    'status': status,
                    'msg': msg
                })
                succ_cnt += 1
            except Exception as e:
                results.append({
                    'order_serial_no': order_serial_no,
                    'status': status,
                    'msg': e.message
                })
        cancel_cn_tracking(results)

    else:
        request_result = "请求异常, 代码" + r.status_code

    return request_result, results, succ_cnt


def lookup(ws):
    request_result = "请求发送成功"
    results = []
    succ_cnt = 0
    xml = dicttoxml.dicttoxml(
        [{'order_serial_no': w.tracking_no, 'mailno': w.cn_tracking, 'print_file': '0', 'json_data': '1'} for w in ws],
        attr_type=False, custom_root='orders', item_func=my_item_func)
    validation = md5(base64_encode(str(xml)) + partnerid + secect)
    post_data = {'partnerid': partnerid,
                 'version': version,
                 'xmldata': base64_encode(str(xml)),
                 'validation': validation
                 }

    r = requests.post(lookup_url, data=post_data)
    if r.status_code == requests.codes.ok:
        root = ET.fromstring(r.text.encode('utf-8'))
        response_list = root.findall('response')
        for res_obj in response_list:
            try:
                pdf_info = json.loads(res_obj.find('json_data').text)
                position = pdf_info[0][0]['position']
                position_no = pdf_info[0][0]['position_no']
                # print json.dumps({'position': position, 'position_no': position_no})

                order_serial_no = res_obj.find('order_serial_no').text
                mailno = res_obj.find('mailno').text
                status = res_obj.find('status').text
                msg = res_obj.find('msg').text
                order_status = res_obj.find('order_status').text
                results.append({
                    'order_serial_no': order_serial_no,
                    'mailno': mailno,
                    'status': status,
                    'order_status': order_status,
                    'yd_info': json.dumps({'position': position, 'position_no': position_no}),
                    'msg': msg
                })
                succ_cnt += 1
            except Exception as e:
                results.append({
                    'order_serial_no': '',
                    'mailno': mailno,
                    'status': status,
                    'order_status': order_status,
                    'yd_info': '',
                    'msg': e.message
                })
    else:
        request_result = "请求异常, 代码" + r.status_code
    return request_result, results, succ_cnt


def cn_transist(ws):
    xml = dicttoxml.dicttoxml(
        [w.cn_tracking.strip() for w in ws], attr_type=False, custom_root='mailnos', item_func=my_item_func)
    validation = md5(base64_encode(str(xml)) + partnerid + secect)
    post_data = {'partnerid': partnerid,
                 'version': version,
                 'xmldata': base64_encode(str(xml)),
                 'validation': validation
                 }
    from requests.adapters import HTTPAdapter

    s = requests.Session()
    s.mount(cn_transist_url, HTTPAdapter(max_retries=3))
    r = s.post(cn_transist_url, data=post_data)
    # return r.text.encode('utf-8')
    return cn_transist_to_dict_list(r)


'''
1 not found, status is -1
[{u'status': -1, u'mailNo': u'7700037590935', u'flag': True, u'expTextName': u'\u97f5\u8fbe'}]
2 has result, status > 0
'''


def cn_transist_to_dict_list(r):
    cn_results = []
    if r.status_code == requests.codes.ok:
        d = xmltodict.parse(r.text.encode('utf-8'))
        if type(d['responses']['response']) == list:
            response_list = d['responses']['response']
        else:
            response_list = [d['responses']['response']]

        for response in response_list:
            cn = {}
            for k in response:
                v = response[k]
                if k == 'traces':
                    cn['data'] = []
                    for trace in v['trace']:
                        cn['data'].append({
                            'context': '[%s] %s' % (trace['station'], trace['remark']),
                            'time': trace['time']
                        })
                else:
                    if k == 'mailno':
                        cn['mailNo'] = v
                    elif k == 'result':
                        cn['flag'] = True if v == 'true' else False
                    elif k == 'status':
                        if not v:
                            cn['status'] = -1
                            break
                        else:
                            cn['status'] = STATUS_MAP[v]
            cn['expTextName'] = '韵达'
            cn_results.append(cn)
        return cn_results
    return None


def waybill_process(w, mail_no, status, position, position_no):
    if status == '1':
        try:
            msg = duplicate_process(mail_no)
            QFTracking.objects.create(tracking_no=mail_no, waybill=w, is_used=True)
            w.cn_tracking = mail_no
            w.yd_info = json.dumps({'position': position, 'position_no': position_no})
            c = Channel.objects.get(name=CH14)
            w.channel = c
            w.save()
            return '成功绑定国内单号' + msg, True
        except Exception as e:
            return '绑定国内单号异常:' + e.message, False
    else:
        return '状态异常', False


def duplicate_process(mail_no):
    msg = ''
    if QFTracking.objects.filter(tracking_no=mail_no).exists():
        qf = QFTracking.objects.filter(tracking_no=mail_no).first()
        if qf.waybill:
            if qf.waybill.cn_tracking != mail_no:
                msg = '重复单号处理: {0},{1}, 韵达单号不同,直接删除qf记录'.format(qf.waybill.tracking_no, qf.waybill.cn_tracking)
                qf.delete()
            else:
                if qf.waybill.status.name == '运单异常' and not qf.waybill.pallet and not qf.waybill.status_set.filter(
                        status__name='国内清关').exists():
                    msg = '重复单号处理: {0},{1}, 韵达单号相同, 未报关,删除qf记录并清除原运单'.format(qf.waybill.tracking_no,
                                                                             qf.waybill.cn_tracking)
                    qf.waybill.cn_tracking = None
                    qf.waybill.save()
                    qf.delete()
                else:  # 报了关口的
                    msg = '重复单号处理: {0},{1}, 已报关, 需要重新叫单'.format(qf.waybill.tracking_no, qf.waybill.cn_tracking)
        else:
            msg = '重复单号处理: 对应运单不存在,直接删除qf记录'
            qf.delete()
    return " " + msg


def fetch_yunda(qs):
    # get A channel yunda cn tracking
    succ_cnt = 0
    error_list = []
    succ_list = []
    for w in qs:
        tracking_no = w.tracking_no
        new_cn_tracking = ''
        msg = ''
        is_succ = False

        if not w.cn_tracking:
            order_serial_no, result_mail_no, result_msg, status, position, position_no = upsert_one(w)

            msg, is_succ = waybill_process(w, result_mail_no, status, position, position_no)

            if is_succ:
                succ_list.append({
                    'tracking_no': order_serial_no,
                    'cn_tracking': result_mail_no,
                    'msg': result_msg
                })
                succ_cnt += 1
            else:
                error_list.append({
                    'tracking_no': order_serial_no,
                    'cn_tracking': '',
                    'msg': result_msg
                })
        else:
            error_list.append({
                'tracking_no': w.tracking_no,
                'cn_tracking': w.cn_tracking,
                'msg': '已有国内单号'
            })

    return succ_cnt, error_list, succ_list


def auto_create():
    qs = Waybill.objects.filter(cn_tracking__isnull=True).filter(channel__name=CH14).filter(
        status__name__in=['已建单', '已传身份证'])
    cnt = 0
    g_cnt = int(math.ceil(len(qs) / 200.0))
    f_list = []
    for i in range(g_cnt):
        request_result, succ_cnt, fail_waybills = bulk_create(qs[i * 200: min(len(qs), (i + 1) * 200)])
        f_list += fail_waybills
        cnt += succ_cnt
    succ_list, fail_list = one_by_one_create(f_list)
    cnt += len(succ_list)
    return cnt
