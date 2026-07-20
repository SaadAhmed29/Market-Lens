@echo off
setlocal
cd /d "C:\Users\Saad\Desktop\MarketLens"
python -m simulator.main
exit /b %ERRORLEVEL%