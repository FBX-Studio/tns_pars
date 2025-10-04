"""
Telegram User API Setup Script
Настройка доступа к Telegram через User API (Telethon)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from telethon import TelegramClient
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def setup_telegram():
    print("=" * 60)
    print("Настройка Telegram User API")
    print("=" * 60)
    print()
    
    # Get credentials
    api_id = os.getenv('TELEGRAM_API_ID', '')
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    phone = os.getenv('TELEGRAM_PHONE', '')
    
    if not api_id or not api_hash:
        print("❌ Ошибка: TELEGRAM_API_ID и TELEGRAM_API_HASH не настроены в .env")
        print()
        print("Шаги для получения API ключей:")
        print("1. Откройте https://my.telegram.org")
        print("2. Войдите с вашим номером телефона")
        print("3. Перейдите в API Development Tools")
        print("4. Создайте новое приложение")
        print("5. Скопируйте api_id и api_hash в .env файл:")
        print()
        print("TELEGRAM_API_ID=your_api_id")
        print("TELEGRAM_API_HASH=your_api_hash")
        print("TELEGRAM_PHONE=+79991234567")
        print()
        return False
    
    if not phone:
        print("❌ Ошибка: TELEGRAM_PHONE не настроен в .env")
        print()
        print("Добавьте в .env:")
        print("TELEGRAM_PHONE=+79991234567")
        print()
        return False
    
    print(f"✓ API ID: {api_id}")
    print(f"✓ Телефон: {phone}")
    print()
    
    # Initialize client
    print("Подключение к Telegram...")
    client = TelegramClient('telegram_session', int(api_id), api_hash)
    
    try:
        await client.start(phone=phone)
        
        if await client.is_user_authorized():
            print()
            print("=" * 60)
            print("✅ Успешно! Telegram User API настроен")
            print("=" * 60)
            print()
            print("Теперь вы можете:")
            print("1. Запустить сбор: python run.py")
            print("2. Или собрать данные: python clear_and_collect.py")
            print()
            return True
        else:
            print("❌ Авторизация не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == '__main__':
    try:
        result = asyncio.run(setup_telegram())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
