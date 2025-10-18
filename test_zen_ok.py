"""
Детальная диагностика Дзен и OK коллекторов
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("ДИАГНОСТИКА ДЗЕН И OK КОЛЛЕКТОРОВ")
print("=" * 80)

# Проверка Selenium
print("\n[ПРОВЕРКА] Selenium и ChromeDriver")
print("-" * 80)
try:
    from selenium import webdriver
    print("OK: Selenium установлен")
    
    from webdriver_manager.chrome import ChromeDriverManager
    print("OK: webdriver-manager установлен")
    
    # Проверка Chrome
    try:
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        print("OK: Chrome WebDriver работает")
        driver.quit()
    except Exception as e:
        print(f"ОШИБКА Chrome: {e}")
        
except Exception as e:
    print(f"ОШИБКА Selenium: {e}")

# Тест Дзен
print("\n[ТЕСТ 1] Дзен коллектор")
print("-" * 80)
try:
    from collectors.zen_selenium_collector import ZenSeleniumCollector
    
    zen = ZenSeleniumCollector()
    print(f"OK: Коллектор загружен")
    print(f"Ключевые слова: {zen.keywords}")
    
    print("\nЗапуск сбора Дзен (это займет ~2 минуты)...")
    print("Собираем статьи БЕЗ комментариев для быстрого теста...")
    
    articles = zen.collect(collect_comments=False)
    
    print(f"\nРезультат: {len(articles)} статей найдено")
    
    if articles:
        print("\nПримеры найденных статей:")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.get('text', '')[:100]}...")
    else:
        print("\n!!! СТАТЬИ НЕ НАЙДЕНЫ")
        print("Возможные причины:")
        print("  1. Яндекс показывает капчу")
        print("  2. Нет статей по ключевым словам")
        print("  3. Изменилась структура HTML Дзена")
        
except Exception as e:
    print(f"\nОШИБКА Дзен: {e}")
    import traceback
    traceback.print_exc()

# Тест OK
print("\n[ТЕСТ 2] OK.ru коллектор")
print("-" * 80)
try:
    from collectors.ok_selenium_collector import OKSeleniumCollector
    import os
    
    ok = OKSeleniumCollector()
    print(f"OK: Коллектор загружен")
    
    # Проверка авторизации
    if ok.ok_login and ok.ok_password:
        print(f"OK: Логин найден ({ok.ok_login})")
        
        if os.path.exists('ok_cookies.pkl'):
            print("OK: Cookies найдены")
        else:
            print("!!! Cookies НЕ НАЙДЕНЫ - нужна авторизация")
        
        print("\nЗапуск сбора OK (это займет ~2 минуты)...")
        print("Собираем посты БЕЗ комментариев для быстрого теста...")
        
        posts = ok.collect(collect_comments=False)
        
        print(f"\nРезультат: {len(posts)} постов найдено")
        
        if posts:
            print("\nПримеры найденных постов:")
            for i, post in enumerate(posts[:3], 1):
                print(f"{i}. {post.get('text', '')[:100]}...")
        else:
            print("\n!!! ПОСТЫ НЕ НАЙДЕНЫ")
            print("Возможные причины:")
            print("  1. OK.ru показывает капчу")
            print("  2. Авторизация не работает")
            print("  3. Нет постов по ключевым словам")
            print("  4. Прокси нужен")
            
    else:
        print("!!! OK логин/пароль НЕ НАЙДЕНЫ")
        
except Exception as e:
    print(f"\nОШИБКА OK: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 80)
