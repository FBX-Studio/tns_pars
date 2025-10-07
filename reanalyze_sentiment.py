"""
Скрипт для переанализа тональности существующих отзывов
"""
import logging
from app_enhanced import app
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def reanalyze_all():
    """Переанализ всех отзывов в базе"""
    
    logger.info("=" * 60)
    logger.info("Переанализ тональности отзывов")
    logger.info("=" * 60)
    
    with app.app_context():
        # Получаем все отзывы
        reviews = Review.query.all()
        total = len(reviews)
        
        if total == 0:
            logger.info("Нет отзывов для анализа")
            return
        
        logger.info(f"Найдено отзывов: {total}")
        logger.info("Инициализация анализатора...")
        
        # Инициализируем анализатор
        analyzer = SentimentAnalyzer()
        
        # Счетчики
        updated = 0
        positive = 0
        negative = 0
        neutral = 0
        errors = 0
        
        logger.info("\nОбработка отзывов...")
        
        for i, review in enumerate(reviews, 1):
            try:
                # Анализируем
                result = analyzer.analyze(review.text)
                
                # Обновляем
                old_label = review.sentiment_label
                review.sentiment_score = result['sentiment_score']
                review.sentiment_label = result['sentiment_label']
                
                # Счетчики
                if result['sentiment_label'] == 'positive':
                    positive += 1
                elif result['sentiment_label'] == 'negative':
                    negative += 1
                else:
                    neutral += 1
                
                updated += 1
                
                # Логируем изменения
                if old_label != result['sentiment_label']:
                    logger.info(f"[{i}/{total}] {old_label} → {result['sentiment_label']}: {review.text[:50]}...")
                
                # Коммитим каждые 10 отзывов
                if i % 10 == 0:
                    db.session.commit()
                    logger.info(f"Обработано: {i}/{total} ({i*100//total}%)")
                    
            except Exception as e:
                logger.error(f"Ошибка обработки отзыва {review.id}: {e}")
                errors += 1
                continue
        
        # Финальный коммит
        db.session.commit()
        
        logger.info("\n" + "=" * 60)
        logger.info("Результаты:")
        logger.info(f"  Всего обработано: {updated}")
        logger.info(f"  Позитивных: {positive} ({positive*100//total if total > 0 else 0}%)")
        logger.info(f"  Негативных: {negative} ({negative*100//total if total > 0 else 0}%)")
        logger.info(f"  Нейтральных: {neutral} ({neutral*100//total if total > 0 else 0}%)")
        if errors > 0:
            logger.info(f"  Ошибок: {errors}")
        logger.info("=" * 60)
        logger.info("✓ Переанализ завершен!")

def show_examples():
    """Показать примеры анализа"""
    
    logger.info("\n" + "=" * 60)
    logger.info("Примеры анализа:")
    logger.info("=" * 60)
    
    with app.app_context():
        analyzer = SentimentAnalyzer()
        
        # Примеры
        examples = [
            "Отличный сервис! Быстро подключили, все работает.",
            "Ужасное обслуживание, долго ждал, никто не помог.",
            "ТНС энерго работает в Нижнем Новгороде.",
            "Очень доволен качеством работы, рекомендую!",
            "Полное разочарование, не рекомендую никому.",
        ]
        
        for text in examples:
            result = analyzer.analyze(text)
            emoji = "🟢" if result['sentiment_label'] == 'positive' else "🔴" if result['sentiment_label'] == 'negative' else "⚪"
            logger.info(f"\n{emoji} {result['sentiment_label'].upper()} (score: {result['sentiment_score']:.2f})")
            logger.info(f"   Текст: {text}")
            if 'debug' in result:
                debug = result['debug']
                logger.info(f"   Debug: pos={debug['positive_score']}, neg={debug['negative_score']}")

if __name__ == '__main__':
    try:
        import sys
        
        # Показываем примеры
        show_examples()
        
        # Если запущен с аргументом --auto, переанализируем без подтверждения
        if '--auto' in sys.argv:
            reanalyze_all()
        else:
            # Запрашиваем подтверждение
            print("\n" + "=" * 60)
            print("Запустите с --auto для автоматического переанализа")
            print("Пример: python reanalyze_sentiment.py --auto")
            print("=" * 60)
            
    except KeyboardInterrupt:
        logger.info("\n\nПрервано пользователем")
    except Exception as e:
        logger.error(f"\nОшибка: {e}", exc_info=True)
