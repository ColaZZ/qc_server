#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required



@route("/rank")
class RankHandler(FoundHandler):
    # @login_required
    def get(self):
        cur = self.cur
        # 前100名排名
        sql = "select u.avatar, u.name, ul.current_score " \
              "left join user as u on u.uuid = ul.uuid " \
              "from user_level as ul " \
              "order by current_score desc "
        cur.execute(sql)
        result = cur.fetchall()
        if not result:
            # data = {"state": -1, "msg": "上报code有误，请核对"}
            return self.write_json(status=-1, msg="请稍后重试")

        data = {}
        for ran in result:
            name = ran.get("name", "")
            avatar = ran.get("avatar", "")
            current_score = ran.get("current_score", 0)
            data['']