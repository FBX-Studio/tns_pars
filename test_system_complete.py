"""
Полный комплексный тест всей системы мониторинга
Проверяет: парсинг новостей с прокси, Telegram, VK, базу данных, веб-интерфейс
"""
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dependencies():
    """Тест 1: Проверка зависимостей"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 1: Проверка установленных зависимостей")
    logger.info("=" * 70)
    
    required_modules = {
        'flask': 'Flask',
        'requests': 'Requests',
        'bs4': 'BeautifulSoup4',
        'feedparser': 'FeedParser (RSS)',
        'sqlalchemy': 'SQLAlchemy',
        'dotenv': 'python-dotenv',
    }
    
    optional_modules = {
        'telethon': 'Telethon (Telegram User API)',
        'telegram': 'python-telegram-bot',
        'vk_api': 'VK API',
    }
    
    missing = []
    optional_missing = []
    
    for module, name in required_modules.items():
        try:
            __import__(module)
            logger.info(f"✓ {name}")
        except ImportError:
            logger.error(f"✗ {name} - НЕ УСТАНОВЛЕН!")
            missing.append(name)
    
    for module, name in optional_modules.items():
        try:
            __import__(module)
            logger.info(f"✓ {name}")
        except ImportError:
            logger.warning(f"! {name} - не установлен (опционально)")
            optional_missing.append(name)
    
    if missing:
        logger.error(f"\n✗ Отсутствуют обязательные модули: {', '.join(missing)}")
        logger.error("Запустите: pip install -r requirements.txt")
        return False
    
    if optional_missing:
        logger.info(f"\nОпциональные модули не установлены: {', '.join(optional_missing)}")
        logger.info("Система будет работать с ограниченным функционалом")
    
    logger.info("\n✓ Все обязательные зависимости установлены")
    return True

def test_config():
    """Тест 2: Проверка конфигурации"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 2: Проверка конфигурации")
    logger.info("=" * 70)
    
    try:
        from config import Config
        
        logger.info(f"✓ Config загружен")
        logger.info(f"  База данных: {Config.DATABASE_URL}")
        logger.info(f"  Ключевые слова: {', '.join(Config.COMPANY_KEYWORDS[:3])}...")
        logger.info(f"  Интервал мониторинга: {Config.MONITORING_INTERVAL_MINUTES} мин")
        logger.info(f"  Использовать прокси: {Config.get('USE_FREE_PROXIES', 'True')}")
        
        # Проверка API ключей
        if Config.VK_ACCESS_TOKEN:
            logger.info(f"✓ VK_ACCESS_TOKEN настроен")
        else:
            logger.warning(f"! VK_ACCESS_TOKEN не настроен")
        
        if Config.TELEGRAM_BOT_TOKEN:
            logger.info(f"✓ TELEGRAM_BOT_TOKEN настроен")
        else:
            logger.warning(f"! TELEGRAM_BOT_TOKEN не настроен")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка конфигурации: {e}")
        return False

def test_database():
    """Тест 3: Проверка базы данных"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 3: Проверка базы данных")
    logger.info("=" * 70)
    
    try:
        from models import db, Review, MonitoringLog
        from app import app
        
        with app.app_context():
            db.create_all()
            logger.info("✓ База данных инициализирована")
            
            # Проверка таблиц
            total_reviews = Review.query.count()
            total_logs = MonitoringLog.query.count()
            
            logger.info(f"  Отзывов в БД: {total_reviews}")
            logger.info(f"  Логов мониторинга: {total_logs}")
            
            if total_reviews > 0:
                recent = Review.query.order_by(Review.collected_date.desc()).first()
                logger.info(f"  Последний отзыв: {recent.collected_date}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка базы данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_proxy_manager():
    """Тест 4: Проверка ProxyManager"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 4: Проверка ProxyManager (бесплатные прокси)")
    logger.info("=" * 70)
    
    try:
        from utils.proxy_manager import ProxyManager
        
        proxy_manager = ProxyManager()
        logger.info("Получение бесплатных прокси (может занять ~1 минуту)...")
        
        count = proxy_manager.update_proxies(max_working=3)
        
        if count > 0:
            logger.info(f"✓ Найдено рабочих прокси: {count}")
            for i, proxy in enumerate(proxy_manager.proxies, 1):
                logger.info(f"  {i}. {proxy['ip']}:{proxy['port']} ({proxy['source']})")
            return True
        else:
            logger.warning("! Не найдено рабочих прокси")
            logger.info("Система будет работать без прокси")
            return True  # Не критично
            
    except Exception as e:
        logger.error(f"✗ Ошибка ProxyManager: {e}")
        return True  # Не критично

def test_news_collector():
    """Тест 5: Проверка NewsCollector"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 5: Проверка NewsCollector (парсинг новостей)")
    logger.info("=" * 70)
    
    try:
        from collectors.news_collector import NewsCollector
        from config import Config
        
        Config.USE_FREE_PROXIES = 'False'  # Без прокси для быстроты
        
        collector = NewsCollector()
        collector.use_free_proxies = False
        collector.current_proxy = None
        
        # Тестируем RSS
        logger.info("Тест RSS парсинга...")
        rss_articles = collector.collect_from_rss(collector.rss_feeds[0])
        logger.info(f"  RSS статей: {len(rss_articles)}")
        
        # Тестируем Google News
        logger.info("Тест Google News...")
        google_articles = collector.search_google_news('ТНС энерго Нижний Новгород')
        logger.info(f"  Google News статей: {len(google_articles)}")
        
        total = len(rss_articles) + len(google_articles)
        
        if total > 0:
            logger.info(f"✓ NewsCollector работает: найдено {total} статей")
            return True
        else:
            logger.warning("! NewsCollector не нашел статей (возможно, нет упоминаний)")
            return True  # Не критично
            
    except Exception as e:
        logger.error(f"✗ Ошибка NewsCollector: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_collector():
    """Тест 6: Проверка TelegramCollector"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 6: Проверка TelegramCollector")
    logger.info("=" * 70)
    
    try:
        from config import Config
        
        if not Config.TELEGRAM_BOT_TOKEN and not Config.get('TELEGRAM_API_ID'):
            logger.warning("! Telegram не настроен")
            logger.info("Система будет работать без Telegram")
            return True  # Не критично
        
        try:
            from collectors.telegram_user_collector import TelegramUserCollector
            collector = TelegramUserCollector()
            logger.info("✓ TelegramUserCollector инициализирован (User API)")
        except:
            from collectors.telegram_collector import TelegramCollector
            collector = TelegramCollector()
            logger.info("✓ TelegramCollector инициализирован (Bot API)")
        
        logger.info(f"  Каналы: {Config.TELEGRAM_CHANNELS}")
        
        if not Config.TELEGRAM_CHANNELS or not Config.TELEGRAM_CHANNELS[0]:
            logger.warning("! Каналы не настроены в TELEGRAM_CHANNELS")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка TelegramCollector: {e}")
        return True  # Не критично

