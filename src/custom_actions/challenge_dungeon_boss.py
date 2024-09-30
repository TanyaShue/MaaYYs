from maa.context import Context
from maa.custom_action import CustomAction
import json
import time
import random

class ChallengeDungeonBoss(CustomAction):

    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        image = context.tasker.controller.cached_image
        detail = context.run_recognition("识别地鬼分数",image,  {"识别地鬼分数": {
                                        "recognition": "OCR", "expected": r"\d+", "roi": [1175, 15, 98, 77]}})
        data = json.loads(detail[2])
        value = int(data['filtered'][0]['text'])
        count = 3 if value > 10000 else 2 if value > 2000 else 1
        print("挑战地鬼数:", count)
        for _ in range(count):
            print("开始挑战第", _+1, "只地鬼")
            context.run_pipeline("点击筛选", {
                "点击筛选": {"post_delay": 2000, "timeout": 100, "recognition": "TemplateMatch", "template": "地域鬼王_筛选.png", "action": "Click", "target": [1102, 17, 58, 73]}})
            context.run_pipeline("点击热门", {
                "点击热门": {"post_delay": 2000, "timeout": 100,  "target": [1185, 220, 50, 120], "action": "Click"}})
            context.run_pipeline("识别挑战位置", {
                "识别挑战位置": {"post_delay": 2000,"timeout": 100, "index": _, "order_by": "Vertical", "recognition": "TemplateMatch", "template": "地鬼_挑战.png", "action": "Click", "roi": [1035, 192, 135, 504]}})


            # 选择挑战等级
            # TODO
            
            print("点击挑战")
            
            # 点击挑战
            te=context.run_pipeline("挑战地鬼", {
                "挑战地鬼": {"post_delay": 2000,"action": "Click", "target": [1109, 493, 102, 63]}})
            print(te)
            time.sleep(5)
            context.run_pipeline("自动挑战", {
                "自动挑战": {"timeout": 100, "action": "Custom", "custom_action": "AutoBattle"}})

            print("等待20秒后重新开始挑战")
            time.sleep(20)
            print("等待识别分享按钮")
            context.run_pipeline("识别分享", {"识别分享": {
                             "recognition": "TemplateMatch", "timeout":300000,"template": "地鬼_分享.png", "action": "Click", "target": [165, 98, 913, 430]}})
            time.sleep(5)
            context.tasker.controller.post_click(random.randint(367, 866), random.randint(185, 638)).wait()
            
            context.run_pipeline("点击叉叉", {
                             "点击叉叉": {"recognition": "TemplateMatch", "template": "地鬼_关闭.png", "action": "Click"}})
        

        print("自动地鬼挑战完成")
        return True

    def stop(self) -> None:
        pass
