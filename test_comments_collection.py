"""
Тестовый скрипт для проверки парсинга комментариев
"""
import logging
from collectors.news_collector import NewsCollector
from collectors.telegram_user_collector import TelegramUserCollector
from collectors.zen_collector import ZenCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_news_comments():
    """Test news comments collection"""
    logger.info("=" * 60)
    logger.info("Testing News Comments Collection")
    logger.info("=" * 60)
    
    try:
        collector = NewsCollector()
        results = collector.collect_with_comments()
        
        articles = [r for r in results if not r.get('is_comment', False)]
        comments = [r for r in results if r.get('is_comment', False)]
        
        logger.info(f"✓ Total articles collected: {len(articles)}")
        logger.info(f"✓ Total comments collected: {len(comments)}")
        
        if comments:
            logger.info("\nSample comment:")
            sample = comments[0]
            logger.info(f"  Author: {sample.get('author', 'N/A')}")
            logger.info(f"  Text: {sample.get('text', '')[:100]}...")
            logger.info(f"  Parent: {sample.get('parent_url', 'N/A')}")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"✗ News comments test failed: {e}")
        return False

def test_telegram_comments():
    """Test Telegram comments collection"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Telegram Comments Collection")
    logger.info("=" * 60)
    
    try:
        collector = TelegramUserCollector()
        results = collector.collect(collect_comments=True)
        
        messages = [r for r in results if not r.get('is_comment', False)]
        comments = [r for r in results if r.get('is_comment', False)]
        
        logger.info(f"✓ Total messages collected: {len(messages)}")
        logger.info(f"✓ Total replies collected: {len(comments)}")
        
        if comments:
            logger.info("\nSample reply:")
            sample = comments[0]
            logger.info(f"  Author: {sample.get('author', 'N/A')}")
            logger.info(f"  Text: {sample.get('text', '')[:100]}...")
            logger.info(f"  Parent: {sample.get('parent_url', 'N/A')}")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"✗ Telegram comments test failed: {e}")
        return False

def test_zen_comments():
    """Test Yandex Zen comments collection"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Yandex Zen Comments Collection")
    logger.info("=" * 60)
    
    try:
        collector = ZenCollector()
        results = collector.collect(collect_comments=True)
        
        articles = [r for r in results if not r.get('is_comment', False)]
        comments = [r for r in results if r.get('is_comment', False)]
        
        logger.info(f"✓ Total articles collected: {len(articles)}")
        logger.info(f"✓ Total comments collected: {len(comments)}")
        
        if comments:
            logger.info("\nSample comment:")
            sample = comments[0]
            logger.info(f"  Author: {sample.get('author', 'N/A')}")
            logger.info(f"  Text: {sample.get('text', '')[:100]}...")
            logger.info(f"  Parent: {sample.get('parent_url', 'N/A')}")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"✗ Zen comments test failed: {e}")
        return False

def main():
    """Run all comment collection tests"""
    logger.info("Starting comment collection tests...")
    
    results = {
        'news': test_news_comments(),
        'telegram': test_telegram_comments(),
        'zen': test_zen_comments()
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    for source, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{source.upper()}: {status}")
    
    total_passed = sum(results.values())
    logger.info(f"\nTotal: {total_passed}/{len(results)} tests passed")

if __name__ == '__main__':
    main()
