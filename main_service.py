import signal
import sys
import logging
from flask import Flask, request, jsonify
from threading import Lock, Event
from typing import Dict
from src.utils.config_projects import Project, ProjectRunData
from src.core.tasker_thread import TaskerThread
import time

app = Flask(__name__)
taskers: Dict[str, TaskerThread] = {}
lock = Lock()
shutdown_event = Event()  # 用于控制关闭事件


@app.route('/create_tasker', methods=['POST'])
def create_tasker():
    data = request.json
    project_key = data.get("project_key")
    project_data = data.get("project")
    project = Project.from_json(project_data)

    with lock:
        if project_key in taskers:
            return jsonify({"status": "error", "message": "Tasker already exists."}), 400

        tasker = TaskerThread(project_key, project)
        tasker.start()
        taskers[project_key] = tasker

    return jsonify({"status": "success", "message": f"Tasker {project_key} created."}), 200

@app.route('/')
def index():
    return 'Hello, Flask!'

@app.route('/send_task', methods=['POST'])
def send_task():
    data = request.json
    project_key = data.get("project_key")
    task_data = data.get("task").get("task")

    with lock:
        tasker = taskers.get(project_key)
        if not tasker:
            return jsonify({"status": "error", "message": "Tasker not found."}), 404
        print(task_data)
        task = ProjectRunData.from_json(task_data) if isinstance(task_data, dict) else task_data
        tasker.send_task(task)

    return jsonify({"status": "success", "message": "Task sent."}), 200

@app.route('/terminate_tasker', methods=['POST'])
def terminate_tasker():
    data = request.json
    project_key = data.get("project_key")

    with lock:
        tasker = taskers.pop(project_key, None)
        if not tasker:
            return jsonify({"status": "error", "message": "Tasker not found."}), 404
        tasker.terminate()

    return jsonify({"status": "success", "message": f"Tasker {project_key} terminated."}), 200


def terminate_all_taskers():
    """优雅地终止所有运行中的线程，如果两秒内未完成则强制终止"""
    logging.info("Terminating all taskers...")
    with lock:
        for project_key, tasker in taskers.items():
            logging.info(f"Terminating tasker {project_key}...")
            tasker.terminate()

    # 等待两秒钟进行优雅关闭
    shutdown_event.wait(timeout=2)

    # 如果仍有未关闭的线程，则强制退出
    if not shutdown_event.is_set():
        logging.warning("Timeout reached. Forcing shutdown.")
        sys.exit(1)
    else:
        logging.info("All taskers terminated successfully.")


def signal_handler(sig, frame):
    logging.info(f"Signal {sig} received. Initiating shutdown...")
    terminate_all_taskers()


if __name__ == "__main__":
    # 捕获信号以确保所有线程在程序结束时正确关闭
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.basicConfig(level=logging.INFO)

    try:
        app.run(host='localhost', port=54345, debug=True)
    except KeyboardInterrupt:
        logging.info("应用正在关闭...")
    finally:
        # 应用退出时强制终止所有子线程
        terminate_all_taskers()
        logging.info("应用已关闭。")
