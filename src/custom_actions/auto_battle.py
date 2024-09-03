from maa.custom_action import CustomAction
import json
import random
import time

class AutoBattle(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        """
        :param context: 运行上下文
        :param task_name: 任务名称。
        :param custom_param: 自定义参数{group_name: 预设组名称,
                                        team_name: 预设名称,
                                        bonus:[1:觉醒副本掉落额外的觉醒材料,
                                               2:八岐大蛇掉落额外的御魂材料,
                                               3:战斗胜利获得的金币增加50%,
                                               4:战斗胜利获得的金币增加100%,
                                               5:战斗胜利获得的经验增加50%,
                                               6:战斗胜利获得的经验增加100%
                                               ],
                                        green_label:从左往右第几个,阴阳师第6个
                                        red_label:从左往右第几个,阴阳师第6个
                }
        :param box: 识别到的区域。
        :param rec_detail: 识别的详细信息。
        :return: 是否执行成功。
        """
        print("5秒后开始战斗")
        time.sleep(5)
        # 加载自定义参数
        json_data = json.loads(custom_param)
        # 点击预设
        if not json_data=={} and json_data["group_name"]:
            context.run_task("点击预设", {"点击预设": {"timeout":100,"action": "Click","target": [49, 658, 26, 51]}})
            # 分组回到最上页
            for _ in range(1):
                context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [39, 582, 113, 36],"start_roi": [39, 270, 120, 38],"delay": 200}}})
            
            # 点击分组
            for count in range(1, 21):
                if context.run_task("点击分组", {"点击分组": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["group_name"],"roi": [34, 241, 132, 440]}}):
                    break
                if count >= 5:
                    context.run_task("返回最上页分组", {"返回最上页分组": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [39, 582, 113, 36],"start_roi": [39, 270, 120, 38],"delay": 400}}})
                else:
                    context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [39, 582, 113, 36],"end_roi": [39, 270, 120, 38],"delay": 400}}})
            else:
                print("点击分组失败")
            

            print("开始执行自定义动作：点击队伍")
            # 点击队伍
            for count in range(1, 10):
                if context.run_task("点击队伍", {"点击队伍": {"timeout":100,"recognition": "OCR","action": "Click","expected": json_data["team_name"],"roi": [254, 235, 263, 355]}}):
                    context.run_task("点击出战", {"点击出战": {"timeout":100,"action": "Click","target": [352, 641, 144, 45]}})
                    print("点击队伍成功")
                    break
                if count >= 5:
                    context.run_task("返回最上页分队", {"返回最上页分队": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"end_roi": [328, 484, 253, 103],"start_roi": [334, 235, 300, 90],"delay": 400}}})
                else:
                    context.run_task("下一页",{"下一页": {"action": "Custom","custom_action": "RandomSwipe","custom_action_param": {"start_roi": [328, 484, 253, 103],"end_roi": [334, 235, 300, 90],"delay": 400}}})
            else:
                print("队伍不存在")
                return False
            
        
        # 点击准备 开始战斗
        x,y=random.randint(1125, 1236),random.randint(539, 634)
        
        print(f"随机点击准备按钮: {x},{y}")

        context.click(x,y)
        
        
        return True

    def stop(self) -> None:
        pass
