import time
import random

from maa.context import Context
from maa.custom_action import CustomAction


class BountyMonsterRecognition(CustomAction):

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("开始执行自定义动作：识别悬赏妖怪")
        cont=0
        while True:
            context.run_pipeline("悬赏封印_识别宝箱")
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("悬赏封印_识别妖怪",img)
            if detail is not None:
                for result in detail.filterd_results:
                    # 点击悬赏妖怪
                    x=random.randint(result.box[0],result.box[0]+result.box[2])
                    y=random.randint(result.box[1],result.box[1]+result.box[3])
                    context.tasker.controller.post_click(x,y).wait()
                    time.sleep(1)
                    # 判断悬赏妖怪类型是否为未发现
                    img = context.tasker.controller.post_screencap().wait().get()
                    detail_not_found = context.run_recognition("识别未发现妖怪", img)
                    print(f"{detail_not_found}")
                    if detail_not_found is None:
                        time.sleep(1)
                        context.run_pipeline("悬赏_开始识别探索")
                        continue
                    time.sleep(1)
                    context.run_pipeline("悬赏封印_关闭线索界面")
            context.run_pipeline("识别探索目标_向上滑动")
            cont+=1
            print("循环次数：", cont)
            if cont>5:
                break

        return True

    def stop(self) -> None:
        pass
