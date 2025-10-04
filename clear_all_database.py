"""
Полная очистка базы данных - удаление ВСЕХ отзывов и логов
"""
from models import db, Review, MonitoringLog
from app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_all_data():
    """Удалить ВСЕ данные из базы"""
    with app.app_context():
        # Подсчет до удаления
        total_reviews = Review.query.count()
        total_logs = MonitoringLog.query.count()
        
        logger.info("=" * 60)
        logger.info("ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")
        logger.info("=" * 60)
        logger.info(f"Найдено отзывов: {total_reviews}")
        logger.info(f"Найдено логов: {total_logs}")
        
        # Удаление всех отзывов
        logger.info("\nУдаление всех отзывов...")
        Review.query.delete()
        
        # Удаление всех логов
        logger.info("Удаление всех логов мониторинга...")
        MonitoringLog.query.delete()
        
        # Сохранение изменений
        db.session.commit()
        
        # Проверка
        remaining_reviews = Review.query.count()
        remaining_logs = MonitoringLog.query.count()
        
        logger.info("\n" + "=" * 60)
        logger.info("РЕЗУЛЬТАТ")
        logger.info("=" * 60)
        logger.info(f"✓ Удалено отзывов: {total_reviews}")
        logger.info(f"✓ Удалено логов: {total_logs}")
        logger.info(f"✓ Осталось отзывов: {remaining_reviews}")
        logger.info(f"✓ Осталось логов: {remaining_logs}")
        logger.info("\n✓ База данных полностью очищена!")
        logger.info("=" * 60)

if __name__ == '__main__':
    clear_all_data()
