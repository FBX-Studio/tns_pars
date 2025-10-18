"""
Сбор данных из Яндекс.Дзен через Selenium с сохранением в БД
"""
import logging
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

from collectors.zen_selenium_collector import ZenSeleniumCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from models import db, Review
from app_enhanced import app
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("СБОР ЯНДЕКС.ДЗЕН ЧЕРЕЗ SELENIUM")
    logger.info("=" * 70)
    logger.info("Selenium обходит капчу, парсинг займет 2-3 минуты")
    logger.info("=" * 70)
    logger.info("")
    
    # Инициализация
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    # Создаем коллектор С передачей sentiment_analyzer
    collector = ZenSeleniumCollector(sentiment_analyzer=sentiment_analyzer)
    
    # Сбор данных
    logger.info("Запуск сбора...")
    try:
        articles = collector.collect(collect_comments=False)
        logger.info(f"✅ Собрано статей: {len(articles)}")
    except Exception as e:
        logger.error(f"❌ Ошибка сбора: {e}")
        sys.exit(1)
    
    if len(articles) == 0:
        logger.warning("⚠️ Не найдено статей")
        return
    
    # Сохранение в БД
    logger.info("")
    logger.info("Сохранение в базу данных...")
    
    saved = 0
    with app.app_context():
        for article in articles:
            # Проверка на дубликат
            existing = Review.query.filter_by(source_id=article['source_id']).first()
            if existing:
                continue
            
            # Анализ
            sentiment = sentiment_analyzer.analyze(article['text'])
            keywords = sentiment_analyzer.extract_keywords(article['text'])
            
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                article['text'],
                sentiment['sentiment_score']
            )
            
            # Создание записи
            review = Review(
                source=article['source'],
                source_id=article['source_id'],
                author=article.get('author'),
                author_id=article.get('author_id'),
                text=article['text'],
                url=article.get('url'),
                published_date=article.get('published_date'),
                sentiment_score=sentiment['sentiment_score'],
                sentiment_label=sentiment['sentiment_label'],
                keywords=','.join(keywords) if keywords else None,
                moderation_status=moderation_status,
                moderation_reason=moderation_reason,
                requires_manual_review=requires_manual,
                processed=not requires_manual,
                is_comment=False
            )
            
            db.session.add(review)
            saved += 1
        
        db.session.commit()
        
        # Статистика
        total = Review.query.count()
        dzen_count = Review.query.filter_by(source='dzen').count()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ РЕЗУЛЬТАТЫ")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых статей: {saved}")
        logger.info(f"✓ Всего в базе из Дзена: {dzen_count}")
        logger.info(f"✓ Всего записей в базе: {total}")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()
