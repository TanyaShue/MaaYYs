import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from core.task_executor import DeviceStatus
from core.tasker_manager import TaskerManager, TaskPriority


class TestTaskSubmissionAndExecution(unittest.TestCase):
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

        # 设置MAA组件的模拟
        self._setup_maa_mocks()

        # 获取TaskerManager实例
        self.tasker_manager = TaskerManager()

    def _setup_maa_mocks(self):
        """设置MAA组件的模拟"""
        # 创建模拟对象
        self.mock_resource = patch('maa.resource.Resource').start()
        self.mock_tasker = patch('maa.tasker.Tasker').start()
        self.mock_controller = patch('maa.controller.AdbController').start()

        # 配置模拟行为
        resource_instance = MagicMock()
        resource_instance.post_bundle.return_value.wait.return_value = None
        self.mock_resource.return_value = resource_instance

        tasker_instance = MagicMock()
        tasker_instance.post_task.return_value = None
        tasker_instance.bind.return_value = None
        self.mock_tasker.return_value = tasker_instance

        controller_instance = MagicMock()
        self.mock_controller.return_value = controller_instance

    def tearDown(self):
        """清理模拟对象"""
        patch.stopall()

    @patch('PySide6.QtCore.QThreadPool.globalInstance')
    def test_create_executor_and_submit_task(self, mock_thread_pool):
        """测试创建执行器并提交任务"""
        # 设置线程池模拟
        mock_thread_pool_instance = MagicMock()
        mock_thread_pool.return_value = mock_thread_pool_instance

        # 获取第一个设备配置
        device_config = self.global_config.devices_config.devices[0]
        device_name = device_config.device_name

        # 为这个设备获取第一个资源的运行时配置
        resource_name = device_config.resources[0].resource_name
        runtime_configs = self.global_config.get_runtime_configs_for_resource(resource_name)

        # 确保runtime_configs不为空并且有任务
        self.assertIsNotNone(runtime_configs)
        self.assertTrue(len(runtime_configs.task_list) > 0)

        # 确保资源路径正确设置
        self.assertTrue(runtime_configs.resource_path.exists())

        # 使用TaskExecutor._tasker属性的模拟来确保任务执行器使用我们的模拟Tasker
        with patch('core.task_executor.TaskExecutor._tasker', new_callable=PropertyMock) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # 创建设备执行器
            success = self.tasker_manager.create_executor(device_config)
            self.assertTrue(success)

            # 验证设备是否处于活跃状态
            self.assertTrue(self.tasker_manager.is_device_active(device_name))

            # 获取设备状态并验证
            device_state = self.tasker_manager.get_executor_state(device_name)
            self.assertIsNotNone(device_state)
            self.assertEqual(DeviceStatus.IDLE, device_state.status)

            # 提交任务
            task_id = self.tasker_manager.submit_task(device_name, runtime_configs, TaskPriority.HIGH)
            self.assertIsNotNone(task_id)

            # 模拟线程执行任务
            args, kwargs = mock_thread_pool_instance.start.call_args
            task_runner = args[0]

            # 手动执行任务
            task_runner.run()

            # 验证Tasker.post_task是否被调用
            self.mock_tasker.return_value.post_task.assert_called()

            # 获取队列信息
            queue_info = self.tasker_manager.get_device_queue_info()
            self.assertIn(device_name, queue_info)

    @patch('PySide6.QtCore.QThreadPool.globalInstance')
    def test_multiple_task_execution(self, mock_thread_pool):
        """测试多个任务的提交和执行"""
        # 设置线程池模拟
        mock_thread_pool_instance = MagicMock()
        mock_thread_pool.return_value = mock_thread_pool_instance

        # 获取设备配置
        device_config = self.global_config.devices_config.devices[0]
        device_name = device_config.device_name

        # 获取资源名称
        resource_name = device_config.resources[0].resource_name
        runtime_configs = self.global_config.get_runtime_configs_for_resource(resource_name)

        # 模拟TaskExecutor._tasker属性
        with patch('core.task_executor.TaskExecutor._tasker', new_callable=PropertyMock) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # 创建执行器
            self.tasker_manager.create_executor(device_config)

            # 提交多个任务
            task_ids = []
            for priority in [TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                task_id = self.tasker_manager.submit_task(device_name, runtime_configs, priority)
                task_ids.append(task_id)
                self.assertIsNotNone(task_id)

            # 验证任务ID不同
            self.assertEqual(len(set(task_ids)), 3, "每个任务应该有唯一的ID")

            # 获取队列长度
            queue_info = self.tasker_manager.get_device_queue_info()
            self.assertGreaterEqual(queue_info[device_name], 2)  # 至少2个任务在队列中(一个正在执行)

            # 模拟任务执行 - 检查第一个任务是否根据优先级启动
            args, kwargs = mock_thread_pool_instance.start.call_args
            task_runner = args[0]
            self.assertEqual(TaskPriority.HIGH, task_runner.task.priority)

    @patch('PySide6.QtCore.QThreadPool.globalInstance')
    def test_task_execution_lifecycle(self, mock_thread_pool):
        """测试任务执行的生命周期"""
        # 设置线程池模拟
        mock_thread_pool_instance = MagicMock()
        mock_thread_pool.return_value = mock_thread_pool_instance

        # 获取设备配置
        device_config = self.global_config.devices_config.devices[0]
        device_name = device_config.device_name

        # 获取资源运行时配置
        resource_name = device_config.resources[0].resource_name
        runtime_configs = self.global_config.get_runtime_configs_for_resource(resource_name)

        # 连接信号处理器模拟
        task_started_mock = MagicMock()
        task_completed_mock = MagicMock()
        task_failed_mock = MagicMock()

        with patch('core.task_executor.TaskExecutor._tasker', new_callable=PropertyMock) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # 创建执行器
            self.tasker_manager.create_executor(device_config)

            # 获取执行器并连接信号
            executor = self.tasker_manager._executors[device_name]
            executor.task_started.connect(task_started_mock)
            executor.task_completed.connect(task_completed_mock)
            executor.task_failed.connect(task_failed_mock)

            # 提交任务
            task_id = self.tasker_manager.submit_task(device_name, runtime_configs)

            # 获取任务运行器
            args, kwargs = mock_thread_pool_instance.start.call_args
            task_runner = args[0]

            # 手动执行任务
            task_runner.run()

            # 验证信号发射
            task_started_mock.assert_called_once_with(task_id)
            task_completed_mock.assert_called_once()
            task_failed_mock.assert_not_called()

            # 验证MAA组件交互
            self.mock_resource.return_value.post_bundle.assert_called_once()
            self.mock_tasker.return_value.bind.assert_called_once()

            # 验证每个任务都被提交给Tasker
            call_count = 0
            for task in runtime_configs.task_list:
                call_count += 1
                self.mock_tasker.return_value.post_task.assert_any_call(
                    task.task_entry, task.pipeline_override
                )

            self.assertEqual(call_count, len(runtime_configs.task_list))

    @patch('PySide6.QtCore.QThreadPool.globalInstance')
    def test_task_failure_handling(self, mock_thread_pool):
        """测试任务失败处理"""
        # 设置线程池模拟
        mock_thread_pool_instance = MagicMock()
        mock_thread_pool.return_value = mock_thread_pool_instance

        # 配置Tasker抛出异常
        self.mock_tasker.return_value.post_task.side_effect = RuntimeError("模拟任务失败")

        # 获取设备配置
        device_config = self.global_config.devices_config.devices[0]
        device_name = device_config.device_name

        # 获取资源运行时配置
        resource_name = device_config.resources[0].resource_name
        runtime_configs = self.global_config.get_runtime_configs_for_resource(resource_name)

        # 连接信号处理器模拟
        task_started_mock = MagicMock()
        task_failed_mock = MagicMock()

        with patch('core.task_executor.TaskExecutor._tasker', new_callable=PropertyMock) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # 创建执行器
            self.tasker_manager.create_executor(device_config)

            # 获取执行器并连接信号
            executor = self.tasker_manager._executors[device_name]
            executor.task_started.connect(task_started_mock)
            executor.task_failed.connect(task_failed_mock)

            # 提交任务
            task_id = self.tasker_manager.submit_task(device_name, runtime_configs)

            # 获取任务运行器
            args, kwargs = mock_thread_pool_instance.start.call_args
            task_runner = args[0]

            # 手动执行任务
            task_runner.run()

            # 验证信号发射
            task_started_mock.assert_called_once_with(task_id)
            task_failed_mock.assert_called_once()

            # 确认任务失败信息
            error_task_id, error_message = task_failed_mock.call_args[0]
            self.assertEqual(task_id, error_task_id)
            self.assertIn("模拟任务失败", error_message)

    def test_stop_executor(self):
        """测试停止执行器"""
        # 获取设备配置
        device_config = self.global_config.devices_config.devices[0]
        device_name = device_config.device_name

        with patch('core.task_executor.TaskExecutor._tasker', new_callable=PropertyMock) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # 创建执行器
            self.tasker_manager.create_executor(device_config)

            # 验证设备处于活跃状态
            self.assertTrue(self.tasker_manager.is_device_active(device_name))

            # 停止执行器
            success = self.tasker_manager.stop_executor(device_name)
            self.assertTrue(success)

            # 验证设备不再活跃
            self.assertFalse(self.tasker_manager.is_device_active(device_name))


if __name__ == "__main__":
    unittest.main()