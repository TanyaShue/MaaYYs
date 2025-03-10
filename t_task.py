import unittest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models.config import DeviceConfig
from app.models.config.device_config import DevicesConfig
from app.models.config.resource_config import ResourceConfig, SelectOption, BoolOption, InputOption, Task, Choice
from app.models.config.global_config import GlobalConfig, RunTimeConfigs, RunTimeConfig
from core.tasker_manager import TaskerManager, TaskPriority


class TestGlobalConfigAndTaskerManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, "config")
        self.resource_dir = os.path.join(self.temp_dir, "resource")

        # Create directory structure
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(os.path.join(self.resource_dir, "resource1"), exist_ok=True)
        os.makedirs(os.path.join(self.resource_dir, "resource2"), exist_ok=True)

        # Create test configuration files
        self._create_devices_config()
        self._create_resource_configs()

        # Initialize GlobalConfig
        self.global_config = GlobalConfig()

        # Mock the MAA components
        self._setup_maa_mocks()

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def _create_devices_config(self):
        """Create a sample devices.json file for testing"""
        devices_config = DevicesConfig(devices=[
            DeviceConfig(
                device_name="TestDevice1",
                adb_config=AdbConfig(
                    adb_path="adb",
                    address="127.0.0.1:5555",
                    screencap_methods=["ADB"],
                    input_methods=["ADB"],
                    config={}
                ),
                resources=[
                    DeviceResource(
                        resource_name="resource1",
                        options=[
                            ResourceOption(option_name="select_option", value="option1"),
                            ResourceOption(option_name="bool_option", value=True),
                            ResourceOption(option_name="input_option", value="test_value")
                        ]
                    )
                ]
            ),
            DeviceConfig(
                device_name="TestDevice2",
                adb_config=AdbConfig(
                    adb_path="adb",
                    address="127.0.0.1:5556",
                    screencap_methods=["ADB"],
                    input_methods=["ADB"],
                    config={}
                ),
                resources=[
                    DeviceResource(
                        resource_name="resource2",
                        options=[]
                    )
                ]
            )
        ])

        devices_config_path = os.path.join(self.config_dir, "devices.json")
        with open(devices_config_path, 'w') as f:
            f.write(devices_config.model_dump_json(indent=2))

    def _create_resource_configs(self):
        """Create sample resource_config.json.json files for testing"""
        # Resource 1
        resource1 = ResourceConfig(
            resource_name="resource1",
            options=[
                SelectOption(
                    name="select_option",
                    display="Select Option",
                    default="option1",
                    choices=[
                        Choice(name="option1", display="Option 1", value="value1"),
                        Choice(name="option2", display="Option 2", value="value2")
                    ],
                    pipeline_override={
                        "value1": {"param1": "value1_param"},
                        "value2": {"param1": "value2_param"}
                    }
                ),
                BoolOption(
                    name="bool_option",
                    display="Bool Option",
                    default=False,
                    pipeline_override={"param2": "bool_{value}"}
                ),
                InputOption(
                    name="input_option",
                    display="Input Option",
                    default="default",
                    pipeline_override={"param3": "input_{value}"}
                )
            ],
            resource_tasks=[
                Task(
                    task_name="Task1",
                    task_display="Task 1",
                    task_entry="Entry1",
                    option=["select_option", "bool_option"]
                ),
                Task(
                    task_name="Task2",
                    task_display="Task 2",
                    task_entry="Entry2",
                    option=["input_option"]
                )
            ]
        )

        resource1_path = os.path.join(self.resource_dir, "resource1", "resource_config.json.json")
        with open(resource1_path, 'w') as f:
            f.write(resource1.model_dump_json(indent=2))

        # Resource 2
        resource2 = ResourceConfig(
            resource_name="resource2",
            options=[],
            resource_tasks=[
                Task(
                    task_name="Task3",
                    task_display="Task 3",
                    task_entry="Entry3",
                    option=[]
                )
            ]
        )

        resource2_path = os.path.join(self.resource_dir, "resource2", "resource_config.json.json")
        with open(resource2_path, 'w') as f:
            f.write(resource2.model_dump_json(indent=2))

    def _setup_maa_mocks(self):
        """Set up mocks for MAA components"""
        # Create mock patches
        self.mock_resource = patch('maa.resource.Resource').start()
        self.mock_tasker = patch('maa.tasker.Tasker').start()
        self.mock_controller = patch('maa.controller.AdbController').start()

        # Configure mock behavior
        resource_instance = MagicMock()
        resource_instance.post_bundle.return_value.wait.return_value = None
        self.mock_resource.return_value = resource_instance

        tasker_instance = MagicMock()
        tasker_instance.post_task.return_value = None
        tasker_instance.bind.return_value = None
        self.mock_tasker.return_value = tasker_instance

        controller_instance = MagicMock()
        self.mock_controller.return_value = controller_instance

    def test_load_configurations(self):
        """Test loading device and resource configurations"""
        # Load device configuration
        devices_config_path = os.path.join(self.config_dir, "devices.json")
        self.global_config.load_devices_config(devices_config_path)

        # Load resource configurations
        self.global_config.load_all_resources_from_directory(self.resource_dir)

        # Verify configurations loaded correctly
        self.assertIsNotNone(self.global_config.devices_config)
        self.assertEqual(2, len(self.global_config.devices_config.devices))
        self.assertEqual("TestDevice1", self.global_config.devices_config.devices[0].device_name)
        self.assertEqual("TestDevice2", self.global_config.devices_config.devices[1].device_name)

        self.assertEqual(2, len(self.global_config.resource_configs))
        self.assertIn("resource1", self.global_config.resource_configs)
        self.assertIn("resource2", self.global_config.resource_configs)

        # Check resource1 details
        resource1 = self.global_config.get_resource_config("resource1")
        self.assertEqual(3, len(resource1.options))
        self.assertEqual(2, len(resource1.resource_tasks))

    def test_get_runtime_configs(self):
        """Test getting runtime configurations for resources"""
        # Load configurations
        devices_config_path = os.path.join(self.config_dir, "devices.json")
        self.global_config.load_devices_config(devices_config_path)
        self.global_config.load_all_resources_from_directory(self.resource_dir)

        # Get runtime configs for resource1
        runtime_configs = self.global_config.get_runtime_configs_for_resource("resource1")

        # Verify runtime configs
        self.assertEqual(2, len(runtime_configs.task_list))
        self.assertEqual(Path(os.path.join(self.resource_dir, "resource1")), runtime_configs.resource_path)

        # Check Task1 details
        task1 = runtime_configs.task_list[0]
        self.assertEqual("Task1", task1.task_name)
        self.assertEqual("Entry1", task1.task_entry)
        self.assertIn("param1", task1.pipeline_override)
        self.assertEqual("value1_param", task1.pipeline_override["param1"])
        self.assertIn("param2", task1.pipeline_override)
        self.assertEqual("bool_True", task1.pipeline_override["param2"])

        # Check Task2 details
        task2 = runtime_configs.task_list[1]
        self.assertEqual("Task2", task2.task_name)
        self.assertEqual("Entry2", task2.task_entry)
        self.assertIn("param3", task2.pipeline_override)
        self.assertEqual("input_test_value", task2.pipeline_override["param3"])

    @patch('PySide6.QtCore.QThreadPool.globalInstance')
    def test_tasker_manager_submit_task(self, mock_thread_pool):
        """Test TaskerManager task submission"""
        # Setup mock thread pool
        mock_thread_pool_instance = MagicMock()
        mock_thread_pool.return_value = mock_thread_pool_instance

        # Load configurations
        devices_config_path = os.path.join(self.config_dir, "devices.json")
        self.global_config.load_devices_config(devices_config_path)
        self.global_config.load_all_resources_from_directory(self.resource_dir)

        # Get runtime configs
        runtime_configs = self.global_config.get_runtime_configs_for_resource("resource1")

        # Create TaskerManager and add a device
        manager = TaskerManager()
        device_config = self.global_config.devices_config.devices[0]

        # Patch the TaskExecutor._tasker property to return our mock
        with patch('core.task_executor.TaskExecutor._tasker', new_callable=MagicMock()) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # Create executor and submit task
            success = manager.create_executor(device_config)
            self.assertTrue(success)

            task_id = manager.submit_task("TestDevice1", runtime_configs, TaskPriority.HIGH)
            self.assertIsNotNone(task_id)

            # Verify device status
            state = manager.get_executor_state("TestDevice1")
            self.assertIsNotNone(state)

            # Stop executor
            success = manager.stop_executor("TestDevice1")
            self.assertTrue(success)

    def test_multiple_devices_task_submission(self):
        """Test submitting tasks to multiple devices"""
        # Load configurations
        devices_config_path = os.path.join(self.config_dir, "devices.json")
        self.global_config.load_devices_config(devices_config_path)
        self.global_config.load_all_resources_from_directory(self.resource_dir)

        # Get runtime configs for each resource
        runtime_configs1 = self.global_config.get_runtime_configs_for_resource("resource1")
        runtime_configs2 = self.global_config.get_runtime_configs_for_resource("resource2")

        # Create TaskerManager
        manager = TaskerManager()

        # Patch the TaskExecutor._tasker property
        with patch('core.task_executor.TaskExecutor._tasker', new_callable=MagicMock()) as mock_tasker_property:
            mock_tasker_property.return_value = self.mock_tasker.return_value

            # Create executors for both devices
            manager.create_executor(self.global_config.devices_config.devices[0])
            manager.create_executor(self.global_config.devices_config.devices[1])

            # Submit tasks to both devices
            task_id1 = manager.submit_task("TestDevice1", runtime_configs1)
            task_id2 = manager.submit_task("TestDevice2", runtime_configs2)

            self.assertIsNotNone(task_id1)
            self.assertIsNotNone(task_id2)

            # Verify active devices
            active_devices = manager.get_active_devices()
            self.assertEqual(2, len(active_devices))
            self.assertIn("TestDevice1", active_devices)
            self.assertIn("TestDevice2", active_devices)

            # Check queue information
            queue_info = manager.get_device_queue_info()
            self.assertEqual(2, len(queue_info))

            # Stop all executors
            manager.stop_all()

            # Verify no active devices
            active_devices = manager.get_active_devices()
            self.assertEqual(0, len(active_devices))


if __name__ == "__main__":
    unittest.main()