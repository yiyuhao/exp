# -*- coding: utf-8 -*
import httplib
import json
import urllib
import urllib2
from datetime import datetime
from decimal import Decimal

import requests

import pytz
import xlsxwriter
from django.conf import settings
from django.utils import timezone

from express import settings
from express.crypto import md5
from pallets.models import CH12, CH17, CH18, CH19


def toEng(chineseStr):
    if not chineseStr:
        return ''

    url = 'https://www.googleapis.com/language/translate/v2?'
    data = {
        'target': 'en',
        'source': 'zh',
        'format': 'text',
        'key': 'AIzaSyB5RJPyU_kvM2Rpz6LQwZ0L-3p85w4itsw',
    }
    if isinstance(chineseStr, list):
        arry = [urllib.quote(to_utf8(x)) for x in chineseStr]
        qstr = "&q=" + "&q=".join(arry)
        url = url + urllib.urlencode(data) + qstr

    elif isinstance(chineseStr, str) or isinstance(chineseStr, unicode):
        data['q'] = to_utf8(chineseStr)
        url = url + urllib.urlencode(data)
    else:
        raise Exception("type error")
    try:
        response = urllib2.urlopen(url, timeout=10)
        a = json.loads(response.read())
        return [o['translatedText'] for o in a['data']['translations']]
    except Exception as e:
        if settings.DEBUG:
            print e
        if isinstance(chineseStr, list):
            return ['']
        else:
            return ['' for x in chineseStr]


def to_utf8(text):
    if isinstance(text, unicode):
        # unicode to utf-8
        return text.encode('utf-8')
    try:
        # maybe utf-8
        return text.decode('utf-8').encode('utf-8')
    except UnicodeError:
        # gbk to utf-8
        return text.decode('gbk').encode('utf-8')


def remove_sheng_shi_zizhiqu(s):
    return s.replace(u"省", '').replace(u"市", '').replace(u'回族自治区', '').replace(u'壮族自治区', '').replace(u'维吾尔自治区',
                                                                                                     '').replace(u"自治区",
                                                                                                                 '')


CN_WAYBILL_STATUS = {
    -1: '待查询',
    0: '查询异常',
    1: '暂无记录',
    2: '在途中',
    3: '派送中',
    4: '已签收',
    5: '用户拒签',
    6: '疑难件',
    7: '无效单',
    8: '超时单',
    9: '签收失败',
    10: '退回',
}


def check_cn_status(w):
    from express.yunda_api import cn_transist
    if w.channel.name in ["A1", 'A2', 'A3']:
        js_obj = cn_transist([w])[0]
        return None if js_obj['status'] == -1 else json.dumps(js_obj)
    # if w.channel.name in ["A1", 'A2', 'A3']:
    #     return get_cn_status(w.cn_tracking, 'yunda')
    elif w.channel.name in [CH17, CH18, CH19]:
        return get_cn_status(w.cn_tracking, 'gnxb')
    else:
        if w.cn_tracking.startswith('5'):
            return get_cn_status(w.cn_tracking, 'huitong')
        elif w.cn_tracking.startswith('9'):
            return get_cn_status(w.cn_tracking, 'gnxb')

        return get_cn_status(w.cn_tracking)


def get_cn_status(nu, company='auto'):
    if nu.lower().startswith('cy') or nu.lower().startswith('be') or nu.lower().startswith('bs'):
        company = 'ems'

    host = 'https://ali-deliver.showapi.com'
    path = '/showapi_expInfo'
    appcode = 'bac2d753f4f24ec79deb4eb18a3ba95a'
    querys = 'com={company}&nu={tracking}'.format(company=company, tracking=nu)
    url = host + path + '?' + querys
    headers = {'Authorization': 'APPCODE ' + appcode}
    try:
        response = requests.get(url, headers=headers)
        a = json.loads(response.text)
        if a['showapi_res_body']['flag']:
            return json.dumps(a['showapi_res_body'])
        else:
            return None
    except Exception as e:
        # print '\n', company, nu
        # print(e)
        # print(e.read())
        return None


def check_waybill_cn_status(nu):
    host = 'https://ali-deliver.showapi.com'
    path = '/showapi_expInfo'
    appcode = 'bac2d753f4f24ec79deb4eb18a3ba95a'
    querys = 'com={company}&nu={tracking}'.format(company='auto', tracking=nu)
    url = host + path + '?' + querys
    request = urllib2.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    result_code = 0
    try:
        response = urllib2.urlopen(request)
        a = json.loads(response.read())
        if a['showapi_res_body']['status']:
            result_code = a['showapi_res_body']['status']
    except Exception as e:
        print(e)
        print(e.read())
        return None
    return CN_WAYBILL_STATUS[result_code]


