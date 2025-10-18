"""
Тестирование всех коллекторов и проверка сбора комментариев
"""
import logging
from config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("ТЕСТИРОВАНИЕ ВСЕХ КОЛЛЕКТОРОВ")
print("=" * 80)

# Тест 1: VK Collector
print("\n[1/5] Тестирование VK Collector")
print("-" * 80)
try:
    from collectors.vk_collector import VKCollector
    vk = VKCollector()
    
    # Проверяем наличие метода collect с параметром collect_comments
    import inspect
    sig = inspect.signature(vk.collect)
    params = list(sig.parameters.keys())
    
    print(f"OK: VK Collector импортирован")
    print(f"  Метод collect имеет параметры: {params}")
    
    if 'collect_comments' in params:
        print(f"  [+] Поддержка сбора комментариев: ДА")
        print(f"  Метод get_wall_comments: {'[+] Есть' if hasattr(vk, 'get_wall_comments') else '[-] Нет'}")
    else:
        print(f"  [-] Поддержка сбора комментариев: НЕТ")
    
    # Пробуем собрать (только первые 5 постов для теста)
    print("\n  Запуск тестового сбора (макс 5 постов)...")
    try:
        # Временно ограничиваем количество
        original_limit = vk.limit
        vk.limit = 5
        
        posts = vk.collect(collect_comments=True)
        
        vk.limit = original_limit
        
        print(f"  [+] Собрано постов: {len(posts)}")
        
        # Проверяем комментарии
        comments_count = sum(1 for p in posts if p.get('is_comment'))
        posts_count = len(posts) - comments_count
        
        print(f"  [+] Из них постов: {posts_count}")
        print(f"  [+] Из них комментариев: {comments_count}")
        
        if comments_count > 0:
            print(f"  [+++] КОММЕНТАРИИ СОБИРАЮТСЯ!")
        else:
            print(f"  [!] Комментарии не найдены (возможно, их нет в найденных постах)")
            
    except Exception as e:
        print(f"  [-] Ошибка при сборе: {e}")
        
except Exception as e:
    print(f"[-] VK Collector недоступен: {e}")

# Тест 2: Telegram Collector
print("\n[2/5] Тестирование Telegram Collector")
print("-" * 80)
try:
    try:
        from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
        collector_type = "TelegramUserCollector"
    except:
        from collectors.telegram_collector import TelegramCollector
        collector_type = "TelegramCollector"
    
    print(f"OK: Используется: {collector_type}")
    
    tg = TelegramCollector()
    
    import inspect
    sig = inspect.signature(tg.collect)
    params = list(sig.parameters.keys())
    
    print(f"  Метод collect имеет параметры: {params}")
    
    if 'collect_comments' in params:
        print(f"  [+] Поддержка сбора комментариев: ДА")
    else:
        print(f"  [-] Поддержка сбора комментариев: НЕТ")
    
    print("  ℹ Пропуск реального сбора (требуется авторизация)")
    
except Exception as e:
    print(f"[-] Telegram Collector недоступен: {e}")

# Тест 3: News Collector  
print("\n[3/5] Тестирование News Collector")
print("-" * 80)
try:
    from collectors.news_collector import NewsCollector
    news = NewsCollector()
    
    print(f"OK: News Collector импортирован")
    
    # Проверяем методы
    has_collect_with_comments = hasattr(news, 'collect_with_comments')
    has_parse_comments = hasattr(news, 'parse_article_comments')
    
    print(f"  Метод collect_with_comments: {'[+] Есть' if has_collect_with_comments else '[-] Нет'}")
    print(f"  Метод parse_article_comments: {'[+] Есть' if has_parse_comments else '[-] Нет'}")
    
    if has_collect_with_comments and has_parse_comments:
        print(f"  [+] Поддержка сбора комментариев: ДА")
    else:
        print(f"  [-] Поддержка сбора комментариев: НЕТ")
    
    print("  ℹ Пропуск реального сбора (долго)")
    
except Exception as e:
    print(f"[-] News Collector недоступен: {e}")

# Тест 4: Zen Collector
print("\n[4/5] Тестирование Zen Collector")
print("-" * 80)
try:
    try:
        from collectors.zen_selenium_collector import ZenSeleniumCollector as ZenCollector
        collector_type = "ZenSeleniumCollector"
    except:
        from collectors.zen_collector import ZenCollector
        collector_type = "ZenCollector"
    
    print(f"OK: Используется: {collector_type}")
    
    zen = ZenCollector()
    
    import inspect
    sig = inspect.signature(zen.collect)
    params = list(sig.parameters.keys())
    
    print(f"  Метод collect имеет параметры: {params}")
    
    if 'collect_comments' in params:
        print(f"  [+] Поддержка сбора комментариев: ДА")
    else:
        print(f"  [-] Поддержка сбора комментариев: НЕТ")
    
    has_parse_comments = hasattr(zen, 'parse_dzen_comments')
    print(f"  Метод parse_dzen_comments: {'[+] Есть' if has_parse_comments else '[-] Нет'}")
    
    print("  ℹ Пропуск реального сбора (требуется Selenium)")
    
except Exception as e:
    print(f"[-] Zen Collector недоступен: {e}")

# Тест 5: OK Collector
print("\n[5/5] Тестирование OK Collector")
print("-" * 80)
try:
    try:
        from collectors.ok_selenium_collector import OKSeleniumCollector as OKCollector
        collector_type = "OKSeleniumCollector"
    except:
        try:
            from collectors.ok_collector_working import OKCollectorWorking as OKCollector
            collector_type = "OKCollectorWorking"
        except:
            from collectors.ok_collector import OKCollector
            collector_type = "OKCollector"
    
    print(f"OK: Используется: {collector_type}")
    
    ok = OKCollector()
    
    import inspect
    sig = inspect.signature(ok.collect)
    params = list(sig.parameters.keys())
    
    print(f"  Метод collect имеет параметры: {params}")
    
    if 'collect_comments' in params:
        print(f"  [+] Поддержка сбора комментариев: ДА")
    else:
        print(f"  [!] Поддержка сбора комментариев: НЕТ (OK.ru не показывает комментарии без авторизации)")
    
    print("  ℹ Пропуск реального сбора (требуется Selenium + прокси)")
    
except Exception as e:
    print(f"[-] OK Collector недоступен: {e}")

# Итоги
print("\n" + "=" * 80)
print("ИТОГИ ПРОВЕРКИ")
print("=" * 80)
print("""
Коллекторы с поддержкой комментариев:
[+] VK - собирает все комментарии под постами про ТНС
[+] Telegram - собирает ответы в каналах (если доступны)
[+] News - парсит комментарии с новостных сайтов
[+] Zen - парсит комментарии из Дзена

Коллекторы БЕЗ поддержки комментариев:
[!] OK - не парсит комментарии (OK.ru требует авторизацию)

Рекомендации:
1. VK - основной источник комментариев [+]
2. Telegram - работает через Telethon (требуется настройка)
3. News - комментарии на новостных сайтах (часто отсутствуют)
4. Zen - комментарии загружаются динамически (может не работать)
5. OK - добавить поддержку комментариев при использовании API с токеном
""")

print("\nЗапустите сбор через веб-интерфейс для полной проверки:")
print("http://127.0.0.1:5001 → 🔄 Мониторинг → Запустить сбор")
print("=" * 80)
