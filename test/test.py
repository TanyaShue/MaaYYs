import socket
import json

def send_request(request_data, host='localhost', port=11234):
    """发送请求到TCP服务器，并接收响应"""
    try:
        with socket.create_connection((host, port)) as sock:
            # 发送请求数据
            message = json.dumps(request_data) + '\n'
            sock.sendall(message.encode('utf-8'))

            # 接收响应数据
            response_data = sock.recv(4096)
            response = response_data.decode('utf-8')
            print(f"Response from server: {response}")

    except Exception as e:
        print(f"Error communicating with server: {e}")

# 测试创建 Tasker 的请求
def test_create_tasker():
    project_data = {
        "project_name": "TestProject",
        "program_name": "TestProgram",
        "adb_config": {
            "adb_path": "/path/to/adb",
            "adb_address": "127.0.0.1:5555"
        },
        "selected_tasks": ["task1", "task2"],
        "option": {
            "select": {
                "option_name": "resolution",
                "option_value": "1080p",
                "option_type": "select"
            },
            "boole": {
                "option_name": "fullscreen",
                "option_value": True,
                "option_type": "boole"
            }
        }
    }

    request = {
        "action": "create_tasker",
        "project": project_data
    }
    send_request(request)

# 测试发送任务的请求
def test_send_task():
    project_key = "/path/to/adb:127.0.0.1:5555"
    task_data = {
        "project_run_tasks": [
            {
                "task_name": "task1",
                "task_entry": "entry1",
                "pipeline_override": {}
            },
            {
                "task_name": "task2",
                "task_entry": "entry2",
                "pipeline_override": {}
            }
        ]
    }

    request = {
        "action": "send_task",
        "project_key": project_key,
        "task": task_data
    }
    send_request(request)

# 测试终止 Tasker 的请求
def test_terminate_tasker():
    project_key = "/path/to/adb:127.0.0.1:5555"
    request = {
        "action": "terminate_tasker",
        "project_key": project_key
    }
    send_request(request)

# 测试终止所有 Tasker 的请求
def test_terminate_all():
    request = {
        "action": "terminate_all"
    }
    send_request(request)

if __name__ == "__main__":
    # 运行不同的测试请求
    test_create_tasker()   # 测试创建 Tasker
    test_send_task()       # 测试发送任务
    test_terminate_tasker()# 测试终止特定 Tasker
    test_terminate_all()   # 测试终止所有 Tasker
