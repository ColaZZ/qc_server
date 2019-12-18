#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uuid
import base64
# import time
# import random
# import hashlib
import requests

from lib.constant import APPID, APPSECRET


# def login_required(f):
#     def _wrapper(self, *args, **kwargs):
#         # print("current_user", self.get_current_user())
#         logged = self.get_current_user()
#         if logged is None:
#             # 无session，返回登录 etc
#             self.write('no login')
#             self.finish()
#         else:
#             ret = f(self, *args, **kwargs)
#
#     return _wrapper

def login_required(f):
    def _wrapper(self, *args, **kwargs):
        # print("current_user", self.get_current_user())
        uuid = self.get_argument("uuid", "")
        session_key = self.get_current_uuid(uuid)
        if session_key is None:
            self.write_json({"state": False, "msg": "请重新登录"})
            # 无session，返回登录 etc
            self.write('no login')
            self.finish()
        else:
            ret = f(self, *args, **kwargs)

    return _wrapper


def generate_cookie_secret():
    cookie_secret = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes + uuid.uuid4().bytes)
    cookie_secret = cookie_secret.decode("utf-8")
    return cookie_secret


def generate_session_secret(length=64, allowed_chars=None, secret_key=None):
    session_secret = base64.b64encode(uuid.uuid1().bytes + uuid.uuid1().bytes + uuid.uuid1().bytes)
    session_secret = session_secret.decode("utf-8")
    return session_secret


# bytes转str
def to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value    #Instance of str


# 获取用户身份标识 from wechat
def get_user_info(js_code):
    req_params = {
        "appid": APPID,         # 小程序ID
        "secret": APPSECRET,     # 小程序secret_key
        "js_code": js_code,
        "grand_type": "authorization_code",
    }

    req_result = requests.get('https://api.weixin.qq.com/sns/jscode2session',
                              params=req_params, timeout=3, verify=False)
    return req_result.json()
