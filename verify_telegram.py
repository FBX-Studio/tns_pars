"""
Проверка подключения Telegram
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from telethon import TelegramClient
import asyncio

API_ID = 25079847
API_HASH = '37a06d1d36fbf3879d3a81935e4b80a0'

async def verify():
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ TELEGRAM")
    print("=" * 70)
    print()
    
    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    try:
        await client.connect()
        print("✓ Подключение к Telegram установлено")
        print()
        
        if await client.is_user_authorized():
            print("=" * 70)
            print("✅ TELEGRAM ПОДКЛЮЧЕН И АВТОРИЗОВАН")
            print("=" * 70)
            print()
            
            me = await client.get_me()
            print(f"Пользователь: {me.first_name} {me.last_name or ''}")
            print(f"Username: @{me.username or 'не установлен'}")
            print(f"Телефон: {me.phone}")
            print(f"ID: {me.id}")
            print()
            print("✓ Аккаунт готов к работе!")
            print()
            
            return True
        else:
            print("=" * 70)
            print("❌ TELEGRAM НЕ АВТОРИЗОВАН")
            print("=" * 70)
            print()
            print("Для авторизации запустите:")
            print("  python setup_telegram.py")
            print()
            
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
        
    finally:
        await client.disconnect()

if __name__ == '__main__':
    result = asyncio.run(verify())
    sys.exit(0 if result else 1)
