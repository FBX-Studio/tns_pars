"""
Финальный сбор данных со всех источников с комментариями
"""
import sys
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Принудительная перезагрузка .env
load_dotenv(override=True)

from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector
from collectors.telegram_user_collector import TelegramUserCollector
from collectors.news_collector import NewsCollector
from collectors.zen_collector import ZenCollector
from collectors.zen_selenium_collector import ZenSeleniumCollector
try:
    from collectors.ok_selenium_collector import OKSeleniumCollector as OKAPICollector
    logger.info("Используется OK Selenium коллектор (обход ограничений API)")
except ImportError:
    try:
        from collectors.ok_api_collector import OKAPICollector
        logger.warning("OK Selenium не найден, используется API коллектор (ограниченный)")
    except ImportError:
        from collectors.ok_collector import OKCollector as OKAPICollector
        logger.warning("Используется базовый OK коллектор")
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator

# Импорт app с обработкой ошибок
try:
    from app_enhanced import app
except ImportError:
    try:
        from app import app
    except ImportError:
        # Создаем минимальный app context если app не найден
        from flask import Flask
        from models import db
        from config import Config
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Сбор данных из всех источников')
    parser.add_argument('--comments', action='store_true', 
                       help='[Устарело] Комментарии теперь собираются всегда')
    parser.add_argument('--no-vk', action='store_true', help='Пропустить VK')
    parser.add_argument('--no-telegram', action='store_true', help='Пропустить Telegram')
    parser.add_argument('--no-news', action='store_true', help='Пропустить новости')
    parser.add_argument('--no-zen', action='store_true', help='Пропустить Яндекс.Дзен')
    parser.add_argument('--no-ok', action='store_true', help='Пропустить Одноклассники')
    parser.add_argument('--zen-selenium', action='store_true', 
                       help='Использовать Selenium для Дзена (используется по умолчанию)')
    parser.add_argument('--zen-simple', action='store_true',
                       help='Использовать простой коллектор Дзена (без Selenium, может не работать)')
    args = parser.parse_args()
    
    logger.info("\n" + "=" * 70)
    logger.info("ФИНАЛЬНЫЙ СБОР ДАННЫХ ИЗ ВСЕХ ИСТОЧНИКОВ")
    collect_comments = True
    if args.comments:
        logger.info("Флаг --comments устарел: комментарии собираются по умолчанию")
    if collect_comments:
        logger.info("Режим: С ПАРСИНГОМ КОММЕНТАРИЕВ (всегда включено)")
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
    
    # Выбор коллектора для Дзена
    # По умолчанию используем Selenium для обхода капчи
    if args.zen_simple:
        logger.info("⚠️ Используется обычный коллектор Дзена (может быть капча)")
        zen_collector = ZenCollector()
    else:
        logger.info("🌐 Используется Selenium для Яндекс.Дзен (обход капчи)")
        zen_collector = ZenSeleniumCollector()
    
    ok_collector = OKAPICollector()
    
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    all_reviews = []
    
    # 1. VK
    if not args.no_vk:
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
    if not args.no_telegram:
        logger.info("\n" + "=" * 70)
        logger.info("2️⃣  СБОР ИЗ TELEGRAM")
        logger.info("(с комментариями/ответами)")
        logger.info("=" * 70)
        logger.info("Каналы: @moynizhny, @bez_cenz_nn, @today_nn, @nizhniy_smi, @nn52signal")
        try:
            tg_reviews = telegram_collector.collect(collect_comments=collect_comments)
            messages = [r for r in tg_reviews if not r.get('is_comment', False)]
            comments = [r for r in tg_reviews if r.get('is_comment', False)]
            logger.info(f"✓ Telegram: найдено {len(messages)} сообщений")
            logger.info(f"✓ Telegram: найдено {len(comments)} ответов")
            all_reviews.extend(tg_reviews)
        except Exception as e:
            logger.error(f"✗ Ошибка Telegram: {e}")
            import traceback
            traceback.print_exc()
    
    # 3. Новости
    if not args.no_news:
        logger.info("\n" + "=" * 70)
        logger.info("3️⃣  СБОР НОВОСТЕЙ (Google News)")
        logger.info("(с комментариями)")
        logger.info("=" * 70)
        try:
            news = news_collector.collect_with_comments()
            articles = [r for r in news if not r.get('is_comment', False)]
            comments = [r for r in news if r.get('is_comment', False)]
            logger.info(f"✓ Новости: найдено {len(articles)} статей")
            logger.info(f"✓ Новости: найдено {len(comments)} комментариев")
            all_reviews.extend(news)
        except Exception as e:
            logger.error(f"✗ Ошибка новостей: {e}")
    
    # 4. Яндекс.Дзен
    if not args.no_zen:
        logger.info("\n" + "=" * 70)
        logger.info("4️⃣  СБОР ИЗ ЯНДЕКС.ДЗЕН")
        logger.info("(с комментариями)")
        logger.info("=" * 70)
        try:
            zen = zen_collector.collect(collect_comments=collect_comments)
            articles = [r for r in zen if not r.get('is_comment', False)]
            comments = [r for r in zen if r.get('is_comment', False)]
            logger.info(f"✓ Дзен: найдено {len(articles)} статей")
            logger.info(f"✓ Дзен: найдено {len(comments)} комментариев")
            all_reviews.extend(zen)
        except Exception as e:
            logger.error(f"✗ Ошибка Дзен: {e}")
    
    # 5. Одноклассники
    if not args.no_ok:
        logger.info("\n" + "=" * 70)
        logger.info("5️⃣  СБОР ИЗ ОДНОКЛАССНИКОВ")
        logger.info("=" * 70)
        try:
            ok_posts = ok_collector.collect()
            logger.info(f"✓ Одноклассники: найдено {len(ok_posts)} постов")
            all_reviews.extend(ok_posts)
        except Exception as e:
            logger.error(f"✗ Ошибка Одноклассники: {e}")
            import traceback
            traceback.print_exc()
    
    # Сохранение
    logger.info("\n" + "=" * 70)
    logger.info("💾 СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
    logger.info("=" * 70)
    logger.info(f"Всего собрано: {len(all_reviews)} записей")
    
    saved = 0
    parent_mapping = {}
    
    with app.app_context():
        for review_data in all_reviews:
            existing = Review.query.filter_by(source_id=review_data['source_id']).first()
            if existing:
                # Store mapping for parent-child relationships
                if not review_data.get('is_comment', False):
                    parent_mapping[review_data['source_id']] = existing.id
                continue
            
            sentiment = sentiment_analyzer.analyze(review_data['text'])
            keywords = sentiment_analyzer.extract_keywords(review_data['text'])
            
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                review_data['text'],
                sentiment['sentiment_score']
            )
            
            # Determine parent_id for comments
            parent_id = None
            if review_data.get('is_comment', False):
                parent_source_id = review_data.get('parent_source_id')
                if parent_source_id:
                    # Try to find in mapping first
                    parent_id = parent_mapping.get(parent_source_id)
                    # If not in mapping, query database
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
            
            # Store new parent for future children
            if not review_data.get('is_comment', False):
                db.session.flush()
                parent_mapping[review_data['source_id']] = review.id
        
        db.session.commit()
        
        total = Review.query.count()
        articles_count = Review.query.filter_by(is_comment=False).count()
        comments_count = Review.query.filter_by(is_comment=True).count()
        
        vk_count = Review.query.filter_by(source='vk', is_comment=False).count()
        tg_count = Review.query.filter_by(source='telegram', is_comment=False).count()
        news_count = Review.query.filter(Review.source.in_(['news', 'web']), Review.is_comment==False).count()
        zen_count = Review.query.filter_by(source='zen', is_comment=False).count()
        ok_count = Review.query.filter_by(source='ok', is_comment=False).count()
        
        positive = Review.query.filter_by(sentiment_label='positive').count()
        negative = Review.query.filter_by(sentiment_label='negative').count()
        neutral = Review.query.filter_by(sentiment_label='neutral').count()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ РЕЗУЛЬТАТЫ СБОРА")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых: {saved}")
        logger.info(f"✓ Всего в базе: {total} ({articles_count} статей, {comments_count} комментариев)")
        logger.info(f"\n📊 По источникам:")
        logger.info(f"   VK: {vk_count}")
        logger.info(f"   Telegram: {tg_count}")
        logger.info(f"   Новости: {news_count}")
        logger.info(f"   Яндекс.Дзен: {zen_count}")
        logger.info(f"   Одноклассники: {ok_count}")
        logger.info(f"\n😊 По тональности:")
        logger.info(f"   Позитивные: {positive}")
        logger.info(f"   Негативные: {negative}")
        logger.info(f"   Нейтральные: {neutral}")
        logger.info("\n💡 Комментарии и ответы собираются автоматически при каждом запуске")
        logger.info("\n✓ Сбор завершен! Откройте веб-интерфейс:")
        logger.info("   python app.py")
        logger.info("   http://localhost:5000")
        logger.info("=" * 70)

if __name__ == '__main__':
    main()
