"""
数据加载模块
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.models import EquipPool, EquipConfig
from core.scoring import ATTR_RANGE

INDENT_STR = "    "


def _is_primitive_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, (str, int, float, bool)) or item is None
        for item in value
    )


def _format_json_compact_lists(obj: Any, indent: int = 0) -> str:
    """JSON 格式化：4 空格缩进，基础类型数组单行"""
    spacing = INDENT_STR * indent
    inner_spacing = INDENT_STR * (indent + 1)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = ["{"]
        items = list(obj.items())
        for index, (key, value) in enumerate(items):
            comma = "," if index < len(items) - 1 else ""
            key_text = json.dumps(key, ensure_ascii=False)
            lines.append(
                f"{inner_spacing}{key_text}: {_format_json_compact_lists(value, indent + 1)}{comma}"
            )
        lines.append(f"{spacing}" + "}")
        return "\n".join(lines)

    if isinstance(obj, list):
        if not obj:
            return "[]"
        if _is_primitive_list(obj):
            return json.dumps(obj, ensure_ascii=False)
        lines = ["["]
        for index, item in enumerate(obj):
            comma = "," if index < len(obj) - 1 else ""
            lines.append(f"{inner_spacing}{_format_json_compact_lists(item, indent + 1)}{comma}")
        lines.append(f"{spacing}]")
        return "\n".join(lines)

    return json.dumps(obj, ensure_ascii=False)


class DataLoader:
    """数据加载器"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化数据加载器

        Args:
            base_path: 基础路径，默认为当前文件的上级目录的上级目录（项目根目录）
        """
        if base_path is None:
            # 从 enhancement_system/core/data_loader.py 向上两级到项目根目录
            base_path = Path(__file__).parent.parent.parent
        self.base_path = Path(base_path)
        self.yuhun_data_path = self.base_path / "御魂数据"
        self.export_path = self.base_path / "yys_export"

    def load_equip_pool(self, filename: str = "ios.json") -> EquipPool:
        """
        加载御魂池数据

        Args:
            filename: 文件名，默认为ios.json

        Returns:
            EquipPool对象
        """
        file_path = self.export_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"御魂池文件不存在: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pool = EquipPool(**data)
        self._normalize_equivalent_scores(pool)
        return pool

    def load_equip_config(self, equip_name: str) -> Optional[EquipConfig]:
        """
        加载指定御魂的配置

        Args:
            equip_name: 御魂名称，如"隐念"

        Returns:
            EquipConfig对象，如果找不到返回None
        """
        # 遍历御魂数据目录下的所有子目录
        for category_dir in self.yuhun_data_path.iterdir():
            if not category_dir.is_dir():
                continue

            config_file = category_dir / f"{equip_name}.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return EquipConfig(**data)

        return None

    def build_two_set_mapping(self) -> Dict[str, List[str]]:
        """
        从御魂配置构建两件套属性 -> 御魂名称列表（用于生成 config/two_set_mapping.json）

        Returns:
            如 {"暴击": ["破势", "针女", ...], "攻击加成": [...]}
        """
        mapping: Dict[str, List[str]] = {}
        for config in self.load_all_equip_configs().values():
            two_set = config.两件套属性
            if two_set not in mapping:
                mapping[two_set] = []
            mapping[two_set].append(config.御魂名称)
        return mapping

    @staticmethod
    def export_two_set_mapping_json(output_path: Optional[Path] = None) -> Path:
        """根据当前御魂配置重新生成两件套映射 JSON"""
        loader = DataLoader()
        mapping = loader.build_two_set_mapping()

        labels: Dict[str, List[str]] = {}
        for attr, names in sorted(mapping.items()):
            sorted_names = sorted(names)
            labels[f"{attr}两件套"] = sorted_names
            labels[attr] = sorted_names

        if output_path is None:
            output_path = Path(__file__).parent.parent / "config" / "two_set_mapping.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = _format_json_compact_lists({"labels": labels}) + "\n"
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def load_all_equip_configs(self) -> Dict[str, EquipConfig]:
        """
        加载所有御魂配置

        Returns:
            字典，key为御魂名称，value为EquipConfig对象
        """
        configs = {}

        for category_dir in self.yuhun_data_path.iterdir():
            if not category_dir.is_dir():
                continue

            for config_file in category_dir.glob("*.json"):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = EquipConfig(**data)
                    configs[config.御魂名称] = config

        return configs

    @staticmethod
    def _normalize_equivalent_scores(pool: EquipPool) -> None:
        """用单次最大值重新计算等效强化次数"""
        for equip in pool.equips:
            for attr in equip.副属性:
                if attr.类型 not in ATTR_RANGE:
                    continue
                _, max_val = ATTR_RANGE[attr.类型]
                numeric = attr.get_numeric_value()
                if '%' in attr.数值:
                    numeric /= 100
                attr.等效强化次数 = round(numeric / max_val, 2)


# 全局单例
_loader_instance: Optional[DataLoader] = None


def get_loader(base_path: Optional[Path] = None) -> DataLoader:
    """
    获取全局DataLoader实例

    Args:
        base_path: 基础路径

    Returns:
        DataLoader实例
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader(base_path)
    return _loader_instance
