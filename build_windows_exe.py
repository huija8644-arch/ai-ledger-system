"""
Windows 单文件 EXE 一键打包脚本
使用 PyInstaller 将整个台账系统打包为单个可执行程序 (.exe)。
打包完成后，生成的 exe 文件直接发给任何 Windows 电脑，无需安装 Python，双击即用！
"""

import os
import sys
import subprocess

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=" * 60)
    print("正在为 Windows 准备 PyInstaller 单文件打包...")
    print("=" * 60)

    try:
        import PyInstaller
    except ImportError:
        print("[*] 正在安装打包工具 pyinstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # PyInstaller 打包指令
    # --onefile: 打包为单文件 exe
    # --add-data: 将 index.html 打包进 exe 内部
    # --name: 程序名称
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name=智能进销存台账系统",
        f"--add-data=index.html{';' if sys.platform == 'win32' else ':'}.",
        "server.py"
    ]

    print("执行命令:", " ".join(cmd))
    subprocess.check_call(cmd)

    print("\n" + "=" * 60)
    print("✓ 打包完成！")
    print("可执行程序已生成在 dist 目录下：dist/智能进销存台账系统.exe")
    print("将该 exe 复制到任何 Windows 电脑双击即可启动运行！")
    print("=" * 60)

if __name__ == "__main__":
    build()
