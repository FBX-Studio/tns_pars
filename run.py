"""
Скрипт для одновременного запуска web-приложения и мониторинга
"""
import subprocess
import sys
import os
import time

def main():
    print("=" * 60)
    print("Запуск системы мониторинга отзывов ПАО «ТНС энерго НН»")
    print("=" * 60)
    print()
    
    if not os.path.exists('.env'):
        print("ОШИБКА: Файл .env не найден!")
        print("Создайте файл .env на основе .env.example")
        print("Инструкция в README.md")
        sys.exit(1)
    
    print("Запуск Web-интерфейса...")
    web_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    time.sleep(3)
    
    print("Запуск системы мониторинга...")
    monitor_process = subprocess.Popen(
        [sys.executable, 'monitor.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    print()
    print("=" * 60)
    print("Система запущена!")
    print("=" * 60)
    print(f"Web-интерфейс: http://localhost:5000")
    print("Мониторинг работает в фоновом режиме")
    print()
    print("Для остановки нажмите Ctrl+C")
    print("=" * 60)
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка системы...")
        web_process.terminate()
        monitor_process.terminate()
        web_process.wait()
        monitor_process.wait()
        print("Система остановлена")

if __name__ == '__main__':
    main()
