# Android APK 打包与签名

MaaYYs 的 Android 产物由 `Aliothmoon/MaaFwApp`（MaaFramework 的 Android 通用壳）打包，
定义在 `.github/workflows/build-release.yml` 的 `android` job 里。

## 产物流向

```
build-release.yml
├── android                → 组装 PI + 编译 Go agent + 签名 + assembleRelease/Debug
│                            → artifact「MaaYYs-android」(android-dist/*.apk)
├── release                → 按 ANDROID_PUBLISH 决定是否把 .apk 放进 GitHub Release
└── android_mirrorchyan    → 上传到 MirrorChyan（rid = 4f6403c3-72e6-4327-b37a-23cbf0dc30f9，os = android）
```

包名：`com.maafw.ts.kusa` = `.github/android/patch_maafwapp.py` 改的 base(`com.maafw.ts`)
+ `.github/android/pi-profile.yaml` 的 `app.id`(`kusa`)。
`app.id` 必须匹配 `[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*`，否则 MaaFwApp 直接报
`app.id must be lowercase package segments`。

**包名一旦发过版就不能再改**：`applicationId` 变了，老用户得卸载重装。

## 需要的 Repository secrets

| Secret | 内容 |
|---|---|
| `ANDROID_KEYSTORE_BASE64` | keystore 文件的 base64，**必须单行** |
| `ANDROID_KEYSTORE_PASSWORD` | store password |
| `ANDROID_KEY_ALIAS` | 别名（本仓库用 `kusa`） |
| `ANDROID_KEY_PASSWORD` | key password（PKCS12 下与 store 相同） |
| `MIRRORCHYANUPLOADTOKENANDROID` | MirrorChyan 上传 token（与桌面端 `MirrorChyanUploadToken`、macOS 的 `MIRRORCHYANUPLOADTOKENMAC` 分开） |

四个签名 secret 要么全配、要么全不配：**只配 1~3 个会直接 `exit 1`**（故意的，不是 bug），
一个都不配则退回 `assembleDebug`，产物名带 `-debug`。

## 生成 keystore

密码用你自定的 16 位；`-dname` 用 ASCII，避免 Windows 控制台编码问题。

```powershell
$keytool = "<JDK>\bin\keytool.exe"   # 没有 JDK 就用 Android Studio / PyCharm 自带的 jbr
$dir = "D:\keys"                     # 放仓库外
$pw  = "<你的密码>"

& $keytool -genkeypair -v `
  -keystore "$dir\maayys-release.jks" `
  -alias "kusa" `
  -keyalg RSA -keysize 4096 -validity 10000 `
  -storetype PKCS12 `
  -storepass $pw -keypass $pw `
  -dname "CN=MaaYYs, OU=TanyaShue, O=TanyaShue, L=Unknown, ST=Unknown, C=CN"

# 自检：大小约 4KB；前 4 字节必须是 30 82(PKCS12) 或 FE ED FE ED(JKS)
$b = [IO.File]::ReadAllBytes("$dir\maayys-release.jks")
"$($b.Length) bytes, $(($b[0..3] | % { $_.ToString('X2') }) -join ' ')"
& $keytool -list -keystore "$dir\maayys-release.jks" -storepass $pw -alias "kusa"

# 转 base64（单行！别用 certutil -encode，它会加头尾和换行）
[Convert]::ToBase64String($b) | Set-Content -NoNewline -Encoding ascii "$dir\maayys-release.jks.b64"
"sha256 = $((Get-FileHash "$dir\maayys-release.jks" -Algorithm SHA256).Hash.ToLower())"
```

把 `.b64` 的内容贴进 `ANDROID_KEYSTORE_BASE64`（贴之前先清空旧值）。

CI 的 `Configure Android signing` 会打印
`keystore: <字节数> bytes | base64: <字符数> chars | sha256: <...>` 和
`keystore aliases: kusa`，拿这两行和本地 `Get-FileHash` 对一下，就能证明
「secret 里的字节 == 本地文件」，一次排除抄写错误。

**离线备份两份 keystore**，密码进密码管理器；`.jks` / `.b64` 已在 `.gitignore` 里，不要入库。

## 发布开关：ANDROID_PUBLISH

`.apk` 默认**不随 GitHub Release 发布、也不上传 MirrorChyan**，只作为 CI artifact 保留
（artifact 名 `MaaYYs-android`，保留 7 天）。原因见下面「已知风险」。

真机验证通过后，在仓库 **Settings → Secrets and variables → Actions → Variables**
新建 `ANDROID_PUBLISH` = `true` 即放开，不需要改代码。

即使开关打开，**debug 变体的 APK 也永远不会发布**——它与 release 同 `applicationId`、
只有签名不同，用户先装了 debug 包，之后正式包会因签名冲突装不上，必须卸载重装。

