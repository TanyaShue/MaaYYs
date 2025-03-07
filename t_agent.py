# import sys
#
# from maa import resource
# from maa.agent.agent_server import AgentServer
# from maa.controller import AdbController
# from maa.custom_recognition import CustomRecognition
# from maa.custom_action import CustomAction
# from maa.context import Context
# from maa.resource import Resource
# from maa.tasker import Tasker
# from maa.toolkit import Toolkit
#
#
# def main():
#     Toolkit.init_option("./")
#
#     socket_id = sys.argv[-1]
#
#     AgentServer.start_up(socket_id)
#     AgentServer.join()
#     AgentServer.shut_down()
#
#
# @AgentServer.custom_recognition("MyRecongition")
# class MyRecongition(CustomRecognition):
#
#     def analyze(
#         self,
#         context: Context,
#         argv: CustomRecognition.AnalyzeArg,
#     ) -> CustomRecognition.AnalyzeResult:
#         reco_detail = context.run_recognition(
#             "MyCustomOCR",
#             argv.image,
#             pipeline_override={"MyCustomOCR": {"roi": [100, 100, 200, 300]}},
#         )
#
#         # context is a reference, will override the pipeline for whole task
#         context.override_pipeline({"MyCustomOCR": {"roi": [1, 1, 114, 514]}})
#         # context.run_recognition ...
#
#         # make a new context to override the pipeline, only for itself
#         new_context = context.clone()
#         new_context.override_pipeline({"MyCustomOCR": {"roi": [100, 200, 300, 400]}})
#         reco_detail = new_context.run_recognition("MyCustomOCR", argv.image)
#
#         click_job = context.tasker.controller.post_click(10, 20)
#         click_job.wait()
#
#         context.override_next(argv.node_name, ["TaskA", "TaskB"])
#
#         return CustomRecognition.AnalyzeResult(
#             box=(0, 0, 100, 100), detail="Hello World!"
#         )
#
#
# @AgentServer.custom_action("MyCustomAction")
# class MyCustomAction(CustomAction):
#
#     def run(
#         self,
#         context: Context,
#         argv: CustomAction.RunArg,
#     ) -> bool:
#         print("MyCustomAction is running!")
#         return True
#

import threading
import time

from maa.agent.agent_server import AgentServer


def service_start():
    socket_id = "test_socket"
    print("启动服务，socket_id:", socket_id)
    AgentServer.start_up(socket_id)
    # AgentServer.join()
    print("服务线程结束。")


def service_stop():
    # 等待 3 秒后结束服务
    time.sleep(3)
    print("准备结束服务。")
    AgentServer.shut_down()
    print("结束服务。")


if __name__ == '__main__':
    # 初始化配置参数
    # Toolkit.init_option("./")

    # 创建两个线程：一个启动服务，一个在3秒后停止服务
    t_start = threading.Thread(target=service_start)
    t_stop = threading.Thread(target=service_stop)

    t_start.start()
    t_stop.start()
    t_start.join()
    t_stop.join()

    print("测试完成。")
