from flask import Flask, request, jsonify
import logging
from threading import Lock
from typing import Dict
from src.utils.config_projects import Project, ProjectRunData
from src.core.tasker_thread import TaskerThread

app = Flask(__name__)
taskers: Dict[str, TaskerThread] = {}
lock = Lock()

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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        app.run(host='localhost', port=54345, debug=True)
    except KeyboardInterrupt:
        logging.info("应用正在关闭...")
    finally:
        # 在此处添加任何清理代码，例如关闭数据库连接、停止后台线程等
        logging.info("应用已关闭。")