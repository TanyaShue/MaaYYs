import time

from maa.context import Context
from maa.custom_action import CustomAction


class ChallengeDungeonBoss(CustomAction):

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        image = context.tasker.controller.post_screencap().wait().get()
        detail = context.run_recognition("识别地鬼分数",image,  {"识别地鬼分数": {
                                        "recognition": "OCR", "expected": r"\d+", "roi": [1175, 15, 98, 77]}})
        value = int(detail.filterd_results[0].text)
        count = 3 if value > 10000 else 2 if value > 2000 else 1
        print("挑战地鬼数:", count)
        for _ in range(count):
            print("开始挑战第", _+1, "只地鬼")

            # 筛选模板容易出现分数不够的情况

            context.run_pipeline("点击筛选", {
                "点击筛选": {"post_delay": 2000, "timeout": 500, "recognition": "TemplateMatch", "template": "地域鬼王_筛选.png", "action": "Click", "target": [1102, 17, 58, 73],"roi":[1077,2,99,121]}})
            context.run_pipeline("点击热门", {
                "点击热门": {"post_delay": 2000, "timeout": 500,  "target": [1185, 220, 50, 120], "action": "Click"}})
            context.run_pipeline("识别挑战位置", {
                "识别挑战位置": {"post_delay": 2000,"timeout": 500, "index": _, "order_by": "Vertical", "recognition": "TemplateMatch", "template": "地鬼_挑战.png", "action": "Click", "roi": [1035, 192, 135, 504]}})


            # 选择挑战等级
            # TODO

            print("点击挑战")

            # 点击挑战
            context.run_pipeline("挑战地鬼", {
                "挑战地鬼": {"post_delay": 2000,"action": "Click", "target": [1109, 493, 102, 63]}})
            time.sleep(5)
            context.run_pipeline("自动挑战", {
                "自动挑战": {"timeout": 100, "action": "Custom", "custom_action": "AutoBattle"}})

            print("等待20秒后重新开始挑战")
            time.sleep(20)
            print("等待识别分享按钮")

            context.run_pipeline("结束战斗",{"结束战斗": {"next":["点击叉叉"],"interrupt":"点击屏幕继续","timeout":300000,},"点击屏幕继续": {
                             "roi":[481,641,380,78],"recognition": "OCR", "expected": "点击屏幕继续", "action": "Click", "target": [275,488,652,112]},"点击叉叉": {"recognition": "TemplateMatch", "template": "地鬼_关闭.png", "action": "Click"}})

        print("自动地鬼挑战完成")
        return True

    def stop(self) -> None:
        pass
