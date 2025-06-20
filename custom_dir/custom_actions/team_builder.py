# -*- coding: UTF-8 -*-
import json
import socket
import threading
import time

from maa.context import Context
from maa.custom_action import CustomAction

from maa.agent.agent_server import AgentServer

@AgentServer.custom_action("TeamBuilder")
class TeamBuilder(CustomAction):
    def __init__(self):
        super().__init__()
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.my_id = None
        self.port = None
        self.clients = []  # 服务器端：存储所有客户端连接
        self.message_event = threading.Event()  # 消息接收事件
        self.last_message = None  # 最后收到的消息

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """简单的通信系统"""
        print("开始执行自定义动作：简单通信")

        # 解析参数
        try:
            params = json.loads(argv.custom_action_param)
            self.my_id = params.get("id")
            self.port = int(params.get("port"))
            if not self.my_id or not self.port:
                print("无效的参数: 需要提供id和port")
                return False
        except Exception as e:
            print(f"参数解析失败: {e}")
            return False

        # 尝试作为客户端连接
        is_client = self.connect_to_server()

        # 如果客户端连接失败，尝试作为服务器启动
        if not is_client:
            if not self.create_server():
                print("无法创建服务")
                return False

            # 作为服务创建者，也连接到自己的服务
            time.sleep(0.5)  # 等待服务器启动
            if not self.connect_to_server():
                print("作为创建者连接服务失败")
                # 继续运行，因为服务器已经创建

        # 客户端逻辑
        if is_client:
            self.send_message("hello")
            if self.wait_for_message(30):
                print(f"已成功连接,准备组队: {self.last_message}")
        # 服务器逻辑
        else:
            if self.wait_for_message(300):
                print(f"已成功连接,准备组队: {self.last_message}")
                self.send_message("you too")

        return True

    def connect_to_server(self):
        """连接到服务器"""
        self._close_socket(self.client_socket)
        self.client_socket = None

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', self.port))

            # 发送自己的ID
            self.client_socket.send(f"ID:{self.my_id}".encode('utf-8'))

            # 启动接收消息的线程
            self.running = True
            threading.Thread(target=self._receive_messages, daemon=True).start()

            print(f"已连接到端口 {self.port} 的服务")
            return True
        except Exception as e:
            print(f"连接到服务器失败: {e}")
            self._close_socket(self.client_socket)
            self.client_socket = None
            return False

    def create_server(self):
        """创建服务器"""
        self._close_socket(self.server_socket)
        self.server_socket = None

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)

            # 启动服务器线程
            self.running = True
            threading.Thread(target=self._run_server, daemon=True).start()

            print(f"已创建端口 {self.port} 的服务")
            return True
        except Exception as e:
            print(f"创建服务器失败: {e}")
            self._close_socket(self.server_socket)
            self.server_socket = None
            return False

    def _run_server(self):
        """服务器线程，接受新连接"""
        while self.running and self.server_socket:
            try:
                self.server_socket.settimeout(1.0)
                client, addr = self.server_socket.accept()

                # 接收客户端ID
                data = client.recv(1024)
                if data and data.decode('utf-8').startswith("ID:"):
                    client_id = data.decode('utf-8')[3:]
                    print(f"客户端 {client_id} 已连接")

                    # 添加到客户端列表
                    self.clients.append((client, client_id))

                    # 创建线程处理客户端消息
                    threading.Thread(target=self._handle_client,
                                     args=(client, client_id),
                                     daemon=True).start()
                else:
                    print("未收到有效的客户端ID")
                    client.close()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"服务器异常: {e}")
                break

        self._close_socket(self.server_socket)
        self.server_socket = None
        print("服务器已关闭")

    def _handle_client(self, client_socket, client_id):
        """处理客户端的消息"""
        while self.running and client_socket:
            try:
                client_socket.settimeout(1.0)
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode('utf-8')

                # 广播消息给所有其他客户端
                self._broadcast_message(f"{client_id}:{message}", client_socket, client_id)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"处理客户端消息异常: {e}")
                break

        # 移除断开连接的客户端
        self.clients = [(c, cid) for c, cid in self.clients if c != client_socket]
        self._close_socket(client_socket)
        print(f"客户端 {client_id} 已断开")

    def _broadcast_message(self, message, sender_socket=None, sender_id=None):
        """广播消息给所有客户端"""
        for client, client_id in self.clients:
            # 不给发送者回发消息
            if client != sender_socket and client_id != sender_id:
                try:
                    client.send(message.encode('utf-8'))
                except Exception:
                    pass  # 发送失败的客户端会在下一次循环中被移除

    def _receive_messages(self):
        """接收消息线程"""
        while self.running and self.client_socket:
            try:
                self.client_socket.settimeout(1.0)
                data = self.client_socket.recv(1024)
                if not data:
                    print("与服务器的连接已断开")
                    break

                message = data.decode('utf-8')

                # 解析消息，格式为"发送者ID:消息内容"
                if ':' in message:
                    sender_id, content = message.split(':', 1)

                    # 忽略自己发送的消息
                    if sender_id == self.my_id:
                        continue

                    print(f"收到来自 {sender_id} 的消息: {content}")
                    self.last_message = content
                    self.message_event.set()
                else:
                    self.last_message = message
                    self.message_event.set()

            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收消息异常: {e}")
                break

        self._close_socket(self.client_socket)
        self.client_socket = None

    def send_message(self, message):
        """发送消息"""
        if not self.client_socket:
            print("未连接到服务器，无法发送消息")
            return False

        try:
            self.client_socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def wait_for_message(self, timeout=30):
        """阻塞等待接收消息"""
        self.message_event.clear()
        return self.message_event.wait(timeout)

    def stop(self):
        """停止通信"""
        self.running = False

        # 关闭所有连接
        self._close_socket(self.client_socket)
        self.client_socket = None

        self._close_socket(self.server_socket)
        self.server_socket = None

        # 关闭所有客户端连接
        for client, _ in self.clients:
            self._close_socket(client)
        self.clients = []

    def _close_socket(self, sock):
        """安全关闭套接字"""
        if sock:
            try:
                sock.close()
            except Exception:
                pass