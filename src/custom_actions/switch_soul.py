import json
import random

from maa.custom_action import CustomAction


class SwitchSoul(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        """
        执行滑动操作，从 custom_param 中获取起始和结束区域，生成随机点并执行滑动。

        :param context: 运行上下文，提供 swipe 方法。
        :param task_name: 任务名称。
        :param custom_param: 自定义参数
        :param box: 识别到的区域。
        :param rec_detail: 识别的详细信息。{
        :return: 滑动是否成功。
        """
        # 读取 box 的参数{"group_name","team_name"}(group_name:分组名称,team_name:队伍名称)
        json_data = json.loads(custom_param)
        print(json_data)
        print(f"json_data: {json_data["group_name"]},{json_data['team_name']}")
        
        # count = 0
        # while True:
        #     if not context.run_task("识别队伍预设",{"识别队伍预设":{"recognition":"OCR","expected":"队伍预设","roi":[729,78,122,48]}}):
                
        #         count += 1
        #     elif count >=10:
        #         break
        
        print("开始执行自定义动作：切换队伍")
        # 点击预设点
        context.click(random.randint(336, 420), random.randint(72, 132))
        for _ in range(3):
            context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 400}}})
        
        print("开始执行自定义动作：点击分组")
        count = 0
        # 点击分组
        while True:
            print("开始执行第" + str(count + 1) + "次自定义动作：点击分组")
            
            if count >= 5:
                context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [1085, 442, 152, 60],"start_roi": [1085, 161, 162, 58],"delay": 400}}})
            elif not context.run_task("点击分组", {"点击分组": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["team_name"],"roi": [1085, 86, 162, 542]}}):
                print("点击分组失败,开始执行下一页")
                context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [1085, 442, 152, 60],"end_roi": [1085, 161, 162, 58],"delay": 400}}})
                count += 1

            else:
                break
                

        return True

    def stop(self) -> None:
        pass
