#!/usr/bin/python3
import time

from lib.routes import route
from apps.found_handler_v2 import RedisHandler
from lib.authenticated_async import authenticated_async
from apps.models.user import User_Tools, User_Coins, User_Mall, User


# 获取道具
@route("/get_tools")
class GetToolHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        tool_id = int(self.get_argument("tool_id", "") or 0)
        count = int(self.get_argument("count", "") or 0)
        coins = int(self.get_argument("coins", "") or 0)

        if not uuid or not tool_id:
            return self.write_json(status=-1, msg="请稍后重试")

        user_info_session_key = "sx_info:" + uuid
        redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
        # self.redis_spare.delete(user_info_session_key)

        # current_coins = int(user_info_session.get("coins", 0))
        # if current_coins - coins < 0:
        #     return self.write_json(status=-2, msg="星星不足,无法购买")
        # current_coins -= coins

        # 更新数据库
        try:
            user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
            current_coins = user_coins.coins
            if current_coins - coins < 0:
                return self.write_json(status=-2, msg="星星不足,无法购买")
            user_coins.coins -= coins

            user_tool = await self.application.objects.get(User_Tools, uuid=uuid, tool_id=tool_id)
            user_tool.count += count
            await self.application.objects.update(user_tool)
            await self.application.objects.update(user_coins)
            # user_tools = await self.application.objects.execute(
            #     User_Tools.select(User_Tools.tool_id, User_Tools.count).where(User_Tools.uuid==uuid)
            # )

            # last_tools = {}
            # use_tool_count = 0
            # for tool in user_tools:
            #     if tool.tool_id == tool_id:
            #         tool.count += count
            #         use_tool_count = tool.count
            #     last_tools[tool.tool_id] = tool.count
            #

            # if use_tool_count:
            #     print(tool_id)
            #     print(use_tool_count)
            #     use_tool = self.application.objects.get(User_Tools, uuid=uuid, )


            user_info_session_key = "sx_info:" + uuid
            self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)
            redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
            redis_tools[tool_id] = user_tool.count

            self.redis_spare.hset(user_info_session_key, "tools", str(redis_tools))
            data = {
                "tools": redis_tools,
                "coins": user_coins.coins
            }
            self.write_json(status=1, msg="购买成功", data=data)
        except User_Coins.DoesNotExist as e:
            return self.write_json(status=-2, msg="请重新刷新配置")
        except User_Tools.DoesNotExist as e:
            return self.write_json(status=-3, msg="请重新获取道具配置")


# 玩家使用道具
@route('/use_tool')
class UserToolHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        tool_id = int(self.get_argument("tool_id", "") or 0)
        count = int(self.get_argument("count", "") or 0)
        coins = int(self.get_argument("coins", "") or 0)


        if not tool_id:
            return self.write_json(status=-1, msg="请稍后重试")

        user_info_session_key = "sx_info:" + uuid
        redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
        # self.redis_spare.delete(user_info_session_key)

        # 数据库
        try:
            user_tools = await self.application.objects.get(User_Tools, uuid=uuid, tool_id=tool_id)
            mysql_count = user_tools.count

            if not coins:

                if mysql_count - count < 0:
                    return self.write_json(status=-3, msg="道具数量不足")

                mysql_count -= count
                user_tools.count = mysql_count
                await self.application.objects.update(user_tools)
                redis_tools[tool_id] = mysql_count

                self.redis_spare.hset(user_info_session_key, "tools", str(redis_tools))

                data = {
                    "tools": redis_tools,
                }
            else:
                user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
                if coins <= user_coins.coins:
                    user_coins.coins -= coins
                else:
                    return self.write_json(status=-4, msg="抱歉,货币数量不足")
                await self.application.objects.update(user_coins)

                self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)

                data = {
                    "tools": redis_tools,
                    "coins": user_coins.coins
                }

            self.write_json(status=1, msg="使用成功", data=data)

        except User_Tools.DoesNotExist as e:
            return self.write_json(status=-2, msg="请重新获取道具配置")


# 广告获取道具
@route('/ad_tools')
class AdToolsHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        tool_id = int(self.get_argument("tool_id", "") or 0)
        count = int(self.get_argument("count", "") or 0)

        if not uuid or not tool_id:
            return self.write_json(status=-1, msg="请稍后重试")
        user_info_session_key = "sx_info:" + uuid
        # 1001 加金币
        if tool_id == 1001:
            try:
                user_mall = await self.application.objects.get(User_Mall, uuid=uuid, action_id=1)
                # user = await self.application.objects.get(User, uuid=uuid)
                try:
                    user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
                    if not user_mall.daily_status:
                        user_coins.coins += 10
                        user_mall.daily_status = 1
                    else:
                        user_coins.coins += 5
                    await self.application.objects.update(user_coins)
                    await self.application.objects.update(user_mall)
                    self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)
                    tool_count = user_coins.coins
                except User_Coins.DoesNotExist as e:
                    return self.write_json(status=-2, msg="请重新刷新配置")
                user_mall.daily_status = 1
                await self.application.objects.update(user_mall)
            except User_Mall.DoesNotExist as e:
                return self.write_json(status=-4, msg="请重新刷新配置")
        else:
            try:
                user_tool = await self.application.objects.get(User_Tools, uuid=uuid, tool_id=tool_id)
                user_tool.count += count
                await self.application.objects.update(user_tool)
                redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
                redis_tools[tool_id] = user_tool.count
                self.redis_spare.hset(user_info_session_key, "tools", str(redis_tools))
                tool_count = user_tool.count
            except User_Tools.DoesNotExist as e:
                return self.write_json(status=-3, msg="请重新刷新配置")



        data = {
            "tool_id": tool_id,
            "count": tool_count
        }
        self.write_json(status=1, msg="广告成功", data=data)


