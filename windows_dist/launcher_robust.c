#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <stdlib.h>

#pragma comment(lib, "ws2_32.lib")

static int is_port_open(int port) {
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) return 0;

    unsigned long mode = 1;
    ioctlsocket(s, FIONBIO, &mode); // 非阻塞模式

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    connect(s, (struct sockaddr*)&addr, sizeof(addr));

    fd_set writeSet;
    FD_ZERO(&writeSet);
    FD_SET(s, &writeSet);

    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = 150000; // 150ms 超时

    int ret = select(0, NULL, &writeSet, NULL, &tv);
    closesocket(s);
    return (ret > 0);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 1. 初始化网络库用于端口检测
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    // 2. 获取程序所在目录并设置为当前目录
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    char *lastSlash = strrchr(exePath, '\\');
    if (lastSlash != NULL) {
        *lastSlash = '\0';
    }
    SetCurrentDirectoryA(exePath);

    // 3. 如果后台服务已经在运行（8765 端口已打开），直接打开浏览器即可
    if (is_port_open(8765)) {
        WSACleanup();
        ShellExecuteA(NULL, "open", "http://127.0.0.1:8765", NULL, NULL, SW_SHOWNORMAL);
        return 0;
    }

    // 4. 构造 python\python.exe 启动命令
    char pyExe[MAX_PATH];
    snprintf(pyExe, sizeof(pyExe), "%s\\python\\python.exe", exePath);

    char cmdArgs[MAX_PATH * 2];
    snprintf(cmdArgs, sizeof(cmdArgs), "\"%s\" server.py", pyExe);

    // 5. 启动后台服务 (纯 Win32 API 静默启动，无任何黑框和终端弹窗)
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    BOOL started = CreateProcessA(NULL, cmdArgs, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, exePath, &si, &pi);
    if (!started) {
        // 如果便携版未找到，回退尝试系统全局 python
        snprintf(cmdArgs, sizeof(cmdArgs), "python server.py");
        started = CreateProcessA(NULL, cmdArgs, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, exePath, &si, &pi);
    }

    if (!started) {
        WSACleanup();
        MessageBoxA(NULL, "未找到可用的 Python 运行环境！\n请确保安装目录下存在 python 文件夹。", "智能进销存台账系统", MB_ICONERROR | MB_OK);
        return 1;
    }

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    // 6. 轮询等待 8765 端口就绪（最多等待 6 秒，一旦就绪立即唤起网页）
    int waited = 0;
    while (waited < 6000) {
        Sleep(200);
        waited += 200;
        if (is_port_open(8765)) {
            break;
        }
    }

    WSACleanup();

    // 7. 唤起系统默认浏览器访问台账界面
    ShellExecuteA(NULL, "open", "http://127.0.0.1:8765", NULL, NULL, SW_SHOWNORMAL);
    return 0;
}
