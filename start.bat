@echo off
cd /d %~dp0
echo LINEタスク抽出ツール
echo.
set /p ANTHROPIC_API_KEY="APIキーを貼り付けてEnterを押してください: "
echo.
echo 起動しています...
start http://localhost:5000
python server.py
pause
