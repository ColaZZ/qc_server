from queue import Queue
import copy
import random

from lib.constant import COLORS

# 读取配置生成颜色阵列


# 随机生成颜色阵列
def random_color_array(level, color_num):
    # 随机颜色种类
    if level <= 50:
        random_list = random.sample(COLORS[:5], color_num)
    else:
        random_list = random.sample(COLORS, color_num)
    test = [random.choice(random_list) for _ in range(100)]
    return [test[i:i + 10] for i in range(0, len(test), 10)], random_list



