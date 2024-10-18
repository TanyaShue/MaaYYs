import socket
import json
import threading
import time
from src.task_service import run_task_service

def start_server():
    """启动服务器的线程，以便在测试期间进行连接。"""
    server_thread = threading.Thread(target=run_task_service, args=('localhost', 11234))
    server_thread.daemon = True  # 使线程在主线程退出时结束
    server_thread.start()
    time.sleep(1)  # 等待服务器启动
    return server_thread

def test_task_service_handler():
    server_thread = start_server()
    print("Server started.")

    # 创建客户端连接
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 11234))

    # 准备发送的测试消息
    test_message = {
        "action": "create_tasker",
        "project_key": "test_project",
        "project": {
            "adb_config": {
                "adb_path": "path/to/adb",
                "adb_address": "127.0.0.1:5037"
            }
        }
    }

    # 发送测试消息
    client_socket.sendall((json.dumps(test_message) + '\n').encode('utf-8'))

    # 接收响应
    response = client_socket.recv(4096).decode('utf-8').strip()
    response_json = json.loads(response)

    # 断言检查
    assert response_json['status'] == 'success'
    assert response_json['message'] == "Tasker test_project created."

    # 关闭客户端连接
    client_socket.close()
    print("Test completed successfully.")

if __name__ == "__main__":
    try:
        test_task_service_handler()
    except Exception as e:
        print(f"Test failed with error: {e}")
