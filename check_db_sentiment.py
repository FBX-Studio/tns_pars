"""
Проверка тональности записей в базе
"""
from app_enhanced import app
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    # Проверяем статистику
    total = Review.query.count()
    positive = Review.query.filter_by(sentiment_label='positive').count()
    negative = Review.query.filter_by(sentiment_label='negative').count()
    neutral = Review.query.filter_by(sentiment_label='neutral').count()
    
    logger.info(f"Всего записей: {total}")
    logger.info(f"Позитивных: {positive}")
    logger.info(f"Негативных: {negative}")
    logger.info(f"Нейтральных: {neutral}")
    
    # Показываем примеры текстов
    logger.info("\n" + "="*60)
    logger.info("ПРИМЕРЫ ТЕКСТОВ И ИХ ТОНАЛЬНОСТЬ:")
    logger.info("="*60)
    
    reviews = Review.query.limit(10).all()
    for review in reviews:
        logger.info(f"\nИсточник: {review.source}")
        logger.info(f"Текст: {review.text[:200]}...")
        logger.info(f"Тональность: {review.sentiment_label} (score: {review.sentiment_score})")
    
    # Тестируем анализатор
    logger.info("\n" + "="*60)
    logger.info("ТЕСТ АНАЛИЗАТОРА:")
    logger.info("="*60)
    
    analyzer = SentimentAnalyzer()
    info = analyzer.get_analyzer_info()
    logger.info(f"Тип анализатора: {info['type']}")
    logger.info(f"Название: {info['name']}")
    
    # Тестовые тексты
    test_texts = [
        "Отличная компания! Быстро помогли, все решили оперативно. Спасибо большое!",
        "Ужасный сервис! Хамство и безобразие! Никому не рекомендую!",
        "ТНС энерго Нижний Новгород объявила о новых тарифах"
    ]
    
    for text in test_texts:
        result = analyzer.analyze(text)
        logger.info(f"\nТекст: {text}")
        logger.info(f"Результат: {result['sentiment_label']} (score: {result['sentiment_score']:.3f})")
