"""
Скрипт для однократного асинхронного сбора отзывов
"""
import asyncio
import sys
from async_monitor import AsyncReviewMonitor
from app import app
from models import db

def main():
    print("=" * 60)
    print("Запуск однократного сбора отзывов (асинхронный режим)")
    print("=" * 60)
    print()
    
    with app.app_context():
        db.create_all()
        
        monitor = AsyncReviewMonitor()
        
        try:
            total = asyncio.run(monitor.run_collection_async())
            print()
            print("=" * 60)
            print(f"✓ Сбор завершен успешно! Собрано отзывов: {total}")
            print("=" * 60)
            return 0
        except KeyboardInterrupt:
            print("\n⚠ Сбор прерван пользователем")
            return 1
        except Exception as e:
            print(f"\n✗ Ошибка при сборе: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    sys.exit(main())
