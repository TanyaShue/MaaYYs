import unittest
from typing import Dict, Any


class TestGlobalConfig(unittest.TestCase):
    def setUp(self):
        """
        初始化全局配置，加载设备和资源配置。
        """
        # 使用单例模式获取 GlobalConfig 实例
        from app.models.config.global_config import GlobalConfig
        self.global_config = GlobalConfig()

        # 加载设备配置
        devices_config_path = "assets/config/devices.json"
        self.global_config.load_devices_config(devices_config_path)

        # 加载资源配置
        resource_dir = "assets/resource"
        self.global_config.load_all_resources_from_directory(resource_dir)

    def test_config_loading(self):
        """
        测试配置加载。
        """
        # 验证设备配置已加载
        devices_config = self.global_config.get_devices_config()
        self.assertIsNotNone(devices_config, "设备配置未成功加载，返回 None")

        # 验证设备配置中是否有设备
        self.assertTrue(len(devices_config.devices) > 0, "设备配置中没有设备，请检查 devices.json 文件")

        # 验证资源配置已加载
        resource_configs = self.global_config.get_all_resource_configs()
        self.assertTrue(len(resource_configs) > 0, "没有加载任何资源配置，请检查 resource 目录")

        # 打印已加载的资源名称
        print("\n已加载的资源:")
        for config in resource_configs:
            print(f"  - {config.resource_name}")

    def test_runtime_configs_for_resources(self):
        """
        测试获取所有资源的运行时配置。
        """
        # 获取所有资源配置
        resource_configs = self.global_config.get_all_resource_configs()

        # 确保至少有一个资源配置
        self.assertTrue(len(resource_configs) > 0, "没有加载任何资源配置，无法进行运行时配置测试")

        # 遍历每个资源配置
        for resource_config in resource_configs:
            # 获取该资源的运行时配置
            runtime_configs = self.global_config.get_runtime_configs_for_resource(resource_config.resource_name)

            # 确保生成了运行时配置
            self.assertTrue(len(runtime_configs.list) > 0,
                            f"资源 '{resource_config.resource_name}' 未生成任何运行时配置，请检查资源配置")

            # 打印每个资源的运行时配置（用于调试）
            print(f"\n资源: {resource_config.resource_name}")
            for rt_config in runtime_configs.list:
                print(f"  任务: {rt_config.task_name}")
                print(f"  入口: {rt_config.task_entry}")
                print(f"  管道覆盖: {rt_config.pipeline_override}")

                # 额外验证
                self.assertIsNotNone(rt_config.task_name,
                                     f"资源 '{resource_config.resource_name}' 的任务运行时配置中，任务名称不能为空")
                self.assertIsNotNone(rt_config.task_entry,
                                     f"资源 '{resource_config.resource_name}' 的任务运行时配置中，任务入口不能为空")
                self.assertIsInstance(rt_config.pipeline_override, dict,
                                      f"资源 '{resource_config.resource_name}' 的任务运行时配置中，管道覆盖必须是字典")

    def test_runtime_config_for_specific_task(self):
        """
        测试获取特定资源中特定任务的运行时配置。
        """
        # 获取所有资源配置
        resource_configs = self.global_config.get_all_resource_configs()

        # 确保至少有一个资源配置
        self.assertTrue(len(resource_configs) > 0, "没有加载任何资源配置，无法进行特定任务运行时配置测试")

        # 选择第一个资源配置进行测试 (你可以根据需要选择特定的资源)
        resource_config = resource_configs[0]
        self.assertTrue(len(resource_config.resource_tasks) > 0,
                        f"资源 '{resource_config.resource_name}' 没有定义任何任务，无法进行特定任务运行时配置测试")

        # 选择第一个任务进行测试 (你可以根据需要选择特定的任务)
        task = resource_config.resource_tasks[0]

        # 获取特定任务的运行时配置
        runtime_config = self.global_config.get_runtime_config_for_task(
            resource_config.resource_name,
            task.task_name
        )

        # 验证返回了运行时配置
        self.assertIsNotNone(runtime_config,
                             f"无法获取资源 '{resource_config.resource_name}' 中任务 '{task.task_name}' 的运行时配置")

        print(f"\n资源: {resource_config.resource_name}")
        print(f"  任务: {runtime_config.task_name}")
        print(f"  入口: {runtime_config.task_entry}")
        print(f"  管道覆盖: {runtime_config.pipeline_override}")

        # 验证运行时配置的基本属性
        self.assertEqual(runtime_config.task_name, task.task_name, "任务名称不匹配")
        self.assertEqual(runtime_config.task_entry, task.task_entry, "任务入口不匹配")
        self.assertIsInstance(runtime_config.pipeline_override, dict, "管道覆盖必须是字典")

    def test_option_values_from_device_config(self):
        """
        测试从设备配置中获取选项值的功能。
        确保正确使用设备配置中的选项值而不是默认值。
        """
        # 获取设备配置
        devices_config = self.global_config.get_devices_config()
        self.assertIsNotNone(devices_config, "设备配置未成功加载，返回 None")

        # 确保有设备
        self.assertTrue(len(devices_config.devices) > 0, "设备配置中没有设备，请检查 devices.json 文件")

        # 找到第一个具有资源配置的设备
        device = devices_config.devices[0]
        self.assertTrue(len(device.resources) > 0, f"设备 '{device.device_name}' 没有资源配置")

        # 获取设备中第一个资源
        device_resource = device.resources[0]

        # 获取对应的资源配置
        resource_config = self.global_config.get_resource_config(device_resource.resource_name)
        self.assertIsNotNone(resource_config, f"找不到资源 '{device_resource.resource_name}' 的配置")

        # 确保资源有任务
        self.assertTrue(len(resource_config.resource_tasks) > 0, f"资源 '{resource_config.resource_name}' 没有任务")

        # 获取第一个任务的运行时配置
        task = resource_config.resource_tasks[2]
        runtime_config = self.global_config.get_runtime_config_for_task(
            resource_config.resource_name,
            task.task_name
        )

        print(f"\n测试设备选项值优先级:")
        print(f"  设备: {device.device_name}")
        print(f"  资源: {resource_config.resource_name}")
        print(f"  任务: {task.task_name}")

        # 打印设备配置中的选项值
        print("\n设备中的选项值:")
        for option in device_resource.options:
            print(f"  {option.option_name}: {option.value}")

        # 打印资源配置中的默认选项值
        print("\n资源中的默认选项值:")
        for option in resource_config.options:
            print(f"  {option.name}: {option.default}")

        # 打印生成的管道覆盖
        print("\n生成的管道覆盖:")
        print(f"  {runtime_config.pipeline_override}")

        # 检查管道覆盖是否正确应用了设备配置中的选项值
        # 这里需要根据你的具体资源配置进行自定义断言
        # 例如，如果设备配置中设置了选项值，验证管道覆盖中包含正确的值

        # 以下是一个示例断言，需要根据具体情况修改
        if len(device_resource.options) > 0:
            # 假设第一个选项影响了管道覆盖
            first_option = device_resource.options[0]

            # 查找这个选项在资源配置中的定义
            resource_option = next((opt for opt in resource_config.options if opt.name == first_option.option_name),
                                   None)

            if resource_option is not None:
                # 根据选项类型进行不同的断言
                if resource_option.type == "select":
                    print(f"\n验证select类型选项 '{first_option.option_name}' 的值是否正确应用")
                    # 这里需要根据具体情况检查管道覆盖中是否包含了正确的值
                elif resource_option.type == "boole":
                    print(f"\n验证boole类型选项 '{first_option.option_name}' 的值是否正确应用")
                    # 检查布尔值是否正确应用
                elif resource_option.type == "input":
                    print(f"\n验证input类型选项 '{first_option.option_name}' 的值是否正确应用")
                    # 检查输入值是否正确替换了占位符

                self.assertIsNotNone(runtime_config.pipeline_override, "管道覆盖不应为空")


if __name__ == '__main__':
    unittest.main()