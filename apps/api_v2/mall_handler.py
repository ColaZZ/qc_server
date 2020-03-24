#!/usr/bin/python3

from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from lib.authenticated_async import authenticated_async
from apps.models.user import User_Mall, User_Coins


# 1. 商店板
@route("/mall")
class MallHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        mall_all = []
        try:
            user_mall = await self.application.objects.execute(
                User_Mall.select(User_Mall.action_id, User_Mall.action_name, User_Mall.status)
                    .where(User_Mall.uuid == uuid)
            )

            for um in user_mall:
                mall_all.append({
                    "id": um.action_id,
                    "action_name": um.action_name,
                    "action_status": um.status
                })

            data = {
                "mall_all": mall_all,
            }
            self.write_json(data)

        except User_Mall.DoesNotExist as e:
            return self.write_json(status=-2, msg="请重新刷新配置")


# 2. 领取按钮
@route("/mall_active")
class MallActiveHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        action_id = self.get_argument("action_id")

        try:
            user_mall = await self.application.objects.get(User_Mall, uuid=uuid, action_id=action_id)

            if user_mall.status == 2:
                return self.write_json(status=-3, msg="您已经领取过该奖励")
            elif user_mall.status == 0:
                return self.write_json(status=-4, msg="抱歉,条件未达到,还不能领取")

            user_mall.status = 0
            if int(action_id) != 2:
                user_mall.status = 2

            # user_mall.status = 2

            user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
            if int(action_id) != 1:
                if int(action_id) == 2:
                    if not user_mall.daily_status:
                        user_coins.coins += 10
                    else:
                        user_coins.coins += 5
                else:
                    user_coins.coins += 10
                await self.application.objects.update(user_coins)

                user_info_session_key = "sx_info:" + uuid
                self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)
            user_mall.daily_status = 1
            await self.application.objects.update(user_mall)

            user_mall_all = await self.application.objects.execute(
                User_Mall.select(User_Mall.action_id, User_Mall.action_name, User_Mall.status)
                    .where(User_Mall.uuid == uuid)
            )
            mall_all = []
            for um in user_mall_all:
                mall_all.append({
                    "id": um.action_id,
                    "action_name": um.action_name,
                    "action_status": um.status
                })
            data = {
                "mall_all": mall_all,
                "coins": user_coins.coins
            }

            # data = [{
            #     "id": user_mall.action_id,
            #     "action_name": user_mall.action_name,
            #     "action_status": user_mall.status,
            #     "mall": mall_all
            # }]
            self.write_json(data)

        except User_Mall.DoesNotExist as e:
            return self.write_json(status=-2, msg="请重新刷新配置")


# 3.客服会话
@route("/mall_csr")
class MallCSRHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        try:
            # await self.application.objects.execute(
            #     User_Mall.update(status=1).where(User_Mall.uuid == uuid and )
            # )
            user_mall = await self.application.objects.get(User_Mall, uuid=uuid, action_id=3)
            if not user_mall.status:
                user_mall.status = 1
                await self.application.objects.update(user_mall)
                user_mall_all = await self.application.objects.execute(
                    User_Mall.select(User_Mall.action_id, User_Mall.action_name, User_Mall.status)
                        .where(User_Mall.uuid == uuid)
                )
                mall_all = []
                for um in user_mall_all:
                    mall_all.append({
                        "id": um.action_id,
                        "action_name": um.action_name,
                        "action_status": um.status
                    })

                return self.write_json(msg="success", data=mall_all)
            return self.write_json(status=-2, msg="抱歉,您已经领取过了")

        except User_Mall.DoesNotExist as e:
            self.write_json(status=-1, msg="请稍后再试")


@route("/mall_env")
class MallEnvHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        env_id = int(self.get_argument("SceneId", "") or 0)
        uuid = self.current_user.uuid

        if int(env_id) == 1089:
            # 收藏渠道4
            try:
                user_mall = await self.application.objects.get(User_Mall, uuid=uuid, action_id=4)
                if not user_mall.status:
                    user_mall.status = 1
                    await self.application.objects.update(user_mall)
            except User_Mall.DoesNotExist as e:
                pass
        elif int(env_id) == 1131:
            # 浮窗渠道5
            try:
                user_mall = await self.application.objects.get(User_Mall, uuid=uuid, action_id=5)
                if not user_mall.status:
                    user_mall.status = 1
                    await self.application.objects.update(user_mall)
            except User_Mall.DoesNotExist as e:
                pass
        self.write_json()