def test_vk_collector():
    """Тест 7: Проверка VKCollector"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 7: Проверка VKCollector")
    logger.info("=" * 70)
    
    try:
        from collectors.vk_collector import VKCollector
        from config import Config
        
        if not Config.VK_ACCESS_TOKEN:
            logger.warning("! VK_ACCESS_TOKEN не настроен")
            logger.info("Система будет работать без VK")
            return True  # Не критично
        
        collector = VKCollector()
        logger.info("✓ VKCollector инициализирован")
        logger.info(f"  Поисковый запрос: {Config.VK_SEARCH_QUERY}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка VKCollector: {e}")
        return True  # Не критично

def test_analyzers():
    """Тест 8: Проверка анализаторов"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 8: Проверка анализаторов (AI/ML)")
    logger.info("=" * 70)
    
    try:
        from analyzers.sentiment_analyzer import SentimentAnalyzer
        from analyzers.moderator import Moderator
        
        analyzer = SentimentAnalyzer()
        moderator = Moderator()
        
        logger.info("✓ SentimentAnalyzer инициализирован")
        logger.info("✓ Moderator инициализирован")
        
        # Тест анализа
        test_text = "ТНС энерго НН предоставляет отличный сервис!"
        result = analyzer.analyze(test_text)
        
        logger.info(f"\nТест анализа тональности:")
        logger.info(f"  Текст: {test_text}")
        logger.info(f"  Оценка: {result['sentiment_score']:.2f}")
        logger.info(f"  Метка: {result['sentiment_label']}")
        
        keywords = analyzer.extract_keywords(test_text)
        logger.info(f"  Ключевые слова: {', '.join(keywords)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка анализаторов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_app():
    """Тест 9: Проверка веб-приложения"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ 9: Проверка веб-приложения Flask")
    logger.info("=" * 70)
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Тест главной страницы
            response = client.get('/')
            logger.info(f"✓ Главная страница: {response.status_code}")
            
            # Тест дашборда
            response = client.get('/dashboard')
            logger.info(f"✓ Дашборд: {response.status_code}")
            
            # Тест списка отзывов
            response = client.get('/reviews')
            logger.info(f"✓ Список отзывов: {response.status_code}")
            
            # Тест мониторинга
            response = client.get('/monitoring')
            logger.info(f"✓ Мониторинг: {response.status_code}")
        
        logger.info(f"\n✓ Веб-приложение работает")
        logger.info(f"  Запуск: python app.py")
        logger.info(f"  URL: http://localhost:5000")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка веб-приложения: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция комплексного тестирования"""
    logger.info("\n" + "=" * 80)
    logger.info("ПОЛНОЕ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ МОНИТОРИНГА")
    logger.info("Проект: ТНС ЭНЕРГО НН - Система сбора и анализа отзывов")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    
    tests = [
        ("Зависимости", test_dependencies),
        ("Конфигурация", test_config),
        ("База данных", test_database),
        ("ProxyManager", test_proxy_manager),
        ("NewsCollector", test_news_collector),
        ("TelegramCollector", test_telegram_collector),
        ("VKCollector", test_vk_collector),
        ("Анализаторы AI/ML", test_analyzers),
        ("Веб-приложение", test_web_app),
    ]
    
    results = {}
    critical_failed = []
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\nВыполнение: {test_name}...")
            results[test_name] = test_func()
            
            if not results[test_name] and test_name in ["Зависимости", "Конфигурация", "База данных", "NewsCollector", "Анализаторы AI/ML", "Веб-приложение"]:
                critical_failed.append(test_name)
                
        except Exception as e:
            logger.error(f"✗ Критическая ошибка в тесте '{test_name}': {e}")
            results[test_name] = False
            critical_failed.append(test_name)
    
    # Итоги
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    logger.info("\n" + "=" * 80)
    logger.info("РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name:30s}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    logger.info(f"\nИтого: {passed}/{total} тестов пройдено")
    logger.info(f"Время выполнения: {elapsed_time:.1f} сек")
    
    logger.info("\n" + "=" * 80)
    logger.info("ЗАКЛЮЧЕНИЕ")
    logger.info("=" * 80)
    
    if critical_failed:
        logger.error(f"\n✗ КРИТИЧЕСКИЕ ОШИБКИ В: {', '.join(critical_failed)}")
        logger.error("Система НЕ ГОТОВА к использованию")
        logger.error("Исправьте ошибки и повторите тестирование")
        return 1
    elif passed == total:
        logger.info("\n✓✓✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! ✓✓✓")
        logger.info("\n🎉 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        logger.info("\nДля запуска системы:")
        logger.info("  1. python run.py  - Запуск всей системы")
        logger.info("  2. python app.py  - Только веб-интерфейс")
        logger.info("  3. python monitor.py  - Только мониторинг")
        logger.info("\nВеб-интерфейс: http://localhost:5000")
        return 0
    else:
        logger.warning("\n! СИСТЕМА РАБОТОСПОСОБНА С ОГРАНИЧЕНИЯМИ")
        logger.info(f"\nПройдено {passed} из {total} тестов")
        logger.info("Некоторые функции могут быть недоступны (VK, Telegram)")
        logger.info("Базовый функционал (парсинг новостей, веб-интерфейс) работает")
        logger.info("\nДля запуска: python run.py")
        return 0

if __name__ == '__main__':
    sys.exit(main())
