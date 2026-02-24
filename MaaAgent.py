import os
import sys

# 添加当前脚本目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.chdir(current_dir)

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit
from custom_dir.custom_actions import *
from custom_dir.custom_recognition import my_recognizer

from custom_dir import set_device_name


def main():
    Toolkit.init_option("./")

    # 如果没有额外参数，使用默认ID
    if len(sys.argv) > 1:
        socket_id = sys.argv[-1]
    else:
        socket_id = "maa-agent-server"

    print(f"使用Socket ID: {socket_id}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本目录: {current_dir}")

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()