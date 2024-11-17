import time
import random
from maa.context import Context
from maa.custom_action import CustomAction


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
            context.run_pipeline("悬赏封印_识别宝箱")

            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("悬赏封印_识别妖怪", img)
            detail_1 = context.run_recognition("悬赏封印_识别挑战次数", img)

            if detail or detail_1:
                results = []
                if detail and hasattr(detail, 'filterd_results'):
                    results.extend(detail.filterd_results)
                if detail_1 and hasattr(detail_1, 'filterd_results'):
                    results.extend(detail_1.filterd_results)

                if results:  # Ensure results are iterable
                    for result in results:
                        roi_source = "悬赏封印_识别妖怪" if detail else "悬赏封印_识别挑战次数"

                        img = context.tasker.controller.post_screencap().wait().get()
                        detail_recognition = context.run_recognition(
                            "悬赏封印_识别完成度",
                            img,
                            {"悬赏封印_识别完成度": {"roi": roi_source, "roi_offset": [-10, -10, 30, 30]}}
                        )

                        if detail_recognition:
                            print("该目标的完成度已满")
                            attempts += 1  # Increment retry count
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
                            context.run_pipeline("悬赏封印_关闭线索界面")
                            continue

                        # Check if no monsters were found
                        img = context.tasker.controller.post_screencap().wait().get()
                        detail_not_found = context.run_recognition("识别未发现妖怪", img)

                        if detail_not_found:
                            time.sleep(1)
                            context.run_pipeline("悬赏封印_关闭线索界面")
                            attempts += 1  # Increment retry count
                            continue
                        else:
                            context.run_pipeline("悬赏_开始识别探索")
                            attempts = 0  # Reset retry count, continue to next recognition
                            break  # Exit current loop

                else:
                    print("没有有效的结果进行处理")
                    context.run_pipeline("识别探索目标_向上滑动")
            else:
                print("未提供有效的 detail 或 detail_1")

            attempts += 1  # Increment retry count
            print(f"尝试次数 attempts=: {attempts}")

        print("识别悬赏妖怪结束")
        return True

    def stop(self) -> None:
        pass
