import socket
import unittest
import threading
import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        self.request.sendall(self.data)

class TestMyTCPHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 设置服务器线程
        HOST, PORT = "localhost", 12347
        cls.server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True  # 设置为守护线程
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def test_server_response(self):
        # 模拟客户端发送数据并接收回显
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("localhost", 12347))
            message = b"Hello, Server"
            sock.sendall(message)

            response = sock.recv(1024)
            self.assertEqual(response, message)

if __name__ == "__main__":
    unittest.main()
