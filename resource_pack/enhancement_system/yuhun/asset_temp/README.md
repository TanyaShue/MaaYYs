# 御魂强化 · 素材源文件目录

将模拟器 **1280×720** 全屏截图放在 `<页面>/` 下，作为生成模板、OCR 区域和标注图的源文件（文件名固定，便于脚本处理）。

每个页面子目录下的 `README.md` 记录该页面源图用途、标注内容、运行时素材和矩阵规则；上级 `readme.md` 只保留全局流程。

`asset_temp/` 路径用于避开 `dev_tools/assets_extract.py` 的递归 JSON 扫描；运行时模板图仍生成到 `select/`、`enhance/`、`result/` 页面目录中。

Gemini 生成的 bbox JSON 和人工检查用标注 PNG 与源图放在同一个页面目录中，例如 `select/select_empty.json`、`select/select_empty_标注.png`。

## 截图清单

| 文件名 | 界面说明 | 操作步骤 |
|--------|----------|----------|
| `select/select_empty.png` | 御魂批量强化 · 选择界面 (0/12) | 未选中任何御魂 |
| `select/select_one_detail.png` | 同上 (1/12) | 选中 1 个，中间弹出详情 |
| `select/select_three_detail.png` | 同上 (3/12) | 选中 3 个，中间弹出详情 |
| `select/select_six_ready.png` | 同上 (6/12) | 已选中 6 个，「全部强化」可点击 |
| `enhance/enhance_calc_dialog.png` | 强化设置 · 未计算 | 点「全部强化」后，显示「计算」按钮 |
| `enhance/enhance_confirm.png` | 强化设置 · 已计算 | 显示素材消耗与「强化」按钮 |
| `result/image.png` | 结果页 · 强化确认状态 | 显示「强化」按钮 |
| `result/result_overview.png` | 强化结果 (6 个御魂) | Lv.0→Lv.3 等结果卡片 |
| `result/result_continue_popup.png` | 结果页 · 继续强化弹窗 | 点「继续强化」后的设置弹窗 |
| `result/result_sample_02_selected.png` | 强化结果样例 | 多个结果卡片选中状态参考 |
| `result/result_sample_03_flagged.png` | 强化结果样例 | 带标记状态参考 |

可选：若分辨率不是 1280×720，请在对应页面的 `temp_layout.json` 中按比例调整坐标后重新跑 `prepare_yuhun_assets.py`。

## 下一步

1. 把截图放进 `<页面>/`。
2. 用 `tools/yuhun_bbox_tool.py` 运行 Gemini 初步标注。
3. 人工确认并修改页面目录下的 `temp_layout.json`。
4. 运行 `python tasks/Yuhun/tools/prepare_yuhun_assets.py --crop-only` 生成模板图与 `select/`、`enhance/`、`result/` 下的运行时 JSON。
5. 运行 `python tasks/Yuhun/tools/prepare_yuhun_assets.py --annotate-all` 重新生成标注图。
6. 确认无误后运行 `dev_tools/assets_extract.py` 生成 `assets.py`。
