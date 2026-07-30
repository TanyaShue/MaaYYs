"""
御魂强化素材准备工具。

常用命令（仓库根目录执行）：
  python tasks/Yuhun/tools/prepare_yuhun_assets.py --status
  python tasks/Yuhun/tools/prepare_yuhun_assets.py --crop-only
  python tasks/Yuhun/tools/prepare_yuhun_assets.py --annotate-select
  python tasks/Yuhun/tools/prepare_yuhun_assets.py --test-select-ocr --select-capture select_one_detail.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
YUHUN_DIR = SCRIPT_DIR.parent
REPO_DIR = YUHUN_DIR.parents[1]
TEMP_ASSET_DIR = YUHUN_DIR / "asset_temp"

if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))


def roi_str(roi: tuple[int, int, int, int]) -> str:
    return ",".join(str(v) for v in roi)


def parse_roi(value: str) -> tuple[int, int, int, int]:
    parts = [int(x) for x in value.split(",")]
    if len(parts) != 4:
        raise ValueError(f"invalid roi: {value}")
    return tuple(parts)


def layout_roi(value) -> list[int]:
    if isinstance(value, dict):
        value = value["roi"]
    return [int(v) for v in value]


def layout_source(value, default: str | None = None) -> str | None:
    if isinstance(value, dict):
        return value.get("sourceImage", default)
    return default


def source_image_path(name: str, page: str) -> Path:
    path = TEMP_ASSET_DIR / name
    if path.exists():
        return path
    return TEMP_ASSET_DIR / page / name


def annotated_image_path(source: Path, suffix: str) -> Path:
    return source.with_name(f"{source.stem}{suffix}")


def source_images(page: str) -> list[Path]:
    folder = TEMP_ASSET_DIR / page
    if not folder.exists():
        return []
    return [
        path
        for path in sorted(folder.glob("*.png"))
        if "_标注" not in path.stem and not path.stem.endswith("_template_check")
    ]


def crop_image(src: Path, roi: tuple[int, int, int, int], dst: Path) -> None:
    from PIL import Image

    if not src.exists():
        raise FileNotFoundError(src)
    x, y, w, h = roi
    with Image.open(src) as img:
        w_img, h_img = img.size
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(x + w, w_img), min(y + h, h_img)
        cropped = img.crop((x1, y1, x2, y2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(dst)
    print(f"  crop -> {dst.relative_to(YUHUN_DIR)} roi={roi_str(roi)}")


def read_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def read_select_layout() -> dict:
    raw = read_json(YUHUN_DIR / "select" / "temp_layout.json")
    if not isinstance(raw, list):
        return raw

    layout = {
        "description": "批量强化·选择页布局源配置。外层按 sourceImage 分组。",
        "resolution": [1280, 720],
        "columns": 4,
        "visible_rows": 4,
        "detail_popup": {},
        "confirm_panel": {},
    }
    for group in raw:
        source = group["sourceImage"]
        for key in ["resolution", "columns", "visible_rows", "selection_templates", "detail_attr_width_shrink_level_ge_3"]:
            if key in group:
                layout[key] = group[key]
        if "grid_spec" in group:
            grid = dict(group["grid_spec"])
            grid["sourceImage"] = source
            layout["grid_spec"] = grid
        if "selection_box_offset" in group:
            layout["selection_box_offset"] = group["selection_box_offset"]
            layout["selection_box_sourceImage"] = source
        for name, roi in group.get("confirm_panel", {}).items():
            layout["confirm_panel"][name] = {"sourceImage": source, "roi": roi}
        for name, roi in group.get("detail_popup", {}).items():
            layout["detail_popup"][name] = {"sourceImage": source, "roi": roi}
    return layout


def read_enhance_layout() -> dict:
    raw = read_json(YUHUN_DIR / "enhance" / "temp_layout.json")
    if not isinstance(raw, list):
        return raw

    layout = {
        "description": "批量强化·强化设置页布局源配置。外层按 sourceImage 分组。",
        "resolution": [1280, 720],
        "actions": {},
    }
    for group in raw:
        source = group["sourceImage"]
        if "resolution" in group:
            layout["resolution"] = group["resolution"]
        for name, action in group.get("actions", {}).items():
            item = dict(action)
            item["sourceImage"] = source
            layout["actions"][name] = item
    return layout


def expand_select_grid(layout: dict) -> dict:
    grid_spec = layout.get("grid_spec")
    anchors = layout.get("grid_anchors")
    if not grid_spec and not anchors:
        return layout

    columns = int(layout.get("columns", 4))
    rows = int(layout.get("visible_rows", 4))
    if grid_spec:
        first_slot = grid_spec["first_slot"]
        cell = [int(v) for v in grid_spec.get("soul_size", first_slot[2:4])]
        gap = [int(v) for v in grid_spec.get("gap", [0, 0])]
        col_step = cell[0] + gap[0]
        row_step = cell[1] + gap[1]
    else:
        first_slot = anchors["slot_1"]
        slot_2 = anchors["slot_2"]
        slot_5 = anchors["slot_5"]
        cell = [int(first_slot[2]), int(first_slot[3])]
        gap = [
            int(slot_2[0]) - int(first_slot[0]) - cell[0],
            int(slot_5[1]) - int(first_slot[1]) - cell[1],
        ]
        col_step = cell[0] + gap[0]
        row_step = cell[1] + gap[1]
    selection_box_offset = layout.get("selection_box_offset", [68, 11, 36, 20])

    slots = []
    for index in range(1, rows * columns + 1):
        row = (index - 1) // columns + 1
        col = (index - 1) % columns + 1
        x = int(first_slot[0]) + (col - 1) * col_step
        y = int(first_slot[1]) + (row - 1) * row_step
        click = [x, y, cell[0], cell[1]]
        selected_box = [
            x + int(selection_box_offset[0]),
            y + int(selection_box_offset[1]),
            int(selection_box_offset[2]),
            int(selection_box_offset[3]),
        ]
        slots.append({
            "index": index,
            "row": row,
            "col": col,
            "click": click,
            "selected_box": selected_box,
        })

    generated = dict(layout)
    generated["slots"] = slots
    return generated


def sync_select_layout() -> None:
    layout_path = YUHUN_DIR / "select" / "temp_layout.json"
    if not layout_path.exists():
        return
    layout = expand_select_grid(read_select_layout())
    ocr_path = YUHUN_DIR / "select" / "ocr.json"
    click_path = YUHUN_DIR / "select" / "click.json"
    image_path = YUHUN_DIR / "select" / "image.json"
    ocr_items = read_json(ocr_path)
    click_items = read_json(click_path)
    image_items = read_json(image_path)
    ocr_by_name = {item["itemName"]: item for item in ocr_items}
    click_by_name = {item["itemName"]: item for item in click_items}

    for slot in layout.get("slots", []):
        idx = slot["index"]
        click_key = f"slot_{idx}"
        if click_key in click_by_name:
            roi = roi_str(tuple(slot["click"]))
            click_by_name[click_key]["roiFront"] = roi
            click_by_name[click_key]["roiBack"] = roi
        selected_roi = roi_str(tuple(slot["selected_box"]))
        selected_key = f"select_slot_{idx}_selected"
        selected_prefix = f"select_slot_{idx}_selected_"
        for item in image_items:
            if item["itemName"] == selected_key or item["itemName"].startswith(selected_prefix):
                item["roiFront"] = selected_roi
                item["roiBack"] = selected_roi

    confirm_panel = layout.get("confirm_panel", {})
    if "select_confirm_count" in ocr_by_name and "counter_ocr" in confirm_panel:
        roi = roi_str(tuple(layout_roi(confirm_panel["counter_ocr"])))
        ocr_by_name["select_confirm_count"]["roiFront"] = roi
        ocr_by_name["select_confirm_count"]["roiBack"] = roi
    for item in image_items:
        if item["itemName"] == "select_enhance_all" and "enhance_all_btn" in confirm_panel:
            roi = roi_str(tuple(layout_roi(confirm_panel["enhance_all_btn"])))
            item["roiFront"] = roi
            item["roiBack"] = roi

    panel = layout.get("detail_popup", {})
    detail_map = {
        "soul_type_level": "soul_type_level",
        "detail_main_attr": "main_attr",
        "detail_sub_attr_1": "sub_attr_1",
        "detail_sub_attr_2": "sub_attr_2",
        "detail_sub_attr_3": "sub_attr_3",
        "detail_sub_attr_4": "sub_attr_4",
    }
    for ocr_name, layout_name in detail_map.items():
        if ocr_name in ocr_by_name and layout_name in panel:
            roi = roi_str(tuple(layout_roi(panel[layout_name])))
            ocr_by_name[ocr_name]["roiFront"] = roi
            ocr_by_name[ocr_name]["roiBack"] = roi

    write_json(ocr_path, list(ocr_by_name.values()))
    write_json(click_path, list(click_by_name.values()))
    write_json(image_path, image_items)
    print("  synced select derived assets")


def sync_enhance_layout() -> None:
    layout_path = YUHUN_DIR / "enhance" / "temp_layout.json"
    if not layout_path.exists():
        return
    layout = read_enhance_layout()
    actions = layout.get("actions", {})
    image_path = YUHUN_DIR / "enhance" / "image.json"
    items = read_json(image_path)
    for item in items:
        action = actions.get(item["itemName"])
        if not action:
            continue
        roi = roi_str(tuple(action["roi"]))
        item["roiFront"] = roi
        item["roiBack"] = roi
        if "sourceImage" in action:
            item["sourceImage"] = action["sourceImage"]
    write_json(image_path, items)
    print("  synced enhance/temp_layout.json")


def shift_roi(roi: list[int], dx: int, dy: int) -> list[int]:
    return [int(roi[0]) + dx, int(roi[1]) + dy, int(roi[2]), int(roi[3])]


def read_result_layout() -> dict:
    raw = read_json(YUHUN_DIR / "result" / "temp_layout.json")
    if not isinstance(raw, list):
        return raw

    layout = {
        "description": "强化结果页布局源配置。外层按 sourceImage 分组，脚本归一化后派生运行时 JSON。",
        "resolution": [1280, 720],
        "actions": {},
        "detail_template": {},
    }
    marker_aliases = {
        "selected_marker": "selected_marker",
        "discarded_marker": "discarded_marker",
    }
    for group in raw:
        source = group["sourceImage"]
        if "resolution" in group:
            layout["resolution"] = group["resolution"]
        if "grid_spec" in group:
            grid = dict(group["grid_spec"])
            grid["sourceImage"] = source
            layout["grid_spec"] = grid
        for name, action in group.get("actions", {}).items():
            item = dict(action)
            item["sourceImage"] = source
            layout["actions"][name] = item
        for name, spec in group.get("detail_template", {}).items():
            item = dict(spec) if isinstance(spec, dict) else {"roi": spec}
            item["sourceImage"] = source
            layout["detail_template"][name] = item
        for key, marker_name in marker_aliases.items():
            if key in group:
                marker = dict(group[key])
                marker["sourceImage"] = source
                layout[marker_name] = marker
        for name, marker in group.get("markers", {}).items():
            item = dict(marker)
            item["sourceImage"] = source
            layout[name] = item
    return layout


def expand_result_grid(layout: dict) -> dict:
    grid = layout.get("grid_spec")
    if not grid:
        return layout

    columns = int(grid.get("columns", layout.get("columns", 3)))
    rows = int(grid.get("rows", 2))
    first_slot = [int(v) for v in grid["first_slot"]]
    soul_size = [int(v) for v in grid.get("soul_size", first_slot[2:4])]
    gap = [int(v) for v in grid.get("gap", [0, 0])]
    col_step = soul_size[0] + gap[0]
    row_step = soul_size[1] + gap[1]
    detail_template = layout.get("detail_template", {})

    slots = []
    for index in range(1, columns * rows + 1):
        row = (index - 1) // columns + 1
        col = (index - 1) % columns + 1
        dx = (col - 1) * col_step
        dy = (row - 1) * row_step
        slot = {
            "index": index,
            "row": row,
            "col": col,
            "offset": [dx, dy],
            "click": shift_roi(first_slot, dx, dy),
        }
        for name, spec in detail_template.items():
            slot[name] = shift_roi(layout_roi(spec), dx, dy)
        slots.append(slot)

    generated = dict(layout)
    generated["slots"] = slots
    return generated


def sync_result_layout() -> None:
    layout_path = YUHUN_DIR / "result" / "temp_layout.json"
    if not layout_path.exists():
        return
    layout = expand_result_grid(read_result_layout())

    click_items = []
    for slot in layout.get("slots", []):
        roi = roi_str(tuple(slot["click"]))
        click_items.append({
            "itemName": f"result_slot_{slot['index']}",
            "roiFront": roi,
            "roiBack": roi,
            "description": f"结果页点击第{slot['index']}个御魂",
        })
    write_json(YUHUN_DIR / "result" / "click.json", click_items)

    ocr_items = []
    for slot in layout.get("slots", []):
        idx = slot["index"]
        ocr_fields = [
            ("main_attr", "主属性名称"),
        ]
        for sub_index in range(1, 5):
            ocr_fields.append((f"sub_attr_{sub_index}", f"副属性{sub_index}"))
            ocr_fields.append((f"sub_attr_{sub_index}_bonus_value", f"副属性{sub_index}强化数值"))
        for field, desc in ocr_fields:
            if field not in slot:
                continue
            roi = roi_str(tuple(slot[field]))
            ocr_items.append({
                "itemName": f"result_slot_{idx}_{field}",
                "roiFront": roi,
                "roiBack": roi,
                "mode": "Single",
                "method": "Default",
                "keyword": "",
                "description": f"结果页第{idx}个御魂{desc}",
            })
    write_json(YUHUN_DIR / "result" / "ocr.json", ocr_items)

    image_items = []
    actions = layout.get("actions", {})
    action_specs = {
        "confirm_enhance": ("result_confirm_enhance", "result_confirm_enhance.png", "强化按钮"),
        "calc": ("result_calc", "result_calc.png", "计算按钮"),
        "continue_enhance": ("result_enhance", "result_enhance.png", "继续强化图标"),
        "discard": ("result_discard", "result_discard.png", "弃置按钮"),
        "restore": ("result_restore", "result_restore.png", "恢复按钮"),
    }
    for action_name, (item_name, image_name, desc) in action_specs.items():
        action = actions.get(action_name)
        if not action:
            continue
        roi = roi_str(tuple(action["roi"]))
        image_items.append({
            "itemName": item_name,
            "imageName": image_name,
            "sourceImage": action["sourceImage"],
            "roiFront": roi,
            "roiBack": roi,
            "method": "Template matching",
            "threshold": action.get("threshold", 0.8),
            "description": f"结果页·{desc}",
        })

    state_templates = {
        "selected_marker": ("result_soul_selected", "result_soul_selected.png", "御魂选中状态"),
        "discarded_marker": ("result_soul_discarded", "result_soul_discarded.png", "御魂弃置状态"),
    }
    for marker_name, (prefix, image_name, desc) in state_templates.items():
        marker = layout.get(marker_name)
        if not marker:
            continue
        roi = marker["roi"]
        sample_offset = marker.get("sample_offset")
        if sample_offset is None:
            sample_index = int(marker.get("sampleIndex", 1))
            sample_slot = next((slot for slot in layout.get("slots", []) if slot["index"] == sample_index), None)
            sample_offset = sample_slot["offset"] if sample_slot else [0, 0]
        base_roi = shift_roi(roi, -int(sample_offset[0]), -int(sample_offset[1]))
        template_roi = roi_str(tuple(roi))
        image_items.append({
            "itemName": f"{prefix}_template",
            "imageName": image_name,
            "sourceImage": marker["sourceImage"],
            "roiFront": template_roi,
            "roiBack": template_roi,
            "method": "Template matching",
            "threshold": marker.get("threshold", 0.8),
            "description": f"结果页·{desc}模板",
        })
        for slot in layout.get("slots", []):
            dx, dy = slot["offset"]
            slot_roi = roi_str(tuple(shift_roi(base_roi, dx, dy)))
            image_items.append({
                "itemName": f"{prefix}_{slot['index']}",
                "imageName": image_name,
                "roiFront": slot_roi,
                "roiBack": slot_roi,
                "method": "Template matching",
                "threshold": marker.get("threshold", 0.8),
                "description": f"结果页第{slot['index']}个御魂{desc}",
            })

    for slot in layout.get("slots", []):
        idx = slot["index"]
        # The shared bonus icon template is cropped from slot 1 / sub attr 3.
        for sub_index in [3, 1, 2, 4]:
            field = f"sub_attr_{sub_index}_bonus"
            if field not in slot:
                continue
            roi = roi_str(tuple(slot[field]))
            image_items.append({
                "itemName": f"result_slot_{idx}_{field}",
                "imageName": "result_sub_attr_bonus.png",
                "sourceImage": "result_overview.png" if idx == 1 else None,
                "roiFront": roi,
                "roiBack": roi,
                "method": "Template matching",
                "threshold": 0.8,
                "description": f"结果页第{idx}个御魂副属性{sub_index}强化标识",
            })
    for item in image_items:
        if item.get("sourceImage") is None:
            item.pop("sourceImage", None)
    write_json(YUHUN_DIR / "result" / "image.json", image_items)
    print("  synced result/temp_layout.json")


def crop_from_image_json(folder: Path, capture: Path, page: str) -> int:
    image_json = folder / "image.json"
    if not image_json.exists() or not capture.exists():
        return 0
    count = 0
    cropped: set[Path] = set()
    for item in read_json(image_json):
        roi_value = item.get("roiFront", "0,0,0,0")
        if not item.get("imageName") or roi_value == "0,0,0,0":
            continue
        dst = folder / item["imageName"]
        if dst in cropped:
            continue
        source = source_image_path(item.get("sourceImage", capture.name), page)
        crop_image(source, parse_roi(roi_value), dst)
        cropped.add(dst)
        count += 1
    return count


def crop_all() -> None:
    sync_select_layout()
    sync_enhance_layout()
    sync_result_layout()

    mapping = {
        "select": source_image_path("select_empty.png", "select"),
        "enhance": source_image_path("enhance_calc_dialog.png", "enhance"),
        "result": source_image_path("result_overview.png", "result"),
    }
    total = 0
    for folder_name, capture in mapping.items():
        print(f"\n[crop] {folder_name} <- {capture.name}")
        total += crop_from_image_json(YUHUN_DIR / folder_name, capture, folder_name)
    print(f"\n共裁剪 {total} 张模板。")


def draw_box(draw, roi: list[int], color: tuple[int, int, int], label: str, width: int = 2) -> None:
    x, y, w, h = [int(v) for v in roi]
    draw.rectangle([x, y, x + w, y + h], outline=color, width=width)
    draw.text((x + 2, y + 2), label, fill=color)


def annotate_select_image(src: Path, layout: dict) -> None:
    from PIL import Image, ImageDraw

    if not src.exists():
        raise FileNotFoundError(src)

    img = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(img)
    src_name = src.name
    grid = layout.get("grid_spec", {})
    if grid.get("sourceImage") == src_name:
        for slot in layout.get("slots", []):
            draw_box(draw, slot["click"], (0, 255, 0), f"S{slot['index']}", width=2)
    if layout.get("selection_box_sourceImage") == src_name:
        for slot in layout.get("slots", []):
            draw_box(draw, slot["selected_box"], (255, 40, 40), f"T{slot['index']}", width=2)

    confirm_panel = layout.get("confirm_panel", {})
    if "counter_ocr" in confirm_panel and layout_source(confirm_panel["counter_ocr"]) == src_name:
        draw_box(draw, layout_roi(confirm_panel["counter_ocr"]), (255, 220, 0), "COUNT", width=2)
    if "enhance_all_btn" in confirm_panel and layout_source(confirm_panel["enhance_all_btn"]) == src_name:
        draw_box(draw, layout_roi(confirm_panel["enhance_all_btn"]), (255, 130, 0), "ENHANCE_ALL", width=3)

    for name, spec in layout.get("detail_popup", {}).items():
        if layout_source(spec) == src_name:
            draw_box(draw, layout_roi(spec), (190, 80, 255), name.upper(), width=2)

    out = annotated_image_path(src, "_标注.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(out.relative_to(YUHUN_DIR))


def annotate_select_layout(capture_name: str | None = None) -> None:
    sync_select_layout()
    layout = expand_select_grid(read_select_layout())
    if capture_name:
        sources = [source_image_path(capture_name, "select")]
    else:
        sources = source_images("select")
    for src in sources:
        annotate_select_image(src, layout)


def annotate_enhance_layout() -> None:
    from PIL import Image, ImageDraw

    sync_enhance_layout()
    layout = read_enhance_layout()
    actions = layout.get("actions", {})

    colors = [(255, 130, 0), (0, 255, 255), (255, 80, 220)]
    for src in source_images("enhance"):
        if not src.exists():
            raise FileNotFoundError(src)

        img = Image.open(src).convert("RGB")
        draw = ImageDraw.Draw(img)
        for index, (name, action) in enumerate(actions.items()):
            if action.get("sourceImage") != src.name:
                continue
            roi = action["roi"]
            color = colors[index % len(colors)]
            draw_box(draw, roi, color, name.upper(), width=3)

        out = annotated_image_path(src, "_标注.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
        print(out.relative_to(YUHUN_DIR))


def annotate_result_image(src: Path, layout: dict) -> None:
    from PIL import Image, ImageDraw

    if not src.exists():
        raise FileNotFoundError(src)

    img = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(img)
    src_name = src.name
    grid = layout.get("grid_spec", {})
    if grid.get("sourceImage") == src_name:
        for slot in layout.get("slots", []):
            draw_box(draw, slot["click"], (0, 255, 0), f"R{slot['index']}", width=2)

    detail_template = layout.get("detail_template", {})
    detail_fields = ["main_attr"]
    for sub_index in range(1, 5):
        detail_fields.extend([
            f"sub_attr_{sub_index}",
            f"sub_attr_{sub_index}_bonus_value",
            f"sub_attr_{sub_index}_bonus",
        ])
    for field in detail_fields:
        spec = detail_template.get(field)
        if not spec or layout_source(spec) != src_name:
            continue
        color = (255, 220, 0)
        if field.endswith("_bonus_value"):
            color = (255, 180, 0)
        elif field.startswith("sub_attr_") and not field.endswith("_bonus"):
            color = (0, 220, 255)
        elif field.endswith("_bonus"):
            color = (255, 80, 80)
        for slot in layout.get("slots", []):
            if field in slot:
                draw_box(draw, slot[field], color, f"{slot['index']}:{field.upper()}", width=2)

    action_labels = {
        "confirm_enhance": "ENHANCE",
        "calc": "CALC",
        "continue_enhance": "CONTINUE",
        "discard": "DISCARD",
        "restore": "RESTORE",
    }
    for name, action in layout.get("actions", {}).items():
        if action.get("sourceImage") != src_name:
            continue
        draw_box(draw, action["roi"], (255, 130, 0), action_labels.get(name, name.upper()), width=3)

    for marker_name, label in [
        ("selected_marker", "SEL"),
        ("discarded_marker", "DROP"),
    ]:
        marker = layout.get(marker_name)
        if not marker or marker.get("sourceImage") != src_name:
            continue
        sample_offset = marker.get("sample_offset")
        if sample_offset is None:
            sample_index = int(marker.get("sampleIndex", 1))
            sample_slot = next((slot for slot in layout.get("slots", []) if slot["index"] == sample_index), None)
            sample_offset = sample_slot["offset"] if sample_slot else [0, 0]
        base_roi = shift_roi(marker["roi"], -int(sample_offset[0]), -int(sample_offset[1]))
        draw_box(draw, marker["roi"], (255, 40, 40), f"{label}_TEMPLATE", width=3)
        for slot in layout.get("slots", []):
            dx, dy = slot["offset"]
            draw_box(draw, shift_roi(base_roi, dx, dy), (255, 40, 40), f"{label}{slot['index']}", width=2)

    out = annotated_image_path(src, "_标注.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(out.relative_to(YUHUN_DIR))


def annotate_result_layout(capture_name: str | None = None) -> None:
    sync_result_layout()
    layout = expand_result_grid(read_result_layout())
    if capture_name:
        sources = [source_image_path(capture_name, "result")]
    else:
        sources = source_images("result")
    for src in sources:
        annotate_result_image(src, layout)


def annotate_all_layouts() -> None:
    annotate_select_layout()
    annotate_enhance_layout()
    annotate_result_layout()


def test_select_ocr(capture_name: str = "select_one_detail.png") -> None:
    import cv2
    import re
    from module.atom.ocr import RuleOcr

    sync_select_layout()
    layout = read_json(YUHUN_DIR / "select" / "temp_layout.json")
    image_path = source_image_path(capture_name, "select")
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(image_path)

    def build_rule(item, roi=None):
        if roi is None:
            roi = parse_roi(item["roiFront"])
        return RuleOcr(
            roi=roi,
            area=roi,
            mode=item["mode"],
            method=item["method"],
            keyword=item.get("keyword", ""),
            name=item["itemName"],
        )

    def parse_soul_level(text: str) -> int:
        match = re.search(r"\+(\d+)", text or "")
        return int(match.group(1)) if match else 0

    def shrink_attr_roi(roi: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        shrink = int(layout.get("detail_attr_width_shrink_level_ge_3", 0))
        if soul_level < 3 or shrink <= 0:
            return roi
        x, y, w, h = roi
        return x, y, max(1, w - shrink), h

    print(f"OCR capture: {image_path.relative_to(YUHUN_DIR)}")
    items = read_json(YUHUN_DIR / "select" / "ocr.json")
    soul_type_level_item = next((item for item in items if item["itemName"] == "soul_type_level"), None)
    soul_level = 0
    if soul_type_level_item:
        rule = build_rule(soul_type_level_item)
        result = rule.ocr(image)
        soul_level = parse_soul_level(result)
        print(f"{soul_type_level_item['itemName']}: {result!r} (level={soul_level})")

    for item in items:
        if item["itemName"] == "soul_type_level":
            continue
        roi = parse_roi(item["roiFront"])
        if item["itemName"].startswith("detail_"):
            roi = shrink_attr_roi(roi)
        rule = build_rule(item, roi)
        result = rule.ocr(image)
        print(f"{item['itemName']}: {result!r}")


def show_status() -> None:
    with open(SCRIPT_DIR / "bbox_targets.yaml", encoding="utf-8") as f:
        targets = yaml.safe_load(f) or {}
    print("asset_temp 状态：\n")
    for spec in targets.values():
        image = spec["image"]
        image_path = TEMP_ASSET_DIR / image
        bbox_path = image_path.with_suffix(".json")
        print(
            f"{image:28} image={'OK' if image_path.exists() else '缺失':4} "
            f"bbox={'OK' if bbox_path.exists() else '无'}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="御魂强化素材准备")
    parser.add_argument("--status", action="store_true", help="查看 asset_temp 状态")
    parser.add_argument("--crop-only", action="store_true", help="同步 layout 并裁剪模板")
    parser.add_argument("--annotate-select", action="store_true", help="生成选择页 16 个御魂 bbox 标注图")
    parser.add_argument("--annotate-enhance", action="store_true", help="生成强化设置页按钮模板标注图")
    parser.add_argument("--annotate-result", action="store_true", help="生成强化结果页 bbox 标注图")
    parser.add_argument("--annotate-all", action="store_true", help="基于所有 temp_layout.json 生成标注图")
    parser.add_argument("--test-select-ocr", action="store_true", help="对选择页 OCR 配置逐项识别并打印结果")
    parser.add_argument("--select-capture", help="选择页标注或 OCR 使用的截图文件名；标注不传则处理全部选择页源图")
    parser.add_argument("--result-capture", help="结果页标注使用的截图文件名；不传则处理全部结果页源图")
    args = parser.parse_args()
    if args.status:
        show_status()
        return
    if args.annotate_select:
        annotate_select_layout(args.select_capture)
        return
    if args.annotate_enhance:
        annotate_enhance_layout()
        return
    if args.annotate_result:
        annotate_result_layout(args.result_capture)
        return
    if args.annotate_all:
        annotate_all_layouts()
        return
    if args.test_select_ocr:
        test_select_ocr(args.select_capture or "select_one_detail.png")
        return
    crop_all()


if __name__ == "__main__":
    main()
