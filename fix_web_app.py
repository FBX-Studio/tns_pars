"""
Скрипт для исправления и перезапуска веб-приложения
"""
import subprocess
import sys
import time

print("=" * 70)
print("ИСПРАВЛЕНИЕ ВЕБ-ПРИЛОЖЕНИЯ")
print("=" * 70)

print("\n1. Остановка старых процессов на порту 5000...")
try:
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq app_enhanced*'], 
                   capture_output=True)
    print("✓ Процессы остановлены")
    time.sleep(2)
except:
    print("⚠ Не удалось остановить процессы (возможно их нет)")

print("\n2. Проверка импортов...")
try:
    from flask import Flask
    from flask_socketio import SocketIO
    from models import db, Review
    print("✓ Все модули доступны")
except Exception as e:
    print(f"✗ Ошибка импорта: {e}")
    sys.exit(1)

print("\n3. Запуск app_enhanced.py...")
print("-" * 70)
print("Приложение будет доступно по адресу: http://localhost:5000")
print("Для остановки нажмите Ctrl+C")
print("-" * 70)

try:
    subprocess.run([sys.executable, 'app_enhanced.py'])
except KeyboardInterrupt:
    print("\n\n✓ Приложение остановлено")
except Exception as e:
    print(f"\n\n✗ Ошибка: {e}")
