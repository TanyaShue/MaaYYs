"""
御魂强化决策系统 - 主程序入口
"""
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from core.models import Equip, MainAttribute, SubAttribute, EquipConfig
from core.data_loader import DataLoader
from core.decision_engine import DecisionEngine


def evaluate_equip(equip_data: dict, equip_name: Optional[str] = None) -> None:
    """
    评估单个御魂

    Args:
        equip_data: 御魂数据字典
        equip_name: 御魂套装名称（如果数据中没有"类型"字段则必须提供）
    """
    loader = DataLoader()
    pool = loader.load_equip_pool()

    equip = Equip(**equip_data)
    if equip_name:
        equip.类型 = equip_name

    config = loader.load_equip_config(equip.类型)
    if not config:
        print(f"[ERROR] 未找到 {equip.类型} 的配置文件")
        return

    engine = DecisionEngine(pool, loader)
    decision = engine.evaluate(equip, config)

    _print_result(equip, config, decision)


def _print_result(equip: Equip, config: EquipConfig, decision) -> None:
    """格式化输出决策结果"""
    print("=" * 60)
    print(f"  御魂: {equip.类型} | {equip.位置 + 1}号位 | +{equip.等级}")
    print(f"  主属性: {equip.主属性.类型} {equip.主属性.数值}")
    print(f"  副属性:")
    for attr in equip.副属性:
        print(f"    - {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f}次)")
    print("-" * 60)
    print(f"  >> 决策: {decision.action}")
    print(f"  >> 理由: {decision.reason}")
    print(f"  >> 当前评分: {decision.current_score:.2f}")
    print(f"  >> 阈值评分: {decision.threshold_score:.2f} (Top {decision.top_n})")
    if decision.probability is not None:
        print(f"  >> 达标概率: {decision.probability*100:.1f}%")
        print(f"  >> 阶段阈值: {decision.stage_threshold*100:.0f}%")
    if decision.current_rank is not None:
        print(f"  >> 当前排名: {decision.current_rank}/{decision.total_count}")
    print("=" * 60)


def demo_with_zero_level_equips():
    """使用0级御魂数据进行演示测试"""
    loader = DataLoader()
    pool = loader.load_equip_pool()

    print("\n" + "=" * 60)
    print("  御魂强化决策系统 - 0级御魂测试")
    print("=" * 60 + "\n")

    # 从池中找一些0级御魂进行测试
    zero_level = pool.filter_by(等级=0)
    print(f"池中0级御魂总数: {len(zero_level)}\n")

    tested = 0
    for eq in zero_level:
        config = loader.load_equip_config(eq.类型)
        if not config:
            continue

        routes = config.get_routes(eq.位置, eq.主属性.类型)
        if not routes:
            continue

        engine = DecisionEngine(pool, loader)
        decision = engine.evaluate(eq, config)
        _print_result(eq, config, decision)
        print()

        tested += 1
        if tested >= 10:
            break

    print(f"\n共测试 {tested} 个0级御魂")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 从命令行参数读取JSON文件
        json_file = sys.argv[1]
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        evaluate_equip(data)
    else:
        demo_with_zero_level_equips()
