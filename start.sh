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

# 自动在默认浏览器中打开
URL="http://127.0.0.1:$PORT"
echo "✓ 后端服务启动成功 (PID: $SERVER_PID)"
echo "✓ 系统访问地址：$URL"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$URL" 2>/dev/null || true
fi

echo "系统正在运行中。按 Ctrl+C 可停止服务。"
wait $SERVER_PID
