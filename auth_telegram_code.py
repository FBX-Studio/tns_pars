"""
Ввод кода из SMS для Telegram
Использование: python auth_telegram_code.py <КОД>
"""
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

# Ваши данные
API_ID = 25079847
API_HASH = '37a06d1d36fbf3879d3a81935e4b80a0'
PHONE = '+79103916790'

async def enter_code(code):
    print("\n" + "=" * 70)
    print("ВВОД КОДА ПОДТВЕРЖДЕНИЯ")
    print("=" * 70)
    print()
    
    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            print("✅ Вы уже авторизованы!")
            me = await client.get_me()
            print(f"Пользователь: {me.first_name} {me.last_name or ''}")
            await client.disconnect()
            return True
        
        print(f"Проверяем код: {code}")
        print()
        
        try:
            # Пробуем войти с кодом
            await client.sign_in(PHONE, code)
            
            if await client.is_user_authorized():
                print("=" * 70)
                print("✅ УСПЕШНО! TELEGRAM АВТОРИЗОВАН")
                print("=" * 70)
                print()
                
                me = await client.get_me()
                print(f"✓ Пользователь: {me.first_name} {me.last_name or ''}")
                print(f"✓ Username: @{me.username or 'не установлен'}")
                print(f"✓ Phone: {me.phone}")
                print()
                print("✓ Сессия сохранена: telegram_session.session")
                print()
                print("Настроенные каналы для мониторинга:")
                print("  • @moynizhny - Мой Нижний")
                print("  • @bez_cenz_nn - Без цензуры НН")
                print("  • @today_nn - Сегодня в НН")
                print("  • @nizhniy_smi - СМИ Нижнего")
                print("  • @nn52signal, @nn_obl, @nnzhest, @nn_ru")
                print()
                print("=" * 70)
                print("TELEGRAM ГОТОВ К РАБОТЕ!")
                print("=" * 70)
                print()
                print("Теперь запустите сбор данных:")
                print("  python run_collection_once.py")
                print()
                print("Или всю систему:")
                print("  python run.py")
                print()
                
                await client.disconnect()
                return True
            
        except SessionPasswordNeededError:
            print("⚠️  У вас включена двухфакторная аутентификация")
            print()
            password = input("Введите пароль от Telegram: ")
            print()
            
            await client.sign_in(password=password)
            
            if await client.is_user_authorized():
                print("✅ Авторизация с паролем успешна!")
                me = await client.get_me()
                print(f"Пользователь: {me.first_name} {me.last_name or ''}")
                print()
                print("✓ Telegram готов к работе!")
                await client.disconnect()
                return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print()
        print("Возможные причины:")
        print("  • Неверный код из SMS")
        print("  • Код устарел (действует 5 минут)")
        print("  • Проблемы с интернетом")
        print()
        print("Попробуйте еще раз:")
        print("  python auth_telegram.py")
        print()
        await client.disconnect()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\n❌ Ошибка: не указан код из SMS")
        print()
        print("Использование:")
        print("  python auth_telegram_code.py <КОД>")
        print()
        print("Пример:")
        print("  python auth_telegram_code.py 12345")
        print()
        sys.exit(1)
    
    code = sys.argv[1].strip()
    result = asyncio.run(enter_code(code))
    sys.exit(0 if result else 1)
