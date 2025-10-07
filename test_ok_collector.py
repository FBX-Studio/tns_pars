"""
Тестирование коллектора Одноклассников
"""
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

from collectors.ok_api_collector import OKAPICollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("ТЕСТ КОЛЛЕКТОРА ОДНОКЛАССНИКОВ (OK API)")
    logger.info("=" * 70)
    logger.info("")
    
    # Инициализация
    logger.info("Инициализация коллектора...")
    collector = OKAPICollector()
    
    # Проверка настроек
    logger.info("")
    logger.info("Проверка настроек:")
    logger.info(f"  APP_ID: {collector.app_id}")
    logger.info(f"  PUBLIC_KEY: {collector.public_key[:20]}..." if collector.public_key else "  PUBLIC_KEY: НЕ УСТАНОВЛЕН")
    logger.info(f"  SECRET_KEY: {collector.secret_key[:20]}..." if collector.secret_key else "  SECRET_KEY: НЕ УСТАНОВЛЕН")
    logger.info(f"  ACCESS_TOKEN: {collector.access_token[:30]}..." if collector.access_token else "  ACCESS_TOKEN: НЕ УСТАНОВЛЕН")
    logger.info(f"  Группы для мониторинга: {len(collector.group_ids)}")
    logger.info(f"  Ключевые слова: {', '.join(collector.keywords)}")
    logger.info("")
    
    # Проверка наличия всех ключей
    if not collector.app_id:
        logger.error("❌ OK_APP_ID не настроен в .env")
        return
    
    if not collector.public_key:
        logger.error("❌ OK_APP_KEY не настроен в .env")
        return
    
    if not collector.secret_key:
        logger.error("❌ OK_SESSION_SECRET_KEY не настроен в .env")
        return
    
    if not collector.access_token:
        logger.error("❌ OK_ACCESS_TOKEN не настроен в .env")
        return
    
    logger.info("✅ Все API ключи настроены")
    logger.info("")
    
    # Сбор данных
    logger.info("=" * 70)
    logger.info("ЗАПУСК СБОРА")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        posts = collector.collect()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("РЕЗУЛЬТАТЫ")
        logger.info("=" * 70)
        logger.info(f"✅ Найдено постов: {len(posts)}")
        logger.info("")
        
        if len(posts) > 0:
            logger.info("Примеры найденных постов:")
            logger.info("")
            for i, post in enumerate(posts[:5], 1):
                logger.info(f"{i}. {post['text'][:100]}...")
                logger.info(f"   Автор: {post.get('author', 'N/A')}")
                logger.info(f"   URL: {post.get('url', 'N/A')}")
                logger.info(f"   Дата: {post.get('published_date', 'N/A')}")
                logger.info("")
        else:
            logger.info("⚠️ Посты не найдены")
            logger.info("")
            logger.info("Возможные причины:")
            logger.info("1. В вашей ленте нет постов с ключевыми словами")
            logger.info("2. Группы для мониторинга не указаны (OK_GROUP_IDS)")
            logger.info("3. API ключи неверны или истекли")
            logger.info("")
            logger.info("Рекомендации:")
            logger.info("1. Подпишитесь на новостные группы НН в OK.ru")
            logger.info("2. Добавьте ID групп в .env: OK_GROUP_IDS=123456,789012")
            logger.info("3. Проверьте access_token (может истечь)")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
