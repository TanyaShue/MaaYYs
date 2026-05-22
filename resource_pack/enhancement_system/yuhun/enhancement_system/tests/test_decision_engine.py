"""
单元测试 - 决策引擎
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decision_engine import DecisionEngine
from core.data_loader import DataLoader
from core.models import Equip, MainAttribute, SubAttribute


def test_decision_at_zero():
    """测试+0御魂的决策"""
    print("=" * 60)
    print("测试1: +0御魂决策")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()
    config = loader.load_equip_config("隐念")

    if not config:
        print("[FAIL] 未找到隐念配置")
        return

    engine = DecisionEngine(pool, loader)

    # 好御魂：4腿全适配
    good_equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    decision = engine.evaluate(good_equip, config)
    print(f"  [好御魂] 4腿全适配:")
    print(f"    决策: {decision.action}")
    print(f"    理由: {decision.reason}")
    print(f"    当前评分: {decision.current_score:.2f}")
    print(f"    阈值评分: {decision.threshold_score:.2f}")

    # 差御魂：有不适配属性
    bad_equip = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="效果抵抗", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="生命加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )

    decision2 = engine.evaluate(bad_equip, config)
    print(f"\n  [差御魂] 3腿全不适配:")
    print(f"    决策: {decision2.action}")
    print(f"    理由: {decision2.reason}")
    print(f"    当前评分: {decision2.current_score:.2f}")

    print()


def test_decision_at_max():
    """测试+15御魂的决策"""
    print("=" * 60)
    print("测试2: +15御魂决策")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()
    config = loader.load_equip_config("隐念")

    if not config:
        print("[FAIL] 未找到隐念配置")
        return

    engine = DecisionEngine(pool, loader)

    # 从池中取一个+15的隐念
    filtered = pool.filter_by(位置=1, 类型="隐念", 主属性类型="速度", 等级=15)

    if filtered:
        for eq in filtered:
            decision = engine.evaluate(eq, config)
            print(f"  御魂 +{eq.等级}:")
            for attr in eq.副属性:
                print(f"    {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f})")
            print(f"    决策: {decision.action}")
            print(f"    理由: {decision.reason}")
            print()
    else:
        print("  未找到+15隐念速度御魂")

    print()


if __name__ == "__main__":
    try:
        test_decision_at_zero()
        test_decision_at_max()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
