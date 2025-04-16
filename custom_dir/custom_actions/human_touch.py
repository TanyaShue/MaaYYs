# -*- coding: UTF-8 -*-
from maa.context import Context
from maa.custom_action import CustomAction
import random
from time import sleep

from app.models.logging.log_manager import log_manager


class HumanTouch(CustomAction):
    count = 0
    def run(self,
        context: Context,
        argv: CustomAction.RunArg,) -> bool:
        logger = log_manager.get_context_logger(context)
        logger.debugger(f"开始执行第{HumanTouch.count + 1}次自定义动作：随机点击")

        # 随机等待
        random_time = random.uniform(1, 3)
        logger.debugger(f"开始等待: 随机等待时间为：{random_time}秒")
        sleep(random_time)
        logger.debugger("随机等待结束，开始随机点击")

        # 获取随机数
        rand_num = random.random()
        logger.debugger(f"随机数为：{rand_num}")
        try:
            if rand_num < 0.45:
                # 随机双击
                x = random.randint(400, 900)
                y = random.randint(520, 700)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(0.5,1.5))
                context.tasker.controller.post_click(x, y).wait()
                logger.debugger(f"双击位置: ({x}, {y})")

            elif rand_num < 0.99:
                # 随机两次单击
                for _ in range(2):
                    sleep(random.uniform(0.5,1.5))
                    x = random.randint(400, 900)
                    y = random.randint(520, 700)
                    context.tasker.controller.post_click(x, y).wait()
                    logger.debugger(f"单击位置: ({x}, {y})")
            else:
                logger.debugger(f"长时间等待开始")
                # 长时间等待
                sleep(random.uniform(100, 200))
                logger.debugger(f"长时间等待结束，开始随机点击")
                x = random.randint(400, 900)
                y = random.randint(520, 700)
                context.tasker.controller.post_click(x, y).wait()
                sleep(random.uniform(1,3))
                context.tasker.controller.post_click(x, y).wait()
                logger.debugger(f"长时间等待后双击位置: ({x}, {y})")

            HumanTouch.count += 1
        except Exception as e:
            logger.debugger(f"执行动作时出错: {e}")
            return False

        # 随机短暂等待
        random_time = random.uniform(3, 4)
        logger.debugger(f"随机等待时间为：{random_time}秒")
        sleep(random_time)
        logger.debugger(f"------------------第{HumanTouch.count}次自定义动作执行结束------------------")

        return True

    def stop(self) -> None:
        pass
