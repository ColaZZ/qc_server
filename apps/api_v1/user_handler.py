#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required
from lib.utils import to_str


@route("/rank")
class RankHandler(FoundHandler):
    # @login_required
    def get(self):
        data = []
        result = self.redis_spare.zrevrange("score", 0, 100, withscores=True)
        if result:
            for key, value in result:
                name = to_str(key)
                score = int(value)
                rank = result.index((key, value)) + 1
                data.append({
                    "rank": rank,
                    "name": name,
                    "score": score
                })
        self.write_json(data)

        # to do 分布式

