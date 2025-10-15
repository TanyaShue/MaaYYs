<div align="center">
  <img src="assets/logo/logo.png" alt="MaaYYs Logo" width="256" height="256" />
  <h1>MaaYYs</h1>
  <p>基于 <a href="https://github.com/MaaXYZ/MaaFramework" target="_blank">MaaFramework</a> 的痒痒鼠自动化应用，助力玩家高效完成日常任务</p>
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python" />
    <a href="https://mirrorchyan.com/zh/projects" target="_blank">
      <img src="https://img.shields.io/badge/Mirror%E9%85%B1-%239af3f6?logo=countingworkspro&logoColor=4f46e5" alt="Mirror酱" />
    </a>
  </p>
</div>  

---

## 目录
- [简介](#简介)
- [功能介绍](#功能介绍)
- [安装与使用指南](#安装与使用指南)
  - [快速开始](#快速开始)
  - [开发者使用](#开发者使用)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [鸣谢](#鸣谢)
- [许可协议](#许可协议)

---

## 简介

**MaaYYs** 是由 Tanyashue 开发的游戏自动化工具，旨在帮助玩家完成每日任务，如签到、领取奖励以及自动挂樱饼副本等。  
**注意：** 本项目仅提供每日任务及部分副本的自动化操作，不支持全自动战斗，部分功能仍在开发和完善中。  
**注意：** 本项目当前仅支持模拟器,不支持pc客户端  

---

## 功能介绍

- **每日任务自动化**  
  自动完成签到、领取每日奖励、邮箱领取及每日商店签到等任务。

- **副本自动化**  
  针对樱饼副本提供自动挂副本功能（注：不支持全自动战斗、自动探索或自动御魂副本）。

- **其他自动化功能**
  - 自动地鬼
  - 自动突破（稳定57级，最后一个任务将自动退出并重试）
  - 自动悬赏
  - 自动结界收菜（挂卡功能暂不支持）
  - 自动逢魔
  - 各种挑战任务的分队预设切换
  - 定时启动脚本
  - 多开模拟器同时运行

> **注意事项：**  
> - 请在各挑战设置中配置分队，否则无法实现自动切换。  
> - 支持自定义分队，分队预设可在对应的任务设置中修改。  
> - 部分游戏场景可能因素材不足而无法识别，欢迎大家贡献素材以完善功能！

---

## 安装与使用指南

### 快速开始

只需**下载全量包**并解压，然后直接运行应用即可。全量包内已包含所需的所有文件和资源，无需额外安装步骤。


### 开发者使用

如果您需要进行二次开发或对项目进行调试，可参考以下步骤：

1. **克隆 MFWPH 项目：**
   ```bash
   git clone https://github.com/TanyaShue/MFWPH.git
   ```

2. **在 MFWPH 目录下的 `assets/resource` 文件夹中克隆 MaaYYs 仓库：**
   ```bash
   cd MFWPH/assets/resource
   git clone https://github.com/TanyaShue/MaaYYs.git
   ```

3. **安装依赖：**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序：**
   ```bash
   python main.py
   ```

> **提示：** 启动后请在各挑战的设置中确保已正确设置分队。   
> **提示：** 确保任务启动时位于庭院(打开游戏的任务不用)

---

## 常见问题

1. **为什么不支持全自动战斗？**  
   由于尊重游戏规则，本项目只提供每日任务和部分副本的自动化，不支持全自动战斗。

2. **可以自定义任务吗？**  
   支持。用户可以通过编写自定义任务流程文件，实现灵活的任务自动化配置。

3. **部分游戏场景无法识别怎么办？**  
   可能是素材不足所致，欢迎大家贡献更多素材，共同完善项目功能。  

4. **启动没办法识别**  
   确保所有任务启动时是在庭院中启动,(除了打开游戏的任务可以在任意位置启动)

---

## 贡献指南

感兴趣可以加群645818258讨论。

欢迎开发者参与贡献。在提交 Pull Request 前请确保：

1. 遵循项目的代码风格与规范。
2. 避免提交涉及全自动副本或御魂副本相关功能的代码。

---

## 鸣谢

本项目由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 提供强力支持，感谢所有参与和支持项目开发的贡献者！

---

## 许可协议

本项目采用 **MIT 许可证** 发布，详情请参阅 [LICENSE 文件](LICENSE)。
