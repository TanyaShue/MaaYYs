import time
import random
from maa.context import Context
from maa.custom_action import CustomAction


class BountyMonsterRecognition(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("开始执行自定义动作：识别悬赏妖怪")
        attempts = 0  # 重试计数

        while attempts < 3:
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("悬赏封印_识别妖怪", img)
            detail_1 = context.run_recognition("悬赏封印_识别挑战次数", img)

            if detail or detail_1:
                for result in detail.filterd_results:
                    context.run_pipeline("悬赏封印_识别宝箱")

                    # 识别该目标的完成度是否已满
                    img = context.tasker.controller.post_screencap().wait().get()
                    detail_recognition = context.run_recognition("悬赏封印_识别完成度", img,{"悬赏封印_识别完成度":{"roi": "悬赏封印_识别妖怪","roi_offset":[-10,-10,30,30]}})
                    if detail_recognition:
                        print("该目标的完成度已满")
                        attempts += 1  # 增加重试计数
                        continue

                    # 随机点击识别到的妖怪位置
                    x = random.randint(result.box[0], result.box[0] + result.box[2])
                    y = random.randint(result.box[1], result.box[1] + result.box[3])
                    context.tasker.controller.post_click(x, y).wait()
                    time.sleep(1)

                    # 检测是否未发现妖怪
                    img = context.tasker.controller.post_screencap().wait().get()
                    detail_not_found = context.run_recognition("识别未发现妖怪", img)

                    if detail_not_found:
                        time.sleep(1)
                        context.run_pipeline("悬赏封印_关闭线索界面")
                        attempts += 1  # 增加重试计数
                        continue
                    else:
                        context.run_pipeline("悬赏_开始识别探索")
                        attempts = 0  # 重置重试计数，继续下一个识别
                        break

                print("未识别到妖怪，滑动继续寻找")
                context.run_pipeline("识别探索目标_向上滑动")

            attempts += 1  # 增加重试计数

            print(f"尝试次数 attempts=: {attempts}")
        print("识别悬赏妖怪结束")
        return True

    def stop(self) -> None:
        pass
