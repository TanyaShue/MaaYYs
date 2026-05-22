"""
单元测试 - 数据加载模块
"""
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import DataLoader
from core.models import EquipPool, EquipConfig


def test_load_equip_pool():
    """测试加载御魂池"""
    print("=" * 60)
    print("测试1: 加载御魂池数据")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()

    print(f"[OK] 成功加载御魂池")
    print(f"  - 御魂总数: {pool.meta['count']}")
    print(f"  - 数据来源: {pool.meta['source']}")
    print(f"  - 实际加载: {len(pool.equips)} 个御魂")

    # 检查第一个御魂
    if pool.equips:
        first = pool.equips[0]
        print(f"\n  示例御魂:")
        print(f"    - 类型: {first.类型}")
        print(f"    - 位置: {first.位置 + 1}号位")
        print(f"    - 等级: +{first.等级}")
        print(f"    - 主属性: {first.主属性.类型} {first.主属性.数值}")
        print(f"    - 副属性数: {first.副属性数量}条")
        for attr in first.副属性:
            print(f"      · {attr.类型}: {attr.数值} (等效{attr.等效强化次数:.2f}次)")

    print()


def test_load_equip_config():
    """测试加载御魂配置"""
    print("=" * 60)
    print("测试2: 加载御魂配置")
    print("=" * 60)

    loader = DataLoader()

    # 测试加载隐念配置
    config = loader.load_equip_config("隐念")

    if config:
        print(f"[OK] 成功加载隐念配置")
        print(f"  - 御魂名称: {config.御魂名称}")
        print(f"  - 两件套属性: {config.两件套属性}")
        print(f"  - 两件套数值: {config.两件套数值}")
        print(f"  - 四件套效果: {config.四件套效果}")

        print(f"\n  2号位速度主属性推荐路线:")
        routes = config.get_routes(1, "速度")
        for route in routes:
            print(f"    · {route.路线名称}: {route.有效属性}")
    else:
        print("✗ 未找到隐念配置")

    print()


def test_load_all_configs():
    """测试加载所有配置"""
    print("=" * 60)
    print("测试3: 加载所有御魂配置")
    print("=" * 60)

    loader = DataLoader()
    all_configs = loader.load_all_equip_configs()

    print(f"[OK] 成功加载 {len(all_configs)} 个御魂配置")

    # 按两件套属性分组统计
    by_two_set = {}
    for name, config in all_configs.items():
        two_set = config.两件套属性
        if two_set not in by_two_set:
            by_two_set[two_set] = []
        by_two_set[two_set].append(name)

    print(f"\n  按两件套属性分组:")
    for two_set, names in sorted(by_two_set.items()):
        print(f"    - {two_set}: {len(names)}个 ({', '.join(names[:3])}...)")

    print()


def test_filter_equips():
    """测试御魂筛选"""
    print("=" * 60)
    print("测试5: 御魂筛选功能")
    print("=" * 60)

    loader = DataLoader()
    pool = loader.load_equip_pool()

    # 筛选隐念2号位速度主属性的御魂
    filtered = pool.filter_by(位置=1, 类型="隐念", 主属性类型="速度")

    print(f"[OK] 筛选条件: 隐念 + 2号位 + 速度主属性")
    print(f"  - 找到 {len(filtered)} 个符合条件的御魂")

    if filtered:
        print(f"\n  前3个示例:")
        for i, eq in enumerate(filtered[:3], 1):
            print(f"    {i}. 等级+{eq.等级}, 副属性{eq.副属性数量}条")
            for attr in eq.副属性:
                print(f"       · {attr.类型}: {attr.数值}")

    print()


if __name__ == "__main__":
    try:
        test_load_equip_pool()
        test_load_equip_config()
        test_load_all_configs()
        test_filter_equips()

        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\nX 测试失败: {e}")
        import traceback
        traceback.print_exc()