## 关于 Android 的 Go agent（重要）

MaaYYs 的 agent 是 Go 写的，MaaFwApp 对「编译型 agent」的支持方式是：
单个 ELF，命名成 `lib*.so`，放到 `<sourceDir>/<abi>/jniLibs/`，`location` 用 `nativeLibs`。

这里有两个容易踩的点：

1. **必须 `CGO_ENABLED=1` + NDK。** maa-framework-go 用 purego 加载动态库，而
   purego 在 Android 上的 `Dlopen` 是 cgo 实现；`CGO_ENABLED=0` 的 Linux 路径会用
   `//go:cgo_import_dynamic` 依赖 glibc 的 `libdl.so.2`，编出来的**不是静态 ELF**，
   Android 上根本装载不了。
2. **`GOOS=android` 会让 maa-framework-go panic。** 它四个 `getMaaXxxLibrary()` 里
   `switch runtime.GOOS` 没有 android 分支，会命中 `default: panic(...)`。
   Android 的库名与 Linux 相同，所以 CI 里先 `go mod vendor`，再用
   `.github/android/patch_maafwgo_android.py` 把 `case "linux":` 补成
   `case "linux", "android":`。补丁按「`case "linux":` 紧跟 `return "lib*.so"`」匹配，
   不依赖函数名；四个库数量对不上就硬失败。上游合并 android 支持后本脚本可整体删除。

另外 `agent/main.go` 用 `MAAFW_LIB_DIR` 覆盖动态库目录：桌面端默认 `<cwd>/maafw`，
Android 上 `<cwd>/maafw` 不存在，由 `pi-profile.yaml` 指到 `{nativeLibs}`。

CI 在编译后立刻用 `readelf` 自检：出现 `libc.so.6` / `libdl.so.2` 等 glibc soname，
或 interpreter 不是 `/system/bin/linker*`，就直接构建失败——把「装机黑屏」
提前成构建期报错。

### 已知风险

**这套 Go agent 的 Android 装载方式尚未在真机上验证过。** 签名、打包、上传链路都已
本地验证，但「APK 装到手机上、agent 能被拉起来、自定义 action/recognition 生效」
只能在真机上确认。

真机验证步骤：

1. 手动触发 `build-release.yml`（`workflow_dispatch`），或推一个改动到 `agent/**` 的分支。
2. 从 workflow artifact 下载 `MaaYYs-android` 里的 `.apk`（release 变体需先配好 4 个 secret）。
3. 装到设备上跑一个用到自定义 action 的任务（例如「御魂」），确认不报
   `本包未带 agent 运行时` / `agent 可执行体不可执行`。
4. 通过后再把 `ANDROID_PUBLISH` 设成 `true`。

如果真机验证失败，退路按代价从低到高：
① 改用 `GOOS=linux` + `CGO_ENABLED=1` + NDK clang（`runtime.GOOS` 仍是 `linux`，
不用打依赖补丁，但属非官方组合）；
② 把 25 个自定义 action / 6 个 recognition 移植成 Python agent（MaaFwApp 的一等公民路径，
有 `jkloning/M9A-Pocket` 可参考）。

## 排错对照表

| 报错 | 原因 |
|---|---|
| `KeytoolException: Failed to read key ... : null` + `Caused by: java.io.EOFException` | **文件不是密钥库 / 被截断**（base64 传错、二次编码、误传了文本文件）。keystore 一定 4KB 上下 |
| `keystore password was incorrect` / `Cannot recover key` | 密码错 |
| `Alias <x> does not exist` | 别名错（区分大小写） |
| `app.id must be lowercase package segments` | `app.id` 有大写或连字符 |
| `本包未带 agent 运行时` | PI 声明了 `agent`，但配方里没有对应 `runtimes` |
| `agent 可执行体不可执行` | agent 没按 `lib*.so` 命名，或没走 `nativeLibs` |
| `agent 运行时数量不足` | `runtimes` 条数与 PI 的 `agent[]` 数量不一致 |
| `找不到可用的 NDK clang`（但 `ls` 里明明有） | NDK wrapper 的文件名是 **`<triple><api>-clang`，`android` 与 API 号之间没有连字符**：`aarch64-linux-android23-clang`。拼成 `...android-23-clang` 就永远找不到 |
| `agent 依赖 glibc soname` | CGO/CC 没真正指向 NDK（编成了 glibc 目标），Android 上装载必失败 |
| `agent 的 interpreter 不是 Android linker` | 同上，产物不是 Android ELF |

## 改 workflow 后记得

Actions 的 re-run 用的仍是**那个 commit 的 workflow 定义**。改了 workflow / 配置文件
必须提交并打新 tag 才生效（不少 job 只在 `is_release` 时跑）。
