"""
强化概率计算模块

使用概率树遍历（动态规划）精确计算御魂强化后达到指定评分的概率。
考虑roll值的均匀分布，使用scipy进行精确概率计算。
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from core.models import Equip, SubAttribute
from core.scoring import Scorer, ATTR_RANGE, ALL_SUB_ATTR_TYPES
import numpy as np
from scipy import stats


@dataclass(frozen=True)
class EnhanceState:
    """
    强化状态（不可变，用作字典key）

    每条副属性用 (类型, 强化次数) 表示。
    为了去重，副属性按类型排序存储。
    """
    sub_attrs: Tuple[Tuple[str, int], ...]

    @property
    def attr_count(self) -> int:
        return len(self.sub_attrs)

    def get_enhance_counts(self) -> List[int]:
        return [count for _, count in self.sub_attrs]

    def total_virtual_legs(self) -> int:
        return sum(count + 1 for _, count in self.sub_attrs)


def _make_state(attrs: List[Tuple[str, int]]) -> EnhanceState:
    """创建排序后的状态"""
    return EnhanceState(sub_attrs=tuple(sorted(attrs)))


def _add_attr_to_state(state: EnhanceState, new_type: str) -> EnhanceState:
    """向状态添加新副属性"""
    attrs = list(state.sub_attrs) + [(new_type, 0)]
    return _make_state(attrs)


def _enhance_attr_in_state(state: EnhanceState, index: int) -> EnhanceState:
    """强化状态中第index条副属性"""
    attrs = list(state.sub_attrs)
    attr_type, count = attrs[index]
    attrs[index] = (attr_type, count + 1)
    return _make_state(attrs)


class EnhancementCalculator:
    """强化概率计算器"""

    def __init__(self, scorer: Scorer, existing_types: Optional[List[str]] = None):
        """
        Args:
            scorer: 评分器
            existing_types: 当前御魂已有的副属性类型（用于排除新增时的重复）
        """
        self.scorer = scorer
        self.existing_types = set(existing_types or [])

    def calculate_probability_distribution(
        self,
        equip: Equip,
        target_level: int
    ) -> Dict[EnhanceState, float]:
        """
        计算从当前等级强化到目标等级的所有可能状态及概率

        Args:
            equip: 当前御魂
            target_level: 目标等级（3/6/9/12/15）

        Returns:
            状态->概率的字典
        """
        current_level = equip.等级
        if target_level <= current_level:
            return {}

        # 初始状态
        initial_attrs = [(attr.类型, attr.强化次数) for attr in equip.副属性]
        initial_state = _make_state(initial_attrs)
        state_probs: Dict[EnhanceState, float] = {initial_state: 1.0}

        # 逐步强化
        for level in range(current_level + 3, target_level + 1, 3):
            state_probs = self._step(state_probs, len(equip.副属性) < 4 and level <= current_level + 3 * (4 - len(equip.副属性)))

        return state_probs

    def _step(self, state_probs: Dict[EnhanceState, float], can_add_new: bool) -> Dict[EnhanceState, float]:
        """
        执行一步强化

        Args:
            state_probs: 当前状态概率分布
            can_add_new: 是否可能新增副属性（腿数<4时）

        Returns:
            新的状态概率分布
        """
        new_probs: Dict[EnhanceState, float] = {}

        for state, prob in state_probs.items():
            if prob < 1e-10:
                continue

            if state.attr_count < 4:
                # 新增副属性：从11种中均匀抽取
                p_each = prob / 11.0
                for attr_type in ALL_SUB_ATTR_TYPES:
                    # 检查是否已存在该类型
                    existing = set(t for t, _ in state.sub_attrs)
                    if attr_type in existing:
                        # 已有该类型则视为强化该属性
                        for i, (t, c) in enumerate(state.sub_attrs):
                            if t == attr_type:
                                new_state = _enhance_attr_in_state(state, i)
                                new_probs[new_state] = new_probs.get(new_state, 0) + p_each
                                break
                    else:
                        new_state = _add_attr_to_state(state, attr_type)
                        new_probs[new_state] = new_probs.get(new_state, 0) + p_each
            else:
                # 4条副属性：按虚拟腿池概率强化
                total_legs = state.total_virtual_legs()
                for i, (attr_type, count) in enumerate(state.sub_attrs):
                    p_select = (count + 1) / total_legs
                    new_state = _enhance_attr_in_state(state, i)
                    new_probs[new_state] = new_probs.get(new_state, 0) + prob * p_select

        return new_probs

    def calculate_score_distribution(
        self,
        equip: Equip,
        target_level: int
    ) -> List[Tuple[float, float]]:
        """
        计算强化到目标等级后的评分概率分布

        Args:
            equip: 当前御魂
            target_level: 目标等级

        Returns:
            (评分, 概率) 列表，按评分降序排列
        """
        state_probs = self.calculate_probability_distribution(equip, target_level)

        # 将状态转换为评分
        score_probs: Dict[float, float] = {}
        for state, prob in state_probs.items():
            score = self._state_to_score(state)
            # 四舍五入到0.01避免浮点精度问题
            score = round(score, 2)
            score_probs[score] = score_probs.get(score, 0) + prob

        result = [(score, prob) for score, prob in score_probs.items()]
        result.sort(key=lambda x: x[0], reverse=True)
        return result

    def calculate_top_n_probability(
        self,
        equip: Equip,
        target_level: int,
        threshold_score: float
    ) -> float:
        """
        计算强化到目标等级后评分超过阈值的概率

        使用全概率公式：
        P(评分 ≥ 阈值) = Σ P(状态路径i) × P(评分 ≥ 阈值 | 状态路径i)

        对每个状态路径，用scipy计算其评分分布（考虑roll的均匀随机性）

        Args:
            equip: 当前御魂
            target_level: 目标等级
            threshold_score: 阈值评分

        Returns:
            超过阈值的概率
        """
        # 1. 枚举所有状态路径及其概率
        state_probs = self.calculate_probability_distribution(equip, target_level)

        # 2. 对每个状态，计算其达到阈值的概率
        total_prob = 0.0
        for state, state_prob in state_probs.items():
            # 计算该状态下评分 ≥ 阈值的概率
            prob_exceed = self._calculate_state_exceed_probability(equip, state, threshold_score)
            total_prob += state_prob * prob_exceed

        return total_prob

    def _calculate_state_exceed_probability(
        self,
        equip: Equip,
        state: EnhanceState,
        threshold_score: float
    ) -> float:
        """
        计算给定状态下评分超过阈值的概率

        状态确定了每条属性被强化的次数，但每次强化的roll值是随机的。
        初始值是确定的（从equip中获取），只有未来的强化是随机的。

        评分 = Σ(适配属性的等效次数)
        等效次数 = 初始等效（确定） + Σ 强化roll（随机）

        Args:
            equip: 当前御魂（包含初始等效值）
            state: 强化状态（确定了每条属性的强化次数）
            threshold_score: 阈值评分

        Returns:
            P(评分 ≥ 阈值 | 状态)
        """
        # 构建评分的随机变量
        # 评分 = Σ (初始等效 + 强化次数 × roll均值) × 权重 + 随机项
        # 随机项 = Σ 权重 × Σ(roll - 均值)

        # 分离确定项和随机项
        # 评分 = Σ(适配属性的等效次数)
        # 等效次数 = (初始roll + Σ强化roll) / 最大值
        # 其中每个roll ~ Uniform(0.8, 1.0) × 最大值
        # 归一化后：等效次数 = 初始等效 + Σ强化等效
        # 其中每个等效 ~ Uniform(0.8, 1.0)

        # 构建当前御魂的初始等效值映射
        initial_equiv_map = {}
        for attr in equip.副属性:
            initial_equiv_map[attr.类型] = attr.等效强化次数

        # 计算确定的评分（初始值）和随机的强化次数
        deterministic_score = 0.0  # 来自初始值的确定评分
        future_enhancements = 0    # 未来强化的总次数（随机部分）

        for attr_type, enhance_count in state.sub_attrs:
            # 只计算适配属性
            if attr_type not in self.scorer.compatible_attrs:
                continue

            # 获取初始等效值（确定）
            initial_equiv = initial_equiv_map.get(attr_type, 0.0)
            deterministic_score += initial_equiv

            # 计算未来强化次数（相对于当前）
            current_enhance_count = 0
            for attr in equip.副属性:
                if attr.类型 == attr_type:
                    current_enhance_count = attr.强化次数
                    break

            future_enhance_count = enhance_count - current_enhance_count
            if future_enhance_count > 0:
                future_enhancements += future_enhance_count

        # 如果没有未来强化，评分是确定的
        if future_enhancements == 0:
            return 1.0 if deterministic_score >= threshold_score else 0.0

        # 未来强化的评分 = Σ roll_i，其中 roll_i ~ Uniform(0.8, 1.0)
        # 变换：roll_i = 0.8 + 0.2 × U_i，U_i ~ Uniform(0, 1)
        # 未来评分 = 0.8n + 0.2 × Σ U_i
        # Σ U_i ~ Irwin-Hall(n)

        # 需要 总评分 ≥ threshold
        # 即 deterministic_score + 0.8n + 0.2 × Σ U_i ≥ threshold
        # 即 Σ U_i ≥ (threshold - deterministic_score - 0.8n) / 0.2

        base_score = deterministic_score + 0.8 * future_enhancements
        required_sum = (threshold_score - base_score) / 0.2

        # P(Σ U_i ≥ required_sum) 其中 Σ U_i ~ Irwin-Hall(n)

        if future_enhancements <= 20:
            # 使用精确的 Irwin-Hall CDF
            prob = self._irwin_hall_sf(required_sum, future_enhancements)
        else:
            # 大n时用正态近似
            mean = future_enhancements * 0.5
            var = future_enhancements / 12.0
            std = np.sqrt(var)
            z = (required_sum - mean) / std
            prob = 1.0 - stats.norm.cdf(z)

        return prob

    def _irwin_hall_sf(self, x: float, n: int) -> float:
        """
        计算Irwin-Hall分布的生存函数 P(X ≥ x)

        X = U1 + U2 + ... + Un，其中 Ui ~ Uniform(0, 1)

        Args:
            x: 阈值
            n: 均匀分布的个数

        Returns:
            P(X ≥ x)
        """
        # 边界情况
        if x <= 0:
            return 1.0
        if x >= n:
            return 0.0

        # Irwin-Hall CDF 的精确公式（分段多项式）
        # CDF(x) = (1/n!) × Σ_{k=0}^{floor(x)} (-1)^k × C(n,k) × (x-k)^n
        # SF(x) = 1 - CDF(x)

        from math import comb, factorial

        cdf = 0.0
        floor_x = int(np.floor(x))

        for k in range(floor_x + 1):
            term = ((-1) ** k) * comb(n, k) * ((x - k) ** n)
            cdf += term

        cdf /= factorial(n)

        return 1.0 - cdf

    def _state_to_score(self, state: EnhanceState) -> float:
        """
        将状态转换为评分（使用期望值）

        等效次数 = 总数值 / 最大值
        总数值 = 初始roll + Σ强化roll
        期望等效 = (初始期望 + 强化次数 × 强化期望) / 最大值
                = (0.9 × 最大值 + 强化次数 × 0.9 × 最大值) / 最大值
                = 0.9 × (1 + 强化次数)
        """
        sub_attrs = []
        for attr_type, enhance_count in state.sub_attrs:
            # 期望等效次数 = 0.9 × (初始1次 + 强化次数)
            equiv = 0.9 * (1 + enhance_count)

            sub_attrs.append(SubAttribute(
                类型=attr_type,
                数值="",
                强化次数=enhance_count,
                等效强化次数=equiv
            ))

        return self.scorer.score_sub_attrs_only(sub_attrs)

    def estimate_max_score_at_level(self, equip: Equip, target_level: int) -> float:
        """估算强化到目标等级的最高可能评分"""
        score_dist = self.calculate_score_distribution(equip, target_level)
        if score_dist:
            return score_dist[0][0]
        return 0.0

    def estimate_expected_score(self, equip: Equip, target_level: int) -> float:
        """估算强化到目标等级的期望评分"""
        score_dist = self.calculate_score_distribution(equip, target_level)
        return sum(score * prob for score, prob in score_dist)
