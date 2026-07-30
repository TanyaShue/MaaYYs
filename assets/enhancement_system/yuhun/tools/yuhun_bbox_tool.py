"""
御魂强化截图 bbox 标定工具。

常用命令（仓库根目录执行）：
  python tasks/Yuhun/tools/yuhun_bbox_tool.py status
  python tasks/Yuhun/tools/yuhun_bbox_tool.py detect --review
  python tasks/Yuhun/tools/yuhun_bbox_tool.py annotate
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("缺少 PyYAML，请先安装 yaml 依赖。") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
YUHUN_DIR = SCRIPT_DIR.parent
TEMP_ASSET_DIR = YUHUN_DIR / "asset_temp"
TARGETS_FILE = SCRIPT_DIR / "bbox_targets.yaml"


@dataclass(frozen=True)
class TargetSpec:
    key: str
    image: str
    targets: list[str]

    @property
    def image_path(self) -> Path:
        return TEMP_ASSET_DIR / self.image

    @property
    def bbox_path(self) -> Path:
        return self.image_path.with_suffix(".json")

    @property
    def annotated_path(self) -> Path:
        return self.image_path.with_name(f"{self.image_path.stem}_标注.png")


def load_targets(path: Path = TARGETS_FILE) -> list[TargetSpec]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    specs: list[TargetSpec] = []
    for key, value in raw.items():
        image = value.get("image")
        targets = value.get("targets") or []
        if image and targets:
            specs.append(TargetSpec(key=key, image=image, targets=list(targets)))
        else:
            print(f"[skip] {key}: 缺少 image 或 targets")
    return specs


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def normalize_bbox_data(data: dict[str, Any]) -> dict[str, dict[str, int]]:
    normalized: dict[str, dict[str, int]] = {}
    for label, bbox in data.items():
        if not isinstance(bbox, dict):
            continue
        try:
            normalized[label] = {
                "x1": int(bbox["x1"]),
                "y1": int(bbox["y1"]),
                "x2": int(bbox["x2"]),
                "y2": int(bbox["y2"]),
            }
        except (KeyError, TypeError, ValueError):
            print(f"[warn] 忽略非法 bbox: {label} -> {bbox}")
    return normalized


def call_gemini_bbox(image_path: Path, targets: list[str], model: str) -> dict[str, Any]:
    from google import genai
    from google.genai.types import GenerateContentConfig, Part
    from PIL import Image
    from pydantic import BaseModel, create_model

    with Image.open(image_path) as img:
        img_width, img_height = img.size

    class BoundingBox(BaseModel):
        x1: int
        y1: int
        x2: int
        y2: int

    response_schema = create_model(
        "BoundingBoxResponse",
        **{target: (BoundingBox, ...) for target in targets},
    )

    system_prompt = f"""You are a bounding box detection assistant.
Given an image with dimensions {img_width}x{img_height} pixels and a list of targets: {targets}

