# -*- coding: UTF-8 -*-
# app.py
import logging
from flask import Flask

from service.api.routes import tasker_bp, tasker_service_manager
from service.sercive_config import ServerConfig
from utils.common import _terminate_adb_processes


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

    # 注册蓝图
    app.register_blueprint(tasker_bp, url_prefix='/api/v1')

    # 注册清理函数
    # @app.teardown_appcontext
    # def cleanup(exception=None):
    #     tasker_manager.terminate_all()

    return app


def main():
    """主函数"""
    _terminate_adb_processes()
    config = ServerConfig.from_env()
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