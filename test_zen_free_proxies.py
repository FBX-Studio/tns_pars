"""
Тест парсинга Яндекс.Дзен через бесплатные прокси
"""
import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("ТЕСТ ПАРСИНГА ЯНДЕКС.ДЗЕН ЧЕРЕЗ БЕСПЛАТНЫЕ ПРОКСИ")
logger.info("=" * 70)

# Проверяем настройки
from config import Config

use_free_proxies = Config.get('USE_FREE_PROXIES', '').lower() == 'true'
use_tor = Config.get('USE_TOR', '').lower() == 'true'

logger.info(f"Настройки:")
logger.info(f"  USE_FREE_PROXIES: {use_free_proxies}")
logger.info(f"  USE_TOR: {use_tor}")

if not use_free_proxies:
    logger.error("❌ USE_FREE_PROXIES=False")
    logger.info("Включите в .env: USE_FREE_PROXIES=True")
    sys.exit(1)

if use_tor:
    logger.warning("⚠️ USE_TOR=True - отключаем для теста бесплатных прокси")
    logger.info("Установите в .env: USE_TOR=False")

logger.info("✅ Бесплатные прокси включены")
logger.info("")

# Загружаем прокси
logger.info("Загрузка бесплатных прокси...")
from utils.proxy_manager import ProxyManager

proxy_manager = ProxyManager()

logger.info("Получение списка прокси из публичных источников...")
proxies = proxy_manager.fetch_proxies()
logger.info(f"✅ Загружено {len(proxies)} прокси")

if len(proxies) == 0:
    logger.error("❌ Не удалось загрузить прокси")
    sys.exit(1)

logger.info("")
logger.info("Проверка прокси (тестируем первые 20)...")
logger.info("Это займет 1-2 минуты...")
logger.info("")

working_proxies = []
tested = 0

for proxy in proxies[:20]:
    tested += 1
    logger.info(f"[{tested}/20] Тестирую: {proxy}")
    
    if proxy_manager.test_proxy(proxy, timeout=5):
        logger.info(f"  ✅ РАБОТАЕТ: {proxy}")
        working_proxies.append(proxy)
        
        if len(working_proxies) >= 5:
            logger.info(f"\n✅ Найдено {len(working_proxies)} рабочих прокси - достаточно для теста")
            break
    else:
        logger.info(f"  ❌ Не работает")

logger.info("")
logger.info("=" * 70)
logger.info(f"РЕЗУЛЬТАТ: {len(working_proxies)} рабочих прокси из {tested} проверенных")
logger.info("=" * 70)

if len(working_proxies) == 0:
    logger.error("❌ Не найдено рабочих прокси")
    logger.info("\nВозможные причины:")
    logger.info("  1. Все бесплатные прокси заблокированы")
    logger.info("  2. Прокси сейчас недоступны")
    logger.info("\nРекомендации:")
    logger.info("  - Используйте Tor с мостами (см. TOR_BRIDGES_SETUP.md)")
    logger.info("  - Или купите платные прокси (200₽/месяц)")
    sys.exit(1)

logger.info("")
logger.info("Рабочие прокси:")
for i, proxy in enumerate(working_proxies, 1):
    logger.info(f"  {i}. {proxy}")

# Обновляем список прокси в менеджере
proxy_manager.proxies = working_proxies

logger.info("")
logger.info("=" * 70)
logger.info("ЗАПУСК ПАРСИНГА ДЗЕНА С ПРОКСИ")
logger.info("=" * 70)

# Импортируем коллектор
try:
    from collectors.zen_collector import ZenCollector
    logger.info("✅ ZenCollector импортирован")
except Exception as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Создаем коллектор
logger.info("")
logger.info("Создание коллектора...")
collector = ZenCollector()

# Устанавливаем рабочие прокси
collector.proxies_list = [f'http://{p}' for p in working_proxies]
logger.info(f"✅ Коллектор создан с {len(working_proxies)} рабочими прокси")

# Запускаем сбор
logger.info("")
logger.info("Запуск сбора данных из Дзена...")
logger.info("Используем ротацию прокси для обхода капчи...")
logger.info("Это может занять 2-3 минуты...")
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
        logger.info("Первые 3 статьи:")
        for i, article in enumerate(articles[:3], 1):
            logger.info(f"\n{i}. {article.get('text', '')[:100]}...")
            logger.info(f"   URL: {article.get('url', 'N/A')}")
            logger.info(f"   Источник: {article.get('source', 'N/A')}")
            logger.info(f"   Дата: {article.get('published_date', 'N/A')}")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ ПАРСИНГ УСПЕШЕН!")
        logger.info("=" * 70)
        logger.info(f"Бесплатные прокси помогли обойти капчу")
        logger.info(f"Найдено {len(articles)} релевантных статей")
    else:
        logger.warning("⚠️ Статьи не найдены")
        logger.info("\nВозможные причины:")
        logger.info("  1. Яндекс показал капчу (даже через прокси)")
        logger.info("  2. Нет статей по ключевым словам")
        logger.info("  3. Все прокси были заблокированы Яндексом")
        logger.info("\nРекомендации:")
        logger.info("  - Попробуйте позже (прокси могут обновиться)")
        logger.info("  - Используйте Tor с мостами")
        logger.info("  - Купите платные прокси для надежности")
        
except Exception as e:
    logger.error(f"❌ Ошибка при сборе: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

logger.info("")
logger.info("=" * 70)
logger.info("ТЕСТ ЗАВЕРШЕН")
logger.info("=" * 70)
