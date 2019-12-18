#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required
from lib.utils import to_str


# 世界排名
@route("/rank")
class RankHandler(FoundHandler):
    # @login_required
    def get(self):
        data = []
        # result = []
        result = self.redis_spare.zrevrange("score", 0, 100, withscores=True)
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
                self.redis_spare.zadd("score", {name: score})
                self.redis_spare.hset("user_avatar", name, avatar)

        self.write_json(data)
        # to do 分布式