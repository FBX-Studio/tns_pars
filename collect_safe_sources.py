"""
Безопасный сбор данных из источников БЕЗ ограничений
(VK и Новостные сайты - они не блокируют)
"""
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from models import db, Review
from collectors.vk_collector import VKCollector
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from app import app
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("БЕЗОПАСНЫЙ СБОР ДАННЫХ")
    logger.info("Источники: VK + Новостные сайты (без блокировок)")
    logger.info("=" * 70)
    
    # Отключаем прокси для скорости
    os.environ['USE_FREE_PROXIES'] = 'False'
    
    # Инициализация
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    # Создаем коллекторы С sentiment_analyzer
    vk_collector = VKCollector()
    vk_collector.sentiment_analyzer = sentiment_analyzer
    
    news_collector = NewsCollector(sentiment_analyzer=sentiment_analyzer)
    news_collector.use_free_proxies = False
    news_collector.current_proxy = None
    
    all_reviews = []
    
    # 1. VK
    logger.info("\n1️⃣ Сбор из VK...")
    try:
        vk_reviews = vk_collector.collect()
        logger.info(f"✓ VK: найдено {len(vk_reviews)} отзывов")
        all_reviews.extend(vk_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка VK: {e}")
    
    # 2. Новости
    logger.info("\n2️⃣ Сбор новостей...")
    try:
        news = news_collector.collect()
        logger.info(f"✓ Новости: найдено {len(news)} статей")
        all_reviews.extend(news)
    except Exception as e:
        logger.error(f"✗ Ошибка новостей: {e}")
    
    # Сохранение
    logger.info(f"\n💾 Сохранение в базу данных...")
    logger.info(f"Всего собрано: {len(all_reviews)} записей")
    
    saved = 0
    parent_mapping = {}
    
    with app.app_context():
        for review_data in all_reviews:
            existing = Review.query.filter_by(source_id=review_data['source_id']).first()
            if existing:
                if not review_data.get('is_comment', False):
                    parent_mapping[review_data['source_id']] = existing.id
                continue
            
            sentiment = sentiment_analyzer.analyze(review_data['text'])
            keywords = sentiment_analyzer.extract_keywords(review_data['text'])
            
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                review_data['text'],
                sentiment['sentiment_score']
            )
            
            parent_id = None
            if review_data.get('is_comment', False):
                parent_source_id = review_data.get('parent_source_id')
                if parent_source_id:
                    parent_id = parent_mapping.get(parent_source_id)
                    if not parent_id:
                        parent = Review.query.filter_by(source_id=parent_source_id).first()
                        if parent:
                            parent_id = parent.id
                            parent_mapping[parent_source_id] = parent_id
            
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
                processed=not requires_manual,
                parent_id=parent_id,
                is_comment=review_data.get('is_comment', False)
            )
            
            db.session.add(review)
            saved += 1
            
            if not review_data.get('is_comment', False):
                db.session.flush()
                parent_mapping[review_data['source_id']] = review.id
        
        db.session.commit()
        
        # Статистика
        total = Review.query.count()
        articles_count = Review.query.filter_by(is_comment=False).count()
        comments_count = Review.query.filter_by(is_comment=True).count()
        
        vk_count = Review.query.filter_by(source='vk', is_comment=False).count()
        news_count = Review.query.filter(Review.source.in_(['news', 'web']), Review.is_comment==False).count()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ РЕЗУЛЬТАТЫ")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых: {saved}")
        logger.info(f"✓ Всего в базе: {total} ({articles_count} статей, {comments_count} комментариев)")
        logger.info(f"\nПо источникам:")
        logger.info(f"  VK: {vk_count}")
        logger.info(f"  Новости: {news_count}")
        
        logger.info("\n💡 Примечание:")
        logger.info("  Telegram, Дзен и OK пропущены из-за ограничений API")
        logger.info("  См. DIAGNOSIS.md для подробностей")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()
