@echo off
setlocal
cd /d "C:\Users\Saad\Desktop\MarketLens"
python -m execution.main
exit /b %ERRORLEVEL%