import json
import time
from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("BonusToggleAction")
class BonusToggleAction(CustomAction):
    BonusType = {
        "exp_100%": "战斗胜利获得的经验增加100%",
        "exp_50%": "战斗胜利获得的经验增加50%",
        "gold_100%": "战斗胜利获得的金币增加100%",
        "gold_50%": "战斗胜利获得的金币增加50%",
        "drop_awake": "觉醒副本掉落额外的觉醒材料",
        "drop_soul": "八岐大蛇掉落额外的御魂材料"
    }

    def run(self,
            context: Context,
            argv: CustomAction.RunArg) -> bool:
        """
        加成开关控制动作
        :param argv: 运行参数, 包括键值对形式的加成设置
        :param context: 运行上下文
        :return: 是否执行成功
        """

        # 读取 custom_param 的参数
        # 示例: {"exp_100%": true, "gold_50%": false, "drop_soul": true}
        # 键为加成类型，值为布尔值表示是否启用
        try:
            json_data = json.loads(argv.custom_action_param)
        except json.JSONDecodeError:
            print(f"解析参数失败: {argv.custom_action_param}")
            return False

        # 验证所有键是否为有效的加成类型
        for bonus_type in json_data.keys():
            if bonus_type not in self.BonusType:
                print(f"无效的加成类型: {bonus_type}")
                return False

        # 验证所有值是否为布尔类型
        for bonus_type, enable in json_data.items():
            if not isinstance(enable, bool):
                print(f"加成类型 {bonus_type} 的值必须为布尔类型，当前为: {type(enable)}")
                return False

        # 处理每个加成设置
        success = True
        print(f"开始设置 {len(json_data)} 个加成:")

        for bonus_type, enable in json_data.items():
            if not self._toggle_single_bonus(context, bonus_type, enable):
                success = False
                print(f"设置 {bonus_type} 加成失败")
            # 在处理多个加成时添加短暂延迟，避免操作过快
            time.sleep(0.5)

        if success:
            print("所有加成设置完成")
        else:
            print("部分加成设置失败")

        return success

    def _toggle_single_bonus(self, context: Context, bonus_type: str, enable: bool) -> bool:
        """
        切换单个加成开关
        :param context: 运行上下文
        :param bonus_type: 加成类型
        :param enable: 是否启用
        :return: 是否成功
        """
        expected_text = self.BonusType.get(bonus_type)
        if not expected_text:
            print(f"未找到加成类型 {bonus_type} 对应的文本")
            return False

        print(f"  - {'启用' if enable else '关闭'} {bonus_type} 加成: {expected_text}")

        # 根据 enable 参数决定执行打开还是关闭任务
        next_task = "通用_打开加成" if enable else "通用_关闭加成"

        try:
            # 执行识别和切换任务
            result = context.run_task("通用_识别加成", {
                "通用_识别加成": {
                    "expected": expected_text,
                    "next": next_task,
                    "time_out":2000
                }
            })

            # 可以根据需要检查 result 来判断是否成功
            return True

        except Exception as e:
            print(f"执行任务失败: {e}")
            return False

    def stop(self) -> None:
        """停止执行的逻辑"""
        print("停止加成开关控制动作")
        pass