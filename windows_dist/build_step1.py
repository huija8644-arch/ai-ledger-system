import os
import shutil
import zipfile
import subprocess

BASE_DIR = "/Users/airnipper163.com/Desktop/Antigravity/ai_ledger_system"
DIST_DIR = os.path.join(BASE_DIR, "windows_release")
os.makedirs(DIST_DIR, exist_ok=True)

# 1. 复制核心脚本与网页资源到打包目录
app_files = ["server.py", "ai_engine.py", "database.py", "index.html", "start.bat", "WINDOWS_DEPLOY_GUIDE.md"]
for f in app_files:
    src = os.path.join(BASE_DIR, f)
    dst = os.path.join(DIST_DIR, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)

# 2. 拷贝配置好的便携式 Python 运行环境
py_src = os.path.join(BASE_DIR, "windows_dist", "python")
py_dst = os.path.join(DIST_DIR, "python")
if os.path.exists(py_src):
    if os.path.exists(py_dst):
        shutil.rmtree(py_dst)
    shutil.copytree(py_src, py_dst)

print("资源拷贝完成，正在编写 Windows 原生启动器源码...")

# 3. 编写 Windows 原生 GUI 启动器源码 (launcher.c)
launcher_c_path = os.path.join(BASE_DIR, "windows_dist", "launcher.c")
launcher_c_code = r'''#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <stdlib.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    char *lastSlash = strrchr(exePath, '\\');
    if (lastSlash != NULL) {
        *lastSlash = '\0';
    }
    SetCurrentDirectoryA(exePath);

    // 释放可能被上次遗留占用的 8765 端口
    system("cmd.exe /c for /f \"tokens=5\" %a in ('netstat -aon ^| findstr \":8765\" ^| findstr \"LISTENING\"') do taskkill /F /PID %a >nul 2>nul");

    char pyPath[MAX_PATH];
    snprintf(pyPath, sizeof(pyPath), "%s\\python\\python.exe", exePath);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE; // 隐藏黑框
    ZeroMemory(&pi, sizeof(pi));

    char cmdLine[MAX_PATH * 2];
    snprintf(cmdLine, sizeof(cmdLine), "\"%s\" server.py", pyPath);

    BOOL started = CreateProcessA(NULL, cmdLine, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, exePath, &si, &pi);
    if (!started) {
        snprintf(cmdLine, sizeof(cmdLine), "python server.py");
        started = CreateProcessA(NULL, cmdLine, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, exePath, &si, &pi);
    }

    if (started) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        MessageBoxA(NULL, "未找到可用 Python 环境！请确保 python 文件夹存在或系统已装 Python。", "智能台账系统", MB_ICONERROR | MB_OK);
        return 1;
    }

    Sleep(1200);
    ShellExecuteA(NULL, "open", "http://127.0.0.1:8765", NULL, NULL, SW_SHOWNORMAL);
    return 0;
}
'''

with open(launcher_c_path, "w", encoding="utf-8") as f:
    f.write(launcher_c_code)

# 4. 编写单文件版自解压运行启动器源码 (single_file_launcher.c)
sfx_c_path = os.path.join(BASE_DIR, "windows_dist", "single_file_launcher.c")
sfx_c_code = r'''#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <stdlib.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char selfPath[MAX_PATH];
    GetModuleFileNameA(NULL, selfPath, MAX_PATH);

    // 获取 %LOCALAPPDATA%\AiLedgerApp
    char localApp[MAX_PATH];
    ExpandEnvironmentStringsA("%LOCALAPPDATA%\\AiLedgerApp", localApp, MAX_PATH);
    CreateDirectoryA(localApp, NULL);

    char checkPy[MAX_PATH];
    snprintf(checkPy, sizeof(checkPy), "%s\\python\\python.exe", localApp);

    // 如果还没有解压过，执行自解压
    if (GetFileAttributesA(checkPy) == INVALID_FILE_ATTRIBUTES) {
        // 利用 Windows 内置 tar 或 powershell 解压 self 内部附加的 zip
        char unzipCmd[MAX_PATH * 3];
        snprintf(unzipCmd, sizeof(unzipCmd), "cmd.exe /c tar -xf \"%s\" -C \"%s\" 2>nul || powershell -NoProfile -Command \"Expand-Archive -Path '%s' -DestinationPath '%s' -Force\"", selfPath, localApp, selfPath, localApp);
        system(unzipCmd);
    }

    SetCurrentDirectoryA(localApp);

    // 释放 8765 端口
    system("cmd.exe /c for /f \"tokens=5\" %a in ('netstat -aon ^| findstr \":8765\" ^| findstr \"LISTENING\"') do taskkill /F /PID %a >nul 2>nul");

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    char runCmd[MAX_PATH * 2];
    snprintf(runCmd, sizeof(runCmd), "\"%s\" server.py", checkPy);

    BOOL started = CreateProcessA(NULL, runCmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, localApp, &si, &pi);
    if (!started) {
        snprintf(runCmd, sizeof(runCmd), "python server.py");
        started = CreateProcessA(NULL, runCmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, localApp, &si, &pi);
    }

    if (started) {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        MessageBoxA(NULL, "自解压运行失败，请确认系统环境正常！", "智能台账系统", MB_ICONERROR | MB_OK);
        return 1;
    }

    Sleep(1200);
    ShellExecuteA(NULL, "open", "http://127.0.0.1:8765", NULL, NULL, SW_SHOWNORMAL);
    return 0;
}
'''

with open(sfx_c_path, "w", encoding="utf-8") as f:
    f.write(sfx_c_code)

print("源码生成完毕，准备调用 mingw-w64 交叉编译...")
