@echo off
chcp 65001 >nul
echo ========================================
echo Система мониторинга ТНС энерго НН
echo ========================================
echo.

if not exist venv\ (
    echo Создание виртуального окружения...
    python -m venv venv
    echo.
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo Проверка зависимостей...
pip install -r requirements.txt --quiet

if not exist .env (
    echo ВНИМАНИЕ: Файл .env не найден!
    echo Создайте .env на основе .env.example
    echo.
    pause
    exit /b 1
)

echo.
echo Запуск системы...
python app_enhanced.py

pause
