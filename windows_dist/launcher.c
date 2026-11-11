#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static BOOL FileExists(const char *path) {
    if (!path || path[0] == '\0') return FALSE;
    DWORD dwAttrib = GetFileAttributesA(path);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

static BOOL QueryRegistryPath(HKEY hRoot, const char *subKey, char *outPath, DWORD outSize) {
    HKEY hKey;
    if (RegOpenKeyExA(hRoot, subKey, 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        DWORD dwType = REG_SZ;
        DWORD dwLen = outSize;
        if (RegQueryValueExA(hKey, NULL, NULL, &dwType, (LPBYTE)outPath, &dwLen) == ERROR_SUCCESS) {
            RegCloseKey(hKey);
            // 去除路径两端可能存在的双引号
            if (outPath[0] == '"') {
                size_t len = strlen(outPath);
                if (len > 1 && outPath[len - 1] == '"') {
                    outPath[len - 1] = '\0';
                }
                memmove(outPath, outPath + 1, len);
            }
            if (FileExists(outPath)) {
                return TRUE;
            }
        }
        RegCloseKey(hKey);
    }
    return FALSE;
}

static BOOL FindBrowserApp(char *outPath, size_t outSize) {
    char tempPath[MAX_PATH];

    // 1. 优先通过系统注册表查找 Microsoft Edge 路径 (HKLM / HKCU)
    if (QueryRegistryPath(HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe", outPath, (DWORD)outSize)) return TRUE;
    if (QueryRegistryPath(HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe", outPath, (DWORD)outSize)) return TRUE;

    // 2. 查找 Google Chrome 注册表路径 (HKLM / HKCU)
    if (QueryRegistryPath(HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe", outPath, (DWORD)outSize)) return TRUE;
    if (QueryRegistryPath(HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe", outPath, (DWORD)outSize)) return TRUE;

    // 3. 常见标准安装路径检测
    char *progFilesX86 = getenv("ProgramFiles(x86)");
    char *progFiles = getenv("ProgramFiles");
    char *localAppData = getenv("LOCALAPPDATA");

    if (progFilesX86) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Microsoft\\Edge\\Application\\msedge.exe", progFilesX86);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }
    if (progFiles) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Microsoft\\Edge\\Application\\msedge.exe", progFiles);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }
    if (localAppData) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Microsoft\\Edge\\Application\\msedge.exe", localAppData);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }
    if (progFiles) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Google\\Chrome\\Application\\chrome.exe", progFiles);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }
    if (progFilesX86) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Google\\Chrome\\Application\\chrome.exe", progFilesX86);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }
    if (localAppData) {
        snprintf(tempPath, sizeof(tempPath), "%s\\Google\\Chrome\\Application\\chrome.exe", localAppData);
        if (FileExists(tempPath)) { strncpy(outPath, tempPath, outSize); return TRUE; }
    }

    return FALSE;
}

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

    // 启动后台 Python 核心服务（隐藏控制台窗口）
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE; // 纯静默后台运行
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
        MessageBoxA(NULL, "未找到可用 Python 运行时！请确保程序目录完整解压。", "智能台账系统", MB_ICONERROR | MB_OK);
        return 1;
    }

    // 等待服务端口初始化完毕
    Sleep(1200);

    // 寻找独立原生 App 窗口宿主 (Edge / Chrome --app 模式)
    char browserPath[MAX_PATH];
    if (FindBrowserApp(browserPath, sizeof(browserPath))) {
        char appCmd[MAX_PATH * 4];
        char *localAppData = getenv("LOCALAPPDATA");
        if (localAppData && localAppData[0] != '\0') {
            snprintf(appCmd, sizeof(appCmd),
                     "\"%s\" --app=\"http://127.0.0.1:8765\" --window-size=1440,900 --user-data-dir=\"%s\\SmartLedger\\app_profile\" --no-first-run --no-default-browser-check",
                     browserPath, localAppData);
        } else {
            snprintf(appCmd, sizeof(appCmd),
                     "\"%s\" --app=\"http://127.0.0.1:8765\" --window-size=1440,900 --no-first-run --no-default-browser-check",
                     browserPath);
        }

        STARTUPINFOA appSi;
        PROCESS_INFORMATION appPi;
        ZeroMemory(&appSi, sizeof(appSi));
        appSi.cb = sizeof(appSi);
        ZeroMemory(&appPi, sizeof(appPi));

        if (CreateProcessA(NULL, appCmd, NULL, NULL, FALSE, 0, NULL, NULL, &appSi, &appPi)) {
            CloseHandle(appPi.hProcess);
            CloseHandle(appPi.hThread);
            return 0;
        }
    }

    // 兜底方案：若极端环境下无 Edge/Chrome，则唤起默认系统浏览器
    ShellExecuteA(NULL, "open", "http://127.0.0.1:8765", NULL, NULL, SW_SHOWNORMAL);
    return 0;
}
