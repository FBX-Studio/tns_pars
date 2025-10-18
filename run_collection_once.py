"""
Запуск единоразового сбора данных БЕЗ прокси (быстрее)
"""
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
try:
    from collectors.zen_selenium_collector import ZenSeleniumCollector
    ZenCollector = ZenSeleniumCollector  # Используем Selenium для обхода капчи
except ImportError:
    try:
        from collectors.zen_collector import ZenCollector
    except ImportError:
        ZenCollector = None
try:
    from collectors.ok_selenium_collector import OKSeleniumCollector as OKAPICollector
    logger.info("OK Selenium коллектор доступен (обход ограничений API)")
except ImportError:
    try:
        from collectors.ok_api_collector import OKAPICollector
        logger.warning("Используется OK API коллектор (ограниченный)")
    except ImportError:
        try:
            from collectors.ok_collector import OKCollector as OKAPICollector
        except ImportError:
            OKAPICollector = None
            logger.warning("OK коллектор недоступен")
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from config import Config
from app_enhanced import app

# Отключаем прокси для быстроты
Config.USE_FREE_PROXIES = 'False'

def collect_once():
    """Одноразовый сбор данных"""
    
    logger.info("=" * 70)
    logger.info("ЗАПУСК ЕДИНОРАЗОВОГО СБОРА ДАННЫХ (БЕЗ ПРОКСИ)")
    logger.info("=" * 70)
    logger.info("Комментарии и ответы собираются автоматически")
    
    vk_collector = VKCollector()
    telegram_collector = TelegramCollector()
    news_collector = NewsCollector()
    news_collector.use_free_proxies = False
    news_collector.current_proxy = None
    
    # Инициализация дополнительных коллекторов
    zen_collector = ZenCollector() if ZenCollector else None
    ok_collector = OKAPICollector() if OKAPICollector else None
    
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    # Передаем sentiment_analyzer во все коллекторы
    vk_collector.sentiment_analyzer = sentiment_analyzer
    telegram_collector.sentiment_analyzer = sentiment_analyzer
    news_collector.sentiment_analyzer = sentiment_analyzer
    if zen_collector:
        zen_collector.sentiment_analyzer = sentiment_analyzer
    if ok_collector:
        ok_collector.sentiment_analyzer = sentiment_analyzer
    
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
    logger.info("\n2️⃣ Сбор из Telegram (с комментариями)...")
    try:
        tg_reviews = telegram_collector.collect(collect_comments=True)
        messages = [r for r in tg_reviews if not r.get('is_comment', False)]
        comments = [r for r in tg_reviews if r.get('is_comment', False)]
        logger.info(f"✓ Telegram: найдено {len(messages)} сообщений, {len(comments)} комментариев")
        all_reviews.extend(tg_reviews)
    except Exception as e:
        logger.error(f"✗ Ошибка Telegram: {e}")
    
    # 3. Новости
    logger.info("\n3️⃣ Сбор новостей (БЕЗ прокси, с комментариями)...")
    try:
        news = news_collector.collect_with_comments()
        articles = [r for r in news if not r.get('is_comment', False)]
        comments = [r for r in news if r.get('is_comment', False)]
        logger.info(f"✓ Новости: найдено {len(articles)} статей, {len(comments)} комментариев")
        all_reviews.extend(news)
    except Exception as e:
        logger.error(f"✗ Ошибка новостей: {e}")
    
    # 4. Яндекс.Дзен (через Selenium для обхода капчи)
    if zen_collector:
        logger.info("\n4️⃣ Сбор из Яндекс.Дзен (Selenium - обход капчи)...")
        logger.info("   Это займет 2-3 минуты...")
        try:
            zen_posts = zen_collector.collect(collect_comments=True)
            articles = [r for r in zen_posts if not r.get('is_comment', False)]
            comments = [r for r in zen_posts if r.get('is_comment', False)]
            logger.info(f"✓ Дзен: найдено {len(articles)} статей, {len(comments)} комментариев")
            all_reviews.extend(zen_posts)
        except Exception as e:
            logger.error(f"✗ Ошибка Дзен: {e}")
    
    # 5. Одноклассники
    if ok_collector:
        logger.info("\n5️⃣ Сбор из Одноклассников...")
        try:
            ok_posts = ok_collector.collect()
            logger.info(f"✓ Одноклассники: найдено {len(ok_posts)} постов")
            all_reviews.extend(ok_posts)
        except Exception as e:
            logger.error(f"✗ Ошибка Одноклассники: {e}")
    
    # Сохранение в БД
    logger.info(f"\n💾 Сохранение в базу данных...")
    logger.info(f"Всего собрано: {len(all_reviews)} записей")
    
    saved = 0
    parent_mapping = {}
    
    with app.app_context():
        for review_data in all_reviews:
            # Проверка дубликатов
            existing = Review.query.filter_by(source_id=review_data['source_id']).first()
            if existing:
                # Store mapping for parent-child relationships
                if not review_data.get('is_comment', False):
                    parent_mapping[review_data['source_id']] = existing.id
                continue
            
            # Анализ
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
                    parent_id = parent_mapping.get(parent_source_id)
                    if not parent_id:
                        parent = Review.query.filter_by(source_id=parent_source_id).first()
                        if parent:
                            parent_id = parent.id
                            parent_mapping[parent_source_id] = parent_id
            
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
        
        # Статистика
        total = Review.query.count()
        articles_count = Review.query.filter_by(is_comment=False).count()
        comments_count = Review.query.filter_by(is_comment=True).count()
        
        logger.info("\n" + "=" * 70)
        logger.info("РЕЗУЛЬТАТЫ СБОРА")
        logger.info("=" * 70)
        logger.info(f"✓ Сохранено новых записей: {saved}")
        logger.info(f"✓ Всего в базе: {total} записей ({articles_count} статей, {comments_count} комментариев)")
        
        # По источникам
        vk_count = Review.query.filter_by(source='vk', is_comment=False).count()
        tg_count = Review.query.filter_by(source='telegram', is_comment=False).count()
        news_count = Review.query.filter(Review.source.in_(['news', 'web']), Review.is_comment==False).count()
        zen_count = Review.query.filter_by(source='zen', is_comment=False).count()
        ok_count = Review.query.filter_by(source='ok', is_comment=False).count()
        
        logger.info(f"\nРаспределение по источникам (статьи):")
        logger.info(f"  VK: {vk_count}")
        logger.info(f"  Telegram: {tg_count}")
        logger.info(f"  Новости: {news_count}")
        logger.info(f"  Яндекс.Дзен: {zen_count}")
        logger.info(f"  Одноклассники: {ok_count}")
        
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
