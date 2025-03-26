# -*- coding: UTF-8 -*-
import json
import random
import time

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

        print("开始执行自定义动作：装备切换御魂")
        print(f"开始执行自定义动作:装备切换御魂   分组名称为：{json_data['group_name']},队伍名称为：{json_data['team_name']}")
        context.run_task("识别预设",{"识别预设":{"timeout":2000,"recognition": "OCR","expected": "预设","roi": [336, 74, 82, 46],"action":"Click"}})

        for _ in range(1):
            context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 200}}})

        print("开始执行自定义动作：点击分组")
        time.sleep(0.5)

        # 点击分组
        for count in range(1, 21):
            time.sleep(1)
            img=context.tasker.controller.post_screencap().wait().get()

            detail =context.run_recognition("点击分组", img,{"点击分组": {"timeout": 500, "recognition": "OCR", "action": "Click",
                                                           "expected": json_data["group_name"],
                                                           "roi": [1085, 86, 162, 542]}})
            time.sleep(1)
            if detail is not None:
                context.tasker.controller.post_click(random.randint(detail.box.x,detail.box.x+detail.box.h),random.randint(detail.box.y,detail.box.y+detail.box.w)).wait()
                break
            if count >= 5:
                context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 400}}})
            else:
                context.run_task("下一页",{"下一页": {"action": "Custom","post_delay": 1000,"custom_action": "RandomSwipe","custom_action_param": {"start_roi": [1085, 442, 152, 60],"end_roi": [1085, 161, 162, 58],"delay": 400}}})
        else:
            print("点击分组失败")

        print("开始执行自定义动作：点击队伍")
        # 点击队伍
        for count in range(1, 10):
            time.sleep(0.5)
            img = context.tasker.controller.post_screencap().wait().get()
            detail = context.run_recognition("点击队伍", img,{"点击队伍": {"timeout":500,"recognition": "OCR","expected": json_data["team_name"],"roi": [567, 138, 288, 356]}})
            if detail is not None:
                time.sleep(0.5)
                roi=[detail.box.x-30,detail.box.y-30,500,80]
                time.sleep(0.5)
                context.run_task("装备御魂", {"装备御魂": {"action": "Click","timeout":500,"recognition": "TemplateMatch","post_delay": 1000,"template": ["通用图标/装备御魂.png","通用图标/装备御魂_2.png"],"roi": roi,"next": "点击确定"},"点击确定": {"action": "Click","timeout":100,"recognition": "OCR","pre_delay":1000,"expected": "确定","roi": [400,350,475,175]}})
                break
            if count >= 5:
                context.run_task("返回最上页分队", {"返回最上页分队": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [585, 495, 273, 112],"start_roi": [588, 171, 410, 76],"delay": 400}}})
            else:
                context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [585, 495, 273, 112],"end_roi": [588, 171, 410, 76],"delay": 400}}})
        else:
            print("队伍不存在")
            return False
        return True

    def stop(self) -> None:
        pass


