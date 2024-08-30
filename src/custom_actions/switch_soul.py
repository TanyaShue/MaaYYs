import json
import random
import time

from maa.custom_action import CustomAction


class SwitchSoul(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        """
        :param context: 运行上下文，提供 swipe 方法。
        :param task_name: 任务名称。
        :param custom_param: 自定义参数
        :param box: 识别到的区域。
        :param rec_detail: 识别的详细信息。{
        :return: 滑动是否成功。
        """
        # 读取 box 的参数{"group_name","group_name"}(group_name:分组名称,team_name:队伍名称)
        json_data = json.loads(custom_param)        
        # 点击预设点
        time.sleep(1)
        context.click(random.randint(336, 420), random.randint(72, 132))
        for _ in range(1):
            context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 200}}})
        
        print("开始执行自定义动作：点击分组")

        # 点击分组
        for count in range(1, 21):
            if context.run_task("点击分组", {"点击分组": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["group_name"],"roi": [1085, 86, 162, 542]}}):
                break
            if count >= 5:
                context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 400}}})
            else:
                context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [1085, 442, 152, 60],"end_roi": [1085, 161, 162, 58],"delay": 400}}})
        else:
            print("点击分组失败")
        
        print("开始执行自定义动作：点击队伍")
        # 点击队伍
        for count in range(1, 10):
            image=context.screencap()
            detil = context.run_recognition(image,"点击队伍", {"点击队伍": {"timeout":100,"recognition": "OCR","expected": json_data["team_name"],"roi": [567, 138, 288, 356]}})
            if detil[0]:
                roi=[detil[1].x-30,detil[1].y-30,500,80]
                context.run_task("装备御魂", {"装备御魂": {"action": "Click","timeout":100,"recognition": "TemplateMatch","template": "装备御魂.png","roi": roi,"next": "点击确定"},"点击确定": {"action": "Click","timeout":100,"recognition": "OCR","expected": "确定","roi": [400,350,475,175]}})
                break
            if count >= 5:
                context.run_task("返回最上页分队", {"返回最上页分队": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [585, 495, 273, 112],"start_roi": [588, 171, 410, 76],"delay": 400}}})
            else:
                context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [585, 495, 273, 112],"end_roi": [588, 171, 410, 76],"delay": 400}}})
        else:
            print("队伍不存在")
        return True

    def stop(self) -> None:
        pass
