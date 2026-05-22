"""
评分计算模块

基于等效强化次数的御魂评分系统，支持属性权重。
"""
from typing import List, Set, Optional, Dict
from core.models import Equip, SubAttribute


# 副属性单次强化范围（最小值，最大值）
ATTR_RANGE = {
    "攻击": (21.6, 27.0),
    "生命": (91.2, 114.0),
    "防御": (4.0, 5.0),
    "防御加成": (0.024, 0.03),
    "暴击": (0.024, 0.03),
    "攻击加成": (0.024, 0.03),
    "生命加成": (0.024, 0.03),
    "速度": (2.4, 3.0),
    "效果抵抗": (0.032, 0.04),
    "效果命中": (0.032, 0.04),
    "暴击伤害": (0.032, 0.04),
}

ALL_SUB_ATTR_TYPES = list(ATTR_RANGE.keys())


class Scorer:
    """御魂评分器"""

    def __init__(self, compatible_attrs: Set[str], weights: Optional[Dict[str, float]] = None):
        """
        Args:
            compatible_attrs: 适配属性集合
            weights: 属性权重字典，默认所有属性权重为1.0
        """
        self.compatible_attrs = compatible_attrs
        self.weights = weights or {attr: 1.0 for attr in compatible_attrs}

    def score(self, equip: Equip) -> float:
        """
        计算御魂综合评分

        评分 = Σ(适配属性等效次数 × 权重)

        Args:
            equip: 御魂对象

        Returns:
            评分值（加权等效强化次数）
        """
        score = 0.0
        for attr in equip.副属性:
            if attr.类型 in self.compatible_attrs:
                weight = self.weights.get(attr.类型, 1.0)
                score += attr.等效强化次数 * weight
        return score

    def score_sub_attrs_only(self, sub_attrs: List[SubAttribute]) -> float:
        """
        仅对副属性列表评分（用于概率计算中的中间状态评估）

        Args:
            sub_attrs: 副属性列表

        Returns:
            评分值（加权等效强化次数）
        """
        score = 0.0
        for attr in sub_attrs:
            if attr.类型 in self.compatible_attrs:
                weight = self.weights.get(attr.类型, 1.0)
                score += attr.等效强化次数 * weight
        return score


def create_scorer_for_route(route) -> Scorer:
    """
    根据Route对象创建评分器

    Args:
        route: Route对象（来自models.Route）

    Returns:
        Scorer实例
    """
    compatible_attrs = set(route.有效属性)
    weights = route.get_weight_dict()
    return Scorer(compatible_attrs, weights)


def calculate_equivalent_enhancement(attr_type: str, value: float) -> float:
    """
    计算等效强化次数

    等效强化次数 = 当前数值 / 最大值（每次强化的最大增量）

    Args:
        attr_type: 属性类型
        value: 当前数值（百分比属性传入小数形式，如3%传入0.03）

    Returns:
        等效强化次数
    """
    if attr_type not in ATTR_RANGE:
        return 0.0

    _, max_val = ATTR_RANGE[attr_type]
    return value / max_val
