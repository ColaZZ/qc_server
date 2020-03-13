#!/usr/bin/python3

import json

from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from lib.authenticated_async import authenticated_async

from apps.models.user import User_Challenge


# 1.闯关入口
@route('/challenge')
class ChallengeHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        user_info_session_key = "sx_info:" + uuid

        challenge_info = eval(self.redis_spare.hget(user_info_session_key, "challenge_info"))

        self.write_json(challenge_info)


#2.挑战结束保存结果
@route('/challenge_next')
class ChallengeNextHandler(RedisHandler):
    @authenticated_async
    async def post(self):
        uuid = self.current_user.uuid
        level = str(self.get_argument("level", "") or 0)
        star = int(self.get_argument("star", "") or 0)
        if not level or not star:
            return self.write_json(status=-1, msg="请稍后重试")
        user_info_session_key = "sx_info:" + uuid
        user_challenge = await self.application.objects.get(User_Challenge, uuid=uuid)
        challenge_info = eval(user_challenge.challenge_info)
        challenge_info[level] = star
        if int(level) < 120:
            next_level = int(level) + 1
            challenge_info[next_level] = 0
        else:
            next_level = level


        user_challenge.challenge_info = json.dumps(challenge_info)
        await self.application.objects.update(user_challenge)

        challenge_info_json = json.dumps(challenge_info)
        self.redis_spare.hset(user_info_session_key, "challenge_info", challenge_info_json)


        # test = await self.application.objects.get(User_Challenge, uuid=uuid)
        data = {
            "next_level": next_level
        }
        self.write_json(data)




