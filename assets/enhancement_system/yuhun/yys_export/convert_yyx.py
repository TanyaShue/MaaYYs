# -*- coding: utf-8 -*-
"""
阴阳师御魂数据转换工具 - 使用yyx格式文件
直接读取yyx格式的JSON文件，包含完整的御魂信息
"""

import json
import argparse
from pathlib import Path

# ============ 属性类型映射表 ============
ATTR_TYPE_MAP = {
    "Attack": "攻击",
    "Hp": "生命",
    "Defense": "防御",
    "AttackRate": "攻击加成",
    "HpRate": "生命加成",
    "DefenseRate": "防御加成",
    "CritRate": "暴击",
    "CritPower": "暴击伤害",
    "Speed": "速度",
    "EffectHitRate": "效果命中",
    "EffectResistRate": "效果抵抗",
}

# 各属性副属性的最大成长值
MAX_GROWTH = {
    "CritPower": 0.04,
    "CritRate": 0.03,
    "Speed": 3.0,
    "HpRate": 0.03,
    "AttackRate": 0.03,
    "DefenseRate": 0.03,
    "EffectHitRate": 0.04,
    "EffectResistRate": 0.04,
    "Attack": 27,
    "Defense": 5,
    "Hp": 114,
}

PERCENT_ATTRS = {"AttackRate", "HpRate", "DefenseRate", "CritRate",
                  "CritPower", "EffectHitRate", "EffectResistRate"}


def format_value(attr_type, value):
    """格式化数值"""
    if attr_type in PERCENT_ATTRS:
        return f"{value*100:.2f}%"
    else:
        if value == int(value):
            return f"{int(value)}"
        return f"{value:.2f}"


def calc_times(value, attr_type):
    """计算强化次数（基于平均成长值）"""
    avg_growth = MAX_GROWTH.get(attr_type, 0.03) * 0.9
    if value <= 0:
        return 1
    times = max(1, round(value / avg_growth))
    return min(times, 6)


def calc_effective_times(value, attr_type):
    """计算等效强化次数（基于最大成长值）"""
    max_growth = MAX_GROWTH.get(attr_type, 0.03)
    if value <= 0:
        return 1.0
    return round(value / max_growth, 2)


def parse_yyx_data(filepath):
    """解析yyx格式数据文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 从data.hero_equips中获取御魂列表
    equips = data.get("data", {}).get("hero_equips", [])

    results = []

    for equip in equips:
        # 直接读取yyx格式的字段
        equip_id = equip.get("id", "")
        suit_name = equip.get("kind", "未知")
        suit_id = equip.get("suit_id", 0)
        pos = equip.get("pos", 0)
        quality = equip.get("quality", 0)
        level = equip.get("level", 0)

        # 主属性
        base_attr = equip.get("base_attr", {})
        main_attr_type = base_attr.get("type", "Unknown")
        main_attr_value = base_attr.get("value", 0)

        # 副属性
        random_attrs = equip.get("random_attrs", [])
        sub_attrs = []
        for attr in random_attrs:
            attr_type = attr.get("type", "Unknown")
            attr_value = attr.get("value", 0)

            sub_attrs.append({
                "类型": ATTR_TYPE_MAP.get(attr_type, attr_type),
                "数值": format_value(attr_type, attr_value),
                "强化次数": calc_times(attr_value, attr_type),
                "等效强化次数": calc_effective_times(attr_value, attr_type),
            })

        results.append({
            "位置": pos,
            "类型": suit_name,
            "品质": quality,
            "等级": level,
            "主属性": {
                "类型": ATTR_TYPE_MAP.get(main_attr_type, main_attr_type),
                "数值": format_value(main_attr_type, main_attr_value),
            },
            "副属性": sub_attrs,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description='阴阳师御魂数据转换工具 - yyx格式')
    parser.add_argument('-i', '--input', required=True, help='输入的yyx格式JSON文件路径')
    parser.add_argument('-o', '--output', help='输出的JSON文件路径（可选，默认为输入文件同目录下的yys_yuhun_from_yyx.json）')

    args = parser.parse_args()

    input_file = Path(args.input)

    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return

    if args.output:
        output_file = Path(args.output)
    else:
        output_file = input_file.parent / "yys_yuhun_from_yyx.json"

    print("=" * 70)
    print("阴阳师御魂数据转换 - 使用yyx格式文件")
    print("=" * 70)
    print(f"输入: {input_file.name}")
    print()

    print("解析转换中...")
    results = parse_yyx_data(input_file)

    output = {
        "meta": {
            "description": "阴阳师御魂数据 - 从yyx格式转换",
            "count": len(results),
            "source": "yyx格式文件",
        },
        "equips": results,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"输出: {output_file}")
    print(f"御魂数量: {len(results)}")

    # 统计
    pos_dist = {}
    suit_dist = {}
    for r in results:
        pos_dist[r["位置"]] = pos_dist.get(r["位置"], 0) + 1
        suit_dist[r["类型"]] = suit_dist.get(r["类型"], 0) + 1

    print(f"\n位置分布: {dict(sorted(pos_dist.items()))}")

    print("\n御魂类型分布（前10）:")
    for name, count in sorted(suit_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name}: {count}")

    print("\n前3个御魂预览:")
    print("-" * 70)
    for r in results[:3]:
        print(f"【{r['位置']}号位】{r['类型']} +{r['等级']}")
        print(f"  主属性: {r['主属性']['类型']}+{r['主属性']['数值']}")
        subs = [f"{s['类型']}+{s['数值']}({s['强化次数']}次)" for s in r['副属性']]
        print(f"  副属性: {' / '.join(subs)}")
        print()


if __name__ == "__main__":
    main()

