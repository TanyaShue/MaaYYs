<div align="center">
  <img src="assets/logo/logo.png" alt="MaaYYs Logo" width="256" height="256" />
  <h1>MaaYYs</h1>
  <p>基于 <a href="https://github.com/MaaXYZ/MaaFramework" target="_blank">MaaFramework</a> 与 <a href="https://github.com/MistEO/MXU" target="_blank">MXU</a> 的阴阳师自动化资源包</p>
  <p>
    <a href="https://github.com/TanyaShue/MaaYYs/actions/workflows/build-release.yml" target="_blank">
      <img src="https://img.shields.io/github/actions/workflow/status/TanyaShue/MaaYYs/build-release.yml?branch=main&label=Build" alt="Build Status" />
    </a>
    <a href="https://github.com/TanyaShue/MaaYYs/releases" target="_blank">
      <img src="https://img.shields.io/github/v/release/TanyaShue/MaaYYs?label=Release" alt="GitHub Release" />
    </a>
    <a href="https://mirrorchyan.com/zh/projects?rid=MaaYYs&source=maayysgh-readme" target="_blank">
      <img src="https://img.shields.io/badge/Mirror%E9%85%B1-%239af3f6?logo=countingworkspro&logoColor=4f46e5" alt="Mirror酱" />
    </a>
    <img src="https://img.shields.io/badge/Go-1.24-00ADD8?logo=go&logoColor=white" alt="Go 1.24" />
    <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
  </p>
</div>

---

## 简介

MaaYYs 是一个面向《阴阳师》模拟器环境的自动化项目，项目本体由 MaaFramework 流程资源、MXU 图形界面和 Go 编写的自定义 agent 组成。

普通用户下载 Release 中的全量包即可使用；开发者可以在本仓库维护任务、素材、资源包和 agent 逻辑。CI 会自动编译 agent、打包 MaaFramework 与 MXU，并发布多平台成品包。

> 本项目仅用于学习与交流。自动化行为可能受到游戏版本、模拟器环境、庭院皮肤、区服包名等因素影响，请自行承担使用风险。

## 下载

