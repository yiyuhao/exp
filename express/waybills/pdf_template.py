# -*- coding: utf-8 -*
from __future__ import unicode_literals
import datetime
import random
from decimal import Decimal
import os

from django.http import HttpResponse
from reportlab.graphics.barcode import code128, code39, code93
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Frame
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm, inch, cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfdoc
from django.conf import settings

from addresses.models import ExpressMark
from pallets.models import *
import json
import uuid

R4 = (4 * inch, 6 * inch)
SMALL_LABEL = ((2 + 5 / 8.0) * inch, 1 * inch)


def get_small_label_response(obj):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % obj[u'tracking_no']

    c = Canvas(response, pagesize=SMALL_LABEL)

    small_one_page(c, obj)

    c.save()
    return response


def get_barcode_label(code):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % 'code'

    c = Canvas(response, pagesize=SMALL_LABEL)

    barcode = code128.Code128(code, barWidth=0.3 * mm, barHeight=0.38 * inch, humanReadable=1,
                              fontSize=12,
                              fontName='Times-Roman')
    barcode.drawOn(c, 0.2 * inch, 0.35 * inch)
    c.showPage()

    c.save()
    return response


def small_one_page(c, obj):
    barcode = code128.Code128(obj[u'tracking_no'], barWidth=0.3 * mm, barHeight=0.38 * inch, humanReadable=1,
                              fontSize=12,
                              fontName='Times-Roman')
    barcode.drawOn(c, 0.2 * inch, 0.3 * inch)
    c.drawString(0.2 * inch, 0.75 * inch, obj[u'detail'])
    c.showPage()


def get_pdf_response(obj):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % obj[u'tracking_no']

    c = Canvas(response, pagesize=letter)

    default_one_page(c, obj)

    c.save()
    return response


def default_one_page(c, obj):
    barcode = code128.Code128(obj[u'tracking_no'], barWidth=0.3 * mm, barHeight=12 * mm, humanReadable=1, fontSize=12,
                              fontName='Times-Roman')
    data = [['HuskyEx', barcode],
            [u'运单信息', obj[u'tracking_no']],
            [u'发件人', obj[u'sender_name']],
            [u'收件人', obj[u'recv_name']],
            [u'商品信息', obj[u'detail']],
            [u'个数', obj[u'total']],
            [u'描述', obj[u'detail']],
            [u'备注', obj[u'remark']],
            ]
    style = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 1), (1, 1), colors.lightgrey),
        ('SPAN', (0, 4), (1, 4)),
        ('BACKGROUND', (0, 4), (1, 4), colors.lightgrey),
        ('FONT', (0, 0), (-1, -1), 'STSong-Light'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTSIZE', (0, 0), (1, 0), 20),
        ('VALIGN', (0, 0), (1, 0), 'MIDDLE'),
        ('FONT', (0, 0), (1, 0), 'Times-Roman'),
        ('FONT', (1, 6), (1, 6), 'Times-Roman'),
        ('VALIGN', (1, 6), (1, 6), 'TOP'),

        ('FONTSIZE', (1, 6), (1, 6), 20),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        # ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.white),
    ]
    height = 4.5 * inch
    width = 7.5 * inch
    t = Table(data, style=style,
              colWidths=[1.5 / 6.0 * width, 4.5 / 6.0 * width],
              rowHeights=[2 / 11.0 * height,
                          1 / 12.0 * height,
                          1 / 12.0 * height,
                          1 / 12.0 * height,
                          1 / 12.0 * height,
                          1 / 12.0 * height,
                          3 / 12.0 * height,
                          1 / 11.0 * height
                          ])
    story = []
    story.append(t)
    f = Frame(0.5 * inch, 6 * inch, 7.5 * inch, 4.5 * inch, showBoundary=0)
    f.addFromList(story, c)
    c.saveState()
    c.setDash(1, 2)
    l = c.beginPath()
    l.moveTo(0.5 * inch, 5.5 * inch)
    l.lineTo(8 * inch, 5.5 * inch)
    l.close()
    c.drawPath(l, stroke=1)
    c.restoreState()
    barcode = code128.Code128(obj[u'tracking_no'], barWidth=0.8 * mm, barHeight=30 * mm, humanReadable=1, fontSize=30,
                              fontName='Times-Roman')
    data2 = [[barcode]]
    style2 = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]
    t2 = Table(data2, style=style2, rowHeights=[4.2 * inch])
    f2 = Frame(0.5 * inch, 0.5 * inch, 7.5 * inch, 4.5 * inch, showBoundary=1)
    story2 = [t2]
    f2.addFromList(story2, c)
    c.showPage()


def yhc_one_page(c, obj):
    # 固定内容
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=1)
    f.addFromList(story, c)
    # 广告
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 7
    style.wordWrap = 'CJK'
    style.leading = 9
    info = u'一号仓 www.1hcang.com'
    text = u'服务最好的跨境进出口服务商, 已开通美国, 日本,澳大利亚, 英国, 德国, 意大利, 韩国, 香港, 加拿大等国家的海淘转运, 海外仓和FBA退货等业务'
    story.append(Paragraph(info, style))
    story.append(Paragraph(text, style))
    f = Frame(0.2 * inch, 0.23 * inch, 2.24 * inch, 0.7 * inch, showBoundary=0)
    f.addFromList(story, c)
    # 从上到下划线
    x1, x2 = 0.08 * inch, 3.92 * inch
    y1 = 5.22 * inch
    y2 = 2.3 * inch
    y3 = 1.01 * inch
    draw_line_horizontal(c, x1, x2, y1)
    draw_line_horizontal(c, x1, x2, y2)
    draw_line_horizontal(c, x1, x2, y3)
    # 一号仓条码
    bx = 0.2 * inch
    by = 1.4 * inch
    barcode = code128.Code128(obj[u"tracking_no"], barWidth=0.35 * mm, barHeight=0.68 * inch, humanReadable=1,
                              fontSize=14)
    barcode.drawOn(c, bx, by)
    c.drawImage('static/img/1hcqr.jpg', 2.76 * inch, 0.12 * inch, width=1.14 * inch, height=1.167 * inch)
    c.drawImage('static/img/1hclogo.jpg', 0.1 * inch, 5.3 * inch, width=1.4 * inch, height=.54 * inch)
    t1 = u'客服: 0755-8939959'
    t2 = u'网址: www.1hcang.com'
    x = 2.26 * inch
    y1 = 5.66 * inch
    y2 = 5.46 * inch
    c.setFont("STSong-Light", 12)
    c.drawString(x, y1, t1)
    c.drawString(x, y2, t2)
    c.drawString(3.13 * inch, 2 * inch, u'无忧专线')
    # 收件人信息
    address_title = u'收件人姓名及地址'
    name_mobile = u'%s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_p_c = u'%s %s' % (obj[u'recv_prov'], obj[u'recv_city'])
    recv_addr = obj[u'recv_address']
    # 商品信息
    us_tracking_no = u'海外挂号: %s' % obj[u'tracking_no']
    goods = u'商品信息: %s' % obj[u'goods']
    story = []
    styleH = ParagraphStyle('Heading1')
    styleH.fontName = "STSong-Light"
    styleH.fontSize = 14
    styleH.wordWrap = 'CJK'
    styleH.leading = 16
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 11
    style.wordWrap = 'CJK'
    style.leading = 16
    style.leftIndent = 12
    style2 = ParagraphStyle('Normal')
    style2.fontName = "STSong-Light"
    style2.fontSize = 11
    style2.wordWrap = 'CJK'
    style2.leading = 16
    story.append(Paragraph(address_title, styleH))
    story.append(Spacer(2.24 * inch, 0.12 * inch))
    story.append(Paragraph(name_mobile, style))
    story.append(Spacer(2.24 * inch, 0.1 * inch))
    story.append(Paragraph(recv_p_c, style))
    story.append(Paragraph(recv_addr, style))
    story.append(Spacer(2.24 * inch, 0.15 * inch))
    story.append(Paragraph(us_tracking_no, style2))
    story.append(Spacer(2.24 * inch, 0.05 * inch))
    story.append(Paragraph(goods, style2))
    f = Frame(0.2 * inch, 2.4 * inch, 3.7 * inch, 2.8 * inch, showBoundary=0)
    f.addFromList(story, c)
    c.showPage()


