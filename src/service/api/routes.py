# -*- coding: UTF-8 -*-
from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Callable
import logging

from src.service.exceptions import TaskerValidationError, TaskerNotFoundError, TaskerError
from src.service.tasker import TaskLogger
from src.service.tasker_service_manager import TaskerServiceManager
from src.utils.config_projects import Project

logger = logging.getLogger(__name__)
tasker_bp = Blueprint('tasker', __name__)
tasker_service_manager = TaskerServiceManager()


def handle_exceptions(f: Callable):
    """异常处理装饰器"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except TaskerValidationError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except TaskerNotFoundError as e:
            return jsonify({"status": "error", "message": str(e)}), 404
        except TaskerError as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    return wrapper


@tasker_bp.route('/create_tasker', methods=['POST'])
@handle_exceptions
def create_tasker():
    """创建Tasker路由"""
    data = request.json
    project_key = data.get("project_key")
    project_data = data.get("project")
    project_resource_path=data.get("resource_path")
    project = Project.from_json(project_data)
    tasker_service_manager.create_tasker(project_key, project,project_resource_path)
    return jsonify({
        "status_code": 200,
        "status": "success",
        "message": f"Tasker {project_key} created successfully"
    })


@tasker_bp.route('/send_task', methods=['POST'])
@handle_exceptions
def send_task():
    """发送任务路由"""
    data = request.json
    project_key = data.get("project_key")
    task_data = data.get("task", {})

    tasker_service_manager.send_task(project_key, task_data)
    return jsonify({
        "status_code": 200,
        "status": "success",
        "message": "Task sent successfully"
    })


@tasker_bp.route('/terminate_tasker', methods=['POST'])
@handle_exceptions
def terminate_tasker():
    """终止Tasker路由"""
    data = request.json
    project_key = data.get("project_key")

    tasker_service_manager.terminate_tasker(project_key)
    return jsonify({
        "status_code": 200,
        "status": "success",
        "message": f"Tasker {project_key} terminated successfully"
    })


@tasker_bp.route('/tasker_status/<project_key>', methods=['GET'])
@handle_exceptions
def get_tasker_status(project_key: str):
    """获取Tasker状态路由"""
    state = tasker_service_manager.get_status(project_key)
    return jsonify({
        "status_code": 200,
        "status": "success",
        "data": {
            "status": state.status.value,
            "created_at": state.created_at.isoformat(),
            "last_active": state.last_active.isoformat(),
            "error": state.error,
            "current_task": state.current_task
        }
    })
@tasker_bp.route('/get_all_devices', methods=['POST'])
@handle_exceptions
def get_all_devices():
    """获取Tasker状态路由"""
    devices = tasker_service_manager.get_all_devices()
    return jsonify({
        "status_code": 200,
        "status": "success",
        "data": {
            "devices": devices
        }
    })

@tasker_bp.route('/tasker_loger/<project_key>', methods=['GET'])
@handle_exceptions
def get_tasker_loger(project_key: str):
    """获取Tasker日志"""
    log = tasker_service_manager(project_key)
    return jsonify({
        "status_code": 200,
        "status": "success",
        "data": {
            "log": log
        }
    })
@tasker_bp.route('/tasker_all_log', methods=['GET'])
@handle_exceptions
def get_tasker_all_loger():
    """获取Tasker日志"""
    log=TaskLogger().get_all_logs()
    TaskLogger().clear_logs()
    return jsonify({
        "status_code": 200,
        "status": "success",
        "data": {
            "log": log
        }
    })