#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uuid
import base64
import time
import random
import hashlib


def login_required(f):
    def _wrapper(self, *args, **kwargs):
        print("current_user", self.get_current_user())
        logged = self.get_current_user()
        if logged is None:
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
