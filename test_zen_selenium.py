"""
Тест парсинга Яндекс.Дзен через Selenium (обход капчи)
"""
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("ТЕСТ ПАРСИНГА ЯНДЕКС.ДЗЕН ЧЕРЕЗ SELENIUM")
logger.info("=" * 70)
logger.info("Selenium запускает реальный Chrome браузер")
logger.info("Это обходит капчу, так как выглядит как реальный пользователь")
logger.info("=" * 70)
logger.info("")

# Импорт коллектора
try:
    from collectors.zen_selenium_collector import ZenSeleniumCollector
    logger.info("✅ ZenSeleniumCollector импортирован")
except Exception as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    logger.error("\nВозможные причины:")
    logger.error("  1. Не установлен Chrome браузер")
    logger.error("  2. Не установлен Selenium: pip install selenium")
    logger.error("  3. Не установлен webdriver-manager: pip install webdriver-manager")
    sys.exit(1)

# Создание коллектора
logger.info("")
logger.info("Создание коллектора...")
collector = ZenSeleniumCollector()
logger.info("✅ Коллектор создан")

# Запуск сбора
logger.info("")
logger.info("=" * 70)
logger.info("ЗАПУСК ПАРСИНГА")
logger.info("=" * 70)
logger.info("Selenium откроет Chrome браузер (headless режим)")
logger.info("Это займет 1-2 минуты...")
logger.info("")

try:
    articles = collector.collect(collect_comments=False)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("РЕЗУЛЬТАТЫ")
    logger.info("=" * 70)
    logger.info(f"✅ Найдено статей: {len(articles)}")
    
    if articles:
        logger.info("")
        logger.info("Найденные статьи:")
        for i, article in enumerate(articles, 1):
            logger.info(f"\n{i}. {article.get('text', '')[:100]}...")
            logger.info(f"   URL: {article.get('url', 'N/A')}")
            logger.info(f"   Автор: {article.get('author', 'N/A')}")
            logger.info(f"   Дата: {article.get('published_date', 'N/A')}")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ ПАРСИНГ УСПЕШЕН!")
        logger.info("=" * 70)
        logger.info(f"Selenium обошел капчу Яндекса")
        logger.info(f"Найдено {len(articles)} релевантных статей")
        logger.info("")
        logger.info("Теперь можно интегрировать в final_collection.py")
        
    else:
        logger.warning("⚠️ Статьи не найдены")
        logger.info("\nВозможные причины:")
        logger.info("  1. Нет статей по ключевым словам")
        logger.info("  2. Яндекс изменил структуру страниц")
        logger.info("  3. Проблема с селекторами")
        
except Exception as e:
    logger.error(f"❌ Ошибка при сборе: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

logger.info("")
logger.info("=" * 70)
logger.info("ТЕСТ ЗАВЕРШЕН")
logger.info("=" * 70)
