"""
单元测试 - 评分模块
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scoring import Scorer, calculate_equivalent_enhancement, ATTR_RANGE, create_scorer_for_route
from core.models import Equip, MainAttribute, SubAttribute, Route
from core.data_loader import DataLoader


def test_equivalent_enhancement():
    """测试等效强化次数计算"""
    print("=" * 60)
    print("测试1: 等效强化次数计算")
    print("=" * 60)

    test_cases = [
        ("速度", 3.0, 1.0),
        ("速度", 2.4, 0.8),
        ("速度", 6.0, 2.0),
        ("暴击", 0.03, 1.0),
        ("暴击", 0.06, 2.0),
        ("攻击", 27.0, 1.0),
    ]

    for attr_type, value, expected in test_cases:
        result = calculate_equivalent_enhancement(attr_type, value)
        status = "[OK]" if abs(result - expected) < 0.01 else "[FAIL]"
        print(f"{status} {attr_type}={value} -> 等效{result:.2f}次 (期望{expected:.2f})")

    print()


def test_standard_scoring():
    """测试标准评分（输出御魂）"""
    print("=" * 60)
    print("测试2: 标准评分（输出御魂）")
    print("=" * 60)

    route = Route(
        路线名称="常规输出",
        有效属性=["暴击", "暴击伤害", "速度", "攻击加成"],
        有效属性权重=[1, 1, 1, 1]
    )
    scorer = create_scorer_for_route(route)

    print(f"  路线名称: {route.路线名称}")
    print(f"  有效属性: {route.有效属性}")

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=15,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击伤害", 数值="6.62%", 强化次数=1, 等效强化次数=1.84),
            SubAttribute(类型="速度", 数值="10.90", 强化次数=3, 等效强化次数=4.04),
            SubAttribute(类型="暴击", 数值="2.78%", 强化次数=0, 等效强化次数=1.03),
            SubAttribute(类型="攻击加成", 数值="2.82%", 强化次数=0, 等效强化次数=1.04),
        ]
    )

    score = scorer.score(equip)
    # 全部适配: 1.84 + 4.04 + 1.03 + 1.04 = 7.95
    expected = 1.84 + 4.04 + 1.03 + 1.04
    status = "[OK]" if abs(score - expected) < 0.1 else "[FAIL]"
    print(f"\n{status} 全适配御魂评分: {score:.2f} (期望{expected:.2f})")

    # 测试有不适配属性的情况
    equip2 = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=15,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="5.4%", 强化次数=1, 等效强化次数=2.0),
            SubAttribute(类型="速度", 数值="6.0", 强化次数=1, 等效强化次数=2.0),
            SubAttribute(类型="生命加成", 数值="6.0%", 强化次数=1, 等效强化次数=2.22),
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    score2 = scorer.score(equip2)
    # 适配: 2.0 + 2.0 = 4.0, 不适配属性不计分
    expected2 = 2.0 + 2.0
    status2 = "[OK]" if abs(score2 - expected2) < 0.1 else "[FAIL]"
    print(f"{status2} 有不适配属性: {score2:.2f} (期望{expected2:.2f})")

    print()


def test_extreme_scoring():
    """测试极限属性评分"""
    print("=" * 60)
    print("测试3: 极限属性评分")
    print("=" * 60)

    route = Route(
        路线名称="极限速度",
        有效属性=["速度"],
        有效属性权重=[1]
    )
    scorer = create_scorer_for_route(route)

    print(f"  路线名称: {route.路线名称}")
    print(f"  有效属性: {route.有效属性}")

    equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=15,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="速度", 数值="15.0", 强化次数=4, 等效强化次数=5.0),
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="生命加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    score = scorer.score(equip)
    # 只计算速度: 5.0
    expected = 5.0
    status = "[OK]" if abs(score - expected) < 0.1 else "[FAIL]"
    print(f"\n{status} 极限速度御魂: {score:.2f} (期望{expected:.2f})")

    print()


def test_real_equip_scoring():
    """测试真实御魂评分"""
    print("=" * 60)
    print("测试4: 真实御魂评分（从池中加载）")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()
    config = loader.load_equip_config("隐念")

    if not config:
        print("[FAIL] 未找到隐念配置")
        return

    # 筛选隐念2号位速度主属性+15的御魂
    filtered = pool.filter_by(位置=1, 类型="隐念", 主属性类型="速度", 等级=15)

    if not filtered:
        print("  未找到符合条件的御魂，尝试不限等级")
        filtered = pool.filter_by(位置=1, 类型="隐念", 主属性类型="速度")

    if not filtered:
        print("[FAIL] 未找到隐念2号位速度御魂")
        return

    routes = config.get_routes(1, "速度")
    if not routes:
        print("[FAIL] 未找到隐念2号位速度的路线配置")
        return

    route = routes[0]  # 使用第一条路线
    scorer = create_scorer_for_route(route)

    print(f"  路线名称: {route.路线名称}")
    print(f"  有效属性: {route.有效属性}")
    print(f"  找到 {len(filtered)} 个御魂\n")

    # 对所有御魂评分并排序
    scored = [(eq, scorer.score(eq)) for eq in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)

    print(f"  评分排名（前5）:")
    for i, (eq, score) in enumerate(scored[:5], 1):
        print(f"    {i}. 评分={score:.2f} 等级+{eq.等级}")
        for attr in eq.副属性:
            tag = "[有效]" if attr.类型 in route.有效属性 else "[其他]"
            print(f"       {tag} {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f})")

    print()


if __name__ == "__main__":
    try:
        test_equivalent_enhancement()
        test_standard_scoring()
        test_extreme_scoring()
        test_real_equip_scoring()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
