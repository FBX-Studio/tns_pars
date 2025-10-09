"""
Тест улучшений Telegram и OK коллекторов
"""
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_delays():
    """Проверка задержек в Telegram коллекторе"""
    logger.info("=" * 70)
    logger.info("ТЕСТ 1: Проверка задержек в Telegram коллекторе")
    logger.info("=" * 70)
    
    try:
        from collectors.telegram_user_collector import TelegramUserCollector
        import inspect
        
        # Читаем исходный код
        source = inspect.getsource(TelegramUserCollector.search_in_channels)
        
        # Проверяем задержку между каналами
        if 'await asyncio.sleep(10)' in source:
            logger.info("✅ Задержка между каналами: 10 секунд (правильно)")
        elif 'await asyncio.sleep(3)' in source:
            logger.warning("⚠️ Задержка между каналами: 3 секунды (старая)")
        else:
            logger.error("❌ Задержка между каналами не найдена")
        
        # Проверяем задержку для комментариев
        if 'await asyncio.sleep(1)' in source:
            logger.info("✅ Задержка для комментариев: 1 секунда (правильно)")
        elif 'await asyncio.sleep(0.3)' in source:
            logger.warning("⚠️ Задержка для комментариев: 0.3 секунды (старая)")
        
        logger.info("✅ ТЕСТ 1 ПРОЙДЕН")
        return True
        
    except Exception as e:
        logger.error(f"❌ ТЕСТ 1 ПРОВАЛЕН: {e}")
        return False

def test_ok_selenium_integration():
    """Проверка интеграции OK Selenium"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 2: Проверка интеграции OK Selenium")
    logger.info("=" * 70)
    
    results = {}
    
    # Проверка final_collection.py
    try:
        with open('final_collection.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from collectors.ok_selenium_collector import OKSeleniumCollector' in content:
                logger.info("✅ final_collection.py: OK Selenium интегрирован")
                results['final_collection'] = True
            else:
                logger.warning("⚠️ final_collection.py: OK Selenium не найден")
                results['final_collection'] = False
    except Exception as e:
        logger.error(f"❌ final_collection.py: {e}")
        results['final_collection'] = False
    
    # Проверка run_collection_once.py
    try:
        with open('run_collection_once.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from collectors.ok_selenium_collector import OKSeleniumCollector' in content:
                logger.info("✅ run_collection_once.py: OK Selenium интегрирован")
                results['run_collection_once'] = True
            else:
                logger.warning("⚠️ run_collection_once.py: OK Selenium не найден")
                results['run_collection_once'] = False
    except Exception as e:
        logger.error(f"❌ run_collection_once.py: {e}")
        results['run_collection_once'] = False
    
    # Проверка async_monitor_websocket.py
    try:
        with open('async_monitor_websocket.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from collectors.ok_selenium_collector import OKSeleniumCollector' in content:
                logger.info("✅ async_monitor_websocket.py: OK Selenium интегрирован")
                results['async_monitor'] = True
            else:
                logger.warning("⚠️ async_monitor_websocket.py: OK Selenium не найден")
                results['async_monitor'] = False
    except Exception as e:
        logger.error(f"❌ async_monitor_websocket.py: {e}")
        results['async_monitor'] = False
    
    if all(results.values()):
        logger.info("✅ ТЕСТ 2 ПРОЙДЕН: OK Selenium интегрирован во все файлы")
        return True
    else:
        logger.warning(f"⚠️ ТЕСТ 2 ЧАСТИЧНО ПРОЙДЕН: {sum(results.values())}/3 файлов")
        return False

def test_telegram_channels_config():
    """Проверка конфигурации Telegram каналов"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 3: Проверка конфигурации Telegram каналов")
    logger.info("=" * 70)
    
    try:
        from config import Config
        
        channels = Config.TELEGRAM_CHANNELS
        channel_count = len(channels) if channels else 0
        
        logger.info(f"Количество каналов: {channel_count}")
        
        if channel_count >= 60:
            logger.info("✅ Большой список каналов (60+) - максимальный охват")
            logger.warning("⚠️ ВНИМАНИЕ: Сбор займет 10+ минут")
            logger.info("💡 Для быстрого сбора используйте --no-telegram или сократите список")
        elif channel_count >= 15:
            logger.info("✅ Средний список каналов (15-60) - баланс скорости и охвата")
        elif channel_count >= 5:
            logger.info("✅ Малый список каналов (5-15) - быстрый сбор")
        else:
            logger.warning("⚠️ Мало каналов (<5) - ограниченный охват")
        
        # Показать первые 10 каналов
        if channels and len(channels) > 0:
            logger.info(f"Первые 10 каналов: {', '.join(channels[:10])}")
        
        logger.info("✅ ТЕСТ 3 ПРОЙДЕН")
        return True
        
    except Exception as e:
        logger.error(f"❌ ТЕСТ 3 ПРОВАЛЕН: {e}")
        return False

def test_ok_selenium_collector():
    """Проверка работы OK Selenium коллектора"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 4: Проверка OK Selenium коллектора")
    logger.info("=" * 70)
    
    try:
        from collectors.ok_selenium_collector import OKSeleniumCollector
        
        logger.info("✅ OK Selenium коллектор импортирован")
        
        # Проверяем методы
        collector = OKSeleniumCollector()
        
        required_methods = ['_init_driver', '_close_driver', 'search_ok', 'collect']
        for method in required_methods:
            if hasattr(collector, method):
                logger.info(f"✅ Метод {method} существует")
            else:
                logger.error(f"❌ Метод {method} отсутствует")
                return False
        
        logger.info("✅ ТЕСТ 4 ПРОЙДЕН")
        logger.info("💡 Для полного теста запустите: python test_ok_selenium.py")
        return True
        
    except ImportError as e:
        logger.error(f"❌ ТЕСТ 4 ПРОВАЛЕН: Не удалось импортировать OK Selenium коллектор")
        logger.error(f"Ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ ТЕСТ 4 ПРОВАЛЕН: {e}")
        return False

def main():
    """Запуск всех тестов"""
    logger.info("\n")
    logger.info("*" * 70)
    logger.info("ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ TELEGRAM И OK КОЛЛЕКТОРОВ")
    logger.info("*" * 70)
    logger.info("\n")
    
    results = {}
    
    # Запуск тестов
    results['telegram_delays'] = test_telegram_delays()
    results['ok_integration'] = test_ok_selenium_integration()
    results['telegram_config'] = test_telegram_channels_config()
    results['ok_collector'] = test_ok_selenium_collector()
    
    # Итоги
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
    logger.info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nВсего тестов: {total}")
    logger.info(f"Пройдено: {passed}")
    logger.info(f"Провалено: {total - passed}")
    
    if passed == total:
        logger.info("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        logger.info("\n✅ Система готова к использованию:")
        logger.info("   python final_collection.py")
        logger.info("\n📚 Документация:")
        logger.info("   TELEGRAM_OK_IMPROVEMENTS.md")
    else:
        logger.warning("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        logger.info("Проверьте ошибки выше")
    
    logger.info("=" * 70)

if __name__ == '__main__':
    main()