def toTZDatetime(datestr, format='%m/%d/%Y', timezone_name=timezone.get_current_timezone_name()):
    naive = datetime.strptime(datestr, format)
    return pytz.timezone(timezone_name).localize(naive, is_dst=None)


def send_sms4(mobile, name, tracking_no):
    text = u'【士奇快递】{0}亲! 快戳 www.huskyex.com/u/?m={1} 补全身份证信息, 别让您的包裹在美国仓滞留'.format(name, tracking_no)
    return sms_base(text, mobile, name, tracking_no)


def send_sms_specail(mobile):
    text = '【士奇快递】尊敬的客户，您好，由于士奇快递后台系统信息匹配有误致使包裹面单上姓名信息错误，电话地址无误，请您签收包裹时正常签收。给您造成了不便，望您能理解，感谢您的支持！'
    return sms_base(text, mobile, '', '')


def send_sms_upload_id_card(mobile, tracking_no, name):
    text = u'【士奇快递】{0}，您的包裹缺少身份证正反面照片，请至 www.huskyex.com/u/?m={1} 补交'.format(name, tracking_no)
    return sms_base(text, mobile, '', '')


def send_sms_person_id_1(mobile, name, tracking_no):
    text = u'【士奇快递】{0}，您的包裹缺少身份证信息，无法清关，请至 www.huskyex.com/u/?m={1} 上传身份证'.format(name, tracking_no)
    return sms_base(text, mobile, '', '')


def send_sms_person_id_2(mobile, name, tracking_no):
    text = u'【士奇快递】{0}，您的包裹缺少身份证信息，无法清关，请至 www.huskyex.com/u/?m={1} 上传身份证（最后一次通知，2日内不传将取消订单，请及时上传保证你的包裹能正常出单发货）'.format(
        name, tracking_no)
    return sms_base(text, mobile, '', '')


def sms_base(text, mobile, name, tracking_no):
    api_key = 'f747236500f7582e653329d1cbd4151b'
    sms_host = "sms.yunpian.com"
    port = 443
    version = "v2"
    sms_send_uri = "/" + version + "/sms/single_send.json"
    params = urllib.urlencode({'apikey': api_key, 'text': to_utf8(text), 'mobile': mobile})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = httplib.HTTPSConnection(sms_host, port=port, timeout=30)
    conn.request("POST", sms_send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return json.loads(response_str)


YHC_WAYBILL_STATUS = {
    -1: '查询失败',
    5: '待收货',
    10: '海外仓入仓（入库）',
    20: '发往国内（出库）',
    21: '起飞',
    25: '到达国内',
    30: '清关中',
    31: '抽检',
    35: '税费',
    40: '国内配送（清关完毕）',
    41: '国内配送-揽件',
    42: '国内配送-疑难件',
    45: '国内配送-用户签收',
    48: '国内配送-用户拒收',
    49: '国内配送-退签或退回寄件',
}


def get_yhc_status(tracking_no):
    '''
    http://testapi.1hcang.com/ExpressTrack/Track?expressno={单据号}&appid={appid}& token={计算后的token }

    :param tracking_no: 
    :return: json response
    
    '''

    appid = 'sauir2'
    appkey = '75a3ac2db45f468484c2f995e1c6d473'
    token = md5(appkey + tracking_no)
    url = 'http://api.1hcang.com/ExpressTrack/Track?expressno={tracking_no}&appid={appid}&token={token}'.format(
        tracking_no=tracking_no, appid=appid, token=token)
    try:
        req = urllib2.Request(url, headers={'Content-Type': 'application/json'})
        res = urllib2.urlopen(req).read()
        return json.loads(res)
    except Exception as e:
        return {"code": 0, "msg": "请求异常"}


def export_xls_pic():
    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook('images.xlsx')
    worksheet = workbook.add_worksheet()

    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 30)

    # Insert an image.
    worksheet.write('A2', 'Insert an image in a cell:')
    worksheet.insert_image('B2', 'python.png')

    # Insert an image offset in the cell.
    worksheet.write('A12', 'Insert an image with an offset:')
    worksheet.insert_image('B12', 'python.png', {'x_offset': 15, 'y_offset': 10})

    # Insert an image with scaling.
    worksheet.write('A23', 'Insert a scaled image:')
    worksheet.insert_image('B23', 'python.png', {'x_scale': 0.5, 'y_scale': 0.5})

    workbook.close()


def is_cn_day_time():
    cn_hour = timezone.now().astimezone(pytz.timezone("Asia/Shanghai")).hour
    return cn_hour >= 7 and cn_hour <= 22


def fetch_usd_cnh():
    url = 'https://forex.1forge.com/1.0.3/convert?from=USD&to=CNH&quantity=100&api_key=iN8mJfG0ytBeV1RUP9GXLpYDWsdSYOyy'
    response = requests.get(url)
    a = json.loads(response.text)
    return Decimal(a['value']) / Decimal('100')
