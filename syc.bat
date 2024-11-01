@echo off
chcp 65001 >nul

REM 定义子模块目录
set SUBMODULE_DIR=assets

REM 检查是否在 Git 仓库内
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo 当前目录不是一个 Git 仓库.
    exit /b 1
)

REM 进入子模块目录
cd %SUBMODULE_DIR%

REM 拉取远程更新
echo 正在从远程仓库拉取最新更新...
git pull origin master 
if %errorlevel% neq 0 (
    echo 拉取失败，请检查网络连接或权限.
    exit /b 1
)

REM 提交并推送本地更改
echo 正在提交本地更改...
git add .
git commit -m "Sync updates for assets"
git push origin master 
if %errorlevel% neq 0 (
    echo 推送失败，请检查网络连接或权限.
    exit /b 1
)

REM 返回上级目录
cd ..

echo 子模块 %SUBMODULE_DIR% 同步完成！
pause
