"""
决策配置加载模块

从 config/decision_config.json 加载阶段概率阈值。
"""
import json
from pathlib import Path
from typing import Dict, Optional


class DecisionConfig:
    """决策配置单例"""

    _instance: Optional['DecisionConfig'] = None

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "decision_config.json"

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stage_thresholds: Dict[int, float] = {
            int(k): v for k, v in data["stage_thresholds"].items()
        }

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> 'DecisionConfig':
        if cls._instance is None:
            cls._instance = DecisionConfig(config_path)
        return cls._instance

    @classmethod
    def reload(cls, config_path: Optional[Path] = None) -> 'DecisionConfig':
        cls._instance = DecisionConfig(config_path)
        return cls._instance


def get_config() -> DecisionConfig:
    return DecisionConfig.get_instance()
