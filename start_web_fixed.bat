@echo off
echo ================================
echo Запуск веб-приложения (исправлено)
echo ================================
echo.
echo Остановка старых процессов...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq app_enhanced*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo.
echo Запуск app_enhanced.py...
echo Приложение будет доступно: http://localhost:5000
echo.
echo Для остановки нажмите Ctrl+C
echo ================================
echo.
python app_enhanced.py
pause
