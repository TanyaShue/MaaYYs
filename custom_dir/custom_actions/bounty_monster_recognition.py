# -*- coding: UTF-8 -*-
import time
import random
import re

from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("BountyMonsterRecognition")
class BountyMonsterRecognition(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        Perform custom action to recognize bounty monsters.
        :param argv: Custom arguments
        :param context: Running context
        :return: True if executed successfully, otherwise False.
        """

        print("开始执行自定义动作：识别悬赏妖怪")
        attempts = 0  # Retry counter

        while attempts < 3:
            context.run_task("悬赏封印_识别宝箱")
            
            # 添加容错
            context.run_task("悬赏封印_关闭章节界面")

            # 识别妖怪 ,以及完成度,避免单独识别文字时失败,导致无法识别
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("悬赏封印_识别妖怪", img)
            detail_1 = context.run_recognition("悬赏封印_识别挑战次数", img)
            detail_2= context.run_recognition("悬赏封印_识别妖怪_图片识别", img)

            if detail or detail_1 or detail_2:
                # 整合识别结果
                results = []
                if detail and hasattr(detail, 'filterd_results'):
                    results.extend(detail.filterd_results)
                if detail_1 and hasattr(detail_1, 'filterd_results'):
                    results.extend(detail_1.filterd_results)
                if detail_2 and hasattr(detail_2, 'filterd_results'):
                    results.extend(detail_2.filterd_results)

                if results:
                    print(f"{results}")
                    for result in results:
                        # 当结果text符合正则直接跳过
                        if result and hasattr(result, "text"):
                            if self.matches_regex(result.text):
                                continue

                        print(f"识别到妖怪：{result}")
                        img = context.tasker.controller.post_screencap().wait().get()
                        detail_recognition = context.run_recognition(
                            "悬赏封印_识别完成度",
                            img,
                            {"悬赏封印_识别完成度": {"roi": result.box, "roi_offset": [-10, -10, 50, 50]}}
                        )

                        if detail_recognition:
                            print("该目标的完成度已满")
                            continue

                        # 随机点击识别到的妖怪位置
                        x = random.randint(result.box[0], result.box[0] + result.box[2])
                        y = random.randint(result.box[1], result.box[1] + result.box[3])
                        context.tasker.controller.post_click(x, y).wait()
                        time.sleep(1)

                        img = context.tasker.controller.post_screencap().wait().get()
                        detail_click = context.run_recognition(
                            "悬赏_线索界面",
                            img
                        )

                        if detail_click is None:
                            print("未处于线索界面，尝试重新识别妖怪")
                            context.run_task("悬赏封印_关闭章节界面")
                            context.run_task("悬赏封印_关闭线索界面")
                            continue

                        # 识别该妖怪是否为未发现
                        img = context.tasker.controller.post_screencap().wait().get()
                        detail_not_found = context.run_recognition("识别未发现妖怪", img)

                        if detail_not_found:
                            time.sleep(1)
                            context.run_task("悬赏封印_关闭线索界面")
                            continue
                        context.run_task("悬赏_开始识别探索")
                        attempts = 0  #成功开始探索 则 重置尝试次数
                        break  # 退出循环,进行下一次尝试
                    # attempts += 1

                else:
                    print("没有有效的结果进行处理")
            else:
                print("未识别到妖怪")
            context.run_task("识别探索目标_向上滑动")

            attempts += 1  # Increment retry count
            print(f"尝试次数 attempts=: {attempts}")

        print("识别悬赏妖怪结束")
        return True

    def stop(self) -> None:
        pass

    def matches_regex(self,text):
        pattern = r"^(\d+)\/(\1)$|^(\d+)7(\3)$"
        return bool(re.match(pattern, text))