#include <windows.h>
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
