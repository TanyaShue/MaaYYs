"""
单元测试 - 排名对比模块
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ranking import RankingEngine
from core.data_loader import DataLoader
from core.models import Equip, MainAttribute, Route
from core.comparison_config import ComparisonConfig


def test_comparison_types():
    """测试同类御魂解析：两件套标签与具体御魂名称"""
    print("=" * 60)
    print("测试1: 同类御魂解析")
    print("=" * 60)

    config = ComparisonConfig()

    two_set = config.resolve_comparison_types(["暴击两件套"], "破势")
    print(f"  暴击两件套 -> {len(two_set)} 个御魂")
    assert "破势" in two_set
    assert "针女" in two_set

    by_attr = config.resolve_comparison_types(["暴击"], "破势")
    assert two_set == by_attr
    print(f"  暴击 -> 与暴击两件套相同")

    by_names = config.resolve_comparison_types(["破势", "针女"], "隐念")
    assert by_names == {"破势", "针女"}
    print(f"  具体名称 -> {by_names}")

    mixed = config.resolve_comparison_types(["暴击两件套", "隐念"], "破势")
    assert "隐念" in mixed
    assert "破势" in mixed
    print(f"  混合配置 -> {len(mixed)} 个御魂")

    empty = config.resolve_comparison_types([], "破势")
    assert empty == {"破势"}
    print(f"  空列表 -> 默认套装")

    print("[OK] 同类御魂解析通过")
    print()


def test_route_based_ranking():
    """测试基于路线的排名"""
    print("=" * 60)
    print("测试2: 基于路线的排名（隐念 2号位 速度）")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()
    config = loader.load_equip_config("隐念")

    if not config:
        print("[FAIL] 未找到隐念配置")
        return

    routes = config.get_routes(1, "速度")
    if not routes:
        print("[FAIL] 未找到隐念2号位速度的路线配置")
        return

    route = routes[0]
    engine = RankingEngine(pool, loader)

    # 创建一个虚拟御魂用于查询
    dummy = Equip(
        位置=1,
        类型="隐念",
        品质=6,
        等级=15,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[]
    )

    threshold, top_n, ranking = engine.get_top_n_threshold_for_route(
        dummy, config, route
    )

    print(f"  路线名称: {route.路线名称}")
    print(f"  有效属性: {route.有效属性}")
    print(f"  Top N: {top_n}")
    print(f"  阈值: {threshold:.2f}")
    print(f"  找到 {len(ranking)} 个御魂")

    if ranking:
        print(f"\n  Top 5:")
        for i, (eq, score) in enumerate(ranking[:5], 1):
            print(f"    {i}. 评分={score:.2f} +{eq.等级}")
            for attr in eq.副属性:
                tag = "[有效]" if attr.类型 in route.有效属性 else "[其他]"
                print(f"       {tag} {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f})")

    print()


def test_top_n_threshold():
    """测试Top N阈值计算"""
    print("=" * 60)
    print("测试3: Top N阈值计算")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()
    engine = RankingEngine(pool, loader)

    # 测试隐念
    config = loader.load_equip_config("隐念")
    if not config:
        print("[FAIL] 未找到隐念配置")
        return

    dummy = Equip(
        位置=1, 类型="隐念", 品质=6, 等级=0,
        主属性=MainAttribute(类型="速度", 数值="57"),
        副属性=[]
    )

    routes = config.get_routes(1, "速度")
    if routes:
        route = routes[0]
        threshold, top_n, ranking = engine.get_top_n_threshold_for_route(dummy, config, route)

        print(f"  隐念 2号位 速度:")
        print(f"    路线名称: {route.路线名称}")
        print(f"    有效属性: {route.有效属性}")
        print(f"    Top N: {top_n}")
        print(f"    阈值评分: {threshold:.2f}")
        print(f"    池中总数: {len(ranking)}")

    # 测试破势
    config2 = loader.load_equip_config("破势")
    if config2:
        routes2 = config2.get_routes(0, "攻击")
        if routes2:
            dummy2 = Equip(
                位置=0, 类型="破势", 品质=6, 等级=0,
                主属性=MainAttribute(类型="攻击", 数值="486"),
                副属性=[]
            )
            route2 = routes2[0]
            threshold2, top_n2, ranking2 = engine.get_top_n_threshold_for_route(dummy2, config2, route2)
            print(f"\n  破势 1号位 攻击:")
            print(f"    路线名称: {route2.路线名称}")
            print(f"    有效属性: {route2.有效属性}")
            print(f"    Top N: {top_n2}")
            print(f"    阈值评分: {threshold2:.2f}")
            print(f"    池中总数: {len(ranking2)}")

        heal_route = next(r for r in routes2 if r.路线名称 == "治疗量")
        _, _, heal_ranking = engine.get_top_n_threshold_for_route(dummy2, config2, heal_route)
        heal_types = {eq.类型 for eq, _ in heal_ranking}
        print(f"\n  破势 治疗量路线（暴击两件套）:")
        print(f"    对比套装数: {len(heal_types)}")
        assert len(heal_types) > 1

    print()


if __name__ == "__main__":
    try:
        test_comparison_types()
        test_route_based_ranking()
        test_top_n_threshold()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
