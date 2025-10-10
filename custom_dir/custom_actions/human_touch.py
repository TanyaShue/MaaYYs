# -*- coding: UTF-8 -*-
import json
import random
from time import sleep

from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("HumanTouch")
class HumanTouch(CustomAction):
    count = 0

    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:

        try:
            # 初始化参数字典，确保即使没有传入参数或解析失败，params也是一个字典
            params = {}
            # 仅在 custom_action_param 非空时才尝试解析
            if argv.custom_action_param:
                try:
                    # 尝试解析JSON字符串
                    decoded_params = json.loads(argv.custom_action_param)
                    # 确保解析结果是一个字典，防止传入 "null" 或其他非字典的JSON
                    if isinstance(decoded_params, dict):
                        params = decoded_params
                    else:
                        print(f"警告: 参数不是一个有效的字典。将使用默认值。收到的参数: {argv.custom_action_param}")
                except json.JSONDecodeError:
                    print(f"警告: 解析JSON参数失败。将使用默认值。收到的参数: {argv.custom_action_param}")

            # --- 新增：解析ROI参数 ---
            # 设置默认点击区域
            x_min, y_min, x_max, y_max = 400, 520, 800, 600

            roi = params.get("roi")
            # 检查传入的roi是否为包含4个数字的列表
            if isinstance(roi, list) and len(roi) == 4 and all(isinstance(n, (int, float)) for n in roi):
                # [x, y, w, h] -> 计算出点击范围的左上角和右下角坐标
                x_min = int(roi[0])
                y_min = int(roi[1])
                x_max = int(roi[0] + roi[2])
                y_max = int(roi[1] + roi[3])
                print(f"成功加载ROI参数: x范围({x_min}, {x_max}), y范围({y_min}, {y_max})")
            elif roi is not None:
                # 如果传入了roi但格式不正确
                print(f"警告: ROI参数格式不正确，应为[x, y, w, h]格式的数组。将使用默认点击区域。收到的ROI: {roi}")
                print(f"使用默认点击区域: x范围({x_min}, {x_max}), y范围({y_min}, {y_max})")
            else:
                # 如果没有传入roi
                print(f"未传入ROI参数，使用默认点击区域: x范围({x_min}, {x_max}), y范围({y_min}, {y_max})")

            # 解析其他参数，如果键不存在，.get() 会返回指定的默认值
            short_wait_min = float(params.get("short_wait_min", 1))
            short_wait_max = float(params.get("short_wait_max", 20))
            long_wait_prob = float(params.get("long_wait_prob", 0.05))
            long_wait_min = float(params.get("long_wait_min", 100))
            long_wait_max = float(params.get("long_wait_max", 200))
            double_click_prob = float(params.get("double_click_prob", 0.45))
            single_click_prob = float(params.get("single_click_prob", 0.50))

            # 检查概率总和是否 <= 1
            if double_click_prob + single_click_prob + long_wait_prob > 1:
                raise ValueError("double_click_prob + single_click_prob + long_wait_prob 必须 <= 1")

            # 随机等待
            random_time = round(random.uniform(short_wait_min, short_wait_max), 2)
            print(f"开始等待: 随机等待时间为：{random_time}秒")
            context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始等待: {random_time} 秒"}}})
            sleep(random_time)
            print("随机等待结束，开始随机点击")

            # 决定点击类型
            rand_num = random.random()
            print(f"随机数为：{rand_num}")

            if rand_num < double_click_prob:
                # 随机双击
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(0.5, 1.5))
                context.tasker.controller.post_click(x, y).wait()
                print(f"双击位置: ({x}, {y})")

            elif rand_num < double_click_prob + single_click_prob:
                # 随机两次单击
                for _ in range(2):
                    sleep(random.uniform(0.5, 1.5))
                    x = random.randint(x_min, x_max)
                    y = random.randint(y_min, y_max)
                    context.tasker.controller.post_click(x, y).wait()
                    print(f"单击位置: ({x}, {y})")

            elif rand_num < double_click_prob + single_click_prob + long_wait_prob:
                # 长时间等待
                print("长时间等待开始")
                t = round(random.uniform(long_wait_min, long_wait_max), 2)
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始较长等待: {t} 秒"}}})
                sleep(t)
                context.run_task("随机等待", {"随机等待": {"focus": {"start": "长时间等待结束"}}})
                print("长时间等待结束，开始随机点击")
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(1, 3))
                context.tasker.controller.post_click(x, y).wait()
                print(f"长时间等待后双击位置: ({x}, {y})")

            else:
                # 默认短等待后单击
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                context.tasker.controller.post_click(x, y).wait()
                print(f"默认单击位置: ({x}, {y})")

            # 计数
            HumanTouch.count += 1
            if HumanTouch.count % 10 == 0:
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"已经执行了 {HumanTouch.count} 次"}}})
                print(f"HumanTouch 已执行 {HumanTouch.count} 次")
            print("任务结束")
        except Exception as e:
            # 捕获其他任何意外错误
            print(f"执行动作时出错: {e}")
            return False

        return True

    def stop(self) -> None:
        pass