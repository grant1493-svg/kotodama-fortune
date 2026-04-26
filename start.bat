@echo off
cd /d %~dp0
echo LINEタスク抽出ツールを起動しています...
start http://localhost:5000
python server.py
pause
