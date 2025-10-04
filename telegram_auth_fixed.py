"""
Полная авторизация Telegram в один шаг
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

API_ID = 25079847
API_HASH = '37a06d1d36fbf3879d3a81935e4b80a0'
PHONE = '+79103916790'

async def main():
    print("\n" + "=" * 70)
    print("АВТОРИЗАЦИЯ TELEGRAM")
    print("=" * 70)
    print()
    
    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    try:
        await client.start(
            phone=PHONE,
            code_callback=lambda: '68280'  # Ваш код
        )
        
        if await client.is_user_authorized():
            print()
            print("=" * 70)
            print("✅ УСПЕШНО! TELEGRAM АВТОРИЗОВАН")
            print("=" * 70)
            print()
            
            me = await client.get_me()
            print(f"✓ Имя: {me.first_name} {me.last_name or ''}")
            print(f"✓ Username: @{me.username or 'не установлен'}")
            print(f"✓ Телефон: {me.phone}")
            print()
            print("✓ Сессия сохранена: telegram_session.session")
            print()
            print("Настроенные каналы:")
            print("  • @moynizhny - Мой Нижний")
            print("  • @bez_cenz_nn - Без цензуры НН")
            print("  • @today_nn - Сегодня в НН")
            print("  • @nizhniy_smi - СМИ Нижнего")
            print("  • @nn52signal, @nn_obl, @nnzhest, @nn_ru")
            print()
            print("=" * 70)
            print("TELEGRAM ГОТОВ! Запустите сбор данных:")
            print("=" * 70)
            print()
            print("  python run_collection_once.py")
            print()
            
            return True
        else:
            print("Авторизация не удалась")
            return False
            
    except SessionPasswordNeededError:
        print()
        print("⚠️  Требуется пароль двухфакторной аутентификации")
        print()
        password = input("Введите пароль Telegram: ")
        
        await client.sign_in(password=password)
        
        if await client.is_user_authorized():
            print()
            print("✅ Успешно авторизован с паролем!")
            me = await client.get_me()
            print(f"Пользователь: {me.first_name}")
            return True
            
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()

if __name__ == '__main__':
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