前往 [GitHub Releases](https://github.com/TanyaShue/MaaYYs/releases) 下载对应系统的 `MXU` 全量包：

| 平台 | 文件名示例 |
| --- | --- |
| Windows x64 | `MaaYYs-win-x86_64-vx.x.x-MXU.zip` |
| Windows ARM64 | `MaaYYs-win-aarch64-vx.x.x-MXU.zip` |
| macOS Intel | `MaaYYs-macos-x86_64-vx.x.x-MXU.tar.gz` |
| macOS Apple Silicon | `MaaYYs-macos-aarch64-vx.x.x-MXU.tar.gz` |
| Linux x64 | `MaaYYs-linux-x86_64-vx.x.x-MXU.tar.gz` |

绝大多数 Windows 用户请选择 `MaaYYs-win-x86_64-*-MXU.zip`。

如果你有 Mirror 酱 CDK，也可以通过 [Mirror 酱高速下载](https://mirrorchyan.com/zh/projects?rid=MaaYYs&source=maayysgh-readme) 获取最新版本。

## 快速开始

1. 下载并解压 `MaaYYs-平台-架构-版本-MXU` 全量包。
2. Windows 双击运行 `mxu.exe`；macOS / Linux 运行解压目录中的 `mxu`。
3. 打开安卓模拟器，并确保模拟器已开启 ADB 调试。
4. 在 MXU 中添加设备，选择自动搜索到的模拟器，或手动填写 ADB 路径和地址。
5. 选择对应资源：官服、B 站服、华为服、应用宝服、OPPO 服、VIVO 服等。
6. 勾选并配置要运行的任务，通常请从庭院界面启动；`打开游戏`、`关闭游戏` 等任务除外。

更详细的图文教程见 [doc/使用指南.md](doc/使用指南.md)。

## 支持的资源

当前 `interface.json` 中内置以下资源配置：

- 官服：适合雷电、MuMu 等模拟器下载的官服客户端。
- 官服2：基础官服资源。
- 官服3：适合 TapTap 下载的官服客户端。
- B 站服。
- 华为渠道服。
- 应用宝渠道服。
- OPPO 渠道服。
- VIVO 渠道服。

如果你的渠道服无法启动或识别，可以在交流群反馈包名、启动方式和卡住的截图。

## 主要任务

当前任务入口包括：

- 启停与通用：打开游戏、关闭游戏、日常奖励领取、网易大神签到、自动购物、式神图鉴分享。
- 日常与养成：式神委派、寮三十捐材料、结界奖励领取、投喂宠物、肝绘卷。
- 副本与挑战：自动御魂、自动御灵、自动业原火、自动秘闻、自动麒麟、困28、组队副本、英杰试炼、契灵探查。
- PVP / 突破 / 活动：结界突破、自动寮突破、自动道馆突破、自动斗技、自动地鬼、自动逢魔、自动阴界之门、自动悬赏、活动爬塔、限时活动。

任务能力以仓库中的 `tasks/*.json` 与 `resource_pack/*/pipeline` 为准。部分任务需要填写队伍预设、挑战次数、目标副本或开关选项，建议尽量避免在队伍预设名称中使用复杂符号和空格，降低 OCR 识别失败概率。

## 常见问题

### 找不到模拟器怎么办？

先确认模拟器已经启动，并开启 ADB 调试。自动搜索失败时，可以手动填写：

- ADB 路径：模拟器安装目录下的 `adb.exe`。
- ADB 地址：常见格式为 `127.0.0.1:5555`、`127.0.0.1:16384` 或 `emulator-5554`。

MuMu 可在设置或设备诊断中查看端口；雷电多开端口通常随实例递增。

### 为什么任务卡在某个界面？

常见原因包括：

- 没有从任务预期界面启动，例如普通任务通常需要在庭院开始。
- 模拟器分辨率、区服客户端、庭院皮肤或游戏 UI 与素材不匹配。
- 队伍预设名称 OCR 识别失败。
- 游戏更新后按钮、图标或页面结构发生变化。

请尽量带上截图、任务名、资源选择、模拟器名称和日志反馈。

### 首次启动为什么比较慢？

全量包已经包含 MaaFramework、MXU、资源和 agent，但首次连接设备、初始化运行目录或加载资源时仍可能需要等待。请不要在初始化过程中频繁暂停或关闭程序。

## 开发说明

### 本地运行完整流程

这个仓库本身主要保存 MaaYYs 的资源、任务配置和 Go agent 源码。`mxu.exe`、`maafw/`、已编译的 `agent.exe` 由 Release 全量包或 CI 产物提供，通常不会作为源码提交。想在本地跑完整流程，推荐先准备一个可运行的全量包目录，再把源码仓库放进去开发。

推荐目录形态：

```text
MaaYYs/
├── mxu.exe                 # Windows 图形界面入口，来自 Release 全量包
├── maafw/                  # MaaFramework 运行库，来自 Release 全量包
├── agent/
│   ├── agent.exe           # 本地编译出的 agent
│   └── *.go                # agent 源码
├── assets/
├── resource_pack/
├── tasks/
├── interface.json
└── README.md
```

如果你是从零开始：

1. 下载最新的 `MaaYYs-win-x86_64-*-MXU.zip` 并解压。
2. 用 git clone 的仓库内容覆盖或替换解压目录中的同名源码目录与文件。
3. 确认仓库根目录下存在 `mxu.exe` 和 `maafw/`。
4. 编译 agent。
5. 启动 `mxu.exe`，添加模拟器设备，选择资源和任务进行验证。

仓库主要结构：

```text
.
├── agent/                 # Go agent，自定义 action / recognition
├── assets/                # 图标、答案表等通用资源
├── doc/                   # 使用文档与截图
├── resource_pack/         # MaaFramework pipeline、image、model 等资源包
├── tasks/                 # MXU / interface 导入的任务配置
├── interface.json         # Maa 项目入口、资源、agent、任务导入配置
└── .github/workflows/     # 构建、发布、Mirror 酱同步工作流
```

### 编译 agent

Windows：

```powershell
cd agent
go mod download
go build -o agent.exe .
```

macOS / Linux：

```bash
cd agent
go mod download
go build -o agent .
chmod +x agent
```

`interface.json` 中配置了：

```json
{
  "agent": {
    "child_exec": ".\\agent\\agent.exe",
    "child_args": []
  }
}
```

所以 Windows 本地调试时，编译出的 `agent.exe` 需要放在 `agent/agent.exe`。如果要在 macOS / Linux 本地调试，需要按对应平台调整 `child_exec`，或使用 CI 打出的对应平台包。

### 启动完整 UI 调试

在仓库根目录确认以下文件存在：

```powershell
Test-Path .\mxu.exe
Test-Path .\maafw\MaaFramework.dll
Test-Path .\agent\agent.exe
```

然后启动：

```powershell
.\mxu.exe
```

启动后按这个顺序验证：

1. 添加设备，确保模拟器处于运行状态且 ADB 调试已开启。
2. 选择资源包，例如官服、B 站服或对应渠道服。
3. 选择一个影响范围小的任务先跑，例如 `日常奖励领取`、`投喂宠物` 或单步较短的测试任务。
4. 确认日志里没有 agent 启动失败、资源加载失败、pipeline 找不到节点等错误。
5. 再验证你实际修改的任务或素材。

### 修改资源后的验证方式

- 改 `tasks/*.json`：通常需要在 MXU 里重新加载资源，必要时重启 MXU。
- 改 `resource_pack/*/pipeline/*.json`：重新启动对应任务验证；如果界面仍使用旧配置，重启 MXU。
- 改 `resource_pack/*/image/*`：重新启动任务验证识别效果。
- 改 `agent/**/*.go`：必须重新 `go build -o agent.exe .`，并重启 MXU 或重新启动任务，让新的 agent 子进程生效。
- 改 `interface.json`：建议直接重启 MXU，确认资源、controller、agent 和 import 都能重新加载。

### 提交前检查

建议提交前至少跑一遍：

```powershell
cd agent
go build -o agent.exe .
cd ..
```

再检查 JSON 是否能被解析：

```powershell
powershell -NoProfile -Command "Get-Content -Raw interface.json | ConvertFrom-Json | Out-Null; Get-ChildItem tasks -Filter *.json | ForEach-Object { Get-Content -Raw $_.FullName | ConvertFrom-Json | Out-Null }; 'json ok'"
```

最后用 `mxu.exe` 跑一次受影响任务。CI 会帮你做多平台 agent 编译和打包，但本地实际跑通能更早发现素材、路径、任务选项和模拟器环境问题。

## CI 与发布

本仓库的主工作流为 `.github/workflows/build-release.yml`：

- 分支 push 与 PR 会在相关文件变化时构建测试包。
- 推送形如 `v1.2.3`、`v1.2.3-beta.1` 的 tag 会触发正式发布。
- 发布时会把 `interface.json` 中的 `version` 更新为 tag。
- CI 会编译 Go agent，并下载固定版本 MaaFramework（v5.11.1）与 MXU。
- 打包内容包括 `maafw/`、`mxu` 或 `mxu.exe`、`agent/`、`assets/`、`resource_pack/`、`tasks/`、`interface.json`、`LICENSE`、`README.md`。
- Windows 产物发布为 `.zip`，macOS / Linux 产物发布为 `.tar.gz`。
- Release note 由 `git-cliff` 和 `.github/cliff.toml` 生成。
- Release 创建后会触发 Mirror 酱上传与 release note 同步。

开发者提交建议使用 Conventional Commits，例如：

```text
feat: 添加新的活动任务
fix: 修复御魂目标识别
docs: 更新使用说明
ci: 调整发布流程
```

包含 `[skip changelog]` 的提交不会进入自动更新日志。

## 贡献

欢迎提交任务、素材、识别修复、文档和 CI 改进。提交 PR 前请尽量确认：

- 修改后的 JSON 可被正常解析。
- 新增素材路径与 pipeline 引用一致。
- 涉及 Go agent 的改动可以通过 `go build`。
- README、使用指南或任务说明与实际行为一致。

交流群：`645818258`。

## 鸣谢

感谢 [MaaFramework](https://github.com/MaaXYZ/MaaFramework)、[MXU](https://github.com/MistEO/MXU)、Mirror 酱以及所有提供素材、反馈和代码贡献的朋友。

## 许可

本项目使用 [MIT License](LICENSE) 发布。
