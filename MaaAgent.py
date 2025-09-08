import argparse
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


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Start Agent Server with custom parameters')

    # Add arguments with default values
    parser.add_argument('-path', '--custom_path', default='./custom_dir',
                        help='Path to custom objects directory (default: ./custom_dir)')
    parser.add_argument('-id', '--socket_id', default='maa-agent-server',
                        help='Socket ID for server connection (default: maa-agent-server)')

    # Parse arguments
    args = parser.parse_args()

    # Initialize toolkit
    Toolkit.init_option("./")

    # Use the arguments
    custom_objects_path = args.custom_path
    socket_id = args.socket_id

    print(f"使用自定义路径: {custom_objects_path}")
    print(f"使用Socket ID: {socket_id}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本目录: {current_dir}")

    print("当前socket_id:", socket_id)
    AgentServer.start_up(socket_id)

    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()