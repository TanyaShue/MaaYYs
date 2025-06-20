#!/usr/bin/env python3
"""
MaaYYs项目中打包Python环境的脚本
用于在GitHub Actions中创建一个嵌入式Python环境
"""

import os
import sys
import subprocess
import shutil
import zipfile
import json
from pathlib import Path
import urllib.request


def run_command(cmd, cwd=None):
    """执行命令并返回输出"""
    print(f"执行命令: {cmd}")
    # 使用绝对路径的工作目录
    if cwd:
        cwd = Path(cwd).absolute()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, encoding='utf-8')
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        raise Exception(f"命令执行失败: {cmd}")
    return result.stdout.strip()


def download_file(url, destination):
    """下载文件"""
    print(f"下载: {url}")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"下载完成: {destination}")
    except Exception as e:
        print(f"下载失败: {e}")
        raise


def package_python_for_maayys():
    """为MaaYYs项目打包Python环境"""
    print("🚀 开始为MaaYYs项目打包Python环境...")

    # 获取当前工作目录
    base_dir = Path.cwd().absolute()

    # 检查是否在MaaYYs目录中
    if not os.path.exists("resource_config.json"):
        print("错误: 请在MaaYYs项目根目录中运行此脚本")
        sys.exit(1)

    # 创建Python运行时目录
    runtime_dir = base_dir / "runtime" / "python"
    if runtime_dir.exists():
        print(f"清理现有目录: {runtime_dir}")
        shutil.rmtree(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    # Python版本配置
    python_version = "3.11.9"  # 使用稳定的3.11版本

    # 下载Windows嵌入式Python
    embed_url = f"https://www.python.org/ftp/python/{python_version}/python-{python_version}-embed-amd64.zip"
    embed_zip = runtime_dir / "python-embed.zip"

    print(f"\n📥 下载Python {python_version} 嵌入式版本...")
    download_file(embed_url, str(embed_zip))

    # 解压Python
    print("📦 解压Python...")
    with zipfile.ZipFile(embed_zip, 'r') as zip_ref:
        zip_ref.extractall(runtime_dir)
    embed_zip.unlink()  # 删除zip文件

    # 下载get-pip.py
    print("\n📥 下载pip安装器...")
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = runtime_dir / "get-pip.py"
    download_file(get_pip_url, str(get_pip_path))

    # 修改python311._pth文件以启用site-packages
    pth_file = runtime_dir / "python311._pth"
    if pth_file.exists():
        print("\n✏️ 配置Python路径...")
        with open(pth_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 取消import site的注释并添加site-packages路径
        with open(pth_file, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() == '#import site':
                    f.write('import site\n')
                else:
                    f.write(line)
            # 添加Lib/site-packages路径
            f.write('Lib\\site-packages\n')

    # 创建必要的目录
    site_packages_dir = runtime_dir / "Lib" / "site-packages"
    site_packages_dir.mkdir(parents=True, exist_ok=True)

    # 安装pip - 使用绝对路径
    print("\n📦 安装pip...")
    python_exe = runtime_dir / "python.exe"
    get_pip_abs_path = get_pip_path.absolute()

    try:
        # 使用绝对路径执行命令
        cmd = f'"{python_exe.absolute()}" "{get_pip_abs_path}" --no-warn-script-location'
        run_command(cmd)
        get_pip_path.unlink()  # 删除get-pip.py
        print("✅ pip安装成功！")
    except Exception as e:
        print(f"警告: pip安装可能未完成: {e}")
        # 尝试备用方法
        try:
            print("尝试备用安装方法...")
            # 确保Scripts目录存在
            scripts_dir = runtime_dir / "Scripts"
            scripts_dir.mkdir(exist_ok=True)
            # 再次尝试安装
            cmd = f'cd /d "{runtime_dir}" && python.exe get-pip.py --no-warn-script-location'
            run_command(cmd, shell=True)
            if get_pip_path.exists():
                get_pip_path.unlink()
            print("✅ pip通过备用方法安装成功！")
        except Exception as e2:
            print(f"错误: pip安装失败: {e2}")

    # 创建启动脚本
    print("\n📝 创建启动脚本...")

    # Windows批处理脚本 - Python
    with open(runtime_dir / "python.bat", "w", encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('"%~dp0python.exe" %*\n')

    # Windows批处理脚本 - Pip
    with open(runtime_dir / "pip.bat", "w", encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('"%~dp0python.exe" -m pip %*\n')

    # PowerShell脚本 - Python
    with open(runtime_dir / "python.ps1", "w", encoding='utf-8') as f:
        f.write('& "$PSScriptRoot\\python.exe" $args\n')

    # PowerShell脚本 - Pip
    with open(runtime_dir / "pip.ps1", "w", encoding='utf-8') as f:
        f.write('& "$PSScriptRoot\\python.exe" -m pip $args\n')

    # 创建requirements.txt模板（如果不存在） - 在脚本同目录
    script_dir = Path(__file__).parent
    requirements_path = script_dir / "requirements.txt"
    if not requirements_path.exists():
        with open(requirements_path, "w", encoding='utf-8') as f:
            f.write("# MaaYYs Python依赖\n")
            f.write("# 在此文件中添加所需的Python包\n")
            f.write("# 例如:\n")
            f.write("# requests\n")
            f.write("# numpy\n")
            f.write("# opencv-python\n")

    # 创建Python运行时配置文件
    runtime_config_dir = base_dir / "runtime"
    runtime_config_dir.mkdir(exist_ok=True)

    runtime_config = {
        "python_version": python_version,
        "python_path": "runtime/python/python.exe",
        "pip_path": "runtime/python/pip.bat",
        "site_packages": "runtime/python/Lib/site-packages",
        "embedded": True
    }

    with open(runtime_config_dir / "python_config.json", "w", encoding='utf-8') as f:
        json.dump(runtime_config, f, indent=2, ensure_ascii=False)

    # 创建使用说明
    with open(runtime_config_dir / "README.md", "w", encoding='utf-8') as f:
        f.write(f"""# MaaYYs Python运行时

## 版本信息
- Python版本: {python_version} (嵌入式版本)
- 包含组件: Python解释器, pip包管理器

## 使用方法

### 运行Python脚本
```batch
runtime\\python\\python.bat your_script.py
```

### 安装Python包
```batch
runtime\\python\\pip.bat install package_name
```

### 从requirements.txt安装依赖
```batch
runtime\\python\\pip.bat install -r requirements.txt
```

## 目录结构
```
runtime/
├── python/              # Python嵌入式环境
│   ├── python.exe      # Python解释器
│   ├── python.bat      # Python启动脚本
│   ├── pip.bat         # Pip启动脚本
│   └── Lib/
│       └── site-packages/  # 第三方包安装目录
├── python_config.json  # Python配置信息
└── README.md          # 本说明文件

requirements.txt        # Python依赖列表（在脚本同目录）
```

## 注意事项
1. 这是Windows专用的嵌入式Python环境
2. 所有第三方包将安装在 `runtime/python/Lib/site-packages` 目录
3. 使用提供的批处理脚本来运行Python和pip命令
4. requirements.txt 文件位于脚本同目录
""")

    print("\n✅ Python环境打包完成！")
    print(f"📁 Python位置: {runtime_dir}")
    print(f"🐍 Python版本: {python_version}")
    print("\n使用方法:")
    print("  运行Python: runtime\\python\\python.bat script.py")
    print("  安装包: runtime\\python\\pip.bat install package_name")

    # 验证pip是否正确安装
    print("\n🔍 验证pip安装...")
    try:
        pip_bat = runtime_dir / "pip.bat"
        version_output = run_command(f'"{pip_bat.absolute()}" --version')
        print(f"✅ pip已正确安装: {version_output}")
    except Exception as e:
        print(f"⚠️ pip验证失败: {e}")
        return

    # 安装requirements.txt中的依赖（如果文件存在且有内容）
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # 检查是否有实际的依赖（排除注释和空行）
            lines = [line.strip() for line in content.split('\n')
                     if line.strip() and not line.strip().startswith('#')]
            if lines:
                print(f"\n📦 安装requirements.txt中的依赖...")
                print(f"📄 requirements.txt位置: {requirements_path}")
                try:
                    pip_bat = runtime_dir / "pip.bat"
                    cmd = f'"{pip_bat.absolute()}" install -r "{requirements_path.absolute()}"'
                    run_command(cmd)
                    print("✅ 依赖安装完成！")
                except Exception as e:
                    print(f"⚠️ 依赖安装失败: {e}")
            else:
                print("\n📋 requirements.txt中没有需要安装的依赖")
    else:
        print(f"\n📝 已创建requirements.txt模板: {requirements_path}")


def main():
    """主函数"""
    try:
        # 检查操作系统
        if sys.platform != 'win32':
            print("警告: 此脚本专为Windows设计，但将继续执行...")

        # 执行打包
        package_python_for_maayys()

        # 如果在GitHub Actions中，设置输出
        if os.environ.get('GITHUB_ACTIONS'):
            print("\n设置GitHub Actions输出...")
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a', encoding='utf-8') as f:
                    f.write("python_packaged=true\n")
                    f.write("python_runtime_path=runtime/python\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()