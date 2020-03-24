#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required
from lib.utils import to_str
from lib.gernerate_colors import random_color_array



# 世界排名
@route("/rank")
class RankHandler(FoundHandler):
    # @login_required
    async def get(self):
        data = []
        # result = []
        result = self.redis_spare.zrevrange("world_rank", 0, 100, withscores=True)
        if result:
            for key, value in result:
                name = to_str(key)
                score = int(value)
                rank = result.index((key, value)) + 1
                avatar = to_str(self.redis_spare.hget("user_avatar", name))
                data.append({
                    "rank": rank,
                    "name": name,
                    "score": score,
                    "avatar": avatar
                })
        else:
            # 缓存失效的情况
            cur = self.cur
            # 前100名排名
            sql = "select a.*, (@rowNum:=@rowNum+1) as rank from (SELECT @rownum := 0) as r, " \
                  "(select avatar, name, current_score from user_level as ul left join user as u on u.uuid=ul.uuid " \
                  "order by ul.current_score DESC ) as a "
            cur.execute(sql)
            result = cur.fetchall()
            if not result:
                return self.write_json(status=-1, msg="请稍后重试")

            for rk in result:
                name = rk.get("name", "")
                avatar = rk.get("avatar", "")
                score = int(rk.get("current_score", 0))
                rank = int(rk.get("rank", 0))
                data.append({
                    "rank": rank,
                    "name": name,
                    "score": score,
                    "avatar": avatar
                })
                # 排好的名次push入redis缓存
                self.redis_spare.zadd("world_rank", {name: score})
                self.redis_spare.hset("user_avatar", name, avatar)

        self.write_json(data)
        # to do 分布式


# TODO 重置游戏
@route("/restart")
class RestartHandler(FoundHandler):
    async def get(self):
        uuid = self.get_argument("uuid", "")

        if not uuid:
            return self.write_json(status=-1, msg="请稍后重试")

        # 1. 删缓存
        user_info_session_key = "sx_info" + uuid
        open_id = to_str(self.redis_spare.hget(user_info_session_key, b"open_id"))
        name = to_str(self.redis_spare.hget(user_info_session_key, b"name"))
        self.redis_spare.delete(user_info_session_key)

        # 2.更新数据库
        cur = self.cur
        sql = "update user_level set `level`= %s, next_level=%s, current_score=%s where uuid =%s"
        cur.execute(sql, [1, 2, 0, uuid])
        cur.connection.commit()

        sql_query = "select `level`, target_score, color_num from game_config where `level`=%s"
        cur.execute(sql_query, [1])
        result = cur.fetchone()
        if not result:
            return self.write_json(status=-2, msg="请重新刷新配置")

        next_target_score = result.get("target_score", 0)
        next_color_num = result.get("color_num", 0)

        # set缓存
        self.save_user_info_session(
            user_uuid=uuid,
            openid=open_id,
            level=1,
            current_score=0,
            target_score=next_target_score,
            color_num=next_color_num
        )

        # 存入排行榜
        self.redis_spare.zadd("world_rank", {name: 0})

        color_array = random_color_array(1, int(next_color_num))

        data = {
            "level": 1,
            "target_score": next_target_score,
            # "next_color_num": next_color_num,
            "current_score": 0,
            "color_array": color_array
        }
        self.write_json(data)
