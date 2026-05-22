"""
决策引擎

根据当前御魂状态、评分、概率计算，输出强化决策。
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from core.models import Equip, EquipConfig, EquipPool, Route
from core.scoring import Scorer, create_scorer_for_route
from core.enhancement_calculator import EnhancementCalculator
from core.ranking import RankingEngine
from core.data_loader import DataLoader
from core.decision_config import get_config


@dataclass
class Decision:
    """决策结果"""
    action: str  # "继续强化" / "弃置" / "保留"
    confidence: float
    reason: str
    current_score: float
    threshold_score: float
    top_n: int
    top_scores: Optional[List[str]] = None
    route_name: Optional[str] = None
    current_rank: Optional[int] = None
    total_count: Optional[int] = None
    probability: Optional[float] = None
    stage_threshold: Optional[float] = None


class DecisionEngine:
    """决策引擎"""

    def __init__(self, pool: EquipPool, loader: DataLoader):
        """
        Args:
            pool: 御魂池
            loader: 数据加载器
        """
        self.pool = pool
        self.loader = loader
        self.ranking_engine = RankingEngine(pool, loader)

    def evaluate(self, equip: Equip, config: EquipConfig) -> Decision:
        """
        评估御魂是否值得继续强化

        Args:
            equip: 当前御魂
            config: 御魂配置

        Returns:
            Decision对象
        """
        routes = config.get_routes(equip.位置, equip.主属性.类型)

        if not routes:
            return Decision(
                action="弃置",
                confidence=1.0,
                reason="未找到该位置和主属性的推荐配置",
                current_score=0,
                threshold_score=0,
                top_n=0,
                top_scores=None
            )

        if len(routes) == 1:
            return self._evaluate_single_route(equip, config, routes[0])
        else:
            return self._evaluate_multi_route(equip, config, routes)

    def _evaluate_multi_route(
        self, equip: Equip, config: EquipConfig, routes: List[Route]
    ) -> Decision:
        """多路线评估：任一路线通过即继续强化"""
        best_decision = None
        best_probability = -1.0

        for route in routes:
            decision = self._evaluate_single_route(equip, config, route)
            if decision.action in ("继续强化", "保留"):
                return decision

            prob = decision.probability if decision.probability is not None else 0.0
            if prob > best_probability:
                best_probability = prob
                best_decision = decision

        best_decision.reason = f"[多路线] {best_decision.reason}"
        return best_decision

    def _evaluate_single_route(
        self, equip: Equip, config: EquipConfig, route: Route
    ) -> Decision:
        """单路线评估"""
        scorer = create_scorer_for_route(route)
        current_score = scorer.score(equip)

        threshold_score, top_n, ranking = self.ranking_engine.get_top_n_threshold_for_route(
            equip, config, route
        )
        top_scores = self._build_top_scores(route, ranking[:top_n])

        min_score = route.属性阈值
        min_score_active = min_score >= threshold_score

        if equip.是否满级:
            decision = self._decide_at_max_level(
                equip, scorer, current_score, threshold_score, top_n, ranking,
                min_score_active=min_score_active, min_score=min_score
            )
        else:
            decision = self._decide_during_enhancement(
                equip, scorer, current_score, threshold_score, top_n, route,
                min_score_active=min_score_active, min_score=min_score
            )

        decision.top_scores = top_scores
        decision.route_name = route.路线名称
        return decision

    @staticmethod
    def _build_top_scores(
        route: Route,
        ranking_slice: List[Tuple[Equip, float]]
    ) -> List[str]:
        """构建Top N展示值（单属性路线显示原始数值）"""
        if len(route.有效属性) == 1:
            attr_type = route.有效属性[0]
            values = []
            for equip, _ in ranking_slice:
                attr = equip.get_sub_attr_by_type(attr_type)
                values.append(attr.数值 if attr else "0")
            return values

        return [f"{score:.1f}" for _, score in ranking_slice]

    def _decide_at_max_level(
        self,
        equip: Equip,
        scorer: Scorer,
        current_score: float,
        threshold_score: float,
        top_n: int,
        ranking: List[Tuple[Equip, float]],
        min_score_active: bool = False,
        min_score: float = 0.0
    ) -> Decision:
        """+15满级时的决策"""
        rank = 1
        for _, score in ranking:
            if score > current_score:
                rank += 1
            else:
                break

        total = len(ranking)
        threshold_hint = f"（最低分数{min_score:.1f}）" if min_score_active else ""

        if current_score >= threshold_score:
            return Decision(
                action="保留",
                confidence=1.0,
                reason=f"评分{current_score:.1f}，排名第{rank}/{total}，进入Top {top_n}{threshold_hint}",
                current_score=current_score,
                threshold_score=threshold_score,
                top_n=top_n,
                current_rank=rank,
                total_count=total
            )
        else:
            return Decision(
                action="弃置",
                confidence=1.0,
                reason=f"评分{current_score:.1f}，排名第{rank}/{total}，未进入Top {top_n}（阈值{threshold_score:.1f}）{threshold_hint}",
                current_score=current_score,
                threshold_score=threshold_score,
                top_n=top_n,
                current_rank=rank,
                total_count=total
            )

    def _decide_during_enhancement(
        self,
        equip: Equip,
        scorer: Scorer,
        current_score: float,
        threshold_score: float,
        top_n: int,
        route: Route,
        min_score_active: bool = False,
        min_score: float = 0.0
    ) -> Decision:
        """强化过程中的决策"""
        next_level = equip.等级 + 3
        stage_threshold = get_config().stage_thresholds.get(next_level, 0.30)

        calc = EnhancementCalculator(scorer)
        probability = calc.calculate_top_n_probability(equip, 15, threshold_score)

        threshold_hint = f"，最低分数{min_score:.1f}" if min_score_active else ""

        if probability >= stage_threshold:
            return Decision(
                action="继续强化",
                confidence=probability,
                reason=f"+{equip.等级}->+15达到Top {top_n}的概率为{probability*100:.1f}%，"
                       f"超过阶段阈值{stage_threshold*100:.0f}%{threshold_hint}",
                current_score=current_score,
                threshold_score=threshold_score,
                top_n=top_n,
                probability=probability,
                stage_threshold=stage_threshold
            )
        else:
            return Decision(
                action="弃置",
                confidence=1 - probability,
                reason=f"+{equip.等级}->+15达到Top {top_n}的概率为{probability*100:.1f}%，"
                       f"低于阶段阈值{stage_threshold*100:.0f}%{threshold_hint}",
                current_score=current_score,
                threshold_score=threshold_score,
                top_n=top_n,
                probability=probability,
                stage_threshold=stage_threshold
            )

    def batch_evaluate(
        self,
        equips: List[Equip],
        config: EquipConfig
    ) -> List[Tuple[Equip, Decision]]:
        """批量评估御魂"""
        return [(eq, self.evaluate(eq, config)) for eq in equips]