Each target may be Chinese UI text, an icon, a button, or a visual area.
For each target, locate it and return x1, y1, x2, y2 in normalized 0-1000 coordinates.
Return JSON only. The keys must exactly match the target strings."""

    mime, _ = guess_type(str(image_path))
    with open(image_path, "rb") as f:
        image_part = Part.from_bytes(data=f.read(), mime_type=mime or "image/png")

    client = genai.Client(location="global")
    response = client.models.generate_content(
        model=model,
        contents=[image_part, "Detect these UI targets: " + ", ".join(targets)],
        config=GenerateContentConfig(
            temperature=0.1,
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )
    return json.loads(response.text.strip())


def normalized_to_pixel(bbox: dict[str, int], width: int, height: int) -> tuple[int, int, int, int]:
    x1 = int(bbox["x1"] * width / 1000)
    y1 = int(bbox["y1"] * height / 1000)
    x2 = int(bbox["x2"] * width / 1000)
    y2 = int(bbox["y2"] * height / 1000)
    return x1, y1, x2, y2


def draw_bounding_boxes(image_path: Path, bbox_path: Path, output_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    data = json.loads(bbox_path.read_text(encoding="utf-8"))
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    try:
        font = ImageFont.truetype("msyh.ttc", 16)
    except OSError:
        font = ImageFont.load_default()

    colors = ["red", "lime", "cyan", "yellow", "magenta", "orange", "white"]
    for index, (label, bbox) in enumerate(data.items()):
        x1, y1, x2, y2 = normalized_to_pixel(bbox, width, height)
        color = colors[index % len(colors)]
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        draw.text((x1 + 4, y1 + 4), label, fill=color, font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def detect_one(spec: TargetSpec, model: str, force: bool) -> bool:
    if not spec.image_path.exists():
        print(f"[missing] {spec.image}")
        return False
    if spec.bbox_path.exists() and not force:
        print(f"[exists] {spec.bbox_path.relative_to(YUHUN_DIR)}，跳过；需要重跑加 --force")
        return True

    print(f"\n[detect] {spec.image}")
    for target in spec.targets:
        print(f"  - {target}")
    data = call_gemini_bbox(spec.image_path, spec.targets, model)
    write_json(spec.bbox_path, normalize_bbox_data(data))
    print(f"[write] {spec.bbox_path.relative_to(YUHUN_DIR)}")
    return True


def annotate_one(spec: TargetSpec) -> bool:
    if not spec.image_path.exists():
        print(f"[missing] {spec.image}")
        return False
    if not spec.bbox_path.exists():
        print(f"[missing] {spec.bbox_path.relative_to(YUHUN_DIR)}")
        return False
    draw_bounding_boxes(spec.image_path, spec.bbox_path, spec.annotated_path)
    print(f"[annotate] {spec.annotated_path.relative_to(YUHUN_DIR)}")
    return True


def confirm_one(spec: TargetSpec) -> bool:
    print(f"请打开标注图确认: {spec.annotated_path}")
    while True:
        answer = input("bbox 是否正确？输入 y/n: ").strip().lower()
        if answer in {"y", "n"}:
            return answer == "y"
        print("请输入 y 或 n。")


def filter_specs(specs: list[TargetSpec], only: str | None) -> list[TargetSpec]:
    if not only:
        return specs
    wanted = {x.strip() for x in only.split(",") if x.strip()}
    return [
        spec
        for spec in specs
        if spec.key in wanted or spec.image in wanted or Path(spec.image).stem in wanted
    ]


def command_status(specs: list[TargetSpec]) -> int:
    print("截图 / bbox / 标注图状态：\n")
    for spec in specs:
        img = "OK" if spec.image_path.exists() else "缺失"
        bbox = "OK" if spec.bbox_path.exists() else "无"
        annotated = "OK" if spec.annotated_path.exists() else "无"
        print(f"{spec.image:28} image={img:4} bbox={bbox:4} annotated={annotated}")
    return 0


def command_detect(args: argparse.Namespace, specs: list[TargetSpec]) -> int:
    selected = filter_specs(specs, args.only)
    for spec in selected:
        if not detect_one(spec, args.model, args.force):
            return 1
        if not annotate_one(spec):
            return 1

    if args.review:
        failed = review_specs(selected)
        while failed:
            names = ", ".join(spec.key for spec in failed)
            print(f"\n以下 bbox 需要重跑: {names}")
            answer = input("是否仅重新调用 Gemini 生成这些失败项？输入 y/n: ").strip().lower()
            if answer != "y":
                return 2
            rerun_failed(failed, args.model)
            failed = review_specs(failed)
    return 0


def review_specs(specs: list[TargetSpec]) -> list[TargetSpec]:
    """统一确认所有标注图，返回用户标记为 n 的项。"""
    failed: list[TargetSpec] = []
    print("\n开始统一确认标注图。")
    for spec in specs:
        if not confirm_one(spec):
            failed.append(spec)
    if not failed:
        print("\n全部 bbox 已确认。")
    return failed


def rerun_failed(specs: list[TargetSpec], model: str) -> None:
    for spec in specs:
        if not detect_one(spec, model=model, force=True):
            continue
        annotate_one(spec)


def command_annotate(args: argparse.Namespace, specs: list[TargetSpec]) -> int:
    ok = True
    for spec in filter_specs(specs, args.only):
        ok = annotate_one(spec) and ok
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="御魂强化 Gemini bbox 标定工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="查看 asset_temp 准备状态")

    detect = sub.add_parser("detect", help="调用 Gemini 识别 bbox 并生成标注图")
    detect.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini 模型名")
    detect.add_argument("--force", action="store_true", help="覆盖已有 bbox json")
    detect.add_argument("--review", action="store_true", help="全部生成后统一 y/n 确认；n 的项可批量重跑")
    detect.add_argument("--only", help="只处理指定 key / 图片名，逗号分隔")

    annotate = sub.add_parser("annotate", help="根据已有 bbox json 重新画标注图")
    annotate.add_argument("--only", help="只处理指定 key / 图片名，逗号分隔")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    specs = load_targets()
    if args.command == "status":
        return command_status(specs)
    if args.command == "detect":
        return command_detect(args, specs)
    if args.command == "annotate":
        return command_annotate(args, specs)
    return 1


if __name__ == "__main__":
    sys.exit(main())
