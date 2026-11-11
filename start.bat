@echo off
chcp 65001 >nul
title 智能进销存台账系统 - 启动管理

echo ========================================================
echo   进销存与往来账款 · 智能实时台账系统 (Windows 一键启动)
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. 优先检测当前目录自带的绿色嵌入式 Python
if exist "%~dp0python\python.exe" (
    echo [✓] 检测到本地绿色便携式 Python 运行时...
    set "PY_CMD=%~dp0python\python.exe"
    goto RUN_SERVER
)

:: 2. 检测系统全局 Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [✓] 检测到系统环境变量已安装 Python...
    set "PY_CMD=python"
    goto RUN_SERVER
)

:: 3. 检测系统 py 命令 (Python 启动器)
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo [✓] 检测到系统 py 启动器...
    set "PY_CMD=py"
    goto RUN_SERVER
)

echo [!] 未检测到可用 Python 环境。
echo 请将 Python 便携版解压至本目录下的 python 文件夹，或安装标准 Python 环境。
pause
exit /b 1

:RUN_SERVER
:: 自动清理 8765 端口占用（如果上次未正常关闭）
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765" ^| findstr "LISTENING"') do (
    echo [*] 正在释放端口 8765 占用进程 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>nul
)

echo [*] 正在启动后台台账核心服务 (http://127.0.0.1:8765)...
start /b "" "%PY_CMD%" server.py

:: 等待 1 秒确保服务启动
timeout /t 1 /nobreak >nul

echo [✓] 核心服务启动成功！正在唤起极智台账专属独立桌面窗口...

:: 优先以原生独立应用窗口模式启动 (Edge / Chrome --app，无地址栏/无标签页)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)
if exist "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%LocalAppData%\Microsoft\Edge\Application\msedge.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" --app="http://127.0.0.1:8765" --window-size=1440,900 --user-data-dir="%LOCALAPPDATA%\SmartLedger\app_profile" --no-first-run --no-default-browser-check
    goto APP_STARTED
)

:: 兜底方案：默认系统浏览器
start http://127.0.0.1:8765

:APP_STARTED
echo.
echo ========================================================
echo   极智台账 PRO 原生独立客户端已成功运行！
echo   【提示】请保持此后台服务窗口最小化运行；
echo   关闭此窗口或按任意键即可退出整个系统。
echo ========================================================
echo.
pause >nul
