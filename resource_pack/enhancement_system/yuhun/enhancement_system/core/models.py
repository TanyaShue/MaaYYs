"""
御魂数据模型定义
"""
from dataclasses import dataclass, field, fields
from typing import List, Optional, Dict, Any


MAIN_ATTR_ALIASES = {
    "暴伤": "暴击伤害",
    "命中": "效果命中",
    "抵抗": "效果抵抗",
}


def normalize_main_attr(main_attr: str) -> str:
    """统一主属性名称（配置与御魂池可能使用不同写法）"""
    return MAIN_ATTR_ALIASES.get(main_attr, main_attr)


@dataclass
class Route:
    """评估路线"""
    路线名称: str
    有效属性: List[str]
    有效属性权重: List[float]
    说明: str = ""
    Top_N: int = 10
    属性阈值: float = 5.4
    同类御魂: List[str] = field(default_factory=list)

    def __post_init__(self):
        """确保权重列表长度与属性列表一致"""
        if len(self.有效属性权重) != len(self.有效属性):
            # 如果权重数量不匹配，用1填充
            self.有效属性权重 = [1.0] * len(self.有效属性)

    def get_weight_dict(self) -> Dict[str, float]:
        """获取属性->权重的字典"""
        return dict(zip(self.有效属性, self.有效属性权重))


def route_from_dict(data: Dict[str, Any]) -> Route:
    """从路线配置字典创建 Route，忽略未知字段"""
    known = {f.name for f in fields(Route)}
    return Route(**{k: v for k, v in data.items() if k in known})


@dataclass
class SubAttribute:
    """副属性"""
    类型: str  # 如"暴击"、"速度"、"攻击加成"等
    数值: str  # 格式化后的数值，如"5.4%"或"10.90"
    强化次数: int  # 该副属性被强化的次数
    等效强化次数: float  # 精确的等效次数

    def get_numeric_value(self) -> float:
        """获取数值的浮点数形式"""
        if '%' in self.数值:
            return float(self.数值.rstrip('%'))
        return float(self.数值)


@dataclass
class MainAttribute:
    """主属性"""
    类型: str  # 如"速度"、"攻击加成"、"暴击"等
    数值: str  # 格式化后的数值

    def get_numeric_value(self) -> float:
        """获取数值的浮点数形式"""
        if '%' in self.数值:
            return float(self.数值.rstrip('%'))
        return float(self.数值)


@dataclass
class Equip:
    """御魂"""
    位置: int  # 0-5
    类型: str  # 御魂套装名称，如"隐念"、"破势"
    品质: int  # 6=六星
    等级: int  # 0/3/6/9/12/15
    主属性: MainAttribute
    副属性: List[SubAttribute] = field(default_factory=list)

    # 缓存字段（运行时计算）
    _评分: Optional[float] = field(default=None, repr=False)
    _排名: Optional[int] = field(default=None, repr=False)

    def __post_init__(self):
        """确保主属性和副属性是正确的类型"""
        if isinstance(self.主属性, dict):
            self.主属性 = MainAttribute(**self.主属性)

        if self.副属性 and isinstance(self.副属性[0], dict):
            self.副属性 = [SubAttribute(**attr) for attr in self.副属性]

    @property
    def 副属性数量(self) -> int:
        """副属性条数（腿数）"""
        return len(self.副属性)

    @property
    def 是否满级(self) -> bool:
        """是否已强化到+15"""
        return self.等级 == 15

    def get_sub_attr_by_type(self, attr_type: str) -> Optional[SubAttribute]:
        """根据类型获取副属性"""
        for attr in self.副属性:
            if attr.类型 == attr_type:
                return attr
        return None


@dataclass
class EquipConfig:
    """御魂配置"""
    御魂名称: str
    两件套属性: str  # 如"攻击"、"生命加成"、"防御加成"
    两件套数值: Optional[str] = None
    四件套效果: Optional[str] = None
    使用说明: List[str] = field(default_factory=list)
    常用搭配: List[Dict[str, Any]] = field(default_factory=list)
    位置配置: Dict[str, Any] = field(default_factory=dict)
    使用举例: List[Dict[str, str]] = field(default_factory=list)

    def get_routes(self, position: int, main_attr: str) -> List[Route]:
        """
        获取指定位置和主属性下的推荐路线

        Args:
            position: 位置（0-5）
            main_attr: 主属性类型

        Returns:
            Route 对象列表
        """
        # 处理135号位
        if position in [0, 2, 4]:
            pos_key = "135号位"
        else:
            pos_key = f"{position + 1}号位"

        if pos_key not in self.位置配置:
            return []

        pos_config = self.位置配置[pos_key]

        # 135号位直接返回
        if position in [0, 2, 4]:
            routes_data = pos_config.get("推荐路线", [])
            return [route_from_dict(route) for route in routes_data]

        # 2/4/6号位需要匹配主属性
        if isinstance(pos_config, list):
            normalized = normalize_main_attr(main_attr)
            for config in pos_config:
                config_main = config.get("主属性")
                if config_main and normalize_main_attr(config_main) == normalized:
                    routes_data = config.get("推荐路线", [])
                    return [route_from_dict(route) for route in routes_data]

        return []


@dataclass
class EquipPool:
    """御魂池"""
    meta: Dict[str, Any]
    equips: List[Equip]

    def __post_init__(self):
        """确保equips是Equip对象列表"""
        if self.equips and isinstance(self.equips[0], dict):
            self.equips = [Equip(**eq) for eq in self.equips]

    def filter_by(self,
                  位置: Optional[int] = None,
                  类型: Optional[str] = None,
                  主属性类型: Optional[str] = None,
                  等级: Optional[int] = None) -> List[Equip]:
        """
        筛选御魂

        Args:
            位置: 位置筛选（0-5）
            类型: 套装类型筛选
            主属性类型: 主属性类型筛选
            等级: 等级筛选

        Returns:
            符合条件的御魂列表
        """
        result = self.equips

        if 位置 is not None:
            result = [eq for eq in result if eq.位置 == 位置]

        if 类型 is not None:
            result = [eq for eq in result if eq.类型 == 类型]

        if 主属性类型 is not None:
            result = [eq for eq in result if eq.主属性.类型 == 主属性类型]

        if 等级 is not None:
            result = [eq for eq in result if eq.等级 == 等级]

        return result
