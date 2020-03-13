from datetime import datetime

from peewee import *
# from bcrypt

from models.models import BaseModel


class User(BaseModel):
    open_id = CharField(max_length=50, null=False, verbose_name="open_id", unique=True, primary_key=True)
    uuid = CharField(max_length=50, verbose_name="uuid", unique=True, null=False, )
    name = CharField(max_length=60, null=True, verbose_name="微信昵称")
    avatar = CharField(max_length=200, verbose_name="微信头像")
    register_time = DateTimeField(default=datetime.now, verbose_name="注册时间")
    phone = CharField(max_length=11, verbose_name="手机号码")
    login_time = DateField(default=datetime.now, verbose_name="每天第一次登录时间")


class User_Level(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    # uuid = ForeignKeyField(User, verbose_name="uuid")
    level = IntegerField(verbose_name="当前关卡", null=False, default=1)
    next_level = IntegerField(verbose_name="下一关卡", null=False, default=2)
    current_score = IntegerField(verbose_name="当前分数", null=False, default=0)
    restart = IntegerField(verbose_name="重置状态", null=False, default=0)
    history_score = IntegerField(verbose_name="历史最高分", null=False, default=0)


class User_Coins(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    # uuid = ForeignKeyField(User, verbose_name="uuid")
    coins = IntegerField(verbose_name="货币数量", null=False, default=0)


class User_Sign(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    lastest_sign_date = DateField(verbose_name="最近签到时间")
    continuous_sign_days = IntegerField(verbose_name="连续签到天数", null=False, default=0)
    extra = IntegerField(verbose_name="双倍领取开关", null=False, default=0)


class User_Tools(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    tool_id = IntegerField(verbose_name="道具id", null=False, default=0)
    count = IntegerField(verbose_name="道具数量", null=False, default=0)


class User_Mall(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    action_id = IntegerField(verbose_name="展示id", null=False, default=0)
    action_name = CharField(max_length=200, verbose_name="展示名称", null=False, default="")
    status = IntegerField(verbose_name="完成状态", null=False, default=0)
    daily_status = IntegerField(verbose_name="每天第一次完成状态", null=False, default=0)


class User_Loto(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    number = IntegerField(verbose_name="抽奖次数", null=False, default=3)


class User_Challenge(BaseModel):
    uuid = CharField(max_length=255, verbose_name="uuid", unique=True)
    challenge_info = BlobField(null=False, verbose_name="挑战信息")




