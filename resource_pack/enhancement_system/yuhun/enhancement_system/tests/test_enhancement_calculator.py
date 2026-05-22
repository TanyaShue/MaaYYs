"""
单元测试 - 强化概率计算模块
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhancement_calculator import EnhancementCalculator, EnhanceState
from core.scoring import Scorer, create_scorer_for_route
from core.models import Equip, MainAttribute, SubAttribute, Route


def test_4leg_one_step():
    """测试4腿御魂单步强化概率"""
    print("=" * 60)
    print("测试1: 4腿御魂单步强化")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    calc = EnhancementCalculator(scorer)
    state_probs = calc.calculate_probability_distribution(equip, 3)

    print(f"  初始: 4腿全适配, 等级+0 -> +3")
    print(f"  可能状态数: {len(state_probs)}")
    total_prob = sum(state_probs.values())
    print(f"  概率总和: {total_prob:.6f} (应为1.0)")

    # 4腿各1/4概率被强化
    print(f"\n  各状态概率:")
    for state, prob in sorted(state_probs.items(), key=lambda x: -x[1]):
        attrs_str = ", ".join(f"{t}(+{c})" for t, c in state.sub_attrs)
        print(f"    P={prob:.4f}: {attrs_str}")

    assert abs(total_prob - 1.0) < 1e-6, f"概率总和不为1: {total_prob}"
    print(f"\n[OK] 概率总和验证通过")
    print()


def test_3leg_one_step():
    """测试3腿御魂单步强化（新增副属性）"""
    print("=" * 60)
    print("测试2: 3腿御魂单步强化（新增副属性）")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    calc = EnhancementCalculator(scorer)
    state_probs = calc.calculate_probability_distribution(equip, 3)

    print(f"  初始: 3腿, 等级+0 -> +3")
    print(f"  可能状态数: {len(state_probs)}")
    total_prob = sum(state_probs.values())
    print(f"  概率总和: {total_prob:.6f}")

    # 应该有11种可能（新增11种属性之一）
    # 其中3种已有的会变成强化
    print(f"\n  部分状态:")
    for state, prob in sorted(state_probs.items(), key=lambda x: -x[1])[:5]:
        attrs_str = ", ".join(f"{t}(+{c})" for t, c in state.sub_attrs)
        print(f"    P={prob:.4f}: {attrs_str}")

    assert abs(total_prob - 1.0) < 1e-6
    print(f"\n[OK] 概率总和验证通过")
    print()


def test_multi_step():
    """测试多步强化"""
    print("=" * 60)
    print("测试3: 多步强化 (+0 -> +6)")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    calc = EnhancementCalculator(scorer)
    state_probs = calc.calculate_probability_distribution(equip, 6)

    print(f"  初始: 4腿全适配, +0 -> +6 (2步)")
    print(f"  可能状态数: {len(state_probs)}")
    total_prob = sum(state_probs.values())
    print(f"  概率总和: {total_prob:.6f}")

    assert abs(total_prob - 1.0) < 1e-6
    print(f"[OK] 概率总和验证通过")
    print()


def test_score_distribution():
    """测试评分分布计算"""
    print("=" * 60)
    print("测试4: 评分概率分布")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    calc = EnhancementCalculator(scorer)
    score_dist = calc.calculate_score_distribution(equip, 3)

    print(f"  +0 -> +3 评分分布:")
    total_prob = 0
    for score, prob in score_dist:
        total_prob += prob
        print(f"    评分={score:.2f}, 概率={prob:.4f}")

    print(f"\n  概率总和: {total_prob:.6f}")
    assert abs(total_prob - 1.0) < 1e-6

    expected_score = calc.estimate_expected_score(equip, 3)
    print(f"  期望评分: {expected_score:.2f}")
    print(f"[OK] 评分分布验证通过")
    print()


def test_top_n_probability():
    """测试Top N概率计算"""
    print("=" * 60)
    print("测试5: Top N概率计算")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    calc = EnhancementCalculator(scorer)

    # 假设阈值为50分
    threshold = 50.0
    prob = calc.calculate_top_n_probability(equip, 15, threshold)
    print(f"  全适配4腿 +0->+15, 超过{threshold}分的概率: {prob:.4f} ({prob*100:.2f}%)")

    # 假设阈值为70分
    threshold2 = 70.0
    prob2 = calc.calculate_top_n_probability(equip, 15, threshold2)
    print(f"  全适配4腿 +0->+15, 超过{threshold2}分的概率: {prob2:.4f} ({prob2*100:.2f}%)")

    print(f"\n[OK] Top N概率计算完成")
    print()


if __name__ == "__main__":
    try:
        test_4leg_one_step()
        test_3leg_one_step()
        test_multi_step()
        test_score_distribution()
        test_top_n_probability()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