def bc_pdf_response2(obj):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % obj['cn_tracking_no']
    '''
        obj = {
            u"cn_tracking_no": u'410014900217',
            u"recv_prov": u"上海",
            u"recv_city": u'上海市',
            u"recv_address": u'虹口区七浦路189号老兴旺9号打发第三方打算',
            u'recv_name': u'张三',
            u'mobile': '1390000000',
            u'goods': u'商品: %s' % u'trunmvd 保健品 * 9, coach 包 * 1, trunmvd 保健品 * 9, coach 包 * 1,trunmvd 保健品 * 9, coach 包 * 1'
        }
    '''
    c = Canvas(response, pagesize=R4)

    ## barcdoe ##
    qfbarcodeSm = code128.Code128(obj['cn_tracking_no'], barWidth=0.43 * mm, barHeight=0.2 * inch, humanReadable=1,
                                  fontSize=8,
                                  fontName='Times-Roman')

    qfbarcodeMd = code128.Code128(obj['cn_tracking_no'], barWidth=0.5 * mm, barHeight=0.35 * inch, humanReadable=1,
                                  fontSize=10,
                                  fontName='Times-Roman')

    qfbarcodeBg = code128.Code128(obj['cn_tracking_no'], barWidth=0.5 * mm, barHeight=0.38 * inch, humanReadable=1,
                                  fontSize=12,
                                  fontName='Times-Roman')

    qfbarcodeSm.drawOn(c, 1.65 * inch, 4.83 * inch)
    qfbarcodeMd.drawOn(c, 0.907 * inch, 3.15 * inch)
    qfbarcodeBg.drawOn(c, 1.45 * inch, 1.85 * inch)

    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)

    ### 从上到下划线 ###
    x1, x2 = 0 * inch, 4 * inch
    y1 = 5.43 * inch
    y2 = 5.03 * inch
    y3 = 4.62 * inch
    y4 = 3.88 * inch
    y5 = 3.52 * inch
    y6 = 3.02 * inch
    y7 = 2.4 * inch  # 分割线
    y8 = 1.711 * inch
    y9 = 1.092 * inch
    y10 = 0.686 * inch

    ys = [y1, y2, y3, y4, y5, y6, y8, y9, y10]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ### 从左到右 ###
    xv1 = 0.287 * inch
    xv2 = 1.71 * inch
    draw_line_vertical(c, y5, y3, xv1)
    draw_line_vertical(c, y10, y8, xv1)
    draw_line_vertical(c, y7, y6, xv2)

    ### 固定内容 ###

    c.drawImage('static/img/ydlogo.jpg', 0.149 * inch, 5.512 * inch, width=1.08 * inch, height=.42 * inch)
    c.drawImage('static/img/ydlogo.jpg', 2.47 * inch, 0.23 * inch, width=1.08 * inch, height=.42 * inch)
    c.drawImage('static/img/qflogo2.jpg', 2.526 * inch, 5.512 * inch, width=.947 * inch, height=.42 * inch)
    c.drawImage('static/img/qflogo2.jpg', 0.316 * inch, 1.749 * inch, width=.947 * inch, height=.42 * inch)
    # im = Image('static/1hclogo.jpg', width=1.4 * inch, height=.54 * inch)
    # c.drawImage(im, 0.08 * inch, 5    .33 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, 4.27 * inch, u'收')
    c.drawString(0.1 * inch, 4.05 * inch, u'件')
    c.drawString(0.1 * inch, 3.74 * inch, u'寄')
    c.drawString(0.1 * inch, 3.54 * inch, u'件')

    c.drawString(0.124 * inch, 1.42 * inch, u'收')
    c.drawString(0.124 * inch, 1.25 * inch, u'件')
    c.drawString(0.124 * inch, 0.90 * inch, u'寄')
    c.drawString(0.124 * inch, 0.724 * inch, u'件')

    c.drawString(0.323 * inch, 0.782 * inch, u'发件人: 北京林德国际运输代理有限公司')
    c.drawString(0.323 * inch, 3.62 * inch, u'发件人: 北京林德国际运输代理有限公司')

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 6
    style.wordWrap = 'CJK'
    style.leading = 6
    info = u'快件送达收件人地址，经收件人或收件人(寄件人)允许的代收人签字，视为送达。您的签字代表您已验收此包裹，并已确认商品信息无误、包装完好、没有划痕、破损等表面质量问题。'
    story.append(Paragraph(info, style))

    f = Frame(0.03 * inch, 2.32 * inch, 1.7 * inch, 0.7 * inch, showBoundary=0)
    f.addFromList(story, c)

    c.drawString(1.74 * inch, 2.83 * inch, u'签收人:')
    c.drawString(1.74 * inch, 2.44 * inch, u'时间:')

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 9
    style.wordWrap = 'CJK'
    style.leading = 9
    info = u'已验视'
    story.append(Paragraph(info, style))

    f = Frame(0.06 * inch, 3.09 * inch, 0.723 * inch, 0.31 * inch, showBoundary=1)
    f.addFromList(story, c)

    ### 收件人信息 ###

    c.setFont("STSong-Light", 13)

    c.drawString(0.136 * inch, 5.15 * inch, obj[u"recv_prov"])
    c.drawString(1.994 * inch, 5.15 * inch, obj[u"recv_city"])

    c.drawString(0.34 * inch, 4.38 * inch, obj[u'recv_name'])
    c.drawString(1.78 * inch, 4.38 * inch, obj[u'mobile'])

    c.setFont("STSong-Light", 10)
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 10
    recv_cb = u'%s   %s   %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_city"] + obj[u"recv_address"])
    story.append(Paragraph(recv_cb, style))

    f = Frame(0.24 * inch, 3.92 * inch, 3.54 * inch, 0.45 * inch, showBoundary=0)
    f.addFromList(story, c)

    c.drawString(0.34 * inch, 1.54 * inch, obj[u'recv_name'])
    c.drawString(1.78 * inch, 1.54 * inch, obj[u'mobile'])

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 10
    story.append(Paragraph(recv_cb, style))

    f = Frame(0.24 * inch, 1.09 * inch, 3.54 * inch, 0.45 * inch, showBoundary=0)
    f.addFromList(story, c)

    ### 商品信息 #####

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 9
    style.wordWrap = 'CJK'
    style.leading = 9
    story.append(Paragraph(obj[u'tracking_no'], style))
    story.append(Paragraph(obj[u'goods'], style))

    f = Frame(0.09 * inch, 0.09 * inch, 2.2 * inch, 0.6 * inch, showBoundary=0)
    f.addFromList(story, c)

    c.save()

    return response


def bc_pdf_response(obj):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % obj['cn_tracking_no']

    c = Canvas(response, pagesize=R4)

    bc_one_page(c, obj)

    c.save()

    return response


def bc_one_page(c, obj):
    ## barcdoe ##
    qfbarcode = code128.Code128(obj['cn_tracking_no'], barWidth=0.02 * inch, barHeight=0.8 * inch, humanReadable=1,
                                fontSize=13,
                                fontName='Times-Roman')
    qfbarcode.drawOn(c, 0.5 * inch, 0.5 * inch)
    ### 从上到下划横线 ###
    x1, x2 = 0.25 * inch, (4 - 0.25) * inch
    y1 = (6 - 0.25) * inch
    y2 = 2 * inch
    y3 = 4 * inch
    y4 = 0.25 * inch
    ys = [y1, y2, y3, y4]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ### 从左到右花竖线 ###
    draw_line_vertical(c, y1, y4, x1)
    draw_line_vertical(c, y1, y4, x2)
    # LOGO
    c.setFontSize(33)
    c.drawString(0.35 * inch, 5.32 * inch, 'HuskyEx')
    # web site
    c.setFontSize(8.5)
    c.drawString(0.38 * inch, 5.19 * inch, 'www.huskyex.com')
    # From
    c.setFontSize(8)
    c.drawString(2.63 * inch, 5.6 * inch, 'From:')
    story = []
    style = ParagraphStyle('Normal')
    style.fontSize = 8
    style.wordWrap = 'LTR'
    info = '77 Glendale Ave, Edison, NJ 08817'
    story.append(Paragraph(info, style))
    f = Frame(2.63 * inch, 5 * inch, 1.25 * inch, 0.55 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)
    # TRAC
    c.setFont('Helvetica-Bold', 10)
    c.drawString(0.376 * inch, 4.9 * inch, 'TRAC: {0}'.format(obj['tracking_no']))
    # SHIP TO
    c.setFont('Helvetica', 10)
    c.drawString(0.376 * inch, 4.66 * inch, 'Ship to:')
    c.setFont('STSong-Light', 10)
    c.drawString(0.932 * inch, 4.66 * inch, u'{0}  {1}'.format(obj['mobile'], obj['recv_name']))
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 10
    info = u'{0}   {1}   {2}'.format(obj['recv_prov'], obj['recv_city'], obj['recv_address'])
    story.append(Paragraph(info, style))
    f = Frame(0.376 * inch, 4 * inch, 3.24 * inch, 0.632 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              topPadding=0, rightPadding=0)
    f.addFromList(story, c)
    # Items
    c.setFont('Helvetica', 10)
    c.drawString(0.376 * inch, 3.75 * inch, u'Items:')
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'LTR'
    style.leading = 10
    story.append(Paragraph(obj[u'goods'], style))
    f = Frame(0.376 * inch, 2.12 * inch, 3.24 * inch, 1.6 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              topPadding=0, rightPadding=0)
    f.addFromList(story, c)
    # TRAC2
    c.setFontSize(10)
    c.drawString(0.376 * inch, 1.817 * inch, 'TRAC: {0}'.format(obj['tracking_no']))
    # logo
    c.setFontSize(16)
    c.drawString(2.78 * inch, 1.79 * inch, 'HuskyEx')
    # us-cn
    c.setFontSize(10)
    c.drawString(0.376 * inch, 1.43 * inch, 'US-CN')
    c.setFontSize(10)
    c.drawString(2.17 * inch, 4.9 * inch, 'US-CN: ' + obj['cn_tracking_no'])
    c.showPage()


def normal_one_page(c, mark, obj):
    ### 从上到下划横线 ###
    x1, x2 = 0.25 * inch, (4 - 0.25) * inch
    y1 = (6 - 0.25) * inch
    y2 = 4 * inch
    y3 = 3 * inch
    y4 = 0.25 * inch
    ys = [y1, y2, y3, y4]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ## barcdoe ##
    qfbarcode_down = code128.Code128(obj['tracking_no'], barWidth=0.02 * inch, barHeight=0.8 * inch, humanReadable=1,
                                     fontSize=13,
                                     fontName='Times-Roman')

    qfbarcode_up = code128.Code128(obj['tracking_no'], barWidth=0.01 * inch, barHeight=0.4 * inch, humanReadable=0,
                                   fontSize=13,
                                   fontName='Times-Roman')

    qfbarcode_down.drawOn(c, 0.5 * inch, 0.5 * inch)
    qfbarcode_up.drawOn(c, 2 * inch, 5.2 * inch)

    # LOGO
    c.setFontSize(20)
    c.drawString(0.35 * inch, 5.32 * inch, 'HuskyEx')

    # TRAC
    c.setFont('Helvetica-Bold', 10)
    c.drawString(0.376 * inch, 4.9 * inch, 'TRAC: {0}'.format(obj['tracking_no']))
    # SHIP TO
    c.setFont('Helvetica', 10)
    c.drawString(0.376 * inch, 4.66 * inch, 'Ship to:')
    c.setFont('STSong-Light', 10)
    c.drawString(0.932 * inch, 4.66 * inch, u'{0}  {1}'.format(obj['mobile'], obj['recv_name']))
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 10
    info = u'{0}   {1}   {2}'.format(obj['recv_prov'], obj['recv_city'], obj['recv_address'])
    story.append(Paragraph(info, style))
    f = Frame(0.376 * inch, 4 * inch, 3.24 * inch, 0.632 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              topPadding=0, rightPadding=0)
    f.addFromList(story, c)
    # Items
    c.setFont('Helvetica', 10)
    c.drawString(0.376 * inch, 3.75 * inch, u'Items:')
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'LTR'
    style.leading = 10
    story.append(Paragraph(obj[u'goods'], style))
    f = Frame(0.376 * inch, 2.12 * inch, 3.24 * inch, 1.6 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              topPadding=0, rightPadding=0)
    f.addFromList(story, c)
    # SHIP 2
    c.setFont('Helvetica', 10)
    c.drawString(0.376 * inch, 2.76 * inch, 'Ship to:')
    c.setFont('STSong-Light', 10)
    c.drawString(0.932 * inch, 2.76 * inch, u'{0}  {1}'.format(obj['mobile'], obj['recv_name']))
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 10
    info = u'{0}   {1}   {2}'.format(obj['recv_prov'], obj['recv_city'], obj['recv_address'])
    story.append(Paragraph(info, style))
    f = Frame(0.376 * inch, 2 * inch, 3.24 * inch, 0.632 * inch, showBoundary=0, leftPadding=0, bottomPadding=0,
              topPadding=0, rightPadding=0)
    f.addFromList(story, c)

    # TRAC2
    c.setFontSize(10)
    c.drawString(0.376 * inch, 1.817 * inch, 'TRAC: {0}'.format(obj['tracking_no']))
    # logo
    c.setFontSize(16)
    c.drawString(2.78 * inch, 1.79 * inch, 'HuskyEx')
    # us-cn
    c.setFontSize(10)
    c.drawString(0.376 * inch, 1.43 * inch, 'US-CN')
    c.setFontSize(15)
    c.drawString(3.2 * inch, 3.5 * inch, mark)
    c.showPage()


