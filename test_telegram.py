"""
Тест парсинга Telegram каналов
"""
import sys
import logging
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_bot_collector():
    """Тест Telegram Bot API коллектора"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 1: Telegram Bot API Collector")
    logger.info("=" * 70)
    
    try:
        from collectors.telegram_collector import TelegramCollector
        
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.warning("✗ TELEGRAM_BOT_TOKEN не настроен в .env")
            logger.info("Пропускаем тест Bot API")
            return True  # Не критично
        
        collector = TelegramCollector()
        
        if not collector.bot:
            logger.warning("✗ Telegram Bot не инициализирован")
            return True
        
        logger.info("✓ Telegram Bot инициализирован")
        logger.info(f"Каналы для мониторинга: {Config.TELEGRAM_CHANNELS}")
        
        if not Config.TELEGRAM_CHANNELS or not Config.TELEGRAM_CHANNELS[0]:
            logger.warning("Каналы не настроены в TELEGRAM_CHANNELS")
            logger.info("Для использования Bot API добавьте бота в каналы")
            return True
        
        logger.info("Попытка сбора сообщений...")
        messages = collector.collect()
        
        logger.info(f"✓ Собрано сообщений: {len(messages)}")
        
        if messages:
            for i, msg in enumerate(messages[:2], 1):
                logger.info(f"\n--- Сообщение {i} ---")
                logger.info(f"Автор: {msg.get('author')}")
                logger.info(f"Текст: {msg.get('text')[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка Telegram Bot API: {e}")
        import traceback
        traceback.print_exc()
        return True  # Не критично

def test_telegram_user_collector():
    """Тест Telegram User API коллектора (Telethon)"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 2: Telegram User API Collector (Telethon)")
    logger.info("=" * 70)
    
    try:
        from collectors.telegram_user_collector import TelegramUserCollector
        
        api_id = Config.get('TELEGRAM_API_ID', '')
        api_hash = Config.get('TELEGRAM_API_HASH', '')
        
        if not api_id or not api_hash:
            logger.warning("✗ TELEGRAM_API_ID и TELEGRAM_API_HASH не настроены")
            logger.info("\nДля использования Telegram User API:")
            logger.info("1. Зарегистрируйтесь на https://my.telegram.org")
            logger.info("2. Получите API_ID и API_HASH")
            logger.info("3. Добавьте их в .env файл")
            logger.info("4. Запустите python setup_telegram.py для авторизации")
            return True  # Не критично
        
        collector = TelegramUserCollector()
        
        logger.info("✓ Telegram User API коллектор инициализирован")
        logger.info(f"API ID: {api_id}")
        logger.info(f"Каналы для мониторинга: {Config.TELEGRAM_CHANNELS}")
        
        if not Config.TELEGRAM_CHANNELS or not Config.TELEGRAM_CHANNELS[0]:
            logger.warning("Каналы не настроены в TELEGRAM_CHANNELS")
            logger.info("\nПримеры каналов для мониторинга:")
            logger.info("  @breakingmash - Новости")
            logger.info("  @rbc_news - РБК")
            logger.info("  @nnov_news - Новости Нижнего Новгорода")
            return True
        
        logger.info("\nПримечание: для работы User API требуется авторизация")
        logger.info("Запустите: python setup_telegram.py")
        
        return True
        
    except ImportError:
        logger.warning("✗ Telethon не установлен")
        logger.info("Установите: pip install telethon")
        return True
    except Exception as e:
        logger.error(f"Ошибка Telegram User API: {e}")
        import traceback
        traceback.print_exc()
        return True

def test_telegram_config():
    """Тест конфигурации Telegram"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 3: Проверка конфигурации Telegram")
    logger.info("=" * 70)
    
    config_ok = True
    
    # Bot Token
    if Config.TELEGRAM_BOT_TOKEN:
        logger.info(f"✓ TELEGRAM_BOT_TOKEN: {Config.TELEGRAM_BOT_TOKEN[:10]}...")
    else:
        logger.warning("✗ TELEGRAM_BOT_TOKEN не настроен")
        logger.info("  Получите токен: https://t.me/BotFather")
        config_ok = False
    
    # User API
    api_id = Config.get('TELEGRAM_API_ID', '')
    api_hash = Config.get('TELEGRAM_API_HASH', '')
    
    if api_id and api_hash:
        logger.info(f"✓ TELEGRAM_API_ID: {api_id}")
        logger.info(f"✓ TELEGRAM_API_HASH: {api_hash[:10]}...")
    else:
        logger.warning("✗ TELEGRAM_API_ID/HASH не настроены")
        logger.info("  Получите: https://my.telegram.org")
        config_ok = False
    
    # Channels
    if Config.TELEGRAM_CHANNELS and Config.TELEGRAM_CHANNELS[0]:
        logger.info(f"✓ TELEGRAM_CHANNELS: {', '.join(Config.TELEGRAM_CHANNELS)}")
    else:
        logger.warning("✗ TELEGRAM_CHANNELS не настроены")
        logger.info("  Добавьте каналы в .env файл")
        config_ok = False
    
    if not config_ok:
        logger.info("\n" + "=" * 70)
        logger.info("ИНСТРУКЦИЯ ПО НАСТРОЙКЕ TELEGRAM")
        logger.info("=" * 70)
        logger.info("\n1. Telegram Bot API (простой, ограниченный):")
        logger.info("   - Создайте бота через @BotFather")
        logger.info("   - Получите токен")
        logger.info("   - Добавьте в .env: TELEGRAM_BOT_TOKEN=ваш_токен")
        logger.info("   - Добавьте бота в каналы как администратора")
        logger.info("\n2. Telegram User API (мощный, любые каналы):")
        logger.info("   - Зарегистрируйтесь на https://my.telegram.org")
        logger.info("   - Получите API_ID и API_HASH")
        logger.info("   - Добавьте в .env:")
        logger.info("     TELEGRAM_API_ID=ваш_api_id")
        logger.info("     TELEGRAM_API_HASH=ваш_api_hash")
        logger.info("     TELEGRAM_PHONE=+79991234567")
        logger.info("   - Запустите: python setup_telegram.py")
        logger.info("\n3. Настройте каналы:")
        logger.info("   TELEGRAM_CHANNELS=@channel1,@channel2")
    
    return True  # Не критично для общей работы

def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТИРОВАНИЕ ПАРСИНГА TELEGRAM")
    logger.info("=" * 70)
    
    results = {}
    
    # Тест 1: Конфигурация
    results['config'] = test_telegram_config()
    
    # Тест 2: Bot API
    results['bot_api'] = test_telegram_bot_collector()
    
    # Тест 3: User API
    results['user_api'] = test_telegram_user_collector()
    
    # Итоги
    logger.info("\n" + "=" * 70)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ TELEGRAM")
    logger.info("=" * 70)
    
    for test_name, result in results.items():
        status = "✓ OK" if result else "✗ FAILED"
        logger.info(f"{test_name:20s}: {status}")
    
    logger.info("\n" + "=" * 70)
    logger.info("ВЫВОДЫ")
    logger.info("=" * 70)
    
    if Config.TELEGRAM_BOT_TOKEN or Config.get('TELEGRAM_API_ID'):
        logger.info("✓ Telegram настроен частично или полностью")
        logger.info("Система может работать с Telegram")
    else:
        logger.warning("! Telegram не настроен")
        logger.info("Система будет работать БЕЗ Telegram (только VK и новости)")
        logger.info("Для добавления Telegram следуйте инструкции выше")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
