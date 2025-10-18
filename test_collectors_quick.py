"""
Быстрая диагностика всех коллекторов
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("ДИАГНОСТИКА КОЛЛЕКТОРОВ")
print("=" * 80)

# 1. VK
print("\n[1/3] VK Collector")
print("-" * 80)
try:
    from collectors.vk_collector import VKCollector
    vk = VKCollector()
    print("OK: VK Collector загружен")
    
    # Проверка токена
    import os
    from dotenv import load_dotenv
    load_dotenv()
    token = os.getenv('VK_ACCESS_TOKEN', '')
    if token:
        print(f"OK: VK токен найден (длина: {len(token)})")
        
        # Пробуем собрать
        print("Запуск сбора (максимум 3 поста)...")
        try:
            posts = vk.collect(collect_comments=False)
            print(f"Результат: {len(posts)} постов найдено")
            if posts:
                print(f"Пример: {posts[0].get('text', '')[:100]}...")
            else:
                print("!!! ПОСТОВ НЕ НАЙДЕНО")
        except Exception as e:
            print(f"ОШИБКА при сборе: {e}")
    else:
        print("!!! VK токен НЕ НАЙДЕН в .env")
        
except Exception as e:
    print(f"ОШИБКА: {e}")

# 2. OK.ru
print("\n[2/3] OK Collector")
print("-" * 80)
try:
    from collectors.ok_selenium_collector import OKSeleniumCollector
    ok = OKSeleniumCollector()
    print("OK: OK Selenium Collector загружен")
    
    # Проверка авторизации
    if ok.ok_login and ok.ok_password:
        print(f"OK: Логин найден ({ok.ok_login})")
        
        # Проверка cookies
        import os
        if os.path.exists('ok_cookies.pkl'):
            print("OK: Cookies файл найден")
        else:
            print("!!! Cookies НЕ НАЙДЕНЫ - нужна авторизация")
        
        print("Запуск сбора (без комментариев)...")
        print("!!! ВНИМАНИЕ: Selenium требует Chrome и время для инициализации")
        print("!!! Пропускаем тест OK - запустите полный сбор через веб-интерфейс")
    else:
        print("!!! OK логин/пароль НЕ НАЙДЕНЫ в .env")
        
except Exception as e:
    print(f"ОШИБКА: {e}")

# 3. Дзен
print("\n[3/3] Zen Collector")
print("-" * 80)
try:
    from collectors.zen_selenium_collector import ZenSeleniumCollector
    zen = ZenSeleniumCollector()
    print("OK: Zen Selenium Collector загружен")
    print(f"Ключевые слова: {zen.keywords}")
    
    print("!!! ВНИМАНИЕ: Selenium требует Chrome и время для инициализации")
    print("!!! Пропускаем тест Zen - запустите полный сбор через веб-интерфейс")
        
except Exception as e:
    print(f"ОШИБКА: {e}")

print("\n" + "=" * 80)
print("РЕКОМЕНДАЦИИ:")
print("=" * 80)
print("""
1. Проверьте VK токен в .env:
   - Откройте .env
   - Найдите VK_ACCESS_TOKEN
   - Проверьте что токен актуален
   
2. Для OK и Дзен:
   - Запустите полный сбор через веб-интерфейс
   - Смотрите логи в реальном времени
   - Они используют Selenium - требуется больше времени

3. Проверьте логи сервера:
   - В консоли где запущен python app_enhanced.py
   - Ищите ошибки с [VK], [OK-Selenium], [ZEN-SELENIUM]

4. Запустите сбор через веб:
   http://127.0.0.1:5002 → Мониторинг → Запустить сбор
""")
