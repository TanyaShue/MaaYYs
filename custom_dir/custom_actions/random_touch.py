# -*- coding: UTF-8 -*-
from maa.context import Context
from maa.custom_action import CustomAction
import random

from app.models.logging.log_manager import log_manager


class RandomTouch(CustomAction):
    def run(self,
            context: Context,
            argv: CustomAction.RunArg, ) -> bool:
        logger = log_manager.get_context_logger(context)
        logger.debug("开始执行自定义动作：随机点击")
        x, y, w, h = argv.box.x, argv.box.y, argv.box.w, argv.box.h
        center_x = x + w / 2
        center_y = y + h / 2
        random_x = random.gauss(center_x, w / 6)
        random_y = random.gauss(center_y, h / 6)
        random_x = min(max(random_x, x), x + w)
        random_y = min(max(random_y, y), y + h)
        context.tasker.controller.post_click(round(random_x), round(random_y)).wait()
        logger.debug(f"随机生成的点: {random_x, random_y}")
        return True

    def stop(self) -> None:
        pass
