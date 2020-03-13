from peewee import *
# from bcrypt

from models.models import BaseModel


class Config(object):
    default_config = None
    tool_config = None
    sign_config = None
    sign_award_config = None
    source_config = None
    loto_config = None
    robot_config = None
    challenge_config = None

    def __init__(self):
        self.default_config = {}
        self.tool_config = {}
        self.sign_award_config = {}
        self.sign_config = {}
        self.source_config = {}
        self.loto_config = {}
        self.robot_config = {}
        self.challenge_config = {}

    def save_default(self, default_dict):
        self.default_config = default_dict


class Game_Config(BaseModel):
    level = IntegerField(verbose_name="关卡数", null=False, default=1)
    target_score = IntegerField(verbose_name="目标分数", null=False, default=0)
    color_num = IntegerField(verbose_name="关卡颜色种类", null=False, default=4)
    direct = IntegerField(verbose_name="看视频通关", null=False, default=0)


class Tools_Config(BaseModel):
    name = CharField(max_length=255, verbose_name="道具名称")
    score = IntegerField(verbose_name="道具消除的分数", null=False, default=0)
