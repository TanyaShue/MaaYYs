# -*- coding: UTF-8 -*-
import logging
import os

from flask import Flask
from src.service.api.routes import tasker_bp, tasker_service_manager
from src.service.sercive_config import ServerConfig
from src.utils.common import _terminate_adb_processes
from src.service.scheduler.scheduler import scheduler

def create_app(config: ServerConfig = None) -> Flask:
    """创建Flask应用"""
    if config is None:
        config = ServerConfig.from_env()

    app = Flask(__name__)

    # # 添加调度器配置
    app.config.update(
        SCHEDULER_ENABLED=config.scheduler_enabled,
        SCHEDULER_TIMEZONE=config.scheduler_timezone,
        SCHEDULER_JOBS=config.scheduler_jobs
    )

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # 注册蓝图
    app.register_blueprint(tasker_bp, url_prefix='/api/v1')

    # 初始化调度器
    if config.scheduler_enabled:
        scheduler.init_app(app)

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
        if config.scheduler_enabled:
            scheduler.scheduler.shutdown()
        logging.info("Application terminated.")

if __name__ == "__main__":
    main()