"""
交互式强化模拟测试脚本

内置示例御魂，模拟强化过程，每次强化后展示状态和决策建议，
用户输入1继续强化，输入2弃置。
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.models import Equip, MainAttribute, SubAttribute
from core.data_loader import DataLoader
from core.decision_engine import DecisionEngine
from core.scoring import ATTR_RANGE, ALL_SUB_ATTR_TYPES, create_scorer_for_route


# 内置示例御魂
SAMPLE_EQUIPS = [
    {
        "name": "破势 1号位 攻击 (3适配+1不适配)",
        "data": {
            "位置": 0, "类型": "破势", "品质": 6, "等级": 0,
            "主属性": {"类型": "攻击", "数值": "486"},
            "副属性": [
                {"类型": "暴击", "数值": "2.78%", "强化次数": 0, "等效强化次数": 0.93},
                {"类型": "暴击伤害", "数值": "3.89%", "强化次数": 0, "等效强化次数": 0.97},
                {"类型": "速度", "数值": "2.7", "强化次数": 0, "等效强化次数": 0.90},
                {"类型": "效果命中", "数值": "3.5%", "强化次数": 0, "等效强化次数": 0.88},
            ]
        }
    },
    {
        "name": "破势 1号位 攻击 (4适配)",
        "data": {
            "位置": 0, "类型": "破势", "品质": 6, "等级": 0,
            "主属性": {"类型": "攻击", "数值": "486"},
            "副属性": [
                {"类型": "暴击", "数值": "2.5%", "强化次数": 0, "等效强化次数": 0.83},
                {"类型": "暴击伤害", "数值": "3.2%", "强化次数": 0, "等效强化次数": 0.80},
                {"类型": "速度", "数值": "2.9", "强化次数": 0, "等效强化次数": 0.97},
                {"类型": "攻击加成", "数值": "2.6%", "强化次数": 0, "等效强化次数": 0.87},
            ]
        }
    },
    {
        "name": "隐念 2号位 速度 (有速度副属性)",
        "data": {
            "位置": 1, "类型": "隐念", "品质": 6, "等级": 0,
            "主属性": {"类型": "速度", "数值": "57"},
            "副属性": [
                {"类型": "速度", "数值": "2.8", "强化次数": 0, "等效强化次数": 0.93},
                {"类型": "暴击", "数值": "2.9%", "强化次数": 0, "等效强化次数": 0.97},
                {"类型": "生命加成", "数值": "2.8%", "强化次数": 0, "等效强化次数": 0.93},
                {"类型": "攻击加成", "数值": "2.5%", "强化次数": 0, "等效强化次数": 0.83},
            ]
        }
    },
    {
        "name": "破势 1号位 攻击 (2适配+1不适配, 3腿)",
        "data": {
            "位置": 0, "类型": "破势", "品质": 6, "等级": 0,
            "主属性": {"类型": "攻击", "数值": "486"},
            "副属性": [
                {"类型": "暴击", "数值": "2.9%", "强化次数": 0, "等效强化次数": 0.97},
                {"类型": "速度", "数值": "2.6", "强化次数": 0, "等效强化次数": 0.87},
                {"类型": "生命加成", "数值": "2.7%", "强化次数": 0, "等效强化次数": 0.90},
            ]
        }
    },
]


def simulate_enhance(equip: Equip) -> Equip:
    """
    模拟一次+3强化

    规则：
    - 如果副属性<4条：随机新增一条（从11种中随机，可能与已有重复则强化已有）
    - 如果副属性=4条：按虚拟腿池概率选择一条强化
    - 强化数值在(min, max)范围内均匀随机
    """
    sub_attrs = list(equip.副属性)

    if len(sub_attrs) < 4:
        # 新增副属性
        new_type = random.choice(ALL_SUB_ATTR_TYPES)
        existing_types = [a.类型 for a in sub_attrs]

        if new_type in existing_types:
            # 已有该类型，强化它
            for i, attr in enumerate(sub_attrs):
                if attr.类型 == new_type:
                    sub_attrs[i] = _enhance_attr(attr)
                    break
        else:
            # 新增
            min_val, max_val = ATTR_RANGE[new_type]
            roll = random.uniform(min_val, max_val)
            equiv = roll / max_val
            sub_attrs.append(SubAttribute(
                类型=new_type,
                数值=_format_value(new_type, roll),
                强化次数=0,
                等效强化次数=round(equiv, 2)
            ))
    else:
        # 虚拟腿池选择
        legs = [attr.强化次数 + 1 for attr in sub_attrs]
        total_legs = sum(legs)
        r = random.random() * total_legs
        cumulative = 0
        chosen = 0
        for i, leg in enumerate(legs):
            cumulative += leg
            if r <= cumulative:
                chosen = i
                break
        sub_attrs[chosen] = _enhance_attr(sub_attrs[chosen])

    return Equip(
        位置=equip.位置,
        类型=equip.类型,
        品质=equip.品质,
        等级=equip.等级 + 3,
        主属性=equip.主属性,
        副属性=sub_attrs
    )


def _enhance_attr(attr: SubAttribute) -> SubAttribute:
    """强化一条副属性"""
    min_val, max_val = ATTR_RANGE[attr.类型]
    roll = random.uniform(min_val, max_val)
    equiv_add = roll / max_val

    # 计算新数值
    old_numeric = attr.等效强化次数 * max_val
    new_numeric = old_numeric + roll
    new_equiv = new_numeric / max_val

    return SubAttribute(
        类型=attr.类型,
        数值=_format_value(attr.类型, new_numeric),
        强化次数=attr.强化次数 + 1,
        等效强化次数=round(new_equiv, 2)
    )


def _format_value(attr_type: str, value: float) -> str:
    """格式化属性数值"""
    percent_types = {"暴击", "暴击伤害", "攻击加成", "生命加成", "防御加成", "效果命中", "效果抵抗"}
    if attr_type in percent_types:
        return f"{value * 100:.2f}%"
    else:
        return f"{value:.2f}"


def print_equip_state(equip: Equip, decision=None):
    """打印御魂当前状态"""
    print()
    print("=" * 50)
    print(f"  {equip.类型} | {equip.位置 + 1}号位 | +{equip.等级}")
    print(f"  主属性: {equip.主属性.类型} {equip.主属性.数值}")
    print(f"  副属性:")
    for attr in equip.副属性:
        enhance_bar = "*" * attr.强化次数
        print(f"    {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f}) {enhance_bar}")

    if decision:
        print("-" * 50)
        if decision.route_name:
            print(f"  [路线] {decision.route_name}")
        print(f"  [建议] {decision.action}")
        print(f"  [理由] {decision.reason}")
        if decision.probability is not None:
            print(f"  [概率] {decision.probability*100:.1f}% (阈值{decision.stage_threshold*100:.0f}%)")
    print("=" * 50)


def run_interactive():
    """交互式强化模拟"""
    print("\n" + "=" * 50)
    print("  御魂强化模拟器")
    print("=" * 50)
    print("\n选择要测试的御魂:\n")

    for i, sample in enumerate(SAMPLE_EQUIPS, 1):
        print(f"  {i}. {sample['name']}")

    print()
    choice = input("请输入编号 (1-4): ").strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(SAMPLE_EQUIPS):
            print("无效选择")
            return
    except ValueError:
        print("无效输入")
        return

    sample = SAMPLE_EQUIPS[idx]
    data = sample["data"]

    # 构建Equip对象
    equip = Equip(
        位置=data["位置"],
        类型=data["类型"],
        品质=data["品质"],
        等级=data["等级"],
        主属性=MainAttribute(**data["主属性"]),
        副属性=[SubAttribute(**a) for a in data["副属性"]]
    )

    # 加载数据
    loader = DataLoader()
    pool = loader.load_equip_pool()
    config = loader.load_equip_config(equip.类型)

    if not config:
        print(f"[ERROR] 未找到 {equip.类型} 的配置")
        return

    engine = DecisionEngine(pool, loader)

    print(f"\n--- 开始强化: {sample['name']} ---")

    # 初始评估
    decision = engine.evaluate(equip, config)
    print_equip_state(equip, decision)

    while equip.等级 < 15:
        print(f"\n  当前等级: +{equip.等级}")
        print(f"  1 = 继续强化 (+{equip.等级} -> +{equip.等级 + 3})")
        print(f"  2 = 弃置")
        action = input("\n  请选择 (1/2): ").strip()

        if action == "2":
            print("\n  >>> 你选择了弃置该御魂。")
            break
        elif action != "1":
            print("  无效输入，请输入1或2")
            continue

        # 模拟强化
        equip = simulate_enhance(equip)
        print(f"\n  >>> 强化完成! +{equip.等级 - 3} -> +{equip.等级}")

        # 重新评估
        decision = engine.evaluate(equip, config)
        print_equip_state(equip, decision)

    if equip.等级 >= 15:
        print("\n  >>> 强化已满! 最终评估:")
        decision = engine.evaluate(equip, config)
        print_equip_state(equip, decision)

        if decision.action == "保留":
            print("\n  恭喜! 该御魂值得保留。")
        else:
            print("\n  该御魂未达标，建议弃置。")

    print("\n--- 模拟结束 ---\n")


if __name__ == "__main__":
    run_interactive()
