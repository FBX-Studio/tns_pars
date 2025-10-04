"""
Прямая настройка Telegram User API
"""
import sys
from telethon import TelegramClient
import asyncio

# Ваши данные
API_ID = 25079847
API_HASH = '37a06d1d36fbf3879d3a81935e4b80a0'
PHONE = '+79103916790'

async def setup_telegram():
    print("=" * 70)
    print("НАСТРОЙКА TELEGRAM USER API")
    print("=" * 70)
    print()
    print(f"✓ API ID: {API_ID}")
    print(f"✓ Телефон: {PHONE}")
    print()
    
    # Создаем клиент
    client = TelegramClient('telegram_session', API_ID, API_HASH)
    
    try:
        print("Подключение к Telegram...")
        await client.start(phone=PHONE)
        
        if await client.is_user_authorized():
            print()
            print("=" * 70)
            print("✅ УСПЕШНО! Telegram User API настроен и авторизован")
            print("=" * 70)
            print()
            print("Сессия сохранена в файл: telegram_session.session")
            print()
            print("Теперь система может:")
            print("  ✓ Читать ЛЮБЫЕ публичные каналы Telegram")
            print("  ✓ Собирать сообщения с упоминаниями компании")
            print("  ✓ Работать автоматически без повторной авторизации")
            print()
            print("Настроенные каналы:")
            print("  @moynizhny - Мой Нижний")
            print("  @bez_cenz_nn - Без цензуры НН")
            print("  @today_nn - Сегодня в НН")
            print("  @nizhniy_smi - СМИ Нижнего")
            print("  @nn52signal - NN52 Signal")
            print("  @nn_obl - Нижегородская область")
            print("  @nnzhest - НН Жесть")
            print("  @nn_ru - NN.RU новости")
            print()
            print("Для запуска сбора:")
            print("  python run_collection_once.py")
            print()
            return True
        else:
            print("❌ Авторизация не удалась")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()

if __name__ == '__main__':
    try:
        print()
        print("ВАЖНО: Вам придет SMS с кодом подтверждения")
        print("Приготовьтесь ввести код из SMS...")
        print()
        input("Нажмите Enter когда будете готовы...")
        print()
        
        result = asyncio.run(setup_telegram())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
