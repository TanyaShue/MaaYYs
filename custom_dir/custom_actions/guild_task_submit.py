# -*- coding: UTF-8 -*-
import json
import time
from maa.context import Context
from maa.custom_action import CustomAction
from maa.agent.agent_server import AgentServer


@AgentServer.custom_action("GuildTaskSubmit")
class GuildTaskSubmit(CustomAction):
    # 定义材料类型和等级
    MATERIAL_TYPES = {
        "御魂材料": ["高级御魂材料", "中级御魂材料", "低级御魂材料"],
        "御灵材料": ["高级御灵材料", "中级御灵材料", "低级御灵材料"],
        "觉醒材料": ["高级觉醒材料", "中级觉醒材料", "低级觉醒材料"],
        "式神材料": ["式神材料"]
    }

    # 定义优先级模式
    PRIORITY_MODES = {
        "high_priority": ["高级", "中级", "低级"],  # 高级优先
        "low_priority": ["低级", "中级", "高级"],  # 低级优先
        "no_priority": [],  # 无优先级
        "specific": []  # 特定材料
    }

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        :param argv: 运行参数
                     字典格式: {
                         "expect_task": "御魂材料",  # 任务类型
                         "priority_mode": "high_priority",  # 优先级模式
                         "specific_material": "高级御魂材料"  # 特定材料（可选）
                     }
        :param context: 运行上下文
        :return: 是否执行成功。
        """
        print("开始执行自定义动作：任务列表")

        try:
            json_data = json.loads(argv.custom_action_param)
            expect_task = json_data.get("expect_task", "")
            priority_mode = json_data.get("priority_mode", "high_priority")
            specific_material = json_data.get("specific_material", "")

            if not expect_task:
                print("无效的 expect_task")
                return False

            print(f"开始执行任务列表 {expect_task}")
            print(f"优先级模式: {priority_mode}")

            # 获取需要提交的材料列表
            materials_to_check = self._get_materials_to_check(
                expect_task, priority_mode, specific_material
            )

            if not materials_to_check:
                print("未找到符合条件的材料类型")
                return False

            print(f"待检查的材料列表: {materials_to_check}")

            # 依次检查材料
            submitted = False
            for material in materials_to_check:
                if self._try_submit_material(context, material):
                    print(f"成功提交材料: {material}")
                    submitted = True
                    break

            if not submitted:
                print("没有找到符合条件且数量充足的材料可以提交")
                return False

            return True

        except Exception as e:
            print(f"执行过程中出现错误: {e}")
            return False

    def _get_materials_to_check(self, expect_task: str, priority_mode: str, specific_material: str) -> list:
        """
        根据任务类型和优先级模式获取需要检查的材料列表

        :param expect_task: 任务类型
        :param priority_mode: 优先级模式
        :param specific_material: 特定材料
        :return: 材料列表
        """
        materials = []

        # 如果指定了特定材料
        if priority_mode == "specific" and specific_material:
            return [specific_material]

        # 根据任务类型获取对应的材料列表
        if expect_task in self.MATERIAL_TYPES:
            base_materials = self.MATERIAL_TYPES[expect_task]

            # 根据优先级模式排序
            if priority_mode == "high_priority":
                return base_materials  # 默认就是高级到低级
            elif priority_mode == "low_priority":
                return base_materials[::-1]  # 反转列表，低级到高级
            elif priority_mode == "no_priority":
                # 无优先级，返回所有材料（保持原顺序）
                return base_materials

        # 如果是通用类型（如"材料"），返回所有材料
        if expect_task == "材料":
            if priority_mode == "no_priority":
                # 无优先级时，按照材料类型顺序返回所有材料
                for mat_type, mat_list in self.MATERIAL_TYPES.items():
                    materials.extend(mat_list)
            else:
                # 有优先级时，按优先级排序
                for priority in self.PRIORITY_MODES.get(priority_mode, ["高级", "中级", "低级"]):
                    for mat_type, mat_list in self.MATERIAL_TYPES.items():
                        for mat in mat_list:
                            if priority in mat:
                                materials.append(mat)
                # 添加没有级别的材料（如式神材料）
                for mat_type, mat_list in self.MATERIAL_TYPES.items():
                    for mat in mat_list:
                        if not any(level in mat for level in ["高级", "中级", "低级"]):
                            materials.append(mat)

        return materials

    def _try_submit_material(self, context: Context, material: str) -> bool:
        """
        尝试提交指定材料

        :param context: 运行上下文
        :param material: 材料名称
        :return: 是否提交成功
        """
        try:
            # 获取当前材料
            print(f"正在检查材料: {material}")
            current_material_result = context.run_task("获取当前材料")

            # 这里假设返回的是一个包含材料信息的结果
            # 实际使用时需要根据具体的返回格式调整
            if not current_material_result:
                print("获取当前材料失败")
                return False

            # 判断当前材料是否符合需求
            # 这里假设返回的结果中有材料名称或类型信息
            # 实际使用时需要根据具体的返回格式调整判断逻辑
            current_material_name = self._extract_material_name(current_material_result)

            if current_material_name == material:
                print(f"当前材料 {current_material_name} 符合需求")

                # 判断材料是否足够
                is_sufficient_result = context.run_task("判断当前材料是否足够")
                is_sufficient = self._extract_sufficiency(is_sufficient_result)

                if is_sufficient:
                    print(f"材料 {material} 数量充足，开始提交")
                    submit_result = context.run_task("提交材料")

                    if submit_result:
                        print(f"材料 {material} 提交成功")
                        return True
                    else:
                        print(f"材料 {material} 提交失败")
                        return False
                else:
                    print(f"材料 {material} 数量不足，需要切换材料")
                    return False
            else:
                print(f"当前材料 {current_material_name} 不符合需求 {material}，尝试切换")
                # 切换到目标材料
                switch_result = context.run_task("切换提交材料")
                if switch_result:
                    print(f"已切换材料，重新检查")
                    # 递归调用，重新检查
                    return self._try_submit_material(context, material)
                else:
                    print(f"切换材料失败")
                    return False

        except Exception as e:
            print(f"提交材料时出现错误: {e}")
            return False

    def _extract_material_name(self, material_result) -> str:
        """
        从获取材料的结果中提取材料名称

        :param material_result: 获取材料的结果
        :return: 材料名称
        """
        # 这里需要根据实际的返回格式来解析
        # 假设返回的是一个字典或对象，包含材料名称
        if isinstance(material_result, dict):
            return material_result.get("name", "")
        elif isinstance(material_result, str):
            return material_result
        else:
            # 根据实际情况调整解析逻辑
            return str(material_result)

    def _extract_sufficiency(self, sufficiency_result) -> bool:
        """
        从判断材料是否足够的结果中提取布尔值

        :param sufficiency_result: 判断结果
        :return: 是否足够
        """
        # 根据实际返回格式调整
        if isinstance(sufficiency_result, bool):
            return sufficiency_result
        elif isinstance(sufficiency_result, dict):
            return sufficiency_result.get("is_sufficient", False)
        elif isinstance(sufficiency_result, str):
            return sufficiency_result.lower() in ["true", "yes", "足够", "充足"]
        else:
            # 默认当作不足处理
            return False

    def stop(self):
        """停止动作"""
        pass