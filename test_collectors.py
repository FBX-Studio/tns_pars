"""
Тестовый скрипт для проверки всех коллекторов
"""
import sys
import logging
from collectors.web_collector import WebCollector
try:
    from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: Telegram User API not available. Install telethon to enable.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_web_collector():
    """Тест web коллектора с прокси"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ WEB КОЛЛЕКТОРА С ПРОКСИ")
    print("="*60 + "\n")
    
    try:
        collector = WebCollector()
        
        # Проверяем режим прокси
        if collector.use_free_proxies:
            print("✓ Режим бесплатных прокси включен")
            print("  Система автоматически найдет рабочие прокси...\n")
        else:
            print("✓ Используются статические прокси из .env")
            if collector.current_proxy:
                print(f"  Прокси: {collector.current_proxy}")
            else:
                print("  Прокси не настроены (работа без прокси)")
        
        print("\nЗапуск сбора новостей...")
        articles = collector.collect()
        
        print(f"\n✓ Собрано статей: {len(articles)}")
        
        if articles:
            print("\nПримеры найденных статей:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article.get('author', 'Unknown')}")
                print(f"   URL: {article.get('url', 'N/A')}")
                print(f"   Текст: {article['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка при тестировании web коллектора: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_telegram_collector():
    """Тест Telegram коллектора"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ TELEGRAM КОЛЛЕКТОРА")
    print("="*60 + "\n")
    
    if not TELEGRAM_AVAILABLE:
        print("✗ Telegram User API недоступен")
        print("  Установите: pip install telethon")
        return False
    
    try:
        from config import Config
        
        # Проверяем наличие API ключей
        if not Config.TELEGRAM_API_ID or not Config.TELEGRAM_API_HASH:
            print("✗ Telegram API ключи не настроены")
            print("  1. Получите ключи на https://my.telegram.org")
            print("  2. Добавьте TELEGRAM_API_ID и TELEGRAM_API_HASH в .env")
            print("  3. Запустите setup_telegram.py для авторизации")
            return False
        
        print("✓ Telegram API ключи настроены")
        
        collector = TelegramCollector()
        
        # Проверяем наличие каналов
        if not collector.channels or not any(ch.strip() for ch in collector.channels):
            print("✗ Telegram каналы не настроены")
            print("  Добавьте TELEGRAM_CHANNELS в .env")
            print("  Пример: TELEGRAM_CHANNELS=@channel1,@channel2")
            return False
        
        print(f"✓ Настроены каналы: {', '.join(collector.channels)}")
        
        print("\nЗапуск сбора сообщений из Telegram...")
        print("(Это может занять некоторое время...)\n")
        
        messages = collector.collect()
        
        print(f"\n✓ Собрано сообщений: {len(messages)}")
        
        if messages:
            print("\nПримеры найденных сообщений:")
            for i, msg in enumerate(messages[:3], 1):
                print(f"\n{i}. Канал: {msg.get('author', 'Unknown')}")
                print(f"   URL: {msg.get('url', 'N/A')}")
                print(f"   Текст: {msg['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка при тестировании Telegram коллектора: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_proxy_manager():
    """Тест менеджера прокси"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МЕНЕДЖЕРА ПРОКСИ")
    print("="*60 + "\n")
    
    try:
        from utils.proxy_manager import ProxyManager
        
        manager = ProxyManager()
        
        print("Поиск бесплатных прокси...")
        print("(Это может занять 1-2 минуты...)\n")
        
        count = manager.update_proxies(max_working=5)
        
        print(f"\n✓ Найдено рабочих прокси: {count}")
        
        if count > 0:
            print("\nСписок рабочих прокси:")
            for i, proxy in enumerate(manager.proxies, 1):
                print(f"{i}. {proxy['ip']}:{proxy['port']} ({proxy['protocol']}) - {proxy['source']}")
            
            print("\nТестирование получения случайного прокси...")
            random_proxy = manager.get_random_proxy()
            if random_proxy:
                print(f"✓ Получен прокси: {random_proxy.get('http', 'Unknown')}")
        else:
            print("\n✗ Не удалось найти рабочие прокси")
            print("  Возможные причины:")
            print("  - Проблемы с интернет-соединением")
            print("  - Источники прокси недоступны")
            print("  - Все прокси заблокированы в вашем регионе")
        
        return count > 0
        
    except Exception as e:
        print(f"\n✗ Ошибка при тестировании менеджера прокси: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ ПАРСИНГА")
    print("="*60)
    
    results = {}
    
    # Тест менеджера прокси
    results['proxy_manager'] = test_proxy_manager()
    
    # Тест web коллектора
    results['web_collector'] = test_web_collector()
    
    # Тест Telegram коллектора
    results['telegram_collector'] = test_telegram_collector()
    
    # Итоговый отчет
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*60 + "\n")
    
    for component, status in results.items():
        status_icon = "✓" if status else "✗"
        status_text = "OK" if status else "FAILED"
        print(f"{status_icon} {component}: {status_text}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nПройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("\n✓ Все компоненты работают корректно!")
        return 0
    else:
        print("\n✗ Некоторые компоненты требуют настройки")
        return 1

if __name__ == '__main__':
    sys.exit(main())
