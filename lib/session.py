#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uuid
import hmac
import ujson
import hashlib
import redis
import base64


# session_id存储结构
class SessionData(object):
    def __init__(self, session_id, hmac_key):
        self.session_id = session_id
        self.hmac_key = hmac_key


#
class Session(SessionData):
    def __int__(self, session_manager, request_handler):
        self.session_manager = session_manager
        self.request_handler = request_handler
        try:
            current_session = session_manager.get(request_handler)
        except InvalidSessionException:
            current_session = session_manager.get()
        for key, data in current_session.iteritems():
            self[key] = data
        self.session_id = current_session.session_id
        self.hmac_key = current_session.hmac_key

    def save(self):
        self.session_manager.set(self.request_handler, self)


class SessionManager(object):
    def __init__(self, secret, store_options, session_timeout):
        self.secret = secret
        self.session_timeout = session_timeout
        try:
            if store_options['redis_pass']:
                self.redis = redis.StrictRedis(host=store_options['redis_host'], port=store_options['redis_port'],
                                               password=store_options['redis_pass'])
            else:
                self.redis = redis.StrictRedis(host=store_options['redis_host'], port=store_options['redis_port'],)
        except Exception as e:
            print(e)

    # 取出session
    def _fetch(self, session_id):
        try:
            session_data = raw_data = self.redis.get(session_id)
            if raw_data is not None:
                self.redis.setex(session_id, self.session_timeout, raw_data)
                session_data = ujson.loads(raw_data)
            if type(session_data) == type({}):
                return session_data
            else:
                return {}
        except IOError:
            return {}

    def get(self, request_handler=None):
        if request_handler is None:
            session_id = None
            hmac_id = None
        else:
            session_id = request_handler.get_secure_cookie("session_id")
            hmac_key = request_handler.get_secure_cookie("verification")
        if session_id is None:
            session_exists = False
            session_id = self._generate_id()

    # sha256加密session_id
    def _generate_id(self):
        new_id = hashlib.sha256(self.secret + str(uuid.uuid4()))
        return new_id.hexdigest()

    # hmac加密
    def _generate_hmac(self, session_id):
        return hmac.new(session_id, self.secret, hashlib.sha256).hexdigest()


# session报错
class InvalidSessionException(Exception):
    pass


def generate_cookie():
    pass