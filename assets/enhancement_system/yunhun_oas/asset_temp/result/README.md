# 强化结果页素材

目标：识别强化结果，决定继续强化、弃置或恢复。

## 源图与标注

源图放在 `asset_temp/result/`，Gemini bbox JSON 和 `*_标注.png` 与源图同目录。当前只保留用于标注的有效源图，多余参考图不放入此目录。

`temp_layout.json` 外层是一个按源图分组的大 list。每个元素都有 `sourceImage`，并只维护这张图上的 bbox。生成标注图时只绘制属于当前源图的 bbox，避免不同页面状态的框混在一起。

| 源图 | 用途 | 标注内容 |
|------|------|----------|
| `image.png` | 强化确认状态 | 强化按钮 |
| `result_continue_popup.png` | 继续强化弹窗 | 计算按钮 |
| `result_overview.png` | 第 1 个御魂详情样本 | 主属性名称、4 条副属性整行、每条副属性对应的强化图标位置和强化属性数值；按 3x2 扩展到全部御魂 |
| `result_sample_02_selected.png` | 结果页操作与选中状态样本 | 继续强化图标、弃置按钮、恢复按钮、第 1 个御魂选中状态高亮框局部 |
| `result_sample_03_flagged.png` | 弃置状态样本 | 第 4 个御魂弃置标识 |

第 1 个御魂详情用于确定单个卡片内的 OCR 和强化标识相对位置。由于结果页御魂按 3x2 排列，主属性、副属性整行、强化图标、强化属性数值、选中状态和弃置状态都由样本框按矩阵规则扩展到 6 个位置，并在标注图中全部画出。

矩阵规则参考选择页：在对应源图分组里用 `grid_spec` 维护 `first_slot`、`soul_size`、`gap`、`columns`、`rows`。状态标识使用 `sampleIndex` 表示样本来自第几个御魂，脚本反推第 1 格相对位置后再扩展到 3x2 全部位置。

## 运行时素材

| 素材 | 类型 | 检测方式 | 是否阵列 | 说明 |
|------|------|----------|----------|------|
| `result_slot_1..6` | `click` | 点击区域 | 是 | 结果页 6 个御魂位置 |
| `result_slot_1..6_main_attr` | `ocr` | `OCR` | 是 | 御魂主属性名称 |
| `result_slot_1..6_sub_attr_1..4` | `ocr` | `OCR` | 是 | 4 条副属性整行，名称和数值使用同一个框 |
| `result_slot_1..6_sub_attr_1..4_bonus` | `template` | `Template matching` | 是 | 4 条副属性强化图标位置 |
| `result_slot_1..6_sub_attr_1..4_bonus_value` | `ocr` | `OCR` | 是 | 4 条副属性强化后的数值区域 |
| `result_soul_selected_1..6` | `template` | `Template matching` | 是 | 结果页御魂选中状态，高亮框局部模板按 3x2 矩阵平移 |
| `result_soul_discarded_1..6` | `template` | `Template matching` | 是 | 结果页御魂弃置状态，弃置标识模板按 3x2 矩阵平移 |
| `result_enhance` | `template` | `Template matching` | 否 | 继续强化图标或继续强化入口 |
| `result_calc` | `template` | `Template matching` | 否 | 继续强化弹窗中的计算按钮 |
| `result_confirm_enhance` | `template` | `Template matching` | 否 | 强化按钮 |
| `result_discard` | `template` | `Template matching` | 否 | 弃置按钮 |
| `result_restore` | `template` | `Template matching` | 否 | 恢复按钮 |

## 当前状态

- `result/temp_layout.json` 已按人工确认后的 bbox 更新，外层为 5 个 `sourceImage` 分组。
- `result/click.json` 由 `grid_spec` 生成 6 个点击区域。
- `result/ocr.json` 当前生成 54 个 OCR 项：每个御魂 1 个主属性、4 个副属性整行、4 个强化数值。
- `result/image.json` 当前生成 43 个模板项：动作按钮、选中/弃置状态、4 条强化图标按 3x2 展开。
- `asset_temp/result/*_标注.png` 已基于当前 `temp_layout.json` 重新生成。

## 下一步

- 运行 `dev_tools/assets_extract.py` 生成运行时 `assets.py`。
- 在流程脚本中接入结果页 OCR、模板匹配和状态决策。
