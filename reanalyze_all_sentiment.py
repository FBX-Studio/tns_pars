"""
Пересчет тональности для всех записей в базе
"""
from app_enhanced import app
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer
import logging
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reanalyze_all():
    """Пересчитать тональность для всех записей"""
    
    logger.info("="*70)
    logger.info("ПЕРЕСЧЕТ ТОНАЛЬНОСТИ ДЛЯ ВСЕХ ЗАПИСЕЙ В БАЗЕ")
    logger.info("="*70)
    
    with app.app_context():
        # Инициализация анализатора
        logger.info("\nИнициализация анализатора тональности...")
        analyzer = SentimentAnalyzer()
        info = analyzer.get_analyzer_info()
        logger.info(f"✓ Анализатор: {info['name']} ({info['type']})")
        
        # Получаем все записи
        total = Review.query.count()
        logger.info(f"\nВсего записей в базе: {total}")
        
        if total == 0:
            logger.warning("База данных пуста!")
            return
        
        # Статистика ДО
        positive_before = Review.query.filter_by(sentiment_label='positive').count()
        negative_before = Review.query.filter_by(sentiment_label='negative').count()
        neutral_before = Review.query.filter_by(sentiment_label='neutral').count()
        
        logger.info(f"\nТОНАЛЬНОСТЬ ДО:")
        logger.info(f"  Позитивных: {positive_before} ({positive_before/total*100:.1f}%)")
        logger.info(f"  Негативных: {negative_before} ({negative_before/total*100:.1f}%)")
        logger.info(f"  Нейтральных: {neutral_before} ({neutral_before/total*100:.1f}%)")
        
        # Пересчитываем
        logger.info(f"\n{'='*70}")
        logger.info("НАЧИНАЕМ ПЕРЕСЧЕТ...")
        logger.info(f"{'='*70}\n")
        
        reviews = Review.query.all()
        updated = 0
        errors = 0
        
        for review in tqdm(reviews, desc="Анализ тональности"):
            try:
                # Анализируем
                sentiment = analyzer.analyze(review.text)
                
                # Обновляем
                review.sentiment_score = sentiment['sentiment_score']
                review.sentiment_label = sentiment['sentiment_label']
                
                updated += 1
                
                # Коммитим пакетами по 50 записей
                if updated % 50 == 0:
                    db.session.commit()
                    logger.debug(f"Обработано: {updated}/{total}")
                
            except Exception as e:
                logger.error(f"Ошибка анализа записи {review.id}: {e}")
                errors += 1
                continue
        
        # Финальный коммит
        db.session.commit()
        
        # Статистика ПОСЛЕ
        logger.info(f"\n{'='*70}")
        logger.info("РЕЗУЛЬТАТЫ")
        logger.info(f"{'='*70}")
        
        positive_after = Review.query.filter_by(sentiment_label='positive').count()
        negative_after = Review.query.filter_by(sentiment_label='negative').count()
        neutral_after = Review.query.filter_by(sentiment_label='neutral').count()
        
        logger.info(f"\n✓ Обновлено записей: {updated}")
        if errors > 0:
            logger.warning(f"✗ Ошибок: {errors}")
        
        logger.info(f"\nТОНАЛЬНОСТЬ ПОСЛЕ:")
        logger.info(f"  Позитивных: {positive_after} ({positive_after/total*100:.1f}%)")
        logger.info(f"  Негативных: {negative_after} ({negative_after/total*100:.1f}%)")
        logger.info(f"  Нейтральных: {neutral_after} ({neutral_after/total*100:.1f}%)")
        
        logger.info(f"\nИЗМЕНЕНИЯ:")
        logger.info(f"  Позитивных: {positive_after - positive_before:+d}")
        logger.info(f"  Негативных: {negative_after - negative_before:+d}")
        logger.info(f"  Нейтральных: {neutral_after - neutral_before:+d}")
        
        # Примеры
        logger.info(f"\n{'='*70}")
        logger.info("ПРИМЕРЫ ПРОАНАЛИЗИРОВАННЫХ ЗАПИСЕЙ:")
        logger.info(f"{'='*70}\n")
        
        for label in ['positive', 'negative', 'neutral']:
            example = Review.query.filter_by(sentiment_label=label).first()
            if example:
                logger.info(f"[{label.upper()}] Score: {example.sentiment_score:.3f}")
                logger.info(f"Источник: {example.source}")
                logger.info(f"Текст: {example.text[:150]}...")
                logger.info("")
        
        logger.info("="*70)
        logger.info("✓ ПЕРЕСЧЕТ ЗАВЕРШЕН!")
        logger.info("="*70)

if __name__ == '__main__':
    try:
        reanalyze_all()
    except KeyboardInterrupt:
        logger.warning("\n⚠ Пересчет прерван пользователем")
    except Exception as e:
        logger.error(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
