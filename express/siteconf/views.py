# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.base import View
from django.shortcuts import render

from siteconf.models import Banner
from blog.models import Post


class IndexView(View):
    """首页"""

    def get(self, request):
        from t import gen_waybill_pdfs
        gen_waybill_pdfs('hangkongtidanhao')

        # 轮播图
        banners = Banner.objects.order_by('index').all()[:2]

        qs = Post.objects.filter(is_del=False).order_by('-create_dt')[:5]

        return render(request, 'index.html', {'post_list': qs,
                                              'banners': banners})
