#include <windows.h>
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
        char unzipArgs[MAX_PATH * 3];
        snprintf(unzipArgs, sizeof(unzipArgs), "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command \"Expand-Archive -Path '%s' -DestinationPath '%s' -Force\"", selfPath, localApp);
        
        STARTUPINFOA siZip;
        PROCESS_INFORMATION piZip;
        ZeroMemory(&siZip, sizeof(siZip));
        siZip.cb = sizeof(siZip);
        siZip.dwFlags = STARTF_USESHOWWINDOW;
        siZip.wShowWindow = SW_HIDE;
        ZeroMemory(&piZip, sizeof(piZip));
        if (CreateProcessA(NULL, unzipArgs, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &siZip, &piZip)) {
            WaitForSingleObject(piZip.hProcess, 30000);
            CloseHandle(piZip.hProcess);
            CloseHandle(piZip.hThread);
        }
    }

    SetCurrentDirectoryA(localApp);

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
