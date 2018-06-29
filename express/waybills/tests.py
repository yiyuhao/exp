from django.test import TestCase

# Create your tests here.
from waybills.tasks import *

tracking_no = '123124'

t = notify_order_send_out.delay(tracking_no, 'abc')