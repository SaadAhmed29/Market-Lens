@echo off
setlocal
cd /d "C:\Users\Saad\Desktop\MarketLens"
python -m data.bybit.main
exit /b %ERRORLEVEL%