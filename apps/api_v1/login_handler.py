#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import uuid

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import get_user_info, to_str
from lib.constant import USER_SESSION_KEY, COLOR_NUM_CONST, TARGET_SCORE_CONST, SESSION_REDIS_EXPIRES


@route('/login')
class LoginHandler(FoundHandler):
    def post(self):
        req_data = json.loads(self.request.body)
        js_code = req_data.get('code', '')

        if not js_code:
            data = {"state": -1, "msg": "上报code有误，请核对"}
            return self.write_json(data)
        value = {}
        cur = self.cur

        # # 获取玩家信息
        user_info = get_user_info(js_code)
        # user_info = {"openid": "sss", "session_key": "www"}
        open_id = user_info.get("openid", "")
        session_key = user_info.get("session_key", "")
        user_session_key = USER_SESSION_KEY + open_id

        # 缓存中尝试获取uuid

        # 用来维护用户的登录态（to do 分布式）
        # self.session[user_session_key] = dict(
        #     user_uuid=user_uuid,
        #     open_id=open_id,
        #     session_key=session_key,
        # )
        # self.session.save()
        user_session = to_str(self.get_session(user_session_key))
        user_uuid = user_session.get("uuid", "")

        if not user_uuid:
            user_uuid = str(uuid.uuid4())
            self.save_user_session(user_uuid, open_id, session_key)

            # 1.（数据库）存储用户信息
            value["user_uuid"] = user_uuid
            save_result = self.save_user_info(open_id=open_id, user_uuid=user_uuid)
            if save_result == "False":
                data = {"state": False, "msg": "id问题，请重新登录"}
                return self.write_json(data)
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
                    data = {"state": False, "msg": "id问题，请重新登录"}
                    return self.write_json(data)
                user_uuid = result.get("uuid", "")
                level = result.get("level", 0)
                current_score = result.get("current_score", 0)
                target_score = result.get("target_score", 0)
                color_num = result.get("color_num", 0)

            else:
                # 未登陆过，生成配置，写数据库，hset缓存
                target_score = current_score = 0
                level = 1
                sql_new = "select color_num from game_config where level = 1"
                cur.execute(sql_new)
                result = cur.fetchone()
                color_num = result.get("color_num", 0)
                next_level = level + 1
                sql_new1 = "insert into user_level (uuid, level, next_level, current_score) values(%s,%s,%s,%s)"
                cur.execute(sql_new1, [user_uuid, level, next_level, current_score])
                cur.connection.commit()

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
            user_info_session = self.get_user_info_session(user_uuid)
            level = to_str(user_info_session.get("level", 1))
            current_score = to_str(user_info_session.get("current_score", 0))
            target_score = to_str(user_info_session.get("target_score", TARGET_SCORE_CONST))
            color_num = to_str(user_info_session.get("color_num", COLOR_NUM_CONST))

        # 微信小程序不能设置cookie，把用户信息存在了headers中
        self.set_header("Authorization", user_uuid)
        data = {"uuid": user_uuid,
                "openid": open_id,
                "level": level,
                "current_score": current_score,
                "target_score": target_score,
                "color_num": color_num
                }
        self.write_json(data, msg="success")



