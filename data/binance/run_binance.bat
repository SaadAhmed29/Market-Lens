@echo off
setlocal
cd /d "C:\Users\Saad\Desktop\MarketLens"
python -m data.binance.main
exit /b %ERRORLEVEL%