#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.constant import USER_SESSION_KEY
from lib.utils import to_str
from lib.gernerate_colors import random_color_array
from apps.models.config import Config


# 下一关接口
@route("/next_level")
class LevelHandler(FoundHandler):
    # @login_required
    async def get(self):
        uuid = self.get_argument("uuid", "")
        level = self.get_argument("level", "")
        score = self.get_argument("score", "")

        if not uuid or not score or not level:
            return self.write_json(status=-1, msg="请稍后重试")


        cur = self.cur
        level = int(level)
        next_level = level + 1
        # 先删缓存，再更新数据库
        # to do 分布式缓存
        # user_session_key = USER_SESSION_KEY + uuid
        # self.session[user_session_key].pop('level')
        # self.session.save()

        # 1. 删缓存
        user_info_session_key = "sx_info:" + uuid
        open_id = to_str(self.redis_spare.hget(user_info_session_key, b"open_id"))
        name = to_str(self.redis_spare.hget(user_info_session_key, b"name"))
        self.redis_spare.delete(user_info_session_key)

        # 2.更新数据库
        score = int(score)
        # print(uuid, level, next_level, score)
        # sql = "insert into user_level (uuid, `level`, next_level,current_score) values(%s, %s, %s, %s)"
        sql = "update user_level set `level`=%s, next_level=%s, current_score=%s where uuid = %s"
        cur.execute(sql, [level, next_level, score, uuid])
        cur.connection.commit()

        sql_query = "select `level`, target_score, color_num from game_config where level in (%s, %s)"
        cur.execute(sql_query, [level, next_level])
        result = cur.fetchall()
        if not result:
            return self.write_json(status=-2, msg="请重新刷新配置")

        next_target_score = next_color_num = 0
        if len(result) == 1:
            # 已到最大关卡
            next_level = level
            for res in result:
                next_target_score = res.get("target_score", 0)
                next_color_num = res.get("color_num", 0)

        elif len(result) == 2:
            # 未达到最大关卡
            for res in result:
                level = res.get("level", 0)
                if level == next_level:
                    next_target_score = res.get("target_score", 0)
                    next_color_num = res.get("color_num", 0)

        # set 缓存
        self.save_user_info_session(
            user_uuid=uuid,
            openid=open_id,
            level=level,
            current_score=score,
            target_score=next_target_score,
            color_num=next_color_num
        )
        # 存入排行榜
        self.redis_spare.zadd("world_rank", {name: score})

        #
        if int(next_level) <= 10:
            default_config = Config.default_config
            color_array = default_config.get(int(next_level), [])
        else:
            color_array = random_color_array(int(next_level), int(next_color_num))


        data = {
            "next_level": next_level,
            "next_target_score": next_target_score,
            # "next_color_num": next_color_num,
            "score": score,
            "color_array": color_array
        }
        self.write_json(data)




