"""
Быстрая проверка работоспособности коллекторов
"""
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_telegram():
    """Тест Telegram коллектора"""
    try:
        from collectors.telegram_user_collector import TelegramUserCollector
        collector = TelegramUserCollector()
        logger.info("✓ Telegram коллектор инициализирован")
        
        # Проверяем настройки
        if not collector.api_id:
            logger.error("✗ TELEGRAM_API_ID не настроен")
            return False
        if not collector.api_hash:
            logger.error("✗ TELEGRAM_API_HASH не настроен")
            return False
        if not collector.phone:
            logger.error("✗ TELEGRAM_PHONE не настроен")
            return False
        
        logger.info(f"  API ID: {collector.api_id}")
        logger.info(f"  Каналов для мониторинга: {len(collector.channels)}")
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка Telegram: {e}")
        return False

def test_zen():
    """Тест Яндекс.Дзен коллектора"""
    try:
        from collectors.zen_collector import ZenCollector
        collector = ZenCollector()
        logger.info("✓ Zen коллектор инициализирован")
        logger.info(f"  Ключевых слов: {len(collector.keywords)}")
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка Zen: {e}")
        return False

def test_ok():
    """Тест OK коллектора"""
    try:
        from collectors.ok_api_collector import OKAPICollector
        collector = OKAPICollector()
        logger.info("✓ OK коллектор инициализирован")
        
        # Проверяем токен
        if not collector.access_token or collector.access_token == 'your_ok_token_here':
            logger.warning("⚠ OK токен не настроен или использует значение по умолчанию")
            logger.info("  Получите токен на: https://ok.ru/dk?st.cmd=appsInfoMyDevList")
            return False
        
        logger.info(f"  Токен настроен: {collector.access_token[:20]}...")
        return True
    except ImportError:
        try:
            from collectors.ok_collector import OKCollector
            collector = OKCollector()
            logger.info("✓ OK коллектор (альтернативный) инициализирован")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка OK: {e}")
            return False
    except Exception as e:
        logger.error(f"✗ Ошибка OK: {e}")
        return False

def main():
    logger.info("=" * 70)
    logger.info("ПРОВЕРКА КОЛЛЕКТОРОВ")
    logger.info("=" * 70)
    
    results = {
        'Telegram': test_telegram(),
        'Яндекс.Дзен': test_zen(),
        'Одноклассники': test_ok()
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("РЕЗУЛЬТАТЫ")
    logger.info("=" * 70)
    
    for name, status in results.items():
        status_str = "✓ OK" if status else "✗ ПРОБЛЕМА"
        logger.info(f"{name}: {status_str}")
    
    passed = sum(results.values())
    total = len(results)
    logger.info(f"\nПройдено тестов: {passed}/{total}")

if __name__ == '__main__':
    main()
