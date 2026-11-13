#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "========================================================================"
echo "  KHỞI ĐỘNG TIKTOK CHAT STUDIO PRO (LOCAL SERVER + CAPCUT + EDGE-TTS)"
echo "========================================================================"

PY_CMD=""
if [ -x ".venv/bin/python" ]; then
    PY_CMD=".venv/bin/python"
elif [ -x "venv/bin/python" ]; then
    PY_CMD="venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "❌ Không tìm thấy Python 3! Hãy cài Python 3 trước."
    exit 1
fi

if ! "$PY_CMD" -c "import PIL, pyJianYingDraft, gtts, edge_tts" >/dev/null 2>&1; then
    echo "📦 Đang cài đặt thư viện Python trong requirements.txt..."
    "$PY_CMD" -m pip install -r requirements.txt
fi

if [ ! -d "node_modules/puppeteer-core" ] && command -v npm >/dev/null 2>&1; then
    echo "📦 Đang cài đặt puppeteer-core..."
    npm install --no-audit --no-fund
fi

echo "🚀 Đang mở TikTok Chat Studio tại http://localhost:8000 ..."
exec "$PY_CMD" studio_server.py
