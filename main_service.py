import logging

import psutil
from flask import Flask, request, jsonify
from threading import Lock, Event
from typing import Dict
from src.utils.config_projects import Project, ProjectRunData
from src.core.tasker_thread import TaskerThread, _terminate_adb_processes

app = Flask(__name__)
taskers: Dict[str, TaskerThread] = {}
lock = Lock()
shutdown_event = Event()

def get_tasker(project_key: str):
    """查找并返回 tasker，如果不存在则返回 None"""
    return taskers.get(project_key)

def create_new_tasker(project_key: str, project: Project) -> TaskerThread:
    """创建新的 TaskerThread 并启动"""
    tasker = TaskerThread(project_key, project)
    tasker.start()
    taskers[project_key] = tasker
    return tasker


@app.route('/create_tasker', methods=['POST'])
def create_tasker():
    data = request.json
    project_key = data.get("project_key")
    project_data = data.get("project")

    if not project_key or not project_data:
        return jsonify({"status": "error", "message": "Invalid parameters."}), 400

    project = Project.from_json(project_data)

    with lock:
        if get_tasker(project_key):
            return jsonify({"status": "error", "message": "Tasker already exists."}), 400
        create_new_tasker(project_key, project)

    return jsonify({"status": "success", "message": f"Tasker {project_key} created."}), 200


@app.route('/')
def index():
    return 'Hello, Flask!'


@app.route('/send_task', methods=['POST'])
def send_task():
    data = request.json
    project_key = data.get("project_key")
    task_data = data.get("task").get("task")

    if not project_key or not task_data:
        return jsonify({"status": "error", "message": "Invalid parameters."}), 400

    with lock:
        tasker = get_tasker(project_key)
        if not tasker:
            return jsonify({"status": "error", "message": "Tasker not found."}), 404

        task = ProjectRunData.from_json(task_data) if isinstance(task_data, dict) else task_data
        tasker.send_task(task)

    return jsonify({"status": "success", "message": "Task sent."}), 200


@app.route('/terminate_tasker', methods=['POST'])
def terminate_tasker():
    data = request.json
    project_key = data.get("project_key")

    if not project_key:
        return jsonify({"status": "error", "message": "Invalid parameters."}), 400

    with lock:
        tasker = taskers.pop(project_key, None)
        if not tasker:
            return jsonify({"status": "error", "message": "Tasker not found."}), 404
        tasker.terminate()

    return jsonify({"status": "success", "message": f"Tasker {project_key} terminated."}), 200


@app.route('/tasker_status/<project_key>', methods=['GET'])
def tasker_status(project_key: str):
    """查询 Tasker 状态"""
    with lock:
        tasker = get_tasker(project_key)
        if not tasker:
            return jsonify({"status": "error", "message": "Tasker not found."}), 404
        return jsonify({"status": "success", "message": f"Tasker {project_key} is running."}), 200


def terminate_all_taskers():
    """优雅地终止所有 taskers"""
    logging.info("Terminating all taskers...")
    with lock:
        for project_key, tasker in taskers.items():
            logging.info(f"Terminating tasker {project_key}...")
            tasker.terminate()
    logging.info("Terminated")


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    try:
        _terminate_adb_processes()
        logging.info("Starting application...")
        app.run(host='localhost', port=54345, debug=False)
    except KeyboardInterrupt:
        logging.info("Application is shutting down...")
    finally:
        terminate_all_taskers()
        logging.info("Application has been terminated.")
