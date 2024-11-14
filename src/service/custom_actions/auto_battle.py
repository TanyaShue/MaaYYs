from maa.context import Context
from maa.custom_action import CustomAction
import json
import random
import time

class AutoBattle(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        """
        :param argv:
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("5秒后开始战斗")
        time.sleep(5)
        # 加载自定义参数
        json_data = json.loads(argv.custom_action_param)
        # 点击预设
        if not json_data=={} and json_data["group_name"]:
            context.run_pipeline("点击预设", {"点击预设": {"timeout":100,"action": "Click","target": [49, 658, 26, 51]}})
            # 分组回到最上页
            for _ in range(1):
                context.run_pipeline("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [39, 582, 113, 36],"start_roi": [39, 270, 120, 38],"delay": 200}}})
            
            # 点击分组
            for count in range(1, 21):
                if context.run_pipeline("点击分组", {"点击分组": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["group_name"],"roi": [34, 241, 132, 440]}}):
                    break
                if count >= 5:
                    context.run_pipeline("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [39, 582, 113, 36],"start_roi": [39, 270, 120, 38],"delay": 400}}})
                else:
                    context.run_pipeline("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [39, 582, 113, 36],"end_roi": [39, 270, 120, 38],"delay": 400}}})
            else:
                print("点击分组失败")
            

            print("开始执行自定义动作：点击队伍")
            # 点击队伍
            for count in range(1, 10):
                if context.run_pipeline("点击队伍", {"点击队伍": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["team_name"],"roi": [254, 235, 263, 355]}}):
                    context.run_pipeline("点击出战", {"点击出战": {"timeout":100,"action": "Click","target": [352, 641, 144, 45]}})
                    print("点击队伍成功")
                    break
                if count >= 5:
                    context.run_pipeline("返回最上页分队", {"返回最上页分队": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [328, 484, 253, 103],"start_roi": [334, 235, 300, 90],"delay": 400}}})
                else:
                    context.run_pipeline("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [328, 484, 253, 103],"end_roi": [334, 235, 300, 90],"delay": 400}}})
            else:
                print("队伍不存在")
                return False
            
        
        # 点击准备 开始战斗
        x,y=random.randint(1125, 1236),random.randint(539, 634)
        
        print(f"随机点击准备按钮: {x},{y}")

        context.tasker.controller.post_click(x,y).wait()
        
        
        return True

    def stop(self) -> None:
        pass
