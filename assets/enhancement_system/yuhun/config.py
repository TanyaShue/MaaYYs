# This Python file uses the following encoding: utf-8
from pydantic import BaseModel, Field

from tasks.Component.config_scheduler import Scheduler
from tasks.Component.config_base import ConfigBase


class YuhunEnhanceConfig(BaseModel):
    """御魂批量强化任务配置。"""
    # 当前批次御魂默认套装（类型 OCR 未就绪时用配置代替）
    default_soul_set: str = Field(
        default="蝠翼",
        title="默认御魂类型",
        description="本批待强化御魂的套装名，与御魂数据目录中的 JSON 文件名一致",
    )
    # 御魂在背包中的位置 0-5 对应 1-6 号位（与 D:\Software\yys\resource\yuhun 一致）
    default_slot: int = Field(
        default=0,
        ge=0,
        le=5,
        title="默认号位",
        description="0=1号位 … 5=6号位",
    )
    # 当前批次御魂初始强化等级；每轮强化后 +3
    initial_level: int = Field(
        default=3,
        ge=0,
        le=15,
        title="初始强化等级",
        description="结果页流程按该等级开始，每次强化后增加 3 级",
    )
    # 交互测试：每步 OCR/识别后询问 y/n
    confirm_each_step: bool = Field(
        default=False,
        title="逐步确认识别",
        description="识别后等待输入 y/n；自动化运行时保持关闭",
    )


class Yuhun(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    enhance_config: YuhunEnhanceConfig = Field(default_factory=YuhunEnhanceConfig)
