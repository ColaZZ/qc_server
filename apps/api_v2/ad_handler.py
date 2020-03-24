# #!/usr/bin/python3
# import time
# import datetime
#
# from peewee import *
#
# from apps.found_handler_v2 import RedisHandler
# from lib.routes import route
# from lib.authenticated_async import authenticated_async
#
#
# @route("/banner_ad")
# class BannerAdHandler(RedisHandler):
#     @authenticated_async
#     async def get(self):
#         uuid = self.current_user.uuid
#         day_time = int(time.mktime(datetime.date.today().timetuple()))
#
#
#
