# -*- coding: UTF-8 -*-
# app.py
import logging
import os

from flask import Flask
from src.service.api.routes import tasker_bp, tasker_service_manager
from src.service.sercive_config import ServerConfig
from src.utils.common import _terminate_adb_processes


def create_app(config: ServerConfig = None) -> Flask:
    """创建Flask应用"""
    if config is None:
        config = ServerConfig.from_env()

    app = Flask(__name__)

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # 仅显示错误级别的日志

    # 注册蓝图
    app.register_blueprint(tasker_bp, url_prefix='/api/v1')

    return app


def main():
    """主函数"""
    _terminate_adb_processes()

    # 从 JSON 文件加载配置
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, "assets", "config", "app_config.json")

    config = ServerConfig.from_json(config_path)

    app = create_app(config)

    try:
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug
        )
    except KeyboardInterrupt:
        logging.info("Application shutting down...")
    finally:
        tasker_service_manager.terminate_all()
        logging.info("Application terminated.")


if __name__ == "__main__":
    main()
