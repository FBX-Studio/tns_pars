"""
Тестовый скрипт для проверки работы мониторинга
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from monitor import ReviewMonitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_collectors():
    """Проверка работы коллекторов"""
    print("=" * 60)
    print("TEST MONITORING SYSTEM")
    print("=" * 60)
    
    monitor = ReviewMonitor()
    
    print("\n1. Checking VK collector...")
    try:
        if monitor.vk_collector.vk:
            print("   [OK] VK API initialized")
        else:
            print("   [WARN] VK API not initialized (check VK_ACCESS_TOKEN)")
    except Exception as e:
        print(f"   [ERROR] VK: {e}")
    
    print("\n2. Checking Telegram collector...")
    try:
        if monitor.telegram_collector.bot_token:
            print("   [OK] Telegram token configured")
        else:
            print("   [WARN] Telegram token not configured (check TELEGRAM_BOT_TOKEN)")
    except Exception as e:
        print(f"   [ERROR] Telegram: {e}")
    
    print("\n3. Checking Web collector...")
    try:
        print(f"   [OK] Web collector ready")
        print(f"   Sites to monitor: {len(monitor.web_collector.news_sites)}")
    except Exception as e:
        print(f"   [ERROR] Web: {e}")
    
    print("\n4. Checking sentiment analyzer...")
    try:
        test_text = "Excellent work!"
        result = monitor.sentiment_analyzer.analyze(test_text)
        print(f"   [OK] Analyzer works: {result['sentiment_label']}")
    except Exception as e:
        print(f"   [ERROR] Analyzer: {e}")
    
    print("\n5. Running test collection...")
    try:
        with app.app_context():
            print("   Starting data collection...")
            monitor.run_collection()
            print("   [OK] Collection completed successfully")
    except Exception as e:
        print(f"   [ERROR] Collection: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == '__main__':
    test_collectors()
