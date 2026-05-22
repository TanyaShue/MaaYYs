"""
生成御魂预览数据文件 yuhun_preview_data.js
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.data_loader import DataLoader
from core.models import Equip, MainAttribute, normalize_main_attr
from core.ranking import RankingEngine


MAIN_ATTR_BY_POS = {
    0: "攻击",
    2: "防御",
    4: "生命",
}

MAX_SCORE_SAMPLES = 50


def iter_position_configs(equip_config):
    """遍历所有位置的主属性配置，从推荐路线读取"""
    for pos in range(6):
        if pos in MAIN_ATTR_BY_POS:
            main_attr = MAIN_ATTR_BY_POS[pos]
            routes = equip_config.get_routes(pos, main_attr)
            if routes:
                yield pos, main_attr, normalize_main_attr(main_attr), routes
            continue

        pos_key = f"{pos + 1}号位"
        raw_config = equip_config.位置配置.get(pos_key, [])
        if isinstance(raw_config, list):
            for entry in raw_config:
                main_attr = entry.get("主属性")
                routes = equip_config.get_routes(pos, main_attr)
                if main_attr and routes:
                    yield pos, main_attr, normalize_main_attr(main_attr), routes


def process_top_n_for_config(
    engine: RankingEngine,
    equip_type: str,
    equip_config,
    position: int,
    display_main_attr: str,
    main_attr: str,
    routes: list,
    summary_rows: list,
) -> None:
    """处理单个御魂配置的Top N数据，不打印只收集"""
    if not routes:
        return

    dummy = Equip(
        位置=position,
        类型=equip_type,
        品质=6,
        等级=15,
        主属性=MainAttribute(类型=main_attr, 数值="0"),
        副属性=[]
    )

    for route in routes:
        threshold, top_n, ranking = engine.get_top_n_threshold_for_route(
            dummy, equip_config, route
        )
        total = len(ranking)
        scores = [score for _, score in ranking[:MAX_SCORE_SAMPLES]]
        summary_rows.append({
            "位置": position + 1,
            "主属性": display_main_attr,
            "路线": route.路线名称,
            "数量": total,
            "阈值": threshold,
            "有效属性数": len(route.有效属性),
            "有效属性列表": route.有效属性,
            "御魂名称": equip_config.御魂名称,
            "两件套属性": equip_config.两件套属性,
            "scores": scores,
        })


def main():
    loader = DataLoader()
    pool = loader.load_equip_pool()
    pool.equips = [eq for eq in pool.equips if eq.等级 == 15]
    equip_configs = loader.load_all_equip_configs()
    if not equip_configs:
        return

    engine = RankingEngine(pool, loader)
    summary_rows = []

    for equip_type in sorted(equip_configs.keys()):
        equip_config = equip_configs[equip_type]
        for pos, display_main_attr, main_attr, routes in iter_position_configs(equip_config):
            process_top_n_for_config(
                engine,
                equip_type,
                equip_config,
                pos,
                display_main_attr,
                main_attr,
                routes,
                summary_rows,
            )

    if summary_rows:
        payload = {
            "equip_type": "全部御魂",
            "summary": summary_rows
        }
        data_path = Path(__file__).parent / "yuhun_preview_data.js"
        content = "window.TOP_N_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
        data_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
