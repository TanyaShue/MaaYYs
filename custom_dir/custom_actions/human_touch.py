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
            # 解析参数
            params = json.loads(argv.custom_action_param)
            short_wait_min = params.get("short_wait_min", 1)
            short_wait_max = params.get("short_wait_max", 20)
            long_wait_prob = params.get("long_wait_prob", 0.05)  # 长时间等待概率
            long_wait_min = params.get("long_wait_min", 100)
            long_wait_max = params.get("long_wait_max", 200)
            double_click_prob = params.get("double_click_prob", 0.45)
            single_click_prob = params.get("single_click_prob", 0.50)

            # 检查概率总和是否 <= 1
            if double_click_prob + single_click_prob + long_wait_prob > 1:
                raise ValueError("double_click_prob + single_click_prob + long_wait_prob 必须 <= 1")

            # 随机等待
            random_time = round(random.uniform(short_wait_min, short_wait_max), 2)
            print(f"开始等待: 随机等待时间为：{random_time}秒")
            context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始等待: {random_time} 秒"}}})
            sleep(random_time)
            context.run_task("随机等待", {"随机等待": {"focus": {"start": "等待结束"}}})
            print("随机等待结束，开始随机点击")

            # 决定点击类型
            rand_num = random.random()
            print(f"随机数为：{rand_num}")

            if rand_num < double_click_prob:
                # 随机双击
                x = random.randint(400, 900)
                y = random.randint(520, 700)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(0.5,1.5))
                context.tasker.controller.post_click(x, y).wait()
                print(f"双击位置: ({x}, {y})")

            elif rand_num < double_click_prob + single_click_prob:
                # 随机两次单击
                for _ in range(2):
                    sleep(random.uniform(0.5,1.5))
                    x = random.randint(400, 900)
                    y = random.randint(520, 700)
                    context.tasker.controller.post_click(x, y).wait()
                    print(f"单击位置: ({x}, {y})")

            elif rand_num < double_click_prob + single_click_prob + long_wait_prob:
                # 长时间等待
                print("长时间等待开始")
                t = random.uniform(long_wait_min, long_wait_max)
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"即将开始等待: {t} 秒"}}})
                sleep(t)
                context.run_task("随机等待", {"随机等待": {"focus": {"start": "等待结束"}}})
                print("长时间等待结束，开始随机点击")
                x = random.randint(400, 900)
                y = random.randint(520, 700)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(1,3))
                context.tasker.controller.post_click(x, y).wait()
                print(f"长时间等待后双击位置: ({x}, {y})")

            else:
                # 默认短等待后单击
                x = random.randint(400, 900)
                y = random.randint(520, 700)
                context.tasker.controller.post_click(x, y).wait()
                print(f"默认单击位置: ({x}, {y})")

            # 计数
            HumanTouch.count += 1
            if HumanTouch.count % 10 == 0:
                context.run_task("随机等待", {"随机等待": {"focus": {"start": f"已经执行了 {HumanTouch.count} 次"}}})
                print(f"HumanTouch 已执行 {HumanTouch.count} 次")

            sleep(random_time)

        except Exception as e:
            print(f"执行动作时出错: {e}")
            return False

        return True

    def stop(self) -> None:
        pass