def qd_one_page(c, obj):
    c.setDash(1, 1)
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2 = 0.067 * inch, 3.922 * inch
    y1 = 0.042 * inch
    y2 = 0.542 * inch
    y3 = 1.505 * inch
    y4 = 2.194 * inch
    y5 = 2.459 * inch
    y6 = 3.163 * inch
    y7 = 3.856 * inch
    y8 = 4.613 * inch
    y9 = 4.999 * inch
    y10 = 5.305 * inch
    y11 = 5.942 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ### 从左到右 ###
    xv1 = 1.513 * inch
    xv2 = 2.028 * inch
    xv3 = 3.046 * inch
    xv4 = 2.034 * inch
    draw_line_vertical(c, y1, y3, x1)
    draw_line_vertical(c, y4, y10, x1)
    draw_line_vertical(c, y1, y3, x2)
    draw_line_vertical(c, y4, y10, x2)
    draw_line_vertical(c, y9, y8, xv2)
    draw_line_vertical(c, y2, y3, xv2)
    draw_line_vertical(c, y9, y8, xv3)
    draw_line_vertical(c, y7, y6, xv4)
    ### 固定内容 ###
    c.drawImage('static/img/ems.png', x1 + 0.02 * inch, y10 + 0.06 * inch, width=1.393 * inch, height=0.566 * inch)
    c.drawImage('static/img/ems.png', x1 + 0.02 * inch, y3 + 0.06 * inch, width=1.393 * inch, height=0.566 * inch)
    ## barcdoe ##
    qfbarcodeBg = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.35 * inch, humanReadable=1,
                                  fontSize=12, fontName='Times-Roman')
    qfbarcodeBg.drawOn(c, 1.303 * inch, 5.5213 * inch)
    qfbarcodeBg.drawOn(c, xv1 - 0.2 * inch, y3 + 0.2 * inch)
    # 寄件
    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.08 * inch, y9 + 0.08 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(x1 + 0.50 * inch, y9 + 0.08 * inch, u'HuskyEx')
    c.drawString(x1 + 0.08 * inch, y8 + 0.08 * inch, u'77 Glendale Ave, Edison, NJ')
    c.setFont("STSong-Light", 11)
    c.drawString(xv2 + 0.08 * inch, y8 + 0.12 * inch, obj[u"recv_prov"])
    c.drawString(xv3 + 0.08 * inch, y8 + 0.12 * inch, u'快递包裹')
    # 收件
    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.08 * inch, y8 - 0.22 * inch, u'收件:')
    c.drawString(x1 + 0.50 * inch, y8 - 0.22 * inch, obj[u'recv_name'])
    c.drawString(xv2 + 0.08 * inch, y8 - 0.22 * inch, obj[u'mobile'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 11
    recv_cb = u'%s' % (obj[u"recv_address"])
    story.append(Paragraph(recv_cb, style))
    f = Frame(x1 + 0.08 * inch, y7 - 0.1 * inch, 3.668 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)
    # 打印时间
    c.setFont("STSong-Light", 8)
    c.drawString(x1 + 0.08 * inch, y6 + 0.52 * inch,
                 u'打印时间: %s' % datetime.datetime.now().today().strftime('%Y/%m/%d %H:%M:%S'))
    c.drawString(x1 + 0.08 * inch, y6 + 0.39 * inch, u'付费方式:')
    c.drawString(x1 + 0.08 * inch, y6 + 0.26 * inch, u'计费重量(KG):')
    c.drawString(xv2 - 0.28 * inch, y6 + 0.26 * inch, '%.2f' % (obj[u'weight'] * Decimal(0.455)))
    c.drawString(x1 + 0.08 * inch, y6 + 0.13 * inch, u'保价金额(元):')
    # 签收信息:
    c.setFont("STSong-Light", 9)
    c.drawString(xv2 + 0.08 * inch, y6 + 0.52 * inch, u'收件人\代收人:')
    c.drawString(xv2 + 0.08 * inch, y6 + 0.32 * inch, u'签收时间:       年     月     日     时')
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 6
    style.wordWrap = 'CJK'
    style.leading = 6
    info = u'快件送达收货人地址, 经收件人或收件人允许的代收人签字, 视为送达!'
    story.append(Paragraph(info, style))
    f = Frame(xv2, y6, 1.8 * inch, 0.23 * inch, showBoundary=0, topPadding=0, bottomPadding=0)
    f.addFromList(story, c)
    # 订单号
    c.drawString(x1 + 0.08 * inch, y5 + 0.46 * inch, u'订单号:')
    c.setFont('Helvetica', 10)
    c.drawString(x1 + 0.8 * inch, y5 + 0.46 * inch, obj[u'tracking_no'])
    c.setFont("STSong-Light", 9)
    c.drawString(xv2 + 0.08 * inch, y5 + 0.46 * inch,
                 u'件数:        %d   重量:            %.2f' % (1, obj[u'weight']))
    # 寄件
    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.08 * inch, y3 - 0.18 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(x1 + 0.50 * inch, y3 - 0.18 * inch, u'HuskyEx')
    c.drawString(x1 + 0.08 * inch, y2 + 0.18 * inch, u'77 Glendale Ave, Edison, NJ')
    # 收件
    c.setFont("STSong-Light", 10)
    c.drawString(xv2 + 0.08 * inch, y3 - 0.18 * inch, u'收件:   %s' % obj[u'recv_name'])
    c.drawString(xv2 + 0.08 * inch, y3 - 0.38 * inch, obj[u'mobile'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 8
    style.wordWrap = 'CJK'
    style.leading = 8
    recv_cb = u'%s' % (obj[u"recv_address"])
    story.append(Paragraph(recv_cb, style))
    f = Frame(xv2 + 0.08 * inch, y2 - 0.05 * inch, 1.78 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=1)
    f.addFromList(story, c)
    ### 商品信息 #####
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 9
    style.wordWrap = 'CJK'
    style.leading = 9
    story.append(Paragraph(u'备注:', style))
    story.append(Paragraph(obj[u'goods'], style))
    f = Frame(x1 + 0.08 * inch, y1 + 0.01 * inch, 2.2 * inch, 0.5 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=1)
    f.addFromList(story, c)
    c.setFont('Helvetica', 9)
    c.drawString(x1 + 0.6 * inch, y1 + 0.38 * inch, obj[u'tracking_no'])
    c.setFont("STSong-Light", 12)
    c.drawString(xv2 + 0.18 * inch, y2 - 0.18 * inch, u'跨境电商直购进口')
    c.drawString(xv2 + 0.58 * inch, y1 + 0.08 * inch, '9610')
    c.showPage()


def fj_one_page(c, obj):
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2 = 0.067 * inch, 3.922 * inch
    y1 = 5.943 * inch
    y2 = 5.117 * inch
    y3 = 3.741 * inch
    y4 = 3.058 * inch
    y5 = 2.324 * inch
    y6 = 1.993 * inch
    y7 = 1.103 * inch
    y8 = 0.191 * inch
    xv1 = 0.819 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7, y8]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ### 从左到右 ###
    draw_line_vertical(c, y2, y4, x1)
    draw_line_vertical(c, y5, y8, x1)
    draw_line_vertical(c, y2, y4, x2)
    draw_line_vertical(c, y5, y8, x2)
    ## barcdoe ##
    qfbarcodeBg = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                  fontSize=12, fontName='Times-Roman')
    qfbarcodeBg.drawOn(c, xv1 + 0.475 * inch, y2 + 0.3 * inch)
    qfbarcodeBg.drawOn(c, xv1 - 0.2 * inch, y5 + 0.25 * inch)

    # LOGO
    c.setFontSize(26)
    c.drawString(x1, y2 + 0.35 * inch, 'HuskyEx')

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y2 - 0.15 * inch, u'始发网点:')
    c.drawString(x1 + 0.04 * inch, y2 - 0.30 * inch, u'寄件人:')
    c.drawString(x1 + 1.2 * inch, y2 - 0.30 * inch, u'寄件人电话: 7323174312')
    c.drawString(x1 + 0.04 * inch, y2 - 0.45 * inch, u'寄件人地址: ')

    c.setFont('Helvetica', 10)
    c.drawString(x1 + 0.60 * inch, y2 - 0.30 * inch, u'HuskyEx')
    c.drawString(x1 + 2.66 * inch, y2 - 0.15 * inch, obj[u'tracking_no'])
    c.drawString(x1 + 0.8 * inch, y2 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y2 - 0.65 * inch, u'送')
    c.drawString(x1 + 0.04 * inch, y2 - 0.80 * inch, u'达')
    c.drawString(x1 + 0.04 * inch, y2 - 0.95 * inch, u'地')
    c.drawString(x1 + 0.04 * inch, y2 - 1.10 * inch, u'址')
    c.drawString(x1 + 0.04 * inch, y2 - 1.30 * inch, u'集包地:')

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 11
    recv_1 = u'收件人: %s   收件人电话: %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_2 = u'收件人地址: %s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story.append(Paragraph(recv_1, style))
    story.append(Paragraph(recv_2, style))
    f = Frame(x1 + 0.28 * inch, y2 - 1.15 * inch, 3.55 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y5 - 0.15 * inch, u'收件人/代签人')
    c.drawString(x1 + 2.30 * inch, y5 - 0.15 * inch, u'签收时间:        年  月  日')
    c.drawString(x1 + 2.30 * inch, y5 - 0.30 * inch, obj[u'cn_tracking_no'])

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 11
    goods_1 = u'托寄物品:   %s' % (obj[u'goods'])
    goods_2 = u'订单编号:  %s  价值' % (obj[u"tracking_no"])
    goods_3 = u'重量:  %s' % (obj[u"weight"])
    goods_4 = u'简述:'
    story.append(Paragraph(goods_1, style))
    story.append(Paragraph(goods_4, style))
    story.append(Paragraph(goods_2, style))
    story.append(Paragraph(goods_3, style))
    f = Frame(x1 + 0.04 * inch, y6 - 0.8 * inch, 3.800 * inch, 0.7 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 9
    style.wordWrap = 'CJK'
    style.leading = 10
    recv1 = u'收件人/To: %s  电话/Tel:%s' % (obj[u'recv_name'], obj[u'mobile'])
    recv2 = u'地址/Address:  %s %s %s %s' % (
        obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    recv3 = u'寄件人/From: HuskyEx  电话/Tel:7323174312'
    recv4 = u'地址/Address: 77 Glendale Ave, Edison, NJ'
    story.append(Paragraph(recv1, style))
    story.append(Paragraph(recv2, style))
    story.append(Paragraph(recv3, style))
    story.append(Paragraph(recv4, style))
    f = Frame(x1 + 0.04 * inch, y7 - 0.8 * inch, 3.800 * inch, 0.7 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    # # 打印时间
    # c.setFont("STSong-Light", 8)
    # c.drawString(x1 + 0.08 * inch, y6 + 0.52 * inch,
    #              u'打印时间: %s' % datetime.datetime.now().today().strftime('%Y/%m/%d %H:%M:%S'))
    # c.drawString(x1 + 0.08 * inch, y6 + 0.39 * inch, u'付费方式:')
    # c.drawString(x1 + 0.08 * inch, y6 + 0.26 * inch, u'计费重量(KG):')
    # c.drawString(xv2 - 0.28 * inch, y6 + 0.26 * inch, '%.2f' % (obj[u'weight'] * Decimal(0.455)))
    # c.drawString(x1 + 0.08 * inch, y6 + 0.13 * inch, u'保价金额(元):')
    # # 签收信息:
    # c.setFont("STSong-Light", 9)
    # c.drawString(xv2 + 0.08 * inch, y6 + 0.52 * inch, u'收件人\代收人:')
    # c.drawString(xv2 + 0.08 * inch, y6 + 0.32 * inch, u'签收时间:       年     月     日     时')
    # story = []
    # style = ParagraphStyle('Normal')
    # style.fontName = "STSong-Light"
    # style.fontSize = 6
    # style.wordWrap = 'CJK'
    # style.leading = 6
    # info = u'快件送达收货人地址, 经收件人或收件人允许的代收人签字, 视为送达!'
    # story.append(Paragraph(info, style))
    # f = Frame(xv2, y6, 1.8 * inch, 0.23 * inch, showBoundary=0, topPadding=0, bottomPadding=0)
    # f.addFromList(story, c)
    # # 订单号
    # c.drawString(x1 + 0.08 * inch, y5 + 0.46 * inch, u'订单号:')
    # c.setFont('Helvetica', 10)
    # c.drawString(x1 + 0.8 * inch, y5 + 0.46 * inch, obj[u'tracking_no'])
    # c.setFont("STSong-Light", 9)
    # c.drawString(xv2 + 0.08 * inch, y5 + 0.46 * inch,
    #              u'件数:        %d   重量:            %.2f' % (1, obj[u'weight']))
    # # 寄件
    # c.setFont("STSong-Light", 10)
    # c.drawString(x1 + 0.08 * inch, y3 - 0.18 * inch, u'寄件:')
    # c.setFont('Helvetica', 10)
    # c.drawString(x1 + 0.50 * inch, y3 - 0.18 * inch, u'HuskyEx')
    # c.drawString(x1 + 0.08 * inch, y2 + 0.18 * inch, u'77 Glendale Ave, Edison, NJ')
    # # 收件
    # c.setFont("STSong-Light", 10)
    # c.drawString(xv2 + 0.08 * inch, y3 - 0.18 * inch, u'收件:   %s' % obj[u'recv_name'])
    # c.drawString(xv2 + 0.08 * inch, y3 - 0.38 * inch, obj[u'mobile'])
    # story = []
    # style = ParagraphStyle('Normal')
    # style.fontName = "STSong-Light"
    # style.fontSize = 8
    # style.wordWrap = 'CJK'
    # style.leading = 8
    # recv_cb = u'%s' % (obj[u"recv_address"])
    # story.append(Paragraph(recv_cb, style))
    # f = Frame(xv2 + 0.08 * inch, y2 - 0.05 * inch, 1.78 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
    #           rightPadding=0, topPadding=1)
    # f.addFromList(story, c)
    # ### 商品信息 #####
    # story = []
    # style = ParagraphStyle('Normal')
    # style.fontName = "STSong-Light"
    # style.fontSize = 9
    # style.wordWrap = 'CJK'
    # style.leading = 9
    # story.append(Paragraph(u'备注:', style))
    # story.append(Paragraph(obj[u'goods'], style))
    # f = Frame(x1 + 0.08 * inch, y1 + 0.01 * inch, 2.2 * inch, 0.5 * inch, showBoundary=0, leftPadding=0,
    #           rightPadding=0, topPadding=1)
    # f.addFromList(story, c)
    # c.setFont('Helvetica', 9)
    # c.drawString(x1 + 0.6 * inch, y1 + 0.38 * inch, obj[u'tracking_no'])
    # c.setFont("STSong-Light", 12)
    # c.drawString(xv2 + 0.18 * inch, y2 - 0.18 * inch, u'跨境电商直购进口')
    # c.drawString(xv2 + 0.58 * inch, y1 + 0.08 * inch, '9610')
    c.showPage()


def ch8_one_page(c, obj):
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2 = 0.067 * inch, 3.922 * inch
    y1 = 5.943 * inch
    y2 = 5.117 * inch
    y3 = 3.741 * inch
    y4 = 3.058 * inch
    y5 = 2.324 * inch
    y6 = 1.993 * inch
    y7 = 1.103 * inch
    y8 = 0.191 * inch
    xv1 = 0.819 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7, y8]
    for y in ys:
        draw_line_horizontal(c, x1, x2, y)

    ### 从左到右 ###
    draw_line_vertical(c, y2, y4, x1)
    draw_line_vertical(c, y5, y8, x1)
    draw_line_vertical(c, y2, y4, x2)
    draw_line_vertical(c, y5, y8, x2)
    ## barcdoe ##
    qfbarcodeBg = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                  fontSize=12, fontName='Times-Roman')
    qfbarcodeBg.drawOn(c, xv1 + 0.475 * inch, y2 + 0.3 * inch)
    qfbarcodeBg.drawOn(c, xv1 - 0.2 * inch, y5 + 0.25 * inch)

    # LOGO
    c.setFontSize(26)
    c.drawString(x1, y2 + 0.35 * inch, 'HuskyEx')

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y2 - 0.15 * inch, u'始发网点:')
    c.drawString(x1 + 0.04 * inch, y2 - 0.30 * inch, u'寄件人:')
    c.drawString(x1 + 1.2 * inch, y2 - 0.30 * inch, u'寄件人电话: 7323174312')
    c.drawString(x1 + 0.04 * inch, y2 - 0.45 * inch, u'寄件人地址: ')

    c.setFont('Helvetica', 10)
    c.drawString(x1 + 0.60 * inch, y2 - 0.30 * inch, u'HuskyEx')
    c.drawString(x1 + 2.66 * inch, y2 - 0.15 * inch, obj[u'tracking_no'])
    c.drawString(x1 + 0.8 * inch, y2 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y2 - 0.65 * inch, u'送')
    c.drawString(x1 + 0.04 * inch, y2 - 0.80 * inch, u'达')
    c.drawString(x1 + 0.04 * inch, y2 - 0.95 * inch, u'地')
    c.drawString(x1 + 0.04 * inch, y2 - 1.10 * inch, u'址')
    c.drawString(x1 + 0.04 * inch, y2 - 1.30 * inch, u'集包地:')

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 11
    recv_1 = u'收件人: %s   收件人电话: %s' % (obj[u'recv_name'], obj[u'mobile'])
    story.append(Paragraph(recv_1, style))

    recv_2 = u'收件人地址: %s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    ft_size = 10 if len(recv_2) <= 55 else 9 if len(recv_2) <= 65 else 8
    print len(recv_2)
    style2 = ParagraphStyle('Normal')
    style2.fontName = "STSong-Light"
    style2.fontSize = ft_size
    style2.wordWrap = 'CJK'
    style2.leading = ft_size + 1
    story.append(Paragraph(recv_2, style2))
    f = Frame(x1 + 0.28 * inch, y2 - 1.15 * inch, 3.55 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 10)
    c.drawString(x1 + 0.04 * inch, y5 - 0.15 * inch, u'收件人/代签人')
    c.drawString(x1 + 2.30 * inch, y5 - 0.15 * inch, u'签收时间:        年  月  日')
    c.drawString(x1 + 2.30 * inch, y5 - 0.30 * inch, obj[u'cn_tracking_no'])

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10
    style.wordWrap = 'CJK'
    style.leading = 11
    goods_1 = u'托寄物品:   %s' % (obj[u'goods'])
    goods_2 = u'订单编号:  %s  价值' % (obj[u"tracking_no"])
    goods_3 = u'重量:  %s' % (obj[u"weight"])
    goods_4 = u'简述:'
    story.append(Paragraph(goods_1, style))
    story.append(Paragraph(goods_4, style))
    story.append(Paragraph(goods_2, style))
    story.append(Paragraph(goods_3, style))
    f = Frame(x1 + 0.04 * inch, y6 - 0.8 * inch, 3.800 * inch, 0.7 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 9
    style.wordWrap = 'CJK'
    style.leading = 10
    recv1 = u'收件人/To: %s  电话/Tel:%s' % (obj[u'recv_name'], obj[u'mobile'])
    recv2 = u'地址/Address:  %s %s %s %s' % (
        obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    recv3 = u'寄件人/From: HuskyEx  电话/Tel:7323174312'
    recv4 = u'地址/Address: 77 Glendale Ave, Edison, NJ'
    story.append(Paragraph(recv1, style))
    story.append(Paragraph(recv2, style))
    story.append(Paragraph(recv3, style))
    story.append(Paragraph(recv4, style))
    f = Frame(x1 + 0.04 * inch, y7 - 0.8 * inch, 3.800 * inch, 0.7 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont('Helvetica', 20)
    c.drawString(x1 + 3.5 * inch, y7 + 0.30 * inch, obj['channel_name'])

    try:
        if obj['yd_info']:
            o = json.loads(obj['yd_info'])

            c.drawString(x1 + 2 * inch, y4 + 0.4 * inch, o['position'])
            c.drawString(x1 + 2 * inch, y4 + 0.1 * inch, o['position_no'])

            c.drawImage('static/img/ydlogo.jpg', x1 + 0.02 * inch, y4 + 0.06 * inch, width=1.393 * inch,
                        height=0.566 * inch)
    except Exception as e:
        print e

    c.showPage()


def e_one_page(c, obj):
    c.drawImage('static/img/ems2.png', 0.20 * inch, 5.23 * inch, width=0.9 * inch, height=0.45 * inch)
    barcodeUp = code128.Code128(obj['cn_tracking_no'], barWidth=0.32 * mm, barHeight=0.4 * inch, humanReadable=1,
                                fontSize=12, fontName='Times-Roman')
    barcodeUp.drawOn(c, 1.4 * inch, 5.3 * inch)
    barcodeDown = code128.Code128(obj['cn_tracking_no'], barWidth=0.32 * mm, barHeight=0.4 * inch, humanReadable=1,
                                  fontSize=12, fontName='Times-Roman')
    barcodeDown.drawOn(c, -0.15 * inch, 0.8 * inch)

    # draw line
    y1 = 0.433 * inch
    y2 = 1.316 * inch
    y3 = 1.912 * inch
    y4 = 2.495 * inch  # 虚线
    y5 = 2.831 * inch

    y6 = 3.031 * inch
    y7 = 3.231 * inch
    y8 = 3.431 * inch
    y9 = 3.631 * inch

    y10 = 4.536 * inch
    y11 = 5.139 * inch  # 虚线
    y12 = 5.803 * inch

    x1 = 1.415 * inch
    x2 = 2.193 * inch
    x3 = 2.464 * inch
    x4 = 2.923 * inch
    x5 = 3.350 * inch

    ys = [y1, y2, y3, y5, y6, y9, y10, y12]
    for y in ys:
        draw_line_horizontal(c, 0, 4 * inch, y)
    for y in [y7, y8]:
        draw_line_horizontal(c, x3, 3.9 * inch, y)

    draw_line_vertical(c, y5, y6, x1)
    draw_line_vertical(c, y1, y2, x2)
    draw_line_vertical(c, y5, y9, x3)
    draw_line_vertical(c, y5, y7, x4)
    draw_line_vertical(c, y5, y7, x5)

    c.setDash(1, 2)
    draw_line_horizontal(c, 0, 4 * inch, y11)
    draw_line_horizontal(c, 0, 4 * inch, y4)

    # 寄送
    c.setFont("STSong-Light", 8)
    c.drawString(0.08 * inch, y11 - 0.15 * inch, u'寄件人/From: HUSKYEX')
    c.drawString(2.5 * inch, y11 - 0.15 * inch, u'电话/Tel: +1 805 868 1682')
    c.drawString(0.08 * inch, y11 - 0.4 * inch, u'地址/Address: 77 Glendale Ave NJ 08817')

    c.drawString(0.08 * inch, y10 - 0.15 * inch, u'收件人/To: %s' % (obj[u'recv_name']))
    c.drawString(2.5 * inch, y10 - 0.15 * inch, u'电话/Tel: %s' % (obj[u'mobile']))
    c.drawString(0.08 * inch, y10 - 0.4 * inch, u'地址/Address: ')
    c.drawString(0.08 * inch, y10 - 0.8 * inch, u'大客户代码: HUSKYEX ')
    c.drawString(2.5 * inch, y10 - 0.8 * inch, u'邮编/Post Code: %s' % (obj[u'zipcode']))

    addr = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])

    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = e_get_addr_font_size(addr, 8)
    style.wordWrap = 'CJK'
    style.leading = e_get_addr_font_size(addr, 8)

    story.append(Paragraph(addr, style))
    f = Frame(0.775 * inch, 3.847 * inch, 2.9 * inch, 0.4 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawString(0.08 * inch, y9 - 0.15 * inch, u'内件描述/Name & Description of Contents:')

    d_len = len(obj[u"goods2"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if d_len <= 25 else 9 if d_len <= 50 else 7
    style.wordWrap = 'CJK'
    style.leading = 10 if d_len <= 25 else 9 if d_len <= 50 else 7
    detail = u'%s ' % (obj[u"goods2"][:60])
    story.append(Paragraph(detail, style))
    f = Frame(0.08 * inch, 3.066 * inch, 2.125 * inch, 0.35 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 10) / 10.0

    l = 25.2 + random.randint(0, 20) / 10.0
    w = 20.1 + random.randint(0, 20) / 10.0
    h = 15.2 + random.randint(0, 20) / 10.0

    v_weight = l * w * h / 6000

    c.drawString(x3 + 0.01 * inch, y9 - 0.15 * inch, u'实际重量: %.1f kg' % est_weight)
    c.drawString(x3 + 0.01 * inch, y8 - 0.15 * inch, u'体积重量: %.1f kg' % v_weight)
    c.drawString(x3 + 0.01 * inch, y7 - 0.15 * inch, u'长/L: ')
    c.drawString(x4 + 0.01 * inch, y7 - 0.15 * inch, u'宽/W: ')
    c.drawString(x5 + 0.01 * inch, y7 - 0.15 * inch, u'高/H: ')

    c.drawString(x3 + 0.01 * inch, y7 - 0.35 * inch, u'%.1f ' % l)
    c.drawString(x4 + 0.01 * inch, y7 - 0.35 * inch, u'%.1f ' % w)
    c.drawString(x5 + 0.01 * inch, y7 - 0.35 * inch, u'%.1f ' % h)

    c.drawString(0.08 * inch, y6 - 0.15 * inch, u'申报价值/Value: %0.2f' % (obj[u'value']))
    c.drawString(x1 + 0.05 * inch, y6 - 0.15 * inch, u'原产地/Origin: ')

    c.drawString(0.08 * inch, y5 - 0.15 * inch, u'收件人签名: ')
    c.drawString(2.5 * inch, y5 - 0.15 * inch, u'签收时间:')

    # 下
    c.drawString(0.08 * inch, y4 - 0.15 * inch, u'寄件人/From: HUSKYEX')
    c.drawString(2.5 * inch, y4 - 0.15 * inch, u'电话/Tel: +1 805 868 1682')
    c.drawString(0.08 * inch, y4 - 0.4 * inch, u'地址/Address: 77 Glendale Ave NJ 08817')

    c.drawString(0.08 * inch, y3 - 0.15 * inch, u'收件人/To: %s' % (obj[u'recv_name']))
    c.drawString(2.5 * inch, y3 - 0.15 * inch, u'电话/Tel: %s' % (obj[u'mobile']))
    c.drawString(0.08 * inch, y3 - 0.4 * inch, u'地址/Address: ')

    addr = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = e_get_addr_font_size(addr, 7)
    style.wordWrap = 'CJK'
    style.leading = e_get_addr_font_size(addr, 7)
    story.append(Paragraph(addr, style))
    f = Frame(0.775 * inch, 1.25 * inch, 2.9 * inch, 0.4 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawString(x2 + 0.01 * inch, y2 - 0.25 * inch, u'渠道编码: ')
    c.drawString(x2 + 0.01 * inch, y2 - 0.45 * inch, u'关联单号: ')
    c.drawString(x2 + 0.01 * inch, y2 - 0.65 * inch, u'原寄地: US')
    c.drawString(0.08 * inch, y1 + 0.1 * inch, u'进口口岸: ')

    c.setFont('Helvetica', 10)
    c.drawString(x2 + 0.5 * inch, y2 - 0.45 * inch, obj[u'tracking_no'])

    c.setFont('Helvetica', 28)
    if u'北京' in obj[u'recv_prov']:
        c.drawString(x2 + 0.8 * inch, y2 - 0.2 * inch, u'')
    elif u'天津' in obj[u'recv_prov'] or '河北' in obj[u'recv_prov'] or '新疆' in obj[u'recv_prov'] or '西藏' in obj[
        'recv_prov'] or '青海' in obj[u'recv_prov'] or '甘肃' in obj[u'recv_prov']:
        c.drawString(x2 + 0.8 * inch, y2 - 0.2 * inch, u'B')
    else:
        c.drawString(x2 + 0.8 * inch, y2 - 0.3 * inch, u'J')

    c.showPage()


def k1_one_page(c, obj):
    c.drawImage('static/img/dg.png', 0.25 * inch, 5.394 * inch, width=0.6 * inch, height=0.54 * inch)

    ### 从上到下划线 ###
    x1 = 1.110 * inch
    y1 = 5.019 * inch
    y2 = 3.558 * inch
    y3 = 3.098 * inch
    y4 = 2.134 * inch
    y5 = 0.944 * inch
    ys = [y1, y2, y3, y4, y5]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    draw_line_vertical(c, y2, y3, x1)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.5 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, 1.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0 * inch, 0.2 * inch)
    c.setFont("STSong-Light", 18)
    c.drawString(0.1 * inch, y1 + 0.1 * inch, '快递包裹')
    c.drawString(2.858 * inch, 0.2 * inch, '快递包裹')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y5 - 0.15 * inch, u'退件地址：福建省晋江内坑镇陆地港国际快件中心301室')

    # 收件
    recv_1 = u'收件人: %s' % (obj[u'recv_name'])
    recv_2 = u'%s' % (obj[u'mobile'])
    recv_3 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])

    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 4.729 * inch, recv_1)
    c.drawString(0.1 * inch, 1.339 * inch, recv_1)

    c.setFont("Helvetica", 12)
    c.drawString(2.69 * inch, 4.729 * inch, recv_2)
    c.drawString(2.69 * inch, 1.339 * inch, recv_2)

    story = []
    f = Frame(0.54 * inch, 0.83 * inch, 3.307 * inch, 0.5 * inch, showBoundary=0, topPadding=0, leftPadding=0,
              rightPadding=0, bottomPadding=0)
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    story.append(Paragraph(recv_3, style))
    f.addFromList(story, c)

    story = []
    f = Frame(0.54 * inch, 4.15 * inch, 3.307 * inch, 0.5 * inch, showBoundary=0, topPadding=0, leftPadding=0,
              rightPadding=0, bottomPadding=0)
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    story.append(Paragraph(recv_3, style))
    f.addFromList(story, c)
    # end 收件

    # 寄件
    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 4.06 * inch, '寄方:')
    c.drawString(0.1 * inch, 1.83 * inch, '寄方:')
    c.drawString(0.1 * inch, 3.749 * inch, '寄方地址:')
    c.drawString(0.1 * inch, 1.607 * inch, '寄方地址:')

    c.setFont("Helvetica", 12)
    c.drawString(2.69 * inch, 4.06 * inch, '7323174312')
    c.drawString(2.69 * inch, 1.83 * inch, '7323174312')

    c.drawString(0.561 * inch, 4.06 * inch, 'HuskyEx')
    c.drawString(0.561 * inch, 1.83 * inch, 'HuskyEx')
    c.drawString(0.82 * inch, 3.749 * inch, '77 Glendale Ave, Edison, NJ')
    c.drawString(0.82 * inch, 1.607 * inch, '77 Glendale Ave, Edison, NJ')
    # end 寄件


    # 重量
    c.setFont("STSong-Light", 12)
    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 20) / 10.0
    c.drawString(0.1 * inch, 3.26 * inch, '重量:  %.2f' % est_weight)
    c.drawString(1.27 * inch, 3.26 * inch, '件数:  1')
    c.drawString(2.55 * inch, 3.26 * inch, '原产地: ')
    # end  重量

    # 内件
    title = '内件描述'
    detail = obj[u'goods2']
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 70 else 9
    style.leading = 10 if len(detail) < 70 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(title, style))
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, 2.55 * inch, 3.55 * inch, 0.5 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)
    # end 内件

    # 编号
    c.setFont("Helvetica", 12)
    c.drawString(0.6 * inch, 2.283 * inch, obj[u'tracking_no'])
    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 2.283 * inch, '编号: ')
    c.drawString(3 * inch, 2.283 * inch, '年 月 日')
    # end 编号

    c.showPage()


