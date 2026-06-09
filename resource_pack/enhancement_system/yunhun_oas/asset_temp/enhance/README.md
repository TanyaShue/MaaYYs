# 强化设置页素材

目标：对已选 6 个御魂执行计算和强化。

## 源图与标注

源图放在 `asset_temp/enhance/`，Gemini bbox JSON 和 `*_标注.png` 与源图同目录。`temp_layout.json` 外层按 `sourceImage` 分组，每张标注图只绘制属于当前源图的 bbox。

| 源图 | 标注内容 |
|------|----------|
| `enhance_calc_dialog.png` | 计算按钮、目标等级 15 |
| `enhance_confirm.png` | 强化按钮、目标强化素材消耗区域 |

## 运行时素材

| 素材 | 类型 | 检测方式 | 是否阵列 | 说明 |
|------|------|----------|----------|------|
| `temp_layout.json` | `layout` | 脚本同步 | 否 | 强化设置页按钮模板 ROI 源配置 |
| `enhance_calc` | `template` | `Template matching` | 否 | 计算按钮 |
| `enhance_confirm` | `template` | `Template matching` | 否 | 强化确认按钮或确认弹窗按钮 |

## 待补充

- 计算完成后的状态确认素材。
- 强化失败或资源不足的异常状态素材。
