# -*- coding: utf-8 -*
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import *


# Create your views here.

def blogs_view(request):
    category = request.GET.get('category', '')

    category_objects = Category.objects.all()

    categories = [{"query": "", "name": "所有分类", "class": "active" if category == "" else ""}]

    for cat in category_objects:
        categories.append({"query": cat.name, "name": cat.name, "class": "active" if cat.name == category else ""})

    qs = Post.objects.filter(is_del=False).order_by('-create_dt')
    recent_news = qs[:3]

    if category:
        qs = Post.objects.filter(Q(is_del=False), Q(category__name=category)).order_by('-create_dt')

    return render(
        request, "blog/blog_list.html", {
            "post_list": qs,
            "categories": categories,
            "category": category,
            "recent_news": recent_news,
        })


def blog_detail_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "blog/detail.html", {"post": post})


def about_view(request):
    return render(request, "about.html")


def service_view(request):
    return render(request, "service.html")