def k2_one_page(c, obj):
    c.drawImage('static/img/k2logo.png', 0.25 * inch, 5.394 * inch, width=0.8 * inch, height=0.54 * inch)

    ### 从上到下划线 ###
    x1 = 1.110 * inch
    y1 = 5.019 * inch
    y2 = 3.558 * inch
    y3 = 3.098 * inch
    y4 = 2.134 * inch
    y5 = 0.944 * inch
    ys = [y1, y2, y3, y4, y5]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    draw_line_vertical(c, y2, y3, x1)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.5 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, 1.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0 * inch, 0.2 * inch)
    c.setFont("STSong-Light", 18)
    c.drawString(0.1 * inch, y1 + 0.1 * inch, '快递包裹')
    c.drawString(2.858 * inch, 0.2 * inch, '快递包裹')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y5 - 0.15 * inch, u'退件地址：福建省晋江内坑镇陆地港国际快件中心301室')

    # 收件
    recv_1 = u'收件人: %s' % (obj[u'recv_name'])
    recv_2 = u'%s' % (obj[u'mobile'])
    recv_3 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])

    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 4.729 * inch, recv_1)
    c.drawString(0.1 * inch, 1.339 * inch, recv_1)

    c.setFont("Helvetica", 12)
    c.drawString(2.69 * inch, 4.729 * inch, recv_2)
    c.drawString(2.69 * inch, 1.339 * inch, recv_2)

    story = []
    f = Frame(0.54 * inch, 0.83 * inch, 3.307 * inch, 0.5 * inch, showBoundary=0, topPadding=0, leftPadding=0,
              rightPadding=0, bottomPadding=0)
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    story.append(Paragraph(recv_3, style))
    f.addFromList(story, c)

    story = []
    f = Frame(0.54 * inch, 4.15 * inch, 3.307 * inch, 0.5 * inch, showBoundary=0, topPadding=0, leftPadding=0,
              rightPadding=0, bottomPadding=0)
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_3) <= 49 else 9 if len(recv_3) <= 55 else 8 if len(recv_3) <= 60 else 7
    story.append(Paragraph(recv_3, style))
    f.addFromList(story, c)
    # end 收件

    # 格口号
    data = [[ExpressMark.get_ems_k2(obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"])]]
    style = [
        ('GRID', (0, 0), (-1, -1), 0.2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 1.6 * cm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('leftPadding', (0, 0), (-1, -1), 0),
        ('rightPadding', (0, 0), (-1, -1), 0),
        ('topPadding', (0, 0), (-1, -1), 0),
        ('bottomPadding', (0, 0), (-1, -1), 0),
    ]
    t = Table(data, style=style, colWidths=[3.6 * cm], rowHeights=[3.6 * cm])
    story = []
    story.append(t)
    f = Frame(6.4 * cm, 6.5 * cm, 3.6 * cm, 3.6 * cm, showBoundary=0, topPadding=0, leftPadding=0,
              rightPadding=0, bottomPadding=0)
    f.addFromList(story, c)

    # 寄件
    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 4.06 * inch, '寄方:')
    c.drawString(0.1 * inch, 1.83 * inch, '寄方:')
    c.drawString(0.1 * inch, 3.749 * inch, '寄方地址:')
    c.drawString(0.1 * inch, 1.607 * inch, '寄方地址:')

    c.setFont("Helvetica", 12)
    c.drawString(2.69 * inch, 4.06 * inch, '7323174312')
    c.drawString(2.69 * inch, 1.83 * inch, '7323174312')

    c.drawString(0.561 * inch, 4.06 * inch, 'HuskyEx')
    c.drawString(0.561 * inch, 1.83 * inch, 'HuskyEx')
    c.drawString(0.82 * inch, 1.607 * inch, '77 Glendale Ave, Edison, NJ')

    c.setFont("Helvetica", 9)
    c.drawString(0.82 * inch, 3.749 * inch, '77 Glendale Ave, Edison, NJ')

    # end 寄件


    # 重量
    c.setFont("STSong-Light", 12)
    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 20) / 10.0
    c.drawString(0.1 * inch, 3.26 * inch, '重量:  %.2f' % est_weight)
    c.drawString(1.27 * inch, 3.26 * inch, '件数:  1')
    c.drawString(1.85 * inch, 3.26 * inch, '原产地: ')
    # end  重量

    # 内件
    title = '内件描述'
    detail = obj[u'goods2']
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 50 else 9 if len(detail) <= 90 else 8 if len(detail) <= 100 else 7
    style.leading = 10 if len(detail) < 50 else 9 if len(detail) <= 90 else 8 if len(detail) <= 100 else 7
    style.wordWrap = 'CJK'

    if len(detail) > 135:
        detail = detail[:135] + "..."
    story.append(Paragraph(title, style))
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, 2.45 * inch, 2.4 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)
    # end 内件

    # 编号
    c.setFont("Helvetica", 12)
    c.drawString(0.6 * inch, 2.283 * inch, obj[u'tracking_no'])
    c.setFont("STSong-Light", 12)
    c.drawString(0.1 * inch, 2.283 * inch, '编号: ')
    c.drawString(3 * inch, 2.283 * inch, '年 月 日')
    # end 编号

    c.showPage()


def jj_one_page(c, obj):
    c.setDash(1, 2)
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2, x3 = 1.519 * inch, 2 * inch, 3 * inch
    y1 = 5.160 * inch
    y2 = 4.393 * inch
    y3 = 3.632 * inch
    y4 = 2.862 * inch
    y5 = 2.351 * inch
    y6 = 1.658 * inch
    y7 = 0.922 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    draw_line_vertical(c, 6 * inch, y1, x1)
    draw_line_vertical(c, y1, y2, x2)
    draw_line_vertical(c, y3, y4, x2)
    draw_line_vertical(c, y6, y7, x2)
    draw_line_vertical(c, 0, y7, x3)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, x1 - 0.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0.2 * inch, y6 + 0.2 * inch)

    # LOGO
    c.setFont("STSong-Light", 20)
    c.drawString(0.1 * inch, y1 + 0.35 * inch, '快递包裹')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y1 - 0.15 * inch, u'寄件:')

    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y1 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y1 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y1 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    c.drawString(x2 + 0.1 * inch, y1 - 0.15 * inch, u'退货地址：福建省晋江内')
    c.drawString(x2 + 0.1 * inch, y1 - 0.3 * inch, u'坑陆地港吉迅公司 ')
    c.drawString(x2 + 0.1 * inch, y1 - 0.45 * inch, u'059582076566')

    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) < 70 else 9
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) < 70 else 9

    story.append(Paragraph(recv_1, style))
    story.append(Paragraph(recv_2, style))
    f = Frame(0.1 * inch, y3 - 0.15 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 20) / 10.0

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y3 - 0.20 * inch, u'付款方式:')
    c.drawString(0.1 * inch, y3 - 0.40 * inch, u'计费重量(KG): %.1f' % (est_weight))
    c.drawString(0.1 * inch, y3 - 0.60 * inch, u'保价金额(元):')

    c.setFont("STSong-Light", 10)
    c.drawString(x2 + 0.1 * inch, y3 - 0.20 * inch, u'收件人/代收人:')
    c.drawString(x2 + 0.1 * inch, y3 - 0.40 * inch, u'签收时间       年    月   日    时')
    c.drawString(x2 + 0.1 * inch, y3 - 0.55 * inch, u'快件送达收件人签收表示')
    c.drawString(x2 + 0.1 * inch, y3 - 0.70 * inch, u'快件已送达')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y4 - 0.15 * inch, u'订单号:')
    c.drawString(x2 + 0.1 * inch, y4 - 0.15 * inch, u'重量: %.1f' % (est_weight))
    c.drawString(x2 + 1 * inch, y4 - 0.15 * inch, u'件数: 1')

    c.drawString(0.8 * inch, y4 - 0.15 * inch, obj[u'tracking_no'])

    detail = u'配送信息: %s' % (obj[u'goods2'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 70 else 9
    style.leading = 10 if len(detail) < 70 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, y5 - 0.47 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawImage('static/img/ems.png', 3 * inch, y6 + 0.12 * inch, width=0.89 * inch, height=0.566 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y6 - 0.15 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y6 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y6 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y6 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    c.drawString(x2 + 0.1 * inch, y6 - 0.2 * inch, recv_1)

    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 40 else 8 if len(recv_2) < 60 else 6
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 60 else 8 if len(recv_2) < 60 else 6
    story.append(Paragraph(recv_2, style))
    f = Frame(x2 + 0.1 * inch, y7 - 0.1 * inch, 1.8 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 7)
    c.drawString(0.1 * inch, y7 - 0.15 * inch, u'收货前请确认包装是否完整, 有无破损, 如有问题请拒签收')
    if u'福建' not in obj[u'recv_prov']:
        c.setFont("STSong-Light", 20)
        c.drawString(0.1 * inch, y7 - 0.45 * inch, u'全程陆运')
    c.setFont("Helvetica", 10)
    c.drawString(0.1 * inch, y7 - 0.7 * inch, u'www.ems.com.cn')
    c.setFont("STSong-Light", 8)
    c.drawString(1.5 * inch, y7 - 0.7 * inch, u'客服: 11183')

    c.setFont("STSong-Light", 24)
    c.drawString(x3 + 0.05 * inch, y7 - 0.55 * inch,
                 ExpressMark.get_ems_mark1(obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"]))

    c.showPage()


def ch20_one_page(c, obj):
    c.setDash(1, 2)
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2, x3 = 1.519 * inch, 2 * inch, 3 * inch
    y1 = 5.160 * inch
    y2 = 4.393 * inch
    y3 = 3.632 * inch
    y4 = 2.862 * inch
    y5 = 2.351 * inch
    y6 = 1.658 * inch
    y7 = 0.922 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    draw_line_vertical(c, 6 * inch, y1, x1)
    draw_line_vertical(c, y1, y2, x2)
    draw_line_vertical(c, y3, y4, x2)
    draw_line_vertical(c, y6, y7, x2)
    draw_line_vertical(c, 0, y7, x3)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, x1 - 0.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0.2 * inch, y6 + 0.2 * inch)

    # LOGO
    c.setFont("STSong-Light", 20)
    c.drawString(0.1 * inch, y1 + 0.35 * inch, '快递包裹')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y1 - 0.15 * inch, u'寄件:')

    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y1 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y1 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y1 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 20)
    c.drawString(x2 + 0.1 * inch, y1 - 0.4 * inch, obj['recv_prov'])

    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) < 70 else 9
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) < 70 else 9

    story.append(Paragraph(recv_1, style))
    story.append(Paragraph(recv_2, style))
    f = Frame(0.1 * inch, y3 - 0.15 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    est_weight = obj[u'weight'] * Decimal(453.592) if obj[u'weight'] != 1 and obj[u'weight'] != 0 \
        else (0.5 + random.randint(0, 20) / 10.0) * 1000

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y3 - 0.20 * inch, u'付款方式:')
    c.drawString(0.1 * inch, y3 - 0.40 * inch, u'计费重量(g): %.1f' % (est_weight))
    c.drawString(0.1 * inch, y3 - 0.60 * inch, u'保价金额(元):')

    c.setFont("STSong-Light", 10)
    c.drawString(x2 + 0.1 * inch, y3 - 0.20 * inch, u'收件人/代收人:')
    c.drawString(x2 + 0.1 * inch, y3 - 0.40 * inch, u'签收时间       年    月   日    时')
    c.drawString(x2 + 0.1 * inch, y3 - 0.55 * inch, u'快件送达收件人签收表示')
    c.drawString(x2 + 0.1 * inch, y3 - 0.70 * inch, u'快件已送达')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y4 - 0.15 * inch, u'订单号:')
    c.drawString(x2 + 0.1 * inch, y4 - 0.15 * inch, u'重量(g): %.1f' % (est_weight))
    c.drawString(x2 + 1 * inch, y4 - 0.15 * inch, u'件数: 1')

    c.drawString(0.8 * inch, y4 - 0.15 * inch, obj[u'tracking_no'])

    detail = u'配送信息: %s' % (obj[u'goods2'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    if len(obj[u'goods2']) > 93:
        detail = detail[:93] + '...'
    style.fontSize = 10 if len(detail) < 93 else 9
    style.leading = 10 if len(detail) < 93 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, y5 - 0.47 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawImage('static/img/ems.png', 3 * inch, y6 + 0.12 * inch, width=0.89 * inch, height=0.566 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y6 - 0.15 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y6 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y6 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y6 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    c.drawString(x2 + 0.1 * inch, y6 - 0.2 * inch, recv_1)

    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 40 else 8 if len(recv_2) < 60 else 6
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 60 else 8 if len(recv_2) < 60 else 6
    story.append(Paragraph(recv_2, style))
    f = Frame(x2 + 0.1 * inch, y7 - 0.1 * inch, 1.8 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 7)
    c.drawString(0.1 * inch, y7 - 0.15 * inch, u'备注')
    c.setFont("STSong-Light", 20)
    c.drawString(0.4 * inch, y7 - 0.22 * inch, u'已验视已安检')
    c.drawString(0.4 * inch, y7 - 0.48 * inch, u'验视员刘泽飞')

    c.setFont("Helvetica", 10)
    c.drawString(0.1 * inch, y7 - 0.7 * inch, u'www.ems.com.cn')
    c.setFont("STSong-Light", 8)
    c.drawString(1.5 * inch, y7 - 0.7 * inch, u'客服: 11183')

    c.showPage()


def e_get_addr_font_size(text, start):
    return start if len(text) <= 55 else start - 1 if len(text) <= 90 else start - 2


def sigang_page(c, obj):
    c.setFont("STSong-Light", 30)
    c.drawString(0.2 * inch, 5 * inch, 'TRAC')

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['tracking'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=15, fontName='Times-Roman')
    qfbarcode1.drawOn(c, 0.2 * inch, 1 * inch)

    qfbarcode2 = code128.Code128(obj['order_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=15, fontName='Times-Roman')
    qfbarcode2.drawOn(c, 0.2 * inch, 2 * inch)

    detail = obj['remark']
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 70 else 9
    style.leading = 10 if len(detail) < 70 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(detail, style))
    f = Frame(0.2 * inch, 4 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)
    c.showPage()


def nn_one_page(c, obj):
    c.setDash(1, 2)
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2, x3 = 1.519 * inch, 2 * inch, 3 * inch
    y1 = 5.160 * inch
    y2 = 4.393 * inch
    y3 = 3.632 * inch
    y4 = 2.862 * inch
    y5 = 2.351 * inch
    y6 = 1.658 * inch
    y7 = 0.922 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    # draw_line_vertical(c, 6 * inch, y1, x1)
    draw_line_vertical(c, y1, y2, x2)
    draw_line_vertical(c, y3, y4, x2)
    draw_line_vertical(c, y6, y7, x2)
    draw_line_vertical(c, 0, y7, x3)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, x1 - 0.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0.2 * inch, y6 + 0.2 * inch)

    # LOGO
    c.drawImage('static/img/XCLOGO.png', 0.1 * inch, y1 + 0.2 * inch, width=0.89 * inch, height=0.566 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y1 - 0.15 * inch, u'寄件:')

    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y1 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y1 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y1 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 6)

    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) < 70 else 9
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) < 70 else 9

    story.append(Paragraph(recv_1, style))
    story.append(Paragraph(recv_2, style))
    f = Frame(0.1 * inch, y3 - 0.15 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 20) / 10.0

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y3 - 0.20 * inch, u'收件人/代收人:')
    c.drawString(0.1 * inch, y3 - 0.40 * inch, u'签收时间       年    月   日    时')

    c.setFont("STSong-Light", 25)
    c.drawString(x2 + 0.1 * inch, y3 - 0.3 * inch, u'已验视')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y4 - 0.15 * inch, u'订单号:')
    c.drawString(x2 + 0.1 * inch, y4 - 0.15 * inch, u'重量: %.1f' % (est_weight))
    c.drawString(x2 + 1 * inch, y4 - 0.15 * inch, u'件数: 1')

    c.drawString(0.8 * inch, y4 - 0.15 * inch, obj[u'tracking_no'])

    detail = u'配送信息: %s' % (obj[u'goods2'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 70 else 9
    style.leading = 10 if len(detail) < 70 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, y5 - 0.47 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawImage('static/img/CP.png', 3 * inch, y6 + 0.12 * inch, width=0.89 * inch, height=0.566 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y6 - 0.15 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y6 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y6 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y6 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    c.drawString(x2 + 0.1 * inch, y6 - 0.2 * inch, recv_1)

    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 40 else 8 if len(recv_2) < 60 else 6
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 60 else 8 if len(recv_2) < 60 else 6
    story.append(Paragraph(recv_2, style))
    f = Frame(x2 + 0.1 * inch, y7 - 0.1 * inch, 1.8 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 7)
    c.drawString(0.1 * inch, y7 - 0.15 * inch, u'收货前请确认包装是否完整, 有无破损, 如有问题请拒签收')
    c.drawString(0.1 * inch, y7 - 0.4 * inch, u'退建地址：中国东盟(广西)国际快件监管中心')
    c.drawString(0.1 * inch, y7 - 0.6 * inch, u'广西是南宁市良庆区银海大道1219号南宁综合')
    c.drawString(0.1 * inch, y7 - 0.8 * inch, u'电子产业园a208, 电话:15289691652')

    # c.setFont("Helvetica", 10)
    # c.drawString(0.1 * inch, y7 - 0.7 * inch, u'www.ems.com.cn')
    # c.setFont("STSong-Light", 8)
    # c.drawString(1.5 * inch, y7 - 0.7 * inch, u'客服: 11183')

    # c.setFont("STSong-Light", 24)
    # c.drawString(x3 + 0.05 * inch, y7 - 0.55 * inch,
    #              ExpressMark.get_ems_mark1(obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"]))

    c.showPage()


def a4_one_page(c, obj):
    c.setDash(1, 2)
    story = []
    f = Frame(0.08 * inch, 0.07 * inch, (4 - 0.08 * 2) * inch, (6 - 0.07 * 2) * inch, showBoundary=0)
    f.addFromList(story, c)
    ### 从上到下划线 ###
    x1, x2, x3 = 1.519 * inch, 2 * inch, 3 * inch
    y1 = 5.160 * inch
    y2 = 4.393 * inch
    y3 = 3.632 * inch
    y4 = 2.862 * inch
    y5 = 2.351 * inch
    y6 = 1.658 * inch
    y7 = 0.922 * inch
    ys = [y1, y2, y3, y4, y5, y6, y7]
    for y in ys:
        draw_line_horizontal(c, 0 * inch, 4 * inch, y)

    ### 从左到右 ###
    # draw_line_vertical(c, 6 * inch, y1, x1)
    draw_line_vertical(c, y1, y2, x2)
    draw_line_vertical(c, y3, y4, x2)
    draw_line_vertical(c, y6, y7, x2)
    draw_line_vertical(c, 0, y7, x3)

    ## barcdoe ##
    qfbarcode1 = code128.Code128(obj['cn_tracking_no'], barWidth=0.48 * mm, barHeight=0.45 * inch, humanReadable=1,
                                 fontSize=12, fontName='Times-Roman')
    qfbarcode1.drawOn(c, x1 - 0.2 * inch, y1 + 0.3 * inch)
    qfbarcode1.drawOn(c, 0.2 * inch, y6 + 0.2 * inch)

    # LOGO
    # c.drawImage('static/img/XCLOGO.png', 0.1 * inch, y1 + 0.2 * inch, width=0.89 * inch, height=0.566 * inch)
    c.setFont("STSong-Light", 18)

    c.drawString(0.1 * inch, y1 + 0.3 * inch, u'快递包裹')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y1 - 0.15 * inch, u'寄件:')

    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y1 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y1 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y1 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')
    c.setFont('Helvetica', 14)
    c.drawString(3.5 * inch, y1 - 0.5 * inch, u'A4')

    c.setFont("STSong-Light", 6)

    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) < 70 else 9
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) < 70 else 9

    story.append(Paragraph(recv_1, style))
    story.append(Paragraph(recv_2, style))
    f = Frame(0.1 * inch, y3 - 0.15 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    est_weight = obj[u'weight'] * Decimal(0.45359) if obj[u'weight'] != 1 else 0.5 + random.randint(0, 20) / 10.0

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y3 - 0.20 * inch, u'收件人/代收人:')
    c.drawString(0.1 * inch, y3 - 0.40 * inch, u'签收时间       年    月   日    时')

    c.setFont("STSong-Light", 25)
    c.drawString(x2 + 0.1 * inch, y3 - 0.3 * inch, u'已验视')

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y4 - 0.15 * inch, u'订单号:')
    c.drawString(x2 + 0.1 * inch, y4 - 0.15 * inch, u'重量: %.1f' % (est_weight))
    c.drawString(x2 + 1 * inch, y4 - 0.15 * inch, u'件数: 1')

    c.drawString(0.8 * inch, y4 - 0.15 * inch, obj[u'tracking_no'])

    detail = u'配送信息: %s' % (obj[u'goods2'])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(detail) < 70 else 9
    style.leading = 10 if len(detail) < 70 else 9
    style.wordWrap = 'CJK'
    story.append(Paragraph(detail, style))
    f = Frame(0.1 * inch, y5 - 0.47 * inch, 3.55 * inch, 0.8 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.drawImage('static/img/CP.png', 3 * inch, y6 + 0.12 * inch, width=0.89 * inch, height=0.566 * inch)

    c.setFont("STSong-Light", 10)
    c.drawString(0.1 * inch, y6 - 0.15 * inch, u'寄件:')
    c.setFont('Helvetica', 10)
    c.drawString(0.4 * inch, y6 - 0.15 * inch, u'HuskyEx')
    c.drawString(0.4 * inch, y6 - 0.30 * inch, u'7323174312')
    c.drawString(0.1 * inch, y6 - 0.45 * inch, u'77 Glendale Ave, Edison, NJ')

    c.setFont("STSong-Light", 10)
    recv_1 = u'收件: %s  %s' % (obj[u'recv_name'], obj[u'mobile'])
    c.drawString(x2 + 0.1 * inch, y6 - 0.2 * inch, recv_1)

    recv_2 = u'%s %s %s %s' % (obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"], obj[u"recv_address"])
    story = []
    style = ParagraphStyle('Normal')
    style.fontName = "STSong-Light"
    style.fontSize = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 40 else 8 if len(recv_2) < 60 else 6
    style.wordWrap = 'CJK'
    style.leading = 10 if len(recv_2) <= 30  else 9 if len(recv_2) < 60 else 8 if len(recv_2) < 60 else 6
    story.append(Paragraph(recv_2, style))
    f = Frame(x2 + 0.1 * inch, y7 - 0.1 * inch, 1.8 * inch, 0.6 * inch, showBoundary=0, leftPadding=0,
              rightPadding=0, topPadding=0)
    f.addFromList(story, c)

    c.setFont("STSong-Light", 7)
    c.drawString(0.1 * inch, y7 - 0.15 * inch, u'收货前请确认包装是否完整, 有无破损, 如有问题请拒签收')
    c.drawString(0.1 * inch, y7 - 0.4 * inch, u'退建地址：广西南宁市良庆区银海大道1219号 ')
    c.drawString(0.1 * inch, y7 - 0.6 * inch, u'王培春 13599265325')

    # c.setFont("Helvetica", 10)
    # c.drawString(0.1 * inch, y7 - 0.7 * inch, u'www.ems.com.cn')
    # c.setFont("STSong-Light", 8)
    # c.drawString(1.5 * inch, y7 - 0.7 * inch, u'客服: 11183')

    # c.setFont("STSong-Light", 24)
    # c.drawString(x3 + 0.05 * inch, y7 - 0.55 * inch,
    #              ExpressMark.get_ems_mark1(obj[u"recv_prov"], obj[u"recv_city"], obj[u"recv_area"]))

    c.showPage()


def draw_line_horizontal(c, x1, x2, y):
    l = c.beginPath()
    l.moveTo(x1, y)
    l.lineTo(x2, y)
    l.close()
    c.drawPath(l, stroke=1)


def draw_line_vertical(c, y1, y2, x):
    l = c.beginPath()
    l.moveTo(x, y1)
    l.lineTo(x, y2)
    l.close()
    c.drawPath(l, stroke=1)


def draw_label(c, obj):
    if obj['channel_name'] == CH3:
        yhc_one_page(c, obj)
    elif obj['channel_name'] == CH1:
        bc_one_page(c, obj)
    elif obj['channel_name'] == CH2:
        default_one_page(c, obj)
    elif obj['channel_name'] == CH4:
        normal_one_page(c, 'DT', obj)
    elif obj['channel_name'] == CH5:
        normal_one_page(c, 'HM', obj)
    elif obj['channel_name'] == CH6:
        qd_one_page(c, obj)
    elif obj['channel_name'] == CH7:
        fj_one_page(c, obj)
    elif obj['channel_name'] in [CH8, CH14]:
        ch8_one_page(c, obj)
    elif obj['channel_name'] == CH12:
        e_one_page(c, obj)
    elif obj['channel_name'] == CH15:
        normal_one_page(c, 'Z1', obj)
    elif obj['channel_name'] == CH16:
        normal_one_page(c, 'H', obj)
    elif obj['channel_name'] in [CH9, CH10, CH11, CH13]:
        fj_one_page(c, obj)
    elif obj['channel_name'] == CH17:
        jj_one_page(c, obj)
    elif obj['channel_name'] == CH18:
        k1_one_page(c, obj)
    elif obj['channel_name'] == CH19:
        k2_one_page(c, obj)
    elif obj['channel_name'] == CH20:
        ch20_one_page(c, obj)
    elif obj['channel_name'] == 'A2':
        ch8_one_page(c, obj)
    elif obj['channel_name'] == 'A3':
        ch8_one_page(c, obj)
    elif obj['channel_name'] == "SF":
        sigang_page(c, obj)
    elif obj['channel_name'] == CH23:
        nn_one_page(c, obj)
    elif obj['channel_name'] == CH24:
        a4_one_page(c, obj)
    else:
        default_one_page(c, obj)


def multi_pdf_response(objs, fname=None):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    fname = str(uuid.uuid1()) + ".pdf" if not fname else fname
    fpath = settings.MEDIA_ROOT + "/" + fname

    c = Canvas(fpath, pagesize=R4)

    i = 1
    for obj in objs:
        c.setFont('Helvetica', 10)
        c.drawString(0.1 * inch, 0.1 * inch, u'{0}/{1}'.format(i, len(objs)))
        draw_label(c, obj)
        i += 1
    c.save()
    return settings.MEDIA_URL + fname


def one_pdf_write(obj, fname=None):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    fname = str(uuid.uuid1()) + ".pdf" if not fname else fname
    fpath = os.path.join(settings.MEDIA_ROOT, fname)

    c = Canvas(fpath, pagesize=R4)

    draw_label(c, obj)
    c.save()

    return settings.MEDIA_URL + fname


def one_r4_pdf_response(obj):
    pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:false,bSilent:true,bShrinkToFit:true}\);)>>'
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="%s.pdf"' % obj['cn_tracking_no']

    c = Canvas(response, pagesize=R4)

    draw_label(c, obj)

    c.save()

    return response
