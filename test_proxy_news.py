"""
Тест парсинга новостных сайтов через бесплатные прокси
"""
import sys
import logging
from collectors.web_collector import WebCollector
from utils.proxy_manager import ProxyManager
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_proxy_manager():
    """Тест ProxyManager - получение и проверка прокси"""
    logger.info("=" * 60)
    logger.info("ТЕСТ 1: ProxyManager - Получение бесплатных прокси")
    logger.info("=" * 60)
    
    proxy_manager = ProxyManager()
    
    logger.info("Получаем бесплатные прокси...")
    count = proxy_manager.update_proxies(max_working=5)
    
    if count > 0:
        logger.info(f"✓ Найдено рабочих прокси: {count}")
        
        # Показываем список прокси
        for i, proxy in enumerate(proxy_manager.proxies, 1):
            logger.info(f"  {i}. {proxy['ip']}:{proxy['port']} ({proxy['source']})")
        
        # Тестируем получение случайного прокси
        random_proxy = proxy_manager.get_random_proxy()
        if random_proxy:
            logger.info(f"✓ Случайный прокси: {random_proxy}")
            return True
    else:
        logger.warning("✗ Не найдено рабочих прокси")
        return False
    
    return True

def test_web_collector_with_proxy():
    """Тест WebCollector с бесплатными прокси"""
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТ 2: WebCollector - Парсинг новостей через прокси")
    logger.info("=" * 60)
    
    # Включаем бесплатные прокси
    Config.USE_FREE_PROXIES = 'True'
    
    web_collector = WebCollector()
    
    # Тестовые сайты
    test_sites = [
        'https://nn.ru',
        'https://www.vn.ru'
    ]
    
    logger.info(f"Тестируемые сайты: {test_sites}")
    web_collector.news_sites = test_sites
    
    try:
        logger.info("Запуск сбора новостей...")
        articles = web_collector.collect()
        
        logger.info(f"\n✓ Собрано статей: {len(articles)}")
        
        if articles:
            logger.info("\nПримеры найденных статей:")
            for i, article in enumerate(articles[:3], 1):
                logger.info(f"\n--- Статья {i} ---")
                logger.info(f"Источник: {article.get('author')}")
                logger.info(f"URL: {article.get('url')}")
                logger.info(f"Текст: {article.get('text')[:200]}...")
                logger.info(f"Дата: {article.get('published_date')}")
        else:
            logger.warning("✗ Статьи не найдены (возможно, нет упоминаний о компании)")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка при сборе новостей: {e}")
        return False

def test_web_collector_without_proxy():
    """Тест WebCollector без прокси (для сравнения)"""
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТ 3: WebCollector - Парсинг БЕЗ прокси")
    logger.info("=" * 60)
    
    # Отключаем прокси
    Config.USE_FREE_PROXIES = 'False'
    Config.HTTP_PROXY = ''
    Config.HTTPS_PROXY = ''
    Config.SOCKS_PROXY = ''
    Config.USE_TOR = 'False'
    
    web_collector = WebCollector()
    
    # Простой тестовый сайт
    web_collector.news_sites = ['https://httpbin.org/html']
    
    try:
        logger.info("Тестируем подключение без прокси...")
        response = web_collector._request_with_retry('https://httpbin.org/ip')
        
        if response:
            logger.info(f"✓ Подключение без прокси работает")
            logger.info(f"Ваш IP: {response.text}")
            return True
    except Exception as e:
        logger.error(f"✗ Ошибка при подключении: {e}")
        return False
    
    return False

def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 60)
    logger.info("ТЕСТИРОВАНИЕ ПАРСИНГА НОВОСТЕЙ С БЕСПЛАТНЫМИ ПРОКСИ")
    logger.info("=" * 60)
    
    results = {
        'proxy_manager': False,
        'web_with_proxy': False,
        'web_without_proxy': False
    }
    
    # Тест 1: ProxyManager
    try:
        results['proxy_manager'] = test_proxy_manager()
    except Exception as e:
        logger.error(f"Ошибка в тесте ProxyManager: {e}")
    
    # Тест 2: WebCollector с прокси
    try:
        results['web_with_proxy'] = test_web_collector_with_proxy()
    except Exception as e:
        logger.error(f"Ошибка в тесте WebCollector с прокси: {e}")
    
    # Тест 3: WebCollector без прокси
    try:
        results['web_without_proxy'] = test_web_collector_without_proxy()
    except Exception as e:
        logger.error(f"Ошибка в тесте WebCollector без прокси: {e}")
    
    # Итоги
    logger.info("\n" + "=" * 60)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        logger.info("Парсинг новостей через бесплатные прокси работает корректно.")
        return 0
    else:
        logger.warning("\n✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        logger.warning("Проверьте ошибки выше для деталей.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
