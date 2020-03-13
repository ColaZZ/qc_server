#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import uuid
import time

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import get_user_info, to_str
from lib.constant import USER_SESSION_KEY, COLOR_NUM_CONST, TARGET_SCORE_CONST, SESSION_REDIS_EXPIRES
from lib.gernerate_colors import random_color_array
from apps.models.config import Config


@route('/login')
class LoginHandler(FoundHandler):
    async def post(self):
        # print(self.request.body)
        req_data = json.loads(to_str(self.request.body))
        js_code = req_data.get('code', '')
        # print(js_code)
        # # js_code = "061GyiJJ0rM1G92nTAHJ0KZfJJ0GyiJB"
        #
        if not js_code:
            data = {"state": -1, "msg": "上报code有误，请核对"}
            return self.write_json(data)
        value = {}
        cur = self.cur

        # # 获取玩家信息
        user_info = get_user_info(js_code)
        # user_info = {"openid": "sss", "session_key": "www"}
        open_id = user_info.get("openid", "")
        if not open_id:
            data = {"state": -2, "msg": "解析code有误，请核对1"}
            return self.write_json(data)
        session_key = user_info.get("session_key", "")
        user_session_key = USER_SESSION_KEY + open_id

        # 缓存中尝试获取uuid
        # print(user_session_key)
        # 用来维护用户的登录态（to do 分布式）
        # self.session[user_session_key] = dict(
        #     user_uuid=user_uuid,
        #     open_id=open_id,
        #     session_key=session_key,
        # )
        # self.session.save()
        # print(user_session_key)
        user_session = self.get_session(user_session_key)
        # print(user_session)

        if user_session == [None] or not user_session:
            user_uuid = str(uuid.uuid4())
            self.save_user_session(user_uuid, open_id, session_key)
            # print(user_uuid, open_id, session_key)
            # 1.（数据库）存储用户信息
            value["user_uuid"] = user_uuid
            save_result = self.save_user_info(open_id=open_id, user_uuid=user_uuid)
            if save_result == "False":
                data = {"state": False, "msg": "id问题，请重新登录1", "open_id": open_id,
                    "user_uuid": user_uuid}
                return self.write_json(data,)
            # 注册过但缓存过期， 查数据库，重新hset
            elif save_result == "already":
                # self.redis_spare.hget(user_session_key, level)
                sql = "select u.uuid, ul.level, ul.current_score, gc.target_score, gc.color_num from user as u " \
                      "left join user_level as ul on ul.uuid = u.uuid " \
                      "left join game_config as gc on gc.level = ul.level " \
                      "where open_id=%s"
                cur.execute(sql, open_id)
                result = cur.fetchone()
                if not result:
                    data = {"state": False, "msg": "id问题，请重新登录2"}
                    return self.write_json(data)
                user_uuid = result.get("uuid", "")
                level = result.get("level", 0)
                current_score = result.get("current_score", 0)
                target_score = result.get("target_score", 0)
                color_num = result.get("color_num", 0)

                # 生成color地图
                # color_array = random_color_array(int(color_num))

            else:
                # 未登陆过，生成配置，写数据库，hset缓存
                target_score = current_score = 0
                level = 1
                sql_new = "select color_num, target_score from game_config where level = 1"
                cur.execute(sql_new)
                result = cur.fetchone()
                color_num = result.get("color_num", 0)
                next_level = level + 1
                target_score = result.get("target_score", 0)
                sql_new1 = "insert into user_level (uuid, level, next_level, current_score) values(%s,%s,%s,%s)"
                cur.execute(sql_new1, [user_uuid, level, next_level, current_score])
                cur.connection.commit()

                # 生成color地图
                # color_array = random_color_array(int(color_num))

            # 2.（缓存）存储用户信息
            self.save_user_info_session(
                user_uuid=user_uuid,
                openid=open_id,
                level=level,
                current_score=current_score,
                target_score=target_score,
                color_num=color_num
            )

        else:
            # print(user_session)
            user_uuid = to_str(user_session.get(b"uuid", ""))
            user_info_session = self.get_user_info_session(user_uuid)
            level = to_str(user_info_session.get(b"level", 1))
            current_score = to_str(user_info_session.get(b"current_score", 0))
            target_score = to_str(user_info_session.get(b"target_score", TARGET_SCORE_CONST))
            color_num = to_str(user_info_session.get(b"color_num", COLOR_NUM_CONST))

        # 微信小程序不能设置cookie，把用户信息存在了headers中
        self.set_header("Authorization", user_uuid)

        # 生成color地图
        if int(level) <= 10:
            default_config = Config.default_config
            color_array = default_config.get(int(level), [])
        else:
            color_array = random_color_array(int(level), int(color_num))

        # 登录判断是否授权过
        user_info_session_key = "sx_info:" + user_uuid
        name = to_str(self.redis_spare.hget(user_info_session_key, "name"))
        if name:
            verified = 1
        else:
            verified = 0

        data = {"uuid": user_uuid,
                "openid": open_id,
                "level": level,
                "current_score": current_score,
                "target_score": target_score,
                # "color_num": color_num,
                "color_array": color_array,
                "verified": verified
                }
        # print(data)
        self.write_json(data, msg="success")


@route('/verify')
class PersonalInfoHandler(FoundHandler):
    async def post(self):
        # print(self.request.body)
        uuid = self.get_argument("uuid", "")
        name = self.get_argument("name", "")
        avatar = self.get_argument("avatar", "")

        # print(uuid, name, avatar)

        if not uuid or not name or not avatar:
            return self.write_json(status=-1, msg="请稍后重试")

        cur = self.cur
        sql = "update `user` set `name`=%s, avatar=%s where uuid = %s "
        cur.execute(sql, (name, avatar, uuid))
        cur.connection.commit()

        user_info_session_key = "sx_info:" + uuid
        self.redis_spare.hset(user_info_session_key, "name", name)
        self.redis_spare.hset("user_avatar", name, avatar)

        self.write_json(msg="success")



