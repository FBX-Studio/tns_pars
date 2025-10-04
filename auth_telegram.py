"""
Авторизация Telegram User API - автоматическая
"""
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

# Ваши данные из .env
API_ID = 25079847
API_HASH = '37a06d1d36fbf3879d3a81935e4b80a0'
PHONE = '+79103916790'

async def authorize():
    print("\n" + "=" * 70)
    print("АВТОРИЗАЦИЯ TELEGRAM USER API")
    print("=" * 70)
    print()
    print(f"API ID: {API_ID}")
    print(f"Телефон: {PHONE}")
    print()
    
    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Проверяем авторизацию
        if await client.is_user_authorized():
            print("✅ Вы уже авторизованы!")
            print("Сессия найдена в файле: telegram_session.session")
            print()
            me = await client.get_me()
            print(f"Пользователь: {me.first_name} {me.last_name or ''}")
            print(f"Username: @{me.username or 'не установлен'}")
            print(f"Phone: {me.phone}")
            print()
            print("✓ Telegram готов к работе!")
            await client.disconnect()
            return True
        
        # Запрашиваем код
        print("Отправляем код подтверждения на телефон...")
        await client.send_code_request(PHONE)
        print()
        print("=" * 70)
        print("SMS КОД ОТПРАВЛЕН НА НОМЕР:", PHONE)
        print("=" * 70)
        print()
        print("ИНСТРУКЦИЯ:")
        print("1. Проверьте SMS на телефоне")
        print("2. Скопируйте код из SMS (например: 12345)")
        print("3. Запустите эту команду:")
        print()
        print(f"   python auth_telegram_code.py <КОД_ИЗ_SMS>")
        print()
        print("Пример:")
        print("   python auth_telegram_code.py 12345")
        print()
        print("=" * 70)
        
        await client.disconnect()
        return False
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        await client.disconnect()
        return False

if __name__ == '__main__':
    result = asyncio.run(authorize())
    sys.exit(0 if result else 1)
