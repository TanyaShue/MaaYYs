# MaaYYs macOS PlayCover 使用手册

本手册适用于 Apple Silicon Mac。MaaYYs 通过启用了 MaaTools 的 PlayCover 控制 iOS 版《阴阳师》；普通版 PlayCover 无法满足连接要求。

## 准备内容

- Apple Silicon Mac。
- MaaYYs macOS 完整包。
- 支持 MaaTools 的 PlayCover。
- 《阴阳师》iOS IPA 文件。

## 1. 安装 PlayCover

从 [面向 Maa 优化的 PlayCover Releases](https://github.com/hguandl/PlayCover/releases) 下载并安装 PlayCover。

首次打开 macOS 可能会提示应用来自互联网。请在系统提示中确认打开；若被系统阻止，可前往“系统设置 - 隐私与安全性”允许打开该应用。

## 2. 安装《阴阳师》IPA

准备《阴阳师》iOS IPA 文件后，将 IPA 拖入 PlayCover，或在 PlayCover 中选择导入 IPA 完成安装。

IPA 可自行获取，例如注册 [MacClub](https://www.maclub.net/) 后下载，或从其他可信来源取得；也可以在项目 QQ 群下载已准备好的 IPA。请自行确认 IPA 的来源、版本和使用权限。

游戏客户端更新后，需要重新安装新版 IPA，并重新完成本手册的第 3 步“PlayCover 绕过与 MaaTools”。

## 3. 启用 PlayCover 绕过与 MaaTools

在 PlayCover 的游戏列表中右键点击《阴阳师》，依次选择“设置 - 绕过”，勾选以下选项：

- 启用 PlayChain
- 启用绕过越狱检测
- 插入内省库
- MaaTools

点击“好”保存设置。

启动《阴阳师》。游戏窗口标题栏末尾出现类似 `[localhost:端口号]` 的内容，表示 MaaTools 已成功启用。请记下方括号中的完整地址，例如 `localhost:1718`；端口号以实际显示为准。

## 4. 在 MaaYYs 中连接游戏

启动 MaaYYs，打开“设置 - 连接设置”，将触控模式设为 `MacPlayTools`，并将“连接地址”填写为游戏标题栏方括号中的完整内容。

保存设置后即可连接游戏、选择资源并启动任务。不要把示例端口写死；每台设备实际显示的端口可能不同。

## 5. 分辨率建议

保持游戏横屏。若任务出现图像识别错误，可在 PlayCover 中把游戏分辨率调整为 1080P 后重试。

完成第 3 至第 5 步后，日常使用只需启动 PlayCover 中的《阴阳师》，再启动 MaaYYs 并连接即可。

## 6. 游戏启动闪退

仅当游戏无法启动并闪退时，才尝试以下修复。该操作会修改游戏客户端二进制文件：请先退出 PlayCover 和《阴阳师》，并备份客户端文件或重新保留 IPA，以便必要时重装恢复。

打开“终端”，粘贴并执行以下命令：

```bash
APP="$HOME/Library/Containers/io.playcover.PlayCover/Applications/com.netease.onmyoji.app"
EXE="$APP/client"

python3 - "$EXE" <<'PY'
import sys

path = sys.argv[1]

with open(path, "rb") as f:
    data = f.read()

old = b"/private"
# Keep the binary length unchanged: 8 bytes become '/' plus seven NUL bytes.
new = b"/" + b"\x00" * 7

count = data.count(old)
print("准备替换:", count, "处")

if count == 0:
    raise SystemExit("没有找到 /private，未修改文件")

with open(path, "wb") as f:
    f.write(data.replace(old, new))

print("替换完成")
PY

codesign -f -s - "$EXE" --deep --preserve-metadata=entitlements
```

命令完成后重新启动 PlayCover 和《阴阳师》。如果仍然闪退，建议重新安装 IPA，并确认使用的是本手册第 1 步提供的 Maa 优化版 PlayCover。

## 常见问题

### 标题栏没有显示 `[localhost:端口号]`

检查第 3 步中的四项绕过设置是否都已勾选，尤其是 `MaaTools`；保存后完全退出并重新启动游戏。

### MaaYYs 无法连接

确认连接地址与标题栏方括号内的内容完全一致，并确认触控模式为 `MacPlayTools`。不要使用默认示例地址代替实际地址。

### 图像识别异常

先确认游戏保持横屏；然后在 PlayCover 中尝试将分辨率调整为 1080P。仍无法解决时，请携带游戏截图、MaaYYs 日志、IPA 版本和 PlayCover 版本反馈。
