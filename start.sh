#!/bin/bash

echo "========================================"
echo "Система мониторинга ТНС энерго НН"
echo "========================================"
echo

if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    echo
fi

echo "Активация виртуального окружения..."
source venv/bin/activate

echo "Проверка зависимостей..."
pip install -r requirements.txt --quiet

if [ ! -f ".env" ]; then
    echo "ВНИМАНИЕ: Файл .env не найден!"
    echo "Создайте .env на основе .env.example"
    echo
    exit 1
fi

echo
echo "Запуск системы..."
python run.py
