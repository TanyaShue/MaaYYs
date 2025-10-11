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
                    # 确保解析结果是一个字典
                    if isinstance(decoded_params, dict):
                        params = decoded_params
                    else:
                        print(f"警告: 参数不是一个有效的字典。将使用默认值。收到的参数: {argv.custom_action_param}")
                except json.JSONDecodeError:
                    print(f"警告: 解析JSON参数失败。将使用默认值。收到的参数: {argv.custom_action_param}")

            # --- 解析ROI参数 ---
            # 设置默认点击区域
            x_min, y_min, x_max, y_max = 400, 520, 800, 600
            print(argv.custom_action_param)
            roi = params.get("ROI_1")
            # 检查传入的roi是否为包含4个数字的列表
            print(roi)
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

            # --- 新增：安全检查，防止min > max的情况 ---
            if x_min > x_max:
                print(f"警告: 检测到 x_min > x_max。已自动交换值为: x范围({x_max}, {x_min})")
                x_min, x_max = x_max, x_min
            if y_min > y_max:
                print(f"警告: 检测到 y_min > y_max。已自动交换值为: y范围({y_max}, {y_min})")
                y_min, y_max = y_max, y_min

            # --- 等待和点击权重解析 ---
            # 等待时间参数
            short_wait_min = float(params.get("short_wait_min", 1))
            short_wait_max = float(params.get("short_wait_max", 20))
            long_wait_min = float(params.get("long_wait_min", 100))
            long_wait_max = float(params.get("long_wait_max", 200))

            # 用于等待时间决策的权重
            short_wait_weight = float(params.get("short_wait_weight", 95))
            long_wait_weight = float(params.get("long_wait_weight", 5))

            # 用于点击类型决策的权重
            single_click_weight = float(params.get("single_click_weight", 50))
            double_click_weight = float(params.get("double_click_weight", 50))

            # --- 独立的加权随机决策 - 等待时间 ---
            total_wait_weight = short_wait_weight + long_wait_weight
            wait_rand_num = random.uniform(0, total_wait_weight)

            if wait_rand_num < long_wait_weight:
                # 长时间等待
                wait_time = round(random.uniform(long_wait_min, long_wait_max), 2)
                print(f"开始长等待: {wait_time}秒")
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始较长等待: {wait_time} 秒"}}})
                sleep(wait_time)
                print("长等待结束。")
            else:
                # 短时间等待
                wait_time = round(random.uniform(short_wait_min, short_wait_max), 2)
                print(f"开始短等待: {wait_time}秒")
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始等待: {wait_time} 秒"}}})
                sleep(wait_time)
                print("短等待结束。")

            # --- 独立的加权随机决策 - 点击类型 ---
            total_click_weight = single_click_weight + double_click_weight
            click_rand_num = random.uniform(0, total_click_weight)

            print("等待结束，开始随机点击。")
            # 此处的 x_min, x_max, y_min, y_max 经过了安全检查，保证是有效范围
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)

            if click_rand_num < double_click_weight:
                # 双击
                print(f"执行双击，位置: ({x}, {y})")
                context.tasker.controller.post_click(x, y).wait()
                # 模拟真实双击的短暂延迟
                sleep(random.uniform(0.1, 0.4))
                context.tasker.controller.post_click(x, y).wait()
            else:
                # 单击
                print(f"执行单击，位置: ({x}, {y})")
                context.tasker.controller.post_click(x, y).wait()

            # --- 计数 ---
            HumanTouch.count += 1
            if HumanTouch.count % 10 == 0:
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"已经执行了 {HumanTouch.count} 次"}}})
                print(f"HumanTouch 已执行 {HumanTouch.count} 次")

            print("任务结束。")

        except Exception as e:
            # 捕获其他任何意外错误
            print(f"执行动作时出错: {e}")
            return False

        return True

    def stop(self) -> None:
        pass