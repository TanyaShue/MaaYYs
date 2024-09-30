import json
import random

from maa.context import Context
from maa.custom_action import CustomAction


class SwitchSoul(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv: 运行参数
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        # 读取 custom_param 的参数{"group_name","group_name"}(group_name:分组名称,team_name:队伍名称)
        json_data = json.loads(argv.custom_action_param)
        # 点击预设点
        # 识别预设点
        image=context.tasker.controller.post_screencap().wait().get()
        detail=context.run_recognition("识别预设",image,{"识别预设":{"timeout":100,"recognition": "OCR","expected": "预设","roi": [336, 74, 82, 46]}})
        context.run_pipeline("")
        if detail[0]:
            context.tasker.controller.post_click(random.randint(336, 411), random.randint(74,120 )).wait()
        
        for _ in range(1):
            context.run_pipeline("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 200}}})
            
        print("开始执行自定义动作：点击分组")


        # 点击分组
        for count in range(1, 21):
            if context.run_pipeline("点击分组", {"点击分组": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["group_name"],"roi": [1085, 86, 162, 542]}}):
                break
            if count >= 5:
                context.run_pipeline("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 400}}})
            else:
                context.run_pipeline("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [1085, 442, 152, 60],"end_roi": [1085, 161, 162, 58],"delay": 400}}})
        else:
            print("点击分组失败")
        
        print("开始执行自定义动作：点击队伍")
        # 点击队伍
        for count in range(1, 10):
            image=context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击队伍",image, {"点击队伍": {"timeout":100,"recognition": "OCR","expected": json_data["team_name"],"roi": [567, 138, 288, 356]}})
            if detail[0]:
                roi=[detail[1].x-30,detail[1].y-30,500,80]
                context.run_pipeline("装备御魂", {"装备御魂": {"action": "Click","timeout":100,"recognition": "TemplateMatch","template": "装备御魂.png","roi": roi,"next": "点击确定"},"点击确定": {"action": "Click","timeout":100,"recognition": "OCR","expected": "确定","roi": [400,350,475,175]}})
                break
            if count >= 5:
                context.run_pipeline("返回最上页分队", {"返回最上页分队": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [585, 495, 273, 112],"start_roi": [588, 171, 410, 76],"delay": 400}}})
            else:
                context.run_pipeline("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [585, 495, 273, 112],"end_roi": [588, 171, 410, 76],"delay": 400}}})
        else:
            print("队伍不存在")
        return True

    def stop(self) -> None:
        pass
