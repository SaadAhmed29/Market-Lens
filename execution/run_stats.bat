@echo off
setlocal
cd /d "C:\Users\Saad\Desktop\MarketLens"
python -m execution.account_stats
exit /b %ERRORLEVEL%