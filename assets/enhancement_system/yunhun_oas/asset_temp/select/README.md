# 御魂选择页素材

目标：在 4x4 待整理区中逐个检查御魂，直到选中 6 个值得强化的御魂。

## 源图与标注

源图放在 `asset_temp/select/`，Gemini bbox JSON 和 `*_标注.png` 与源图同目录。`temp_layout.json` 外层按 `sourceImage` 分组，每张标注图只绘制属于当前源图的 bbox。

| 源图 | 标注内容 |
|------|----------|
| `select_empty.png` | 全部强化、第 1 个御魂等级数字、列表第 1 个御魂图标区域 |
| `select_one_detail.png` | 主属性文字区域、副属性第 1-4 行 |
| `select_three_detail.png` | 3 个御魂已选状态参考；当前无运行时 bbox，保留给后续减号按钮等素材标注 |
| `select_six_ready.png` | 确认强化御魂数量文字、全部强化、第 1/2/3/5/7/8 个御魂选中标记区域 |

## 运行时素材

| 素材 | 类型 | 检测方式 | 是否阵列 | 说明 |
|------|------|----------|----------|------|
| `grid_spec` | `layout` | 脚本推导 | 是 | 只维护第一个御魂 bbox、横纵间距、御魂尺寸，生成 16 个候选格 |
| `slot_1..slot_16` | `click` | 点击区域 | 是 | 由 `grid_spec` 生成，用于点击候选御魂 |
| `select_slot_1_selected..select_slot_16_selected` | `template` | `Template matching` | 是 | 使用单模板 `select_slot_selected.png`，在每个平移 ROI 内判断是否选中 |
| `soul_type_level` | `ocr` | `OCR` | 否 | 位于详情弹窗，识别御魂类型和等级，如 `招财猫+12` |
| `detail_main_attr` | `ocr` | `OCR` | 否 | 详情弹窗主属性；等级 `>=3` 时宽度减少 30 px |
| `detail_sub_attr_1..4` | `ocr` | `OCR` | 否 | 详情弹窗副属性；等级 `>=3` 时宽度减少 30 px |
| `select_confirm_count` | `ocr` | `OCR` | 否 | 右侧确认区 `(N/12)`，用于校验选中数量 |
| `select_enhance_all` | `template` | `Template matching` | 否 | 点击「全部强化」进入强化设置页 |

## 流程摘要

按候选格顺序点击御魂，OCR 详情后调用 `D:\Software\yys\resource\yuhun` 判断是否值得强化。不值得则再次点击取消选中，值得则保留，直到选满 6 个。进入强化前需要校验状态器记录、最终计算结果和画面选中状态一致。
