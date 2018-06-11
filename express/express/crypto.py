# -*- coding: utf-8 -*

from __future__ import unicode_literals

import base64
import hashlib


def md5(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()


def base64_encode(s):
    return base64.b64encode(s)


def base64_decode(str):
    return base64.decodestring(str)