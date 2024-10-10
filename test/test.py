# python -m pip install maafw
from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

from src.custom_actions.challenge_dungeon_boss import ChallengeDungeonBoss


def main():
    user_path = "../assets"
    Toolkit.init_option(user_path)

    resource = Resource()
    res_job = resource.post_path("../assets/resource/base")
    res_job.wait()

    adb_devices = Toolkit.find_adb_devices()
    if not adb_devices:
        print("No ADB device found.")
        exit()

    # for demo, we just use the first device
    device = adb_devices[0]
    controller = AdbController(
        adb_path=device.adb_path,
        address=device.address,
        screencap_methods=device.screencap_methods,
        input_methods=device.input_methods,
        config=device.config,
    )
    controller.post_connection().wait()

    tasker = Tasker()
    tasker.bind(resource, controller)

    if not tasker.inited:
        print("Failed to init MAA.")
        exit()

    resource.register_custom_action("ChallengeDungeonBoss", ChallengeDungeonBoss())

    # print(task_detail.raw_detail)
    # do something with task_detail





if __name__ == "__main__":
    main()