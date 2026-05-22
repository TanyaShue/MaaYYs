"""
排名对比模块

对已有御魂池中的御魂进行评分排名，获取Top N阈值。
"""
from typing import List, Tuple, Set
from core.models import Equip, EquipPool, EquipConfig, Route
from core.scoring import create_scorer_for_route
from core.comparison_config import get_comparison_config


class RankingEngine:
    """排名引擎"""

    def __init__(self, pool: EquipPool, loader=None):
        self.pool = pool
        self.loader = loader
        self._comparison_config = get_comparison_config()

    def _resolve_comparison_types(
        self,
        equip: Equip,
        route: Route,
    ) -> Set[str]:
        """解析排名对比范围：默认同套装，同类御魂则跨套装或指定御魂"""
        return self._comparison_config.resolve_comparison_types(
            route.同类御魂,
            equip.类型,
        )

    def get_top_n_threshold_for_route(
        self,
        equip: Equip,
        config: EquipConfig,
        route: Route
    ) -> Tuple[float, int, List[Tuple[Equip, float]]]:
        """
        获取指定路线的Top N阈值评分

        Args:
            equip: 当前御魂
            config: 御魂配置
            route: 评估路线

        Returns:
            (阈值评分, Top N值, 完整排名列表)
        """
        scorer = create_scorer_for_route(route)
        top_n = route.Top_N
        min_score = route.属性阈值
        comparison_types = self._resolve_comparison_types(equip, route)

        filtered = [
            eq for eq in self.pool.equips
            if eq.位置 == equip.位置
            and eq.主属性.类型 == equip.主属性.类型
            and eq.类型 in comparison_types
        ]
        scored = [(eq, scorer.score(eq)) for eq in filtered]
        scored.sort(key=lambda x: x[1], reverse=True)

        if len(scored) >= top_n:
            threshold = scored[top_n - 1][1]
        elif scored:
            threshold = scored[-1][1]
        else:
            threshold = 0.0

        threshold = max(threshold, min_score)

        return threshold, top_n, scored
