#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import uuid

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import get_user_info


@route('/login')
class LoginHandler(FoundHandler):
    def post(self):
        # req_data = json.loads(self.request.body)
        # js_code = req_data.get('code', '')
        #
        # if not js_code:
        #     data = {"state": False, "msg": "上报code有误，请核对"}
        #     return self.write_json(data)
        value = {}

        # # 获取玩家信息
        # user_info = get_user_info(js_code)
        user_info = {"open_id": "sss", "session_key": "www"}
        # open_id = user_info.get("open_id", "")
        # session_key = user_info.get("session_key", "")
        user_uuid = str(uuid.uuid4())
        open_id = "121212"
        session_key = "asdasdsad"

        # 用来维护用户的登录态
        user_session_key = "sx" + user_uuid
        print(type(user_session_key))
        self.session[user_session_key] = dict(
            user_uuid=user_uuid,
            open_id=open_id,
            session_key=session_key
        )
        print(user_session_key)
        self.session.save()
        print(self.session.get(user_session_key))

        # 微信小程序不能设置cookie，把用户信息存在了headers中
        self.set_header("Authorization", user_uuid)

        # 存储用户信息
        value["user_uuid"] = user_uuid
        save_result = self.save_user_info(open_id=open_id, value=value)
        if not save_result:
            data = {"state": False, "msg": "id问题，请重新登录"}
            return self.write_json(data)

        data = {"user_id": user_uuid}
        self.write_json(data)



