import base64
import json
import random
import time

'''
    根据长度生成滑块轨迹
'''
def mt(x_distance, start_x=1100, y_range=(480, 500)):
    """
    生成鼠标轨迹数据，模拟 x 轴移动，y 轴随机变化。

    :param x_distance: x 轴要移动的总距离
    :param start_x: x 轴起始值，默认为 1100
    :param y_range: y 轴的随机范围 (min_y, max_y)
    :return: 轨迹列表，格式为 [{"x": ..., "y": ..., "t": ...}, ...]
    """
    trajectory = []
    current_x = start_x
    current_y = random.randint(*y_range)
    current_time = int(time.time() * 1000)  # 当前时间戳（毫秒）
    step = random.randint(1, 4)  # x 轴每次移动的最小步长

    while current_x < start_x + x_distance:
        current_x += random.randint(step, step + 2)  # 每次随机移动步长
        current_y += random.choice([-1, 0, 1])  # y 轴小幅随机变化
        current_y = max(y_range[0], min(y_range[1], current_y))  # 限制 y 范围
        current_time += random.randint(2, 10)  # 模拟时间流逝（2-10ms 变化）

        trajectory.append({"x": current_x, "y": current_y, "t": current_time})

    return trajectory

'''
    加密滑块轨迹
'''
def ef(unit_distance):
    """对轨迹数据进行 Base64 编码"""
    json_str = json.dumps(unit_distance, separators=(',', ':'))  # 转换为 JSON 字符串
    return base64.b64encode(json_str.encode("utf-8")).decode()
