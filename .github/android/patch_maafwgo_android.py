#!/usr/bin/env python3
"""给 vendor 进来的 maa-framework-go 打上 Android 支持补丁。

背景
----
maa-framework-go 通过 purego 动态加载 MaaFramework 的四个动态库，库名由
`getMaaXxxLibrary()` 里的 `switch runtime.GOOS` 决定，形如：

    func getMaaToolkitLibrary() string {
        switch runtime.GOOS {
        case "darwin":
            return "libMaaToolkit.dylib"
        case "linux":
            return "libMaaToolkit.so"
        case "windows":
            return "MaaToolkit.dll"
        default:
            panic(fmt.Errorf("GOOS=%s is not supported", runtime.GOOS))
        }
    }

`runtime.GOOS` 在 Android 构建里就是字面量 "android"，会落进 default 直接 panic，
所以 GOOS=android 下 `maa.Init()` 必然崩。而 Android 上的库名与 Linux 完全一致
（都是 `libXxx.so`），因此补丁只是把 `case "linux":` 改成 `case "linux", "android":`。

匹配的是「`case "linux":` 紧跟 `return "lib*.so"`」这个语义模式，而不是函数名——
这样上游改名、增删函数都不影响，同时也不会误伤别处无关的 GOOS 分支。
四个库（MaaFramework / MaaToolkit / MaaAgentServer / MaaAgentClient）都要改，
数量对不上就硬失败，避免悄悄发出一个起不来的 agent。

为什么在 CI 里补而不是直接改仓库
--------------------------------
vendor 目录由 `go mod vendor` 现场生成、不入库；补丁在生成之后、编译之前施加，
既不用 fork 依赖，也不用把整个依赖抄进仓库。等上游合并了 android 分支，
本脚本会识别出「已是补丁后状态」而安静通过，届时可整体删除。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VENDOR_NATIVE_DIR = Path(
    "vendor/github.com/MaaXYZ/maa-framework-go/v4/internal/native"
)

EXPECTED_COUNT = 4

LINUX_CASE = '\tcase "linux":'
PATCHED_CASE = '\tcase "linux", "android":'
# 只有「紧接着返回 lib*.so」的 linux 分支才是我们要改的库名 switch
RETURN_SO = re.compile(r'^\t\treturn "lib[\w.]*\.so"$')


def patch_text(text: str) -> tuple[str, list[str], int]:
    """返回 (新文本, 本次新补的库名, 已是补丁状态的库名数)。"""
    lines = text.splitlines(keepends=True)
    newly: list[str] = []
    already = 0

    for index in range(len(lines) - 1):
        current = lines[index].rstrip("\r\n")
        following = lines[index + 1].rstrip("\r\n")
        if not RETURN_SO.match(following):
            continue
        if current == LINUX_CASE:
            lines[index] = lines[index].replace(LINUX_CASE, PATCHED_CASE)
            newly.append(following.strip().removeprefix('return "').removesuffix('"'))
        elif current == PATCHED_CASE:
            already += 1

    return "".join(lines), newly, already


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "module",
        nargs="?",
        type=Path,
        default=Path("agent"),
        help="Go module 根目录（含 go.mod 与 vendor/），默认 agent",
    )
    parser.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    native = (args.module / VENDOR_NATIVE_DIR).resolve()
    if not native.is_dir():
        raise SystemExit(
            f"找不到 vendor 后的 native 目录：{native}\n"
            "请先在 module 目录执行 `go mod vendor`。"
        )

    total_new = 0
    total_already = 0
    for path in sorted(native.glob("*.go")):
        text = path.read_text(encoding="utf-8")
        updated, newly, already = patch_text(text)
        total_new += len(newly)
        total_already += already
        if newly:
            if not args.check:
                path.write_text(updated, encoding="utf-8")
            print(f"{'would patch' if args.check else 'patched'} {path.name}: {', '.join(newly)}")

    total = total_new + total_already
    if total != EXPECTED_COUNT:
        raise SystemExit(
            f"预期 {EXPECTED_COUNT} 个库名 switch，实际找到 {total} 个"
            f"（新补 {total_new}，已补 {total_already}）。\n"
            f"扫描目录：{native}\n"
            "上游 maa-framework-go 结构可能已变化，请检查 "
            ".github/android/patch_maafwgo_android.py 里的匹配规则。"
        )

    print(
        f"Android library-name patch: {total}/{EXPECTED_COUNT} 个 switch 已就位"
        + (f"（本次新补 {total_new} 个）" if total_new and not args.check else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
