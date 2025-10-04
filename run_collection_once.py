"""
Запуск единоразового сбора данных БЕЗ прокси (быстрее)
"""
from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector
try:
    from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
except ImportError:
    from collectors.telegram_collector import TelegramCollector
try:
    from collectors.news_collector import NewsCollector
except ImportError:
    from collectors.web_collector import WebCollector as NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from config import Config
from app import app
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Отключаем прокси для быстроты
Config.USE_FREE_PROXIES = 'False'

def collect_once():
    """Одноразовый сбор данных"""
    
    logger.info("=" * 70)
    logger.info("ЗАПУСК ЕДИНОРАЗОВОГО СБОРА ДАННЫХ (БЕЗ ПРОКСИ)")
    logger.info("=" * 70)
    
    vk_collector = VKCollector()
    telegram_collector = TelegramCollector()
    news_collector = NewsCollector()
    news_collector.use_free_proxies = False
    news_collector.current_proxy = None
    
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    all_reviews = []
    
    # 1. VK
    logger.info("\n1️⃣ Сбор из VK...")
    try:
        vk_reviews = vk_collector.collect()
        logger.info(f"✓ VK: найдено {len(vk_reviews)} отзывов")
        all_reviews.extend(vk_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка VK: {e}")
    
    # 2. Telegram
    logger.info("\n2️⃣ Сбор из Telegram...")
    try:
        tg_reviews = telegram_collector.collect()
        logger.info(f"✓ Telegram: найдено {len(tg_reviews)} сообщений")
        all_reviews.extend(tg_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка Telegram: {e}")
    
    # 3. Новости
    logger.info("\n3️⃣ Сбор новостей (БЕЗ прокси)...")
    try:
        news = news_collector.collect()
        logger.info(f"✓ Новости: найдено {len(news)} статей")
        all_reviews.extend(news)
    except Exception as e:
        logger.error(f"✗ Ошибка новостей: {e}")
    
    # Сохранение в БД
    logger.info(f"\n💾 Сохранение в базу данных...")
    logger.info(f"Всего собрано: {len(all_reviews)} записей")
    
    saved = 0
    with app.app_context():
        for review_data in all_reviews:
            # Проверка дубликатов
            existing = Review.query.filter_by(source_id=review_data['source_id']).first()
            if existing:
                continue
            
            # Анализ
            sentiment = sentiment_analyzer.analyze(review_data['text'])
            keywords = sentiment_analyzer.extract_keywords(review_data['text'])
            
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                review_data['text'],
                sentiment['sentiment_score']
            )
            
            # Создание записи
            review = Review(
                source=review_data['source'],
                source_id=review_data['source_id'],
                author=review_data.get('author'),
                author_id=review_data.get('author_id'),
                text=review_data['text'],
                url=review_data.get('url'),
                published_date=review_data.get('published_date'),
                sentiment_score=sentiment['sentiment_score'],
                sentiment_label=sentiment['sentiment_label'],
                keywords=','.join(keywords) if keywords else None,
                moderation_status=moderation_status,
                moderation_reason=moderation_reason,
                requires_manual_review=requires_manual,
                processed=not requires_manual
            )
            
            db.session.add(review)
            saved += 1
        
        db.session.commit()
        
        # Статистика
        total = Review.query.count()
        
        logger.info("\n" + "=" * 70)
        logger.info("РЕЗУЛЬТАТЫ СБОРА")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых записей: {saved}")
        logger.info(f"✓ Всего в базе: {total} записей")
        
        # По источникам
        vk_count = Review.query.filter_by(source='vk').count()
        tg_count = Review.query.filter_by(source='telegram').count()
        news_count = Review.query.filter(Review.source.in_(['news', 'web'])).count()
        
        logger.info(f"\nРаспределение по источникам:")
        logger.info(f"  VK: {vk_count}")
        logger.info(f"  Telegram: {tg_count}")
        logger.info(f"  Новости: {news_count}")
        
        # По тональности
        positive = Review.query.filter_by(sentiment_label='positive').count()
        negative = Review.query.filter_by(sentiment_label='negative').count()
        neutral = Review.query.filter_by(sentiment_label='neutral').count()
        
        logger.info(f"\nТональность:")
        logger.info(f"  Позитивные: {positive}")
        logger.info(f"  Негативные: {negative}")
        logger.info(f"  Нейтральные: {neutral}")
        
        logger.info("\n✓ Сбор завершен успешно!")
        logger.info("=" * 70)

if __name__ == '__main__':
    collect_once()
