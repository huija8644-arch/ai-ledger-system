#!/bin/bash
# 服装进销存与往来账款 · 智能实时台账系统 一键启动脚本
cd "$(dirname "$0")"

echo "=========================================================="
echo "🚀 正在启动 服装进销存与往来账款 · AI 实时智能台账系统..."
echo "=========================================================="

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3，请先安装 Python 3.8+ 后重试。"
    exit 1
fi

# 检查端口占用（默认 8765）
PORT=8765
PID=$(lsof -ti :$PORT)
if [ -n "$PID" ]; then
    echo "⚠️ 端口 $PORT 已被进程 $PID 占用，正在重启服务..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

echo "正在启动本地后端服务 (SQLite 本地事务数据库 + AI 语义引擎)..."
python3 server.py &
SERVER_PID=$!

sleep 1.5

# 自动唤起专属独立 App 桌面窗口
URL="http://127.0.0.1:$PORT"
echo "✓ 后端核心服务启动成功 (PID: $SERVER_PID)"
echo "✓ 系统服务地址：$URL"
echo "✓ 正在唤起独立原生应用窗口..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -d "/Applications/Microsoft Edge.app" ]; then
        open -na "Microsoft Edge" --args --app="$URL" --window-size=1440,900
    elif [ -d "/Applications/Google Chrome.app" ]; then
        open -na "Google Chrome" --args --app="$URL" --window-size=1440,900
    elif [ -d "/Applications/Brave Browser.app" ]; then
        open -na "Brave Browser" --args --app="$URL" --window-size=1440,900
    else
        open "$URL"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v microsoft-edge &> /dev/null; then
        microsoft-edge --app="$URL" --window-size=1440,900 &
    elif command -v google-chrome &> /dev/null; then
        google-chrome --app="$URL" --window-size=1440,900 &
    elif command -v chromium-browser &> /dev/null; then
        chromium-browser --app="$URL" --window-size=1440,900 &
    else
        xdg-open "$URL" 2>/dev/null || true
    fi
fi

echo "系统正在运行中。按 Ctrl+C 可停止服务。"
wait $SERVER_PID
