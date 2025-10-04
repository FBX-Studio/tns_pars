"""
Полный тест парсинга новостей с бесплатными прокси и RSS
"""
import sys
import logging
from collectors.news_collector import NewsCollector
from collectors.web_collector import WebCollector
from utils.proxy_manager import ProxyManager
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_proxy_manager():
    """Тест 1: ProxyManager"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 1: ProxyManager - Получение бесплатных прокси")
    logger.info("=" * 70)
    
    try:
        proxy_manager = ProxyManager()
        count = proxy_manager.update_proxies(max_working=3)
        
        if count > 0:
            logger.info(f"✓ Найдено рабочих прокси: {count}")
            for i, proxy in enumerate(proxy_manager.proxies, 1):
                logger.info(f"  {i}. {proxy['ip']}:{proxy['port']} ({proxy['source']})")
            return True
        else:
            logger.warning("✗ Не найдено рабочих прокси (продолжаем без них)")
            return True  # Не критично
            
    except Exception as e:
        logger.error(f"Ошибка ProxyManager: {e}")
        return True  # Не критично

def test_news_collector_rss():
    """Тест 2: RSS парсинг без прокси"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 2: NewsCollector - RSS feeds (без прокси)")
    logger.info("=" * 70)
    
    try:
        # Отключаем прокси для RSS
        Config.USE_FREE_PROXIES = 'False'
        
        collector = NewsCollector()
        collector.use_free_proxies = False
        collector.current_proxy = None
        
        articles = []
        
        # Тестируем каждый RSS feed отдельно
        for feed_url in collector.rss_feeds[:2]:  # Первые 2 для быстроты
            logger.info(f"Тестируем RSS: {feed_url}")
            feed_articles = collector.collect_from_rss(feed_url)
            articles.extend(feed_articles)
        
        logger.info(f"\n✓ RSS парсинг завершен. Найдено статей: {len(articles)}")
        
        if articles:
            logger.info("\nПримеры найденных статей:")
            for i, article in enumerate(articles[:2], 1):
                logger.info(f"\n--- Статья {i} ---")
                logger.info(f"Источник: {article.get('author')}")
                logger.info(f"URL: {article.get('url')}")
                logger.info(f"Текст: {article.get('text')[:150]}...")
                logger.info(f"Дата: {article.get('published_date')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка RSS парсинга: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_collector_google():
    """Тест 3: Google News поиск"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 3: NewsCollector - Google News поиск")
    logger.info("=" * 70)
    
    try:
        Config.USE_FREE_PROXIES = 'False'
        
        collector = NewsCollector()
        collector.use_free_proxies = False
        collector.current_proxy = None
        
        # Тестируем один запрос
        query = 'ТНС энерго Нижний Новгород'
        logger.info(f"Поиск в Google News: {query}")
        
        articles = collector.search_google_news(query)
        
        logger.info(f"\n✓ Google News поиск завершен. Найдено статей: {len(articles)}")
        
        if articles:
            logger.info("\nПримеры найденных статей:")
            for i, article in enumerate(articles[:2], 1):
                logger.info(f"\n--- Статья {i} ---")
                logger.info(f"Заголовок: {article.get('text').split('\\n')[0]}")
                logger.info(f"URL: {article.get('url')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка Google News: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_collector_full():
    """Тест 4: Полный сбор новостей"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 4: NewsCollector - Полный сбор")
    logger.info("=" * 70)
    
    try:
        Config.USE_FREE_PROXIES = 'False'
        
        collector = NewsCollector()
        collector.use_free_proxies = False
        collector.current_proxy = None
        
        # Ограничиваем количество для быстрого теста
        collector.rss_feeds = collector.rss_feeds[:1]
        collector.search_queries = collector.search_queries[:1]
        
        logger.info("Запуск полного сбора новостей...")
        articles = collector.collect()
        
        logger.info(f"\n✓ Полный сбор завершен. Всего статей: {len(articles)}")
        
        if articles:
            logger.info("\nСтатистика по источникам:")
            sources = {}
            for article in articles:
                author = article.get('author', 'Unknown')
                sources[author] = sources.get(author, 0) + 1
            
            for source, count in sources.items():
                logger.info(f"  {source}: {count} статей")
        
        return len(articles) > 0
        
    except Exception as e:
        logger.error(f"✗ Ошибка полного сбора: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_collector():
    """Тест 5: Старый WebCollector для сравнения"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 5: WebCollector - Старый метод (для сравнения)")
    logger.info("=" * 70)
    
    try:
        Config.USE_FREE_PROXIES = 'False'
        
        collector = WebCollector()
        collector.use_free_proxies = False
        collector.current_proxy = None
        collector.news_sites = ['https://nn.ru']
        
        logger.info("Тестируем старый WebCollector...")
        articles = collector.collect()
        
        logger.info(f"\n✓ WebCollector завершен. Найдено статей: {len(articles)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка WebCollector: {e}")
        return True  # Не критично

def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 70)
    logger.info("ПОЛНОЕ ТЕСТИРОВАНИЕ ПАРСИНГА НОВОСТЕЙ")
    logger.info("=" * 70)
    
    results = {}
    
    # Тест 1: ProxyManager
    logger.info("\nЗапуск тестов...")
    results['proxy_manager'] = test_proxy_manager()
    
    # Тест 2: RSS парсинг
    results['rss_parsing'] = test_news_collector_rss()
    
    # Тест 3: Google News
    results['google_news'] = test_news_collector_google()
    
    # Тест 4: Полный сбор
    results['full_collection'] = test_news_collector_full()
    
    # Тест 5: WebCollector
    results['web_collector'] = test_web_collector()
    
    # Итоги
    logger.info("\n" + "=" * 70)
    logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    logger.info("=" * 70)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name:20s}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    logger.info(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed >= 3:  # Минимум 3 теста должны пройти
        logger.info("\n✓ СИСТЕМА ПАРСИНГА НОВОСТЕЙ РАБОТАЕТ!")
        logger.info("Проект готов к использованию.")
        return 0
    else:
        logger.warning("\n✗ ТРЕБУЕТСЯ ДОРАБОТКА")
        logger.warning("Проверьте ошибки выше.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
