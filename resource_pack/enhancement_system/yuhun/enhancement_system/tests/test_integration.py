"""
完整集成测试 - 使用0级御魂数据测试决策系统
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Equip, MainAttribute, SubAttribute
from core.data_loader import DataLoader
from core.decision_engine import DecisionEngine


def print_decision(equip, config, decision):
    """格式化输出"""
    print(f"  [{equip.类型}] {equip.位置+1}号位 +{equip.等级} 主属性:{equip.主属性.类型}")
    for attr in equip.副属性:
        print(f"    - {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f})")
    print(f"  -> {decision.action} | {decision.reason}")
    print()


def test_constructed_equips():
    """用构造的0级御魂测试各种场景"""
    print("=" * 60)
    print("场景测试: 构造的0级御魂")
    print("=" * 60 + "\n")

    loader = DataLoader()
    pool = loader.load_equip_pool()
    engine = DecisionEngine(pool, loader)

    # 场景1: 破势 1号位 - 4腿全适配（暴击/暴伤/速度/攻击加成）
    print("--- 场景1: 破势 1号位 4腿全适配 ---")
    config = loader.load_equip_config("破势")
    eq1 = Equip(
        位置=0, 类型="破势", 品质=6, 等级=0,
        主属性=MainAttribute(类型="攻击", 数值="486"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d1 = engine.evaluate(eq1, config)
    print_decision(eq1, config, d1)

    # 场景2: 破势 1号位 - 3腿适配 + 1腿不适配
    print("--- 场景2: 破势 1号位 3适配+1不适配 ---")
    eq2 = Equip(
        位置=0, 类型="破势", 品质=6, 等级=0,
        主属性=MainAttribute(类型="攻击", 数值="486"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d2 = engine.evaluate(eq2, config)
    print_decision(eq2, config, d2)

    # 场景3: 破势 1号位 - 2腿适配 + 2腿不适配
    print("--- 场景3: 破势 1号位 2适配+2不适配 ---")
    eq3 = Equip(
        位置=0, 类型="破势", 品质=6, 等级=0,
        主属性=MainAttribute(类型="攻击", 数值="486"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="生命加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d3 = engine.evaluate(eq3, config)
    print_decision(eq3, config, d3)

    # 场景4: 破势 1号位 - 3腿（缺一条）全适配
    print("--- 场景4: 破势 1号位 3腿全适配 ---")
    eq4 = Equip(
        位置=0, 类型="破势", 品质=6, 等级=0,
        主属性=MainAttribute(类型="攻击", 数值="486"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d4 = engine.evaluate(eq4, config)
    print_decision(eq4, config, d4)

    # 场景5: 破势 1号位 - 2腿全不适配
    print("--- 场景5: 破势 1号位 2腿全不适配 ---")
    eq5 = Equip(
        位置=0, 类型="破势", 品质=6, 等级=0,
        主属性=MainAttribute(类型="攻击", 数值="486"),
        副属性=[
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="生命加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d5 = engine.evaluate(eq5, config)
    print_decision(eq5, config, d5)

    # 场景6: 隐念 2号位速度 - 极限速度场景
    print("--- 场景6: 隐念 2号位速度 有速度副属性 ---")
    config_yn = loader.load_equip_config("隐念")
    eq6 = Equip(
        位置=1, 类型="隐念", 品质=6, 等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="速度", 数值="3.0", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="暴击伤害", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d6 = engine.evaluate(eq6, config_yn)
    print_decision(eq6, config_yn, d6)

    # 场景7: 隐念 2号位速度 - 无速度副属性
    print("--- 场景7: 隐念 2号位速度 无速度副属性 ---")
    eq7 = Equip(
        位置=1, 类型="隐念", 品质=6, 等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[
            SubAttribute(类型="暴击", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="攻击加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="效果命中", 数值="4.0%", 强化次数=0, 等效强化次数=1.0),
            SubAttribute(类型="生命加成", 数值="3.0%", 强化次数=0, 等效强化次数=1.0),
        ]
    )
    d7 = engine.evaluate(eq7, config_yn)
    print_decision(eq7, config_yn, d7)


def test_pool_zero_level():
    """从池中筛选0级御魂测试"""
    print("=" * 60)
    print("池中0级御魂抽样测试")
    print("=" * 60 + "\n")

    loader = DataLoader()
    pool = loader.load_equip_pool()
    engine = DecisionEngine(pool, loader)

    # 统计决策分布
    continue_count = 0
    discard_count = 0
    total = 0

    zero_equips = pool.filter_by(等级=0)

    for eq in zero_equips[:100]:
        config = loader.load_equip_config(eq.类型)
        if not config:
            continue
        routes = config.get_routes(eq.位置, eq.主属性.类型)
        if not routes:
            continue

        decision = engine.evaluate(eq, config)
        total += 1
        if decision.action == "继续强化":
            continue_count += 1
        else:
            discard_count += 1

    print(f"  测试总数: {total}")
    print(f"  继续强化: {continue_count} ({continue_count/total*100:.1f}%)")
    print(f"  弃置: {discard_count} ({discard_count/total*100:.1f}%)")
    print()


if __name__ == "__main__":
    try:
        test_constructed_equips()
        test_pool_zero_level()

        print("=" * 60)
        print("[OK] 集成测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
