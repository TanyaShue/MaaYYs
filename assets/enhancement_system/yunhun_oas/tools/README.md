# 御魂强化工具目录

这里放御魂强化流程专用工具。

## 工具

- `yuhun_bbox_tool.py`：读取 `bbox_targets.yaml`，调用 Gemini 标 bbox，在源图同目录输出 `*.json` 和 `*_标注.png`。
- `bbox_targets.yaml`：每张截图需要 Gemini 定位的 UI 元素。
- `prepare_yuhun_assets.py`：同步 layout 到 `ocr.json` / `click.json`，按 roi 裁剪模板图。

## 常用命令

```bash
python tasks/Yuhun/tools/yuhun_bbox_tool.py status
python tasks/Yuhun/tools/yuhun_bbox_tool.py detect --review
python tasks/Yuhun/tools/yuhun_bbox_tool.py annotate

python tasks/Yuhun/tools/prepare_yuhun_assets.py --crop-only
python tasks/Yuhun/tools/prepare_yuhun_assets.py --annotate-select
python tasks/Yuhun/tools/prepare_yuhun_assets.py --annotate-select --select-capture select_one_detail.png
python tasks/Yuhun/tools/prepare_yuhun_assets.py --test-select-ocr --select-capture select_one_detail.png
```
