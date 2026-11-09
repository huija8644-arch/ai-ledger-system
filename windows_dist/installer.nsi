; ========================================================
; NSIS 脚本: 智能进销存与往来账款实时台账系统 (正式安装向导版)
; ========================================================

Unicode true
SetCompressor /SOLID lzma

!define PRODUCT_NAME "智能进销存台账系统"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "AI Ledger Studio"
!define PRODUCT_WEB_SITE "http://127.0.0.1:8765"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\智能进销存台账系统.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"

; MUI 2 现代向导界面
!include "MUI2.nsh"

; 图标设置
!define MUI_ICON "app.ico"
!define MUI_UNICON "app.ico"
!define MUI_ABORTWARNING

; 安装向导页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; 安装完成页面 (带有立即运行复选框)
!define MUI_FINISHPAGE_RUN "$INSTDIR\智能进销存台账系统.exe"
!define MUI_FINISHPAGE_RUN_TEXT "立即启动 智能进销存台账系统"
!insertmacro MUI_PAGE_FINISH

; 卸载向导页面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言设置 (简体中文)
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装程序基础元信息
Name "${PRODUCT_NAME} v${PRODUCT_VERSION}"
OutFile "..\智能进销存台账系统_安装程序_Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\智能进销存台账系统"
InstallDirRegKey HKCU "Software\${PRODUCT_NAME}" ""
ShowInstDetails show
ShowUnInstDetails show

; ================= 初始化回调 (双击向导第一瞬间执行) =================
Function .onInit
  ; 用户双击打开安装包的第一瞬间，立刻在后台静默强制关闭旧程序与端口，杜绝文件锁死
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Stop-Process -Name \'智能进销存台账系统\' -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-Process | Where-Object { $$_.Path -like \'*智能进销存台账系统*\' } | Stop-Process -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'taskkill /F /IM "智能进销存台账系统.exe" /T'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $$_.OwningProcess -Force -ErrorAction SilentlyContinue }"'
  Sleep 300
FunctionEnd

; ================= 安装节 =================
Section "MainSection" SEC01
  ; 再次保险执行一次进程清理，等待句柄彻底归还操作系统
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Stop-Process -Name \'智能进销存台账系统\' -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-Process | Where-Object { $$_.Path -like \'*智能进销存台账系统*\' } | Stop-Process -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'taskkill /F /IM "智能进销存台账系统.exe" /T'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $$_.OwningProcess -Force -ErrorAction SilentlyContinue }"'

  ; 循环确保旧 EXE 文件句柄完全释放
  StrCpy $R0 0
  TryDeleteExe:
    ClearErrors
    Delete "$INSTDIR\智能进销存台账系统.exe"
    IfErrors 0 ExeDeleted
    IntOp $R0 $R0 + 1
    IntCmp $R0 10 ExeDeleted ExeDeleted 0
    Sleep 400
    nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-Process | Where-Object { $$_.Path -like \'*智能进销存台账系统*\' } | Stop-Process -Force -ErrorAction SilentlyContinue"'
    Goto TryDeleteExe
  ExeDeleted:

  SetOutPath "$INSTDIR"
  SetOverwrite on

  ; 释放打包好的全量文件
  File /r "..\windows_release\*.*"

  ; 创建快捷方式 (桌面 + 开始菜单)
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\智能进销存台账系统.exe" "" "$INSTDIR\智能进销存台账系统.exe" 0
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\智能进销存台账系统.exe" "" "$INSTDIR\智能进销存台账系统.exe" 0
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\卸载${PRODUCT_NAME}.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

  ; 生成卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; 写入注册表 (控制面板 卸载项)
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\智能进销存台账系统.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
SectionEnd

; ================= 卸载节 =================
Section Uninstall
  ; 关闭运行中的程序
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Stop-Process -Name \'智能进销存台账系统\' -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-Process | Where-Object { $$_.Path -like \'*智能进销存台账系统*\' } | Stop-Process -Force -ErrorAction SilentlyContinue"'
  nsExec::Exec 'taskkill /F /IM "智能进销存台账系统.exe" /T'
  nsExec::Exec 'powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $$_.OwningProcess -Force -ErrorAction SilentlyContinue }"'
  Sleep 500

  ; 询问是否保留历史账套数据库
  MessageBox MB_YESNO|MB_ICONQUESTION "是否保留您的台账历史数据文件 (ledger.db)？$\n$\n点击【是】保留您的账套数据；$\n点击【否】彻底删除所有数据。" IDYES KeepDb
  Delete "$INSTDIR\ledger.db"
KeepDb:

  ; 删除快捷方式
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\*.*"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

  ; 删除安装目录
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\static"
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ; 清理注册表
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "Software\${PRODUCT_NAME}"
  SetAutoClose true
SectionEnd
