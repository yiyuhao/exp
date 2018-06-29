# coding=utf-8
from celery.result import AsyncResult
from django.conf import settings

from express.celery import app
from celery.utils.log import get_task_logger
from waybills.models import *
from celery.exceptions import SoftTimeLimitExceeded

logger = get_task_logger(__name__)


@app.task(bind=True, soft_time_limit=10800)
def update_cn_tracking(self):
    try:
        l = [u'国内派送', u'海关查验']
        qs = Waybill.objects.filter(status__name__in=l)[:10] if settings.DEBUG else Waybill.objects.filter(
            status__name__in=l)
        errors = []
        i = 0
        for w in qs:
            i += 1
            try:
                self.update_state(state='PROGRESS', meta={'current': i, 'total': qs.count()})
                # logger.info('{0}'.format(self.AsyncResult(self.request.id).info))
                w.update_cn_tracking_info()
            except Exception as e:
                errors.append({"tracking_no": w.cn_tracking, "err": e.message})

        return {'total': qs.count(), 'succ': qs.count() - len(errors), 'fail': len(errors), "errors": errors}
    except SoftTimeLimitExceeded:
        return {'total': qs.count(), 'succ': qs.count() - len(errors), 'fail': len(errors), "errors": errors}


@app.task(bind=True, soft_time_limit=5000)
def update_cn_tracking_by_air_waybill_no(self, air_waybill_no):
    l = [u'国内派送', u'海关查验']
    qs = Waybill.objects.filter(status__name__in=l).filter(pallet__air_waybill__air_waybill_no=air_waybill_no)[
         :10] if settings.DEBUG else Waybill.objects.filter(status__name__in=l).filter(
        pallet__air_waybill__air_waybill_no=air_waybill_no)
    errors = []
    i = 0
    for w in qs:
        i += 1
        try:
            self.update_state(state='PROGRESS', meta={'current': i, 'total': qs.count()})
            # logger.info('{0}'.format(self.AsyncResult(self.request.id).info))
            w.update_cn_tracking_info()
        except Exception as e:
            errors.append({"tracking_no": w.cn_tracking, "err": e.message})

    return {'total': qs.count(), 'succ': qs.count() - len(errors), 'fail': len(errors), "errors": errors}


def get_task_status(task_id):
    task = AsyncResult(task_id)

    return task.state, task.info


@app.task(bind=True)
def update_yhc_cn_tracking(self):
    qs = Waybill.objects.filter(channel__name=CH3).filter(status__name=u'国内清关')[
         :10] if settings.DEBUG else Waybill.objects.filter(channel__name=CH3).filter(status__name=u'国内清关').order_by(
        'create_dt')
    errors = []
    i = 0
    for w in qs:
        i += 1
        try:
            self.update_state(state='PROGRESS', meta={'current': i, 'total': qs.count()})
            # logger.info('{0}'.format(self.AsyncResult(self.request.id).info))
            w.update_yhc_status()
        except Exception as e:
            errors.append({"tracking_no": w.cn_tracking, "err": e.message})

    return {'total': qs.count(), 'succ': qs.count() - len(errors), 'fail': len(errors), "errors": errors}


@app.task(bind=True, soft_time_limit=10)
def update_waybill_cn_tracking(self, id):
    try:
        w = Waybill.objects.get(id=id)
        w.update_cn_tracking_info()
        return {'waybill': w.tracking_no, "error": ""}
    except SoftTimeLimitExceeded:
        return {'waybill': w.tracking_no, "error": '超时'}
    except Exception as e:
        return {'waybill': w.tracking_no, "error": e.message}


        # @app.task(bind=True,soft_time_limit=10)
        # def test(self):
        #     import time
        #     try:
        #         t_end = time.time() + 15
        #         while time.time() < t_end:
        #             pass
        #     except SoftTimeLimitExceeded:
        #         print 'hello time out'
        #     except Exception as e:
        #         print ''
