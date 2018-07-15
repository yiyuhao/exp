from django.test import TestCase

# Create your tests here.
from wand.image import Image
from wand.color import Color
from PIL import Image as im
from express import settings
from pallets.models import *
from waybills.models import *
import os

from waybills.pdf_template import one_pdf_write
import shutil


def convert_pdf_to_jpg(input_path, output_path):
    with Image(filename=input_path, resolution=300) as img:
        img.background_color = Color('white')
        img.format = 'jpg'
        img.compression_quality = 60
        img.save(filename=output_path)


def gen_waybill_pdfs(air_waybill_no):
    qs = Waybill.objects.filter(pallet__air_waybill__air_waybill_no=air_waybill_no).order_by('tracking_no')
    qs = Waybill.objects.all()
    cnt = 0
    base_path = os.path.join(settings.MEDIA_ROOT, air_waybill_no)
    if os.path.isdir(base_path):
        shutil.rmtree(base_path)
    os.mkdir(base_path)
    for w in qs:
        fname = os.path.join(air_waybill_no, w.cn_tracking + '.pdf')
        one_pdf_write(w.get_wrap_pdf(), fname)
        fpath = os.path.join(settings.MEDIA_ROOT, fname)
        convert_pdf_to_jpg(fpath, fpath.replace('pdf', 'y.JPG'))
        os.remove(fpath)
        cnt += 1
        print cnt


def gen_waybill_pdfs2(folder_name, qs):
    print folder_name
    cnt = 0
    if not os.path.isdir(settings.MEDIA_ROOT + '/' + folder_name):
        os.mkdir(settings.MEDIA_ROOT + '/' + folder_name)
    else:
        shutil.rmtree(settings.MEDIA_ROOT + '/' + folder_name)
        os.mkdir(settings.MEDIA_ROOT + '/' + folder_name)
    for w in qs:
        fname = folder_name + '/' + w.cn_tracking + '.pdf'
        one_pdf_write(w.get_wrap_pdf(), fname)
        fpath = settings.MEDIA_ROOT + "/" + fname
        convert_pdf_to_jpg(fpath, fpath.replace('pdf', 'y.JPG'))
        os.remove(fpath)
        cnt += 1
        print cnt


def gen_batch(folder_names, l_qs):
    if len(folder_names) != len(l_qs):
        return
    else:
        for (folder_name, qs) in zip(folder_names, l_qs):
            gen_waybill_pdfs2(folder_name, qs)


if __name__ == '__main__':
    gen_waybill_pdfs('000001')
    pass
