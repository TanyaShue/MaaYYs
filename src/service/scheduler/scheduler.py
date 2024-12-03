# -*- coding: UTF-8 -*-
from flask_apscheduler import APScheduler
from flask import Flask
import logging
import importlib
from typing import Optional


class TaskScheduler:
    def __init__(self):
        self.scheduler = APScheduler()
        self.logger = logging.getLogger(__name__)

    def init_app(self, app: Flask) -> None:
        """初始化调度器"""
        # 配置调度器
        app.config.update(
            SCHEDULER_API_ENABLED=True,
            SCHEDULER_TIMEZONE=app.config['SCHEDULER_TIMEZONE']
        )
        # 初始化调度器
        self.scheduler.init_app(app)

        # 如果启用了调度器，添加预定义的任务(scheduler初始化会自动添加任务)
        # if app.config['SCHEDULER_ENABLED']:
        #     self._add_scheduled_jobs(app.config['SCHEDULER_JOBS'])

        # 启动调度器
        self.scheduler.start()
        self.logger.info("Scheduler started")

    def _import_function(self, func_path: str):
        """导入函数"""
        try:
            module_path, func_name = func_path.rsplit(':', 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        except Exception as e:
            self.logger.error(f"Error importing function {func_path}: {str(e)}")
            raise

    def _add_scheduled_jobs(self, jobs_config: dict) -> None:
        """添加预定义的调度任务"""
        for job_id, job_config in jobs_config.items():
            try:
                # 获取函数路径并导入
                func_path = job_config.pop('func')
                func = self._import_function(func_path)

                # 添加任务
                self.scheduler.add_job(
                    id=job_id,
                    func=func,  # 使用导入的函数而不是字符串路径
                    **job_config
                )
                self.logger.info(f"Added scheduled job: {job_id}")
            except Exception as e:
                self.logger.error(f"Failed to add job {job_id}: {str(e)}")

    def add_job(self, job_id: str, **job_kwargs) -> None:
        """添加新的调度任务"""
        try:
            if 'func' in job_kwargs and isinstance(job_kwargs['func'], str):
                job_kwargs['func'] = self._import_function(job_kwargs['func'])
            self.scheduler.add_job(id=job_id, **job_kwargs)
            self.logger.info(f"Added new job: {job_id}")
        except Exception as e:
            self.logger.error(f"Failed to add job {job_id}: {str(e)}")
            raise

    def remove_job(self, job_id: str) -> None:
        """移除调度任务"""
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job: {job_id}")
        except Exception as e:
            self.logger.error(f"Failed to remove job {job_id}: {str(e)}")
            raise


scheduler = TaskScheduler()