from debug.custom_actions import *
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit


def main():
    Toolkit.init_option("./")

    # socket_id = sys.argv[-1]
    socket_id = "111-222-333-444"

    print("当前socket_id:", socket_id)
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()
if __name__ == "__main__":
    main()