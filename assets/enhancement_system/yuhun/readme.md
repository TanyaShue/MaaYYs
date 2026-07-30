# 御魂强化自动化

目标：自动完成阴阳师御魂批量强化。流程从御魂选择页开始，逐个识别御魂类型、等级、主属性和副属性，调用外部御魂决策模块 `D:\Software\yys\resource\yuhun` 判断是否值得强化；不值得则取消选中，直到选满 6 个。随后进入强化设置页执行计算和强化，再在强化结果页判断继续强化或弃置，循环直到御魂强化到 15 或弃置。

## 开发规范

新流程开发统一按这个顺序推进：

1. 规划流程：明确目标、页面划分、页面动作、终止条件和状态器。
2. 约定单页素材：先写清素材用途、类型、检测方式、是否阵列、坐标来源、验证截图和动态规则。
3. 生成素材并截图验证：生成配置、裁剪模板、输出标注图，用户确认后继续。
4. 逐页重复素材准备：一个页面稳定后再进入下一个页面。
5. 流程脚本调试：连接模拟器实际跑流程，每一步识别后都要求用户输入 `y/n`，`n` 则停止并回到素材配置。

脚本运行时只依赖两类识别：`OCR` 和 `Template matching`。

## 目录规范

```text
tasks/Yuhun/
├── readme.md                 # 本文：流程、规范、素材大纲、TODO
├── asset_temp/               # 标定用源截图和工具输出，避开 assets_extract.py
│   ├── README.md
│   ├── select/               # 选择页源截图、bbox、标注图和 README.md
│   ├── enhance/              # 强化设置页源截图、bbox、标注图和 README.md
│   ├── result/               # 强化结果页源截图、bbox、标注图和 README.md
│   └── _unused/              # 暂不使用的参考截图
├── select/                   # 御魂选择页面素材
│   ├── temp_layout.json      # 页面源布局，只存人工可维护参数
│   ├── image.json            # 模板匹配素材
│   ├── ocr.json              # OCR 素材
│   ├── click.json            # 点击区域
│   └── *.png                 # 裁剪后的模板图
├── enhance/                  # 强化设置页面运行时素材
├── result/                   # 强化结果页面运行时素材
├── tools/                    # bbox、素材生成、OCR 测试工具
├── assets.py                 # 由 dev_tools/assets_extract.py 生成的运行时资产
├── config.py                 # 本任务配置；是否值得强化的决策逻辑在 D:\Software\yys\resource\yuhun
├── script_common.py          # 共享状态、OCR 解析、决策模块接入和等级更新逻辑
├── script_select.py          # 御魂选择页脚本
├── script_enhance.py         # 强化设置页脚本
├── script_result.py          # 强化结果页脚本
└── script_task.py            # 主流程串联入口：选择 -> 强化 -> 结果循环
```

目录约定：

- `asset_temp/<page>/` 放原始截图、Gemini bbox JSON 和标注 PNG。
- 标注图与源图同目录，文件名统一使用 `*_标注.png`；带 `sourceImage` 的 bbox 只画在对应源图上。
- 页面目录按页面语义命名，如 `select/`、`enhance/`、`result/`。
- `temp_layout.json` 是源配置，不写入大量派生 bbox；文件名带 `temp`，避免 `assets_extract.py` 扫描。
- `image.json`、`ocr.json`、`click.json` 是运行时资产输入，可由工具从 `temp_layout.json` 同步生成。
- 裁剪得到的运行时模板图必须放在对应页面目录，和 `image.json` 同目录，以符合 `assets_extract.py` 的 `imageName` 路径约定。

`assets_extract.py` 约束：

- 它会递归读取任务目录下所有 `*.json`，但跳过路径中包含 `temp` 的文件。
- 它生成 `RuleImage.file` 时只使用 `image.json` 所在目录加 `imageName`，不读取 `sourceImage`。
- 因此，所有非运行时 JSON 必须放在带 `temp` 的路径中，例如 `asset_temp/` 或 `temp_layout.json`。
- 运行时模板 PNG 必须和对应页面的 `image.json` 放在同一个目录，例如 `enhance/enhance_calc.png`。
- `sourceImage` 只给素材准备工具使用，用于从 `asset_temp/<page>/` 的源截图裁剪运行时模板。

单页素材规范：

- 每个页面目录都保留 `temp_layout.json`，作为人工维护的 bbox 源配置。
- `temp_layout.json` 只存手动标定参数，如按钮 ROI、源图、阵列起点、间距、动态规则；不要写入大量派生坐标。
- 对多张源图共同组成的页面，`temp_layout.json` 优先使用按 `sourceImage` 分组的 list，便于逐图标注和人工调整。
- `prepare_yuhun_assets.py` 负责从 `temp_layout.json` 同步生成或更新 `image.json`、`ocr.json`、`click.json`。
- `asset_temp/<page>/` 中的源图、bbox JSON、标注 PNG 只用于开发和验证，不作为运行时资产直接引用。
- 用户确认标注图后，再运行 `--crop-only` 生成页面目录下的运行时模板 PNG。
- 每个页面的源图用途、标注目标和运行时素材清单写在 `asset_temp/<page>/README.md`，主文档只保留全局流程和规范。

素材准备闭环：

1. 提供素材描述：在文档和 `tools/bbox_targets.yaml` 中说明当前页面有哪些素材、用途、识别方式、是否阵列、是否有动态规则。
2. Gemini 初步标框：运行 `yuhun_bbox_tool.py detect --review`，在 `asset_temp/<page>/` 的源图旁生成 `<截图名>.json` 和 `<截图名>_标注.png`。
3. 生成源布局：根据 Gemini bbox JSON 和页面规则，由素材脚本生成或更新页面目录下的 `temp_layout.json`。
4. 人工微调：人工查看 `*_标注.png`，只修改 `temp_layout.json` 中需要手动维护的源参数。
5. 同步运行时资产：运行 `prepare_yuhun_assets.py --crop-only`，脚本基于 `temp_layout.json` 更新 `image.json`、`ocr.json`、`click.json`，并裁剪运行时模板 PNG。
6. 验证后提取：标注图和 OCR 测试通过后，再运行 `dev_tools/assets_extract.py` 生成运行时 `assets.py`。

## 工具链

素材准备工具链：

1. `tools/bbox_targets.yaml`：记录每张 `asset_temp/<page>/*.png` 要交给 Gemini 检测的 UI 元素。
2. `yuhun_bbox_tool.py`：调用 Gemini 标框，在源图同目录输出 bbox JSON 和 `*_标注.png`。
3. `prepare_yuhun_assets.py`：基于 `temp_layout.json` 同步运行时 JSON、裁剪模板、生成页面标注图、测试 OCR。
4. `dev_tools/assets_extract.py`：从页面目录的运行时 JSON 和模板 PNG 生成 `assets.py`。

常用命令：

```powershell
.\toolkit\python tasks\Yuhun\tools\yuhun_bbox_tool.py status
.\toolkit\python tasks\Yuhun\tools\yuhun_bbox_tool.py detect --review
.\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --status
.\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --crop-only
.\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --annotate-select
.\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --annotate-enhance
.\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --annotate-all
$env:PYTHONIOENCODING='utf-8'; .\toolkit\python tasks\Yuhun\tools\prepare_yuhun_assets.py --test-select-ocr --select-capture select_one_detail.png
.\toolkit\python dev_tools\assets_extract.py
```

## 素材描述规范

每个素材都应说明：

| 字段 | 含义 | 是否必填 |
|------|------|----------|
| `itemName` | 程序内唯一名称 | 是 |
| `description` | 给用户和模型看的语义描述 | 是 |
| `assetType` | `click`、`ocr`、`template`、`layout`、`array` | 建议 |
| `method` | `OCR` 或 `Template matching`；点击区域可为空 | 识别素材必填 |
| `array.enabled` | 是否由阵列规则生成 | 阵列素材必填 |
| `array.source` | 阵列源配置，如 `select/temp_layout.json` | 阵列素材必填 |
| `sourceImage` | 裁剪模板使用的截图 | 模板素材必填 |
| `roiFront` / `roiBack` | 运行时 ROI | 运行时素材必填 |
| `dynamicRules` | 动态调整规则，如等级 `>=3` 时宽度减少 | 有动态规则时必填 |

现有框架已经使用 `itemName`、`description`、`method`、`sourceImage`、`roiFront`、`roiBack`。后续新增字段用于文档化和通用工具扩展，运行时代码可以暂时忽略。

## 页面流程

| 页面 | 目标 | 大致动作 | 进入下一页条件 |
|------|------|----------|----------------|
| 御魂选择页面 | 选出 6 个值得强化的御魂 | 点击候选御魂、OCR 详情、计算 worth、不值得则取消选中、最终校验选中状态 | 选中数量为 6，状态器与画面一致 |
| 强化设置页面 | 对已选御魂执行计算和强化 | 点击计算、确认强化 | 强化动作完成并进入结果页 |
| 强化结果页面 | 判断继续强化或弃置 | OCR 主属性、副属性整行和本轮强化数值，模板匹配强化图标、选中状态、弃置状态，保留值得继续强化的御魂，弃置不值得的御魂 | 本轮处理完成，返回选择页或继续强化 |

## 脚本结构

运行脚本按页面拆分，便于单页调试：

| 脚本 | 职责 | 入口要求 |
|------|------|----------|
| `script_common.py` | 公共基类、`SelectSoulInfo`、OCR 后处理、属性解析、决策配置切换、最低等级御魂 +3 | 不单独运行 |
| `script_select.py` | 选择页逐个识别 16 个候选御魂，调用决策模块，选满 6 个后点击「全部强化」 | 当前画面已在御魂批量强化选择页 |
| `script_enhance.py` | 强化设置页点击「计算」和「强化」；计算按钮按 1s 间隔点到消失，强化按钮单击一次 | 当前画面已在强化设置页 |
| `script_result.py` | 结果页识别 6 个御魂，先用低阈值配置决定弃置，再用正常配置决定继续强化，并循环处理 | 由 `script_task.py` 传入选择页记录的御魂状态 |
| `script_task.py` | 主流程入口，持续循环执行选择页、强化页和结果页流程 | 当前画面已在御魂批量强化选择页 |

脚本直接运行时会使用 `Config("tmp_ios")` 和 `Device(config)` 连接设备，不会主动执行 `RestartTask(...).app_start()`，因此调试前需要手动停在对应页面。

常用运行命令：

```powershell
cd tasks\Yuhun
..\..\toolkit\python .\script_select.py
..\..\toolkit\python .\script_enhance.py
..\..\toolkit\python .\script_task.py
```

决策模块位于 `D:\Software\yys\resource\yuhun`。选择页和继续强化默认使用 `enhancement_system\config\decision_config.json`；结果页弃置判断使用 `enhancement_system\config\decision_config_low.json`。

等级状态由脚本维护：选择页记录初始等级；每次强化后，本轮参与继续强化的御魂中所有最低等级御魂都会 `current_level += 3`，更高等级御魂不变。

结果页弃置后，游戏会把弃置御魂挪到列表末尾；脚本也会同步重排内存中的御魂顺序，保证后续 `result_slot_N` 仍对应画面上的第 N 个御魂。

结果页继续强化后，游戏会把本轮强化的御魂挪到列表最前；脚本会同步把继续强化的未弃置御魂移动到前方，未参与强化的未弃置御魂排在其后，弃置御魂仍在末尾。

## 页面文档

各页面的素材图、标注目标、运行时资产和页面内流程放在对应 `asset_temp` 页面目录，避免主文档持续变大：

| 页面 | 文档 | 内容 |
|------|------|------|
| 御魂选择页 | `asset_temp/select/README.md` | 4x4 候选御魂阵列、详情 OCR、选中状态、全部强化入口 |
| 强化设置页 | `asset_temp/enhance/README.md` | 计算按钮、强化按钮和强化设置页状态 |
| 强化结果页 | `asset_temp/result/README.md` | 结果页源图、3x2 御魂详情 OCR、强化图标/数值、状态标识矩阵、继续/弃置/恢复操作 |

## TODO

### 素材工具链

- [x] 建立 `asset_temp/`、`select/`、`enhance/`、`result/`、`tools/` 目录结构
- [x] 准备 `bbox_targets.yaml`，描述每张截图需要 Gemini 定位的 UI 元素
- [x] 实现 `yuhun_bbox_tool.py detect --review`
- [x] 实现 `prepare_yuhun_assets.py --crop-only`
- [x] 用 `select_slot_selected.png` 单模板匹配判断待整理区御魂是否选中
- [x] 选择页 OCR 测试通过，并支持等级 `>=3` 时属性框宽度减少 30 px
- [x] 三页 `temp_layout.json` 统一为按 `sourceImage` 分组的 list
- [x] 根据确认后的 bbox 微调 `result/temp_layout.json`，并生成 `result/image.json`、`result/ocr.json`、`result/click.json`
- [x] 运行 `dev_tools/assets_extract.py` 生成 `tasks/Yuhun/assets.py`

### 强化流程实现

- [x] 新建/完善 `script_task.py`，连接模拟器并从当前御魂批量强化界面开始运行
- [x] 选择界面：依次点击御魂，OCR 识别类型、等级、主属性、副属性
- [x] 调试模式可开启每步识别后等待用户输入 `y/n`；默认关闭以支持自动化运行
- [x] 调用 `D:\Software\yys\resource\yuhun` 判断是否值得强化；不值得则取消选中
- [x] 选满 6 个后点击「全部强化」→「计算」→「强化」
- [x] 结果页：识别 6 个御魂主属性、副属性整行、本轮强化图标和强化数值
- [x] 结果页：先用低阈值配置决定弃置，再用正常配置决定继续强化
- [x] 循环直到全部御魂强化到 15 或弃置
- [x] 点击返回，回到御魂选择界面继续下一轮

### 后续优化

- [ ] 将默认号位从 `default_slot` 配置逐步改为画面 OCR / 模板识别。
- [ ] 将更多常见御魂名称 OCR 误识别加入 `SOUL_TYPE_OCR_FIXES`。
- [ ] 根据实机日志继续微调结果页强化图标、弃置标识和选中状态模板。
