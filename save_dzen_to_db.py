"""
Сбор и сохранение новостей из Дзен в базу данных
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True, encoding='utf-8')

from collect_dzen_duckduckgo import DzenDuckDuckGoCollector
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from app_enhanced import app
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("="*70)
    print("СБОР И СОХРАНЕНИЕ НОВОСТЕЙ ИЗ ЯНДЕКС.ДЗЕН")
    print("="*70)
    
    # Сбор новостей
    collector = DzenDuckDuckGoCollector()
    articles = collector.collect()
    
    if not articles:
        print("\n❌ Новости не найдены")
        return
    
    print("\n" + "="*70)
    print("СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
    print("="*70)
    
    # Инициализация анализаторов
    sentiment_analyzer = SentimentAnalyzer()
    moderator = Moderator()
    
    saved = 0
    skipped = 0
    
    with app.app_context():
        for article_data in articles:
            # Проверяем дубликаты
            existing = Review.query.filter_by(source_id=article_data['source_id']).first()
            if existing:
                logger.info(f"⊘ Пропущено (дубликат): {article_data['text'][:50]}...")
                skipped += 1
                continue
            
            # Анализ тональности
            sentiment = sentiment_analyzer.analyze(article_data['text'])
            keywords = sentiment_analyzer.extract_keywords(article_data['text'])
            
            # Модерация
            moderation_status, moderation_reason, requires_manual = moderator.moderate(
                article_data['text'],
                sentiment['sentiment_score']
            )
            
            # Создание записи
            review = Review(
                source=article_data['source'],
                source_id=article_data['source_id'],
                author=article_data.get('author'),
                author_id=article_data.get('author_id'),
                text=article_data['text'],
                url=article_data.get('url'),
                published_date=article_data.get('published_date'),
                sentiment_score=sentiment['sentiment_score'],
                sentiment_label=sentiment['sentiment_label'],
                keywords=','.join(keywords) if keywords else None,
                moderation_status=moderation_status,
                moderation_reason=moderation_reason,
                requires_manual_review=requires_manual,
                processed=not requires_manual
            )
            
            db.session.add(review)
            logger.info(f"✓ Сохранено: {article_data['text'][:50]}...")
            saved += 1
        
        db.session.commit()
        
        # Статистика
        total = Review.query.count()
        zen_count = Review.query.filter_by(source='zen').count()
        
        print("\n" + "="*70)
        print("РЕЗУЛЬТАТЫ")
        print("="*70)
        print(f"✓ Новых статей сохранено: {saved}")
        print(f"⊘ Пропущено (дубликаты): {skipped}")
        print(f"\n📊 Статистика базы данных:")
        print(f"   Всего записей: {total}")
        print(f"   Статей из Дзен: {zen_count}")
        print("\n✓ Готово! Откройте веб-интерфейс:")
        print("   python app_enhanced.py")
        print("   http://localhost:5000")
        print("="*70)

if __name__ == '__main__':
    main()
