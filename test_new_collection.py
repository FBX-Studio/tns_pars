"""
Быстрый тест: собрать 1-2 новости и проверить что тональность определяется
"""
import logging
from app_enhanced import app
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer
from collectors.news_collector import NewsCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_new_collection():
    """Тест нового сбора с проверкой тональности"""
    
    logger.info("="*70)
    logger.info("ТЕСТ: НОВЫЙ СБОР С ОПРЕДЕЛЕНИЕМ ТОНАЛЬНОСТИ")
    logger.info("="*70)
    
    with app.app_context():
        # Запоминаем количество записей ДО
        count_before = Review.query.count()
        logger.info(f"\nЗаписей в базе ДО сбора: {count_before}")
        
        # Создаем анализатор и коллектор
        logger.info("\nИнициализация...")
        sentiment_analyzer = SentimentAnalyzer()
        news_collector = NewsCollector(sentiment_analyzer=sentiment_analyzer)
        
        info = sentiment_analyzer.get_analyzer_info()
        logger.info(f"✓ Анализатор: {info['name']}")
        
        # Ограничиваем сбор для теста
        news_collector.search_queries = news_collector.search_queries[:1]
        
        # Собираем
        logger.info("\nЗапуск сбора (1 запрос)...")
        logger.info("-"*70)
        articles = news_collector.collect()
        logger.info("-"*70)
        
        if not articles:
            logger.warning("\n⚠ Новости не найдены (возможно, нет новых релевантных статей)")
            return
        
        logger.info(f"\n✓ Собрано статей: {len(articles)}")
        
        # Проверяем тональность
        logger.info("\nПроверка тональности в собранных данных:")
        
        with_sentiment = 0
        without_sentiment = 0
        
        for i, article in enumerate(articles[:5], 1):
            has_sentiment = 'sentiment_label' in article and article.get('sentiment_label')
            
            if has_sentiment:
                with_sentiment += 1
                status = "✓"
            else:
                without_sentiment += 1
                status = "✗"
            
            logger.info(f"\n{i}. {status} Статья:")
            logger.info(f"   Текст: {article.get('text', '')[:80]}...")
            
            if has_sentiment:
                logger.info(f"   Тональность: {article['sentiment_label']} (score: {article['sentiment_score']:.3f})")
            else:
                logger.info(f"   ТОНАЛЬНОСТЬ НЕ ОПРЕДЕЛЕНА!")
        
        # Сохраняем в БД
        logger.info(f"\n{'-'*70}")
        logger.info("Сохранение в базу данных...")
        
        saved = 0
        for article in articles:
            # Проверяем дубликаты
            existing = Review.query.filter_by(source_id=article['source_id']).first()
            if existing:
                continue
            
            # Если нет тональности - анализируем (подстраховка)
            if 'sentiment_label' not in article or not article.get('sentiment_label'):
                sentiment = sentiment_analyzer.analyze(article['text'])
                article['sentiment_score'] = sentiment['sentiment_score']
                article['sentiment_label'] = sentiment['sentiment_label']
            
            # Сохраняем
            review = Review(
                source=article['source'],
                source_id=article['source_id'],
                author=article.get('author'),
                author_id=article.get('author_id'),
                text=article['text'],
                url=article.get('url'),
                published_date=article.get('published_date'),
                sentiment_score=article['sentiment_score'],
                sentiment_label=article['sentiment_label']
            )
            
            db.session.add(review)
            saved += 1
        
        db.session.commit()
        
        # Проверяем что сохранилось
        count_after = Review.query.count()
        
        logger.info(f"\n{'='*70}")
        logger.info("РЕЗУЛЬТАТЫ:")
        logger.info(f"{'='*70}")
        logger.info(f"Собрано статей: {len(articles)}")
        logger.info(f"С тональностью при сборе: {with_sentiment}/{len(articles)}")
        logger.info(f"Сохранено в БД: {saved}")
        logger.info(f"Всего в базе ПОСЛЕ: {count_after} (было {count_before})")
        
        if saved > 0:
            # Показываем последнюю добавленную
            logger.info(f"\nПоследняя добавленная запись:")
            latest = Review.query.order_by(Review.id.desc()).first()
            logger.info(f"  ID: {latest.id}")
            logger.info(f"  Источник: {latest.source}")
            logger.info(f"  Тональность: {latest.sentiment_label} ({latest.sentiment_score:.3f})")
            logger.info(f"  Текст: {latest.text[:100]}...")
        
        logger.info(f"\n{'='*70}")
        
        if with_sentiment == len(articles) and saved > 0:
            logger.info("✓ ВСЕ ОТЛИЧНО! Тональность определяется корректно!")
        elif with_sentiment > 0:
            logger.warning("⚠ ЧАСТИЧНО РАБОТАЕТ: Не все статьи получили тональность")
        else:
            logger.error("✗ ПРОБЛЕМА: Тональность не определяется!")
        
        logger.info(f"{'='*70}\n")

if __name__ == '__main__':
    try:
        test_new_collection()
    except KeyboardInterrupt:
        logger.warning("\n⚠ Тест прерван")
    except Exception as e:
        logger.error(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
