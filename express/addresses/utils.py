# coding=utf-8

import os
import shutil
import StringIO
import zipfile

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.conf import settings
from PIL import Image
from PIL.ExifTags import TAGS
from openpyxl import Workbook

from pallets.models import AirWaybill
from waybills.models import Waybill


def compress_id_card_image(person):
    for id_card in (person.id_card_front, person.id_card_backside):
        image = Image.open(id_card)  # 通过cp.picture 获得图像
        image = rotate_by_exif(image)
        width = image.width
        height = image.height

        # 压缩率
        if width >= 2000 or height >= 2000:
            rate = 0.2
        elif width >= 1000 or height >= 1000:
            rate = 0.4
        else:
            continue

        width = int(width * rate)
        height = int(height * rate)
        image.thumbnail((width, height), Image.ANTIALIAS)  # 生成缩略图
        image.save(u'media/' + unicode(id_card))  # 保存到原路径
        person.save()


def rotate_by_exif(img):
    if hasattr(img, '_getexif'):
        # key-value: 根据exif Orientation的值key 进行逆时针旋转value度
        rotate_map = {
            6: 270,
            8: 90,
            3: 180,
        }
        exif_info = img._getexif()
        if exif_info is not None:
            for tag, value in exif_info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == 'Orientation':
                    # 旋转图像
                    img = img.rotate(rotate_map.get(value, 0))
    return img


def id_card_images_to_one_paper(person):
    """将身份证正反面照片粘贴至一张上"""

    front = person.id_card_front
    back = person.id_card_backside

    high_size = front.height + back.height  # 两张身份证图片总高
    width_size = max(front.width, back.width)  # 两张身份证图片最大的宽

    # PIL处理
    id_front = Image.open(front)
    id_backside = Image.open(back)

    # init
    images = [id_front, id_backside]
    result = Image.new('RGB', (width_size, high_size))  # 最终拼接的图像的大小

    # 拼接
    offset = 0
    right = front.height
    for image in images:
        result.paste(image, (0, offset, width_size, right))
        offset += image.height  # 从上往下拼接，左上角的纵坐标递增
        right += image.height  # 左下角的纵坐标也递增

    file_name = '{}_id_card.jpg'.format(person.id)

    # 保存
    image_io = StringIO.StringIO()
    result.save(image_io, format='JPEG')
    id_card_image = InMemoryUploadedFile(image_io, None, file_name, 'image/jpeg',
                                         image_io.len, None)

    person.id_card = id_card_image


def rm_dir(path):
    """rm -rf"""
    ls = os.listdir(path)
    for i in ls:
        c_path = os.path.join(path, i)
        if os.path.isdir(c_path):
            rm_dir(c_path)
        else:
            os.remove(c_path)
    os.removedirs(path)


def zip_dir(src_path, des_path, file_name):
    """
    :param src_path: 需要被压缩的文件夹
    :param des_path: 将输出到des_path
    :param file_name: zip文件的name
    :return: file path of zip
    """

    zip_filename = os.path.join(des_path, u'{}.zip'.format(file_name))
    zip_handler = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(src_path):
        for f in files:
            zip_handler.write(os.path.join(root, f), f)
    zip_handler.close()

    return zip_filename


class IdCardsZipper(object):
    def __init__(self, air_waybill_id):
        self.exception = None
        self.air_waybill_id = air_waybill_id
        self._set_air_waybill_no()
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.tmp_path = os.path.join(self.base_path, self.air_waybill_no)
        os.makedirs(self.tmp_path)

    def __enter__(self):
        self.zip_file = self._get_zip()
        self.zip_file_name = os.path.basename(self.zip_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 删除临时文件夹
        rm_dir(self.tmp_path)
        # 删除zip文件
        if self.zip_file is not None:
            os.remove(self.zip_file)
            
    def _set_air_waybill_no(self):
        air_waybill = AirWaybill.objects.get(pk=self.air_waybill_id)
        self.air_waybill_no = air_waybill.air_waybill_no

    def _get_zip(self):
        # 筛选出运单
        query = Waybill.objects.filter(pallet__air_waybill__id=self.air_waybill_id).query
        query.group_by = ['people']
        waybills = QuerySet(query=query, model=Waybill)

        try:
            # 创建excel
            excel = Workbook()
            excel_name = os.path.join(self.tmp_path, u'运单{}中身份证未拼合单号.xlsx'.format(self.air_waybill_no))
            sheet = excel.active
            sheet.title = u"身份证未拼合单号信息"
            sheet['A1'] = u'身份证未拼合单号'
            sheet['B1'] = u'已打包身份证双面照影印件的单号'
            a_index = b_index = 1

            for waybill in waybills:
                people = waybill.people
                if people.id_card:
                    # 写入excel
                    b_index += 1
                    sheet['B%d' % b_index] = waybill.cn_tracking
                    # 提供收货人身份证影印件, 需要为JPG格式, 并且以: "分单号+"."+s.JPG"命名
                    new_file_path = os.path.join(self.tmp_path, u'{}.s.jpg'.format(waybill.cn_tracking))
                    # 将所有文件copy到临时文件夹
                    shutil.copyfile(people.id_card.file.name, new_file_path)
                # 压缩文件中同时附上一个excel表, 表中有运单没有对应拼合身份证文件的单号
                else:
                    a_index += 1
                    sheet['A%d' % a_index] = waybill.cn_tracking

            excel.save(excel_name)

            # 压缩
            zip_filename = zip_dir(
                src_path=self.tmp_path,
                des_path=self.base_path,
                file_name=self.air_waybill_no
            )

            return zip_filename
        except Exception as e:
            self.exception = e
            return None