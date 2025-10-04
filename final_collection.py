"""
Финальный сбор данных со всех источников
"""
import sys
import os
from dotenv import load_dotenv

# Принудительная перезагрузка .env
load_dotenv(override=True)

from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector
from collectors.telegram_user_collector import TelegramUserCollector
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from app import app
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("\n" + "=" * 70)
    logger.info("ФИНАЛЬНЫЙ СБОР ДАННЫХ ИЗ ВСЕХ ИСТОЧНИКОВ")
    logger.info("=" * 70)
    
    # Проверка Telegram API
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    logger.info(f"\nTelegram API ID: {api_id}")
    logger.info(f"Telegram API Hash: {api_hash[:10] if api_hash else 'NOT SET'}...")
    logger.info(f"Telegram Phone: {os.getenv('TELEGRAM_PHONE')}")
    
    # Отключаем прокси для быстроты
    os.environ['USE_FREE_PROXIES'] = 'False'
    
    # Инициализация
    vk_collector = VKCollector()
    telegram_collector = TelegramUserCollector()
    news_collector = NewsCollector()
    news_collector.use_free_proxies = False
    news_collector.current_proxy = None
    
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    all_reviews = []
    
    # 1. VK
    logger.info("\n" + "=" * 70)
    logger.info("1️⃣  СБОР ИЗ VK")
    logger.info("=" * 70)
    try:
        vk_reviews = vk_collector.collect()
        logger.info(f"✓ VK: найдено {len(vk_reviews)} отзывов")
        all_reviews.extend(vk_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка VK: {e}")
    
    # 2. Telegram
    logger.info("\n" + "=" * 70)
    logger.info("2️⃣  СБОР ИЗ TELEGRAM")
    logger.info("=" * 70)
    logger.info("Каналы: @moynizhny, @bez_cenz_nn, @today_nn, @nizhniy_smi, @nn52signal")
    try:
        tg_reviews = telegram_collector.collect()
        logger.info(f"✓ Telegram: найдено {len(tg_reviews)} сообщений")
        all_reviews.extend(tg_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка Telegram: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Новости
    logger.info("\n" + "=" * 70)
    logger.info("3️⃣  СБОР НОВОСТЕЙ (Google News)")
    logger.info("=" * 70)
    try:
        news = news_collector.collect()
        logger.info(f"✓ Новости: найдено {len(news)} статей")
        all_reviews.extend(news)
    except Exception as e:
        logger.error(f"✗ Ошибка новостей: {e}")
    
    # Сохранение
    logger.info("\n" + "=" * 70)
    logger.info("💾 СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
    logger.info("=" * 70)
    logger.info(f"Всего собрано: {len(all_reviews)} записей")
    
    saved = 0
    with app.app_context():
        for review_data in all_reviews:
            existing = Review.query.filter_by(source_id=review_data['source_id']).first()
            if existing:
                continue
            
            sentiment = sentiment_analyzer.analyze(review_data['text'])
            keywords = sentiment_analyzer.extract_keywords(review_data['text'])
            
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                review_data['text'],
                sentiment['sentiment_score']
            )
            
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
        
        total = Review.query.count()
        vk_count = Review.query.filter_by(source='vk').count()
        tg_count = Review.query.filter_by(source='telegram').count()
        news_count = Review.query.filter(Review.source.in_(['news', 'web'])).count()
        
        positive = Review.query.filter_by(sentiment_label='positive').count()
        negative = Review.query.filter_by(sentiment_label='negative').count()
        neutral = Review.query.filter_by(sentiment_label='neutral').count()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ РЕЗУЛЬТАТЫ СБОРА")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых: {saved}")
        logger.info(f"✓ Всего в базе: {total}")
        logger.info(f"\n📊 По источникам:")
        logger.info(f"   VK: {vk_count}")
        logger.info(f"   Telegram: {tg_count}")
        logger.info(f"   Новости: {news_count}")
        logger.info(f"\n😊 По тональности:")
        logger.info(f"   Позитивные: {positive}")
        logger.info(f"   Негативные: {negative}")
        logger.info(f"   Нейтральные: {neutral}")
        logger.info("\n✓ Сбор завершен! Откройте веб-интерфейс:")
        logger.info("   python app.py")
        logger.info("   http://localhost:5000")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()
