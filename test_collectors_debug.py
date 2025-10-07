"""
Тестовый скрипт для проверки коллекторов
"""
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_news_collector():
    """Тест коллектора новостей"""
    print("\n" + "="*60)
    print("ТЕСТ КОЛЛЕКТОРА НОВОСТЕЙ (RSS)")
    print("="*60)
    
    try:
        from collectors.news_collector_light import NewsCollectorLight
        
        collector = NewsCollectorLight()
        print(f"\n📌 Ключевые слова: {collector.keywords}")
        print(f"📌 RSS URL: {collector.rss_url}")
        
        print("\n▶ Запуск сбора новостей...")
        articles = collector.collect()
        
        print(f"\n✅ РЕЗУЛЬТАТ: Найдено статей: {len(articles)}")
        
        if articles:
            print("\n📰 Первые 3 найденные статьи:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article.get('text', '')[:150]}...")
                print(f"   URL: {article.get('url', 'N/A')}")
        else:
            print("\n⚠ Статьи не найдены!")
            print("Возможные причины:")
            print("  1. RSS не содержит статей с ключевыми словами")
            print("  2. Проблема с доступом к RSS")
            print("  3. Изменился формат RSS")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    return articles if 'articles' in locals() else []

def test_telegram_collector():
    """Тест Telegram коллектора"""
    print("\n" + "="*60)
    print("ТЕСТ TELEGRAM КОЛЛЕКТОРА")
    print("="*60)
    
    try:
        from collectors.telegram_user_collector import TelegramUserCollector
        from config import Config
        
        collector = TelegramUserCollector()
        
        print(f"\n📌 API ID: {'✓ Настроен' if collector.api_id else '✗ НЕ НАСТРОЕН'}")
        print(f"📌 API Hash: {'✓ Настроен' if collector.api_hash else '✗ НЕ НАСТРОЕН'}")
        print(f"📌 Телефон: {collector.phone if collector.phone else '✗ НЕ НАСТРОЕН'}")
        print(f"📌 Количество каналов: {len(collector.channels)}")
        
        if not collector.api_id or not collector.api_hash:
            print("\n⚠ Telegram API не настроен!")
            print("Для настройки:")
            print("  1. Зайдите на https://my.telegram.org")
            print("  2. Получите API_ID и API_HASH")
            print("  3. Обновите .env файл")
            return []
        
        if collector.channels:
            print(f"\n📋 Первые 5 каналов:")
            for channel in collector.channels[:5]:
                print(f"   - {channel}")
        
        print("\n▶ Запуск сбора из Telegram (это может занять время)...")
        print("⏳ Подключение к Telegram...")
        
        messages = collector.collect()
        
        print(f"\n✅ РЕЗУЛЬТАТ: Найдено сообщений: {len(messages)}")
        
        if messages:
            print("\n💬 Первые 3 найденных сообщения:")
            for i, msg in enumerate(messages[:3], 1):
                print(f"\n{i}. Канал: {msg.get('author', 'N/A')}")
                print(f"   Текст: {msg.get('text', '')[:150]}...")
                print(f"   URL: {msg.get('url', 'N/A')}")
        else:
            print("\n⚠ Сообщения не найдены!")
            print("Возможные причины:")
            print("  1. В каналах нет упоминаний ТНС энерго НН")
            print("  2. Фильтры слишком строгие")
            print("  3. Проблема с авторизацией в Telegram")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    return messages if 'messages' in locals() else []

def test_vk_collector():
    """Тест VK коллектора"""
    print("\n" + "="*60)
    print("ТЕСТ VK КОЛЛЕКТОРА")
    print("="*60)
    
    try:
        from collectors.vk_collector import VKCollector
        
        collector = VKCollector()
        
        print(f"\n📌 VK Token: {'✓ Настроен' if collector.access_token else '✗ НЕ НАСТРОЕН'}")
        print(f"📌 Поисковый запрос: {collector.search_query}")
        
        if not collector.access_token:
            print("\n⚠ VK токен не настроен!")
            return []
        
        print("\n▶ Запуск сбора из VK...")
        posts = collector.collect()
        
        print(f"\n✅ РЕЗУЛЬТАТ: Найдено постов: {len(posts)}")
        
        if posts:
            print("\n📝 Первые 3 найденных поста:")
            for i, post in enumerate(posts[:3], 1):
                print(f"\n{i}. {post.get('text', '')[:150]}...")
        else:
            print("\n⚠ Посты не найдены!")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    return posts if 'posts' in locals() else []

if __name__ == '__main__':
    # Настройка вывода UTF-8
    import sys
    import codecs
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("\n" + "="*60)
    print("DIAGNOSTIKA KOLLEKTOROV")
    print("="*60)
    
    # Проверка конфигурации
    from config import Config
    print(f"\nKonfiguracija:")
    print(f"  Kljuchevye slova: {Config.COMPANY_KEYWORDS}")
    print(f"  Geo-filtr: {'Vkluchen' if Config.GEO_FILTER_ENABLED else 'Vykluchen'}")
    print(f"  Jazykovoj filtr: {'Vkluchen' if Config.LANGUAGE_FILTER_ENABLED else 'Vykluchen'}")
    
    # Тест коллекторов
    news = test_news_collector()
    telegram = test_telegram_collector()
    vk = test_vk_collector()
    
    # Итоги
    print("\n" + "="*60)
    print("ITOGI DIAGNOSTIKI")
    print("="*60)
    print(f"Novosti (RSS): {len(news)} statej")
    print(f"Telegram: {len(telegram)} soobshhenij")
    print(f"VK: {len(vk)} postov")
    print(f"VSEGO: {len(news) + len(telegram) + len(vk)} zapisej")
    print("="*60)
