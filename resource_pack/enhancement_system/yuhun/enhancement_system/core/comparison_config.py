"""
同类御魂对比配置

从 config/two_set_mapping.json 加载两件套标签映射，
支持「暴击两件套」等标签和具体御魂名称两种写法。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set


class ComparisonConfig:
    """同类御魂对比配置"""

    _instance: Optional["ComparisonConfig"] = None

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "two_set_mapping.json"

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.labels: Dict[str, List[str]] = data.get("labels", {})

    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> "ComparisonConfig":
        if cls._instance is None:
            cls._instance = ComparisonConfig(config_path)
        return cls._instance

    @classmethod
    def reload(cls, config_path: Optional[Path] = None) -> "ComparisonConfig":
        cls._instance = ComparisonConfig(config_path)
        return cls._instance

    def resolve_comparison_types(
        self,
        labels: List[str],
        default_equip: str,
    ) -> Set[str]:
        """
        解析同类御魂标签为御魂名称集合

        支持：
        - 两件套标签：如「暴击两件套」「暴击」
        - 具体御魂名称：如「破势」「针女」

        Args:
            labels: 路线配置中的同类御魂列表
            default_equip: 未配置或解析失败时的默认御魂类型

        Returns:
            参与排名对比的御魂名称集合
        """
        if not labels:
            return {default_equip}

        equip_types: Set[str] = set()

        for label in labels:
            mapped = self._resolve_label(label)
            if mapped:
                equip_types.update(mapped)
            else:
                equip_types.add(label)

        return equip_types or {default_equip}

    def _resolve_label(self, label: str) -> Optional[List[str]]:
        if label in self.labels:
            return self.labels[label]

        if label.endswith("两件套"):
            short = label.removesuffix("两件套")
            if short in self.labels:
                return self.labels[short]

        return None


def get_comparison_config() -> ComparisonConfig:
    return ComparisonConfig.get_instance()
