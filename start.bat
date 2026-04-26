@echo off
cd /d %~dp0

if not exist ".env" (
    echo .envファイルが見つかりません。
    echo 同じフォルダに .env ファイルを作成して、
    echo ANTHROPIC_API_KEY=sk-ant-ここにキーを貼り付け
    echo と書いてください。
    pause
    exit /b 1
)

echo LINEタスク抽出ツールを起動しています...
start http://localhost:5000
python server.py
pause
