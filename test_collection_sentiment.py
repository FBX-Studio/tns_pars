"""
Тестовый запуск сбора с проверкой тональности
"""
import logging
from analyzers.sentiment_analyzer import SentimentAnalyzer
from collectors.news_collector import NewsCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("="*70)
logger.info("ТЕСТ: СБОР НОВОСТЕЙ С АНАЛИЗОМ ТОНАЛЬНОСТИ")
logger.info("="*70)

# Инициализация анализатора
logger.info("\n1. Инициализация анализатора...")
sentiment_analyzer = SentimentAnalyzer()
info = sentiment_analyzer.get_analyzer_info()
logger.info(f"✓ Анализатор: {info['name']}")
logger.info(f"✓ Тип: {info['type']}")

# Тест анализатора
logger.info("\n2. Тест анализатора на примере текста...")
test_text = "Отличная работа! Быстро помогли решить проблему."
result = sentiment_analyzer.analyze(test_text)
logger.info(f"Текст: {test_text}")
logger.info(f"✓ Результат: {result['sentiment_label']} (score: {result['sentiment_score']:.3f})")

# Создание коллектора С передачей анализатора
logger.info("\n3. Создание коллектора С анализатором...")
news_collector = NewsCollector(sentiment_analyzer=sentiment_analyzer)

# Проверяем что анализатор передался
if news_collector.sentiment_analyzer:
    logger.info("✓ sentiment_analyzer успешно передан в коллектор")
    logger.info(f"✓ Тип: {type(news_collector.sentiment_analyzer)}")
else:
    logger.error("✗ sentiment_analyzer НЕ передан в коллектор!")

# Запуск сбора (только 1-2 новости для теста)
logger.info("\n4. Запуск тестового сбора (1 запрос)...")
logger.info("="*70)

# Ограничиваем количество запросов для теста
news_collector.search_queries = news_collector.search_queries[:1]

try:
    articles = news_collector.collect()
    
    logger.info("\n" + "="*70)
    logger.info("РЕЗУЛЬТАТЫ СБОРА:")
    logger.info("="*70)
    logger.info(f"Собрано статей: {len(articles)}")
    
    if articles:
        logger.info("\nПРОВЕРКА ТОНАЛЬНОСТИ В СОБРАННЫХ ДАННЫХ:")
        logger.info("-"*70)
        
        for i, article in enumerate(articles[:5], 1):
            logger.info(f"\n{i}. Статья:")
            logger.info(f"   Источник: {article.get('source', 'unknown')}")
            logger.info(f"   Текст: {article.get('text', '')[:100]}...")
            
            # Проверяем наличие полей тональности
            has_score = 'sentiment_score' in article
            has_label = 'sentiment_label' in article
            
            if has_score and has_label:
                logger.info(f"   ✓ sentiment_score: {article['sentiment_score']:.3f}")
                logger.info(f"   ✓ sentiment_label: {article['sentiment_label']}")
            else:
                logger.error(f"   ✗ ТОНАЛЬНОСТЬ НЕ ОПРЕДЕЛЕНА!")
                logger.error(f"      has_score: {has_score}")
                logger.error(f"      has_label: {has_label}")
        
        # Общая статистика
        with_sentiment = sum(1 for a in articles if 'sentiment_label' in a and a.get('sentiment_label'))
        logger.info(f"\n" + "="*70)
        logger.info(f"ИТОГО: {with_sentiment}/{len(articles)} статей с тональностью")
        logger.info("="*70)
        
        if with_sentiment == 0:
            logger.error("\n✗ ПРОБЛЕМА: НИ ОДНА СТАТЬЯ НЕ ПОЛУЧИЛА ТОНАЛЬНОСТЬ!")
            logger.error("   Проверьте логи выше для деталей")
        elif with_sentiment < len(articles):
            logger.warning(f"\n⚠ ЧАСТИЧНАЯ ПРОБЛЕМА: Только {with_sentiment}/{len(articles)} статей с тональностью")
        else:
            logger.info("\n✓ ВСЕ СТАТЬИ УСПЕШНО ПРОАНАЛИЗИРОВАНЫ!")
    else:
        logger.warning("Статьи не найдены (возможно, нет подходящих новостей)")
        
except Exception as e:
    logger.error(f"\n✗ ОШИБКА при сборе: {e}")
    import traceback
    traceback.print_exc()
