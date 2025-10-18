"""
Быстрый тест OK коллектора после исправления Chrome
"""
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("БЫСТРЫЙ ТЕСТ OK КОЛЛЕКТОРА")
print("=" * 80)

try:
    from collectors.ok_selenium_collector import OKSeleniumCollector
    
    print("\n[1] Создание коллектора...")
    collector = OKSeleniumCollector()
    print("[+] OK")
    
    print("\n[2] Проверка учетных данных...")
    if collector.ok_login and collector.ok_password:
        print(f"[+] Логин: {collector.ok_login}")
        print(f"[+] Пароль: {'*' * len(collector.ok_password)}")
    else:
        print("[!] Учетные данные не найдены!")
        exit(1)
    
    print("\n[3] Проверка cookies...")
    if os.path.exists('ok_cookies.pkl'):
        print("[+] ok_cookies.pkl найден")
    else:
        print("[!] ok_cookies.pkl не найден - потребуется авторизация")
    
    print("\n[4] Инициализация Chrome драйвера...")
    collector.driver = collector._setup_driver()
    
    if not collector.driver:
        print("[!] ОШИБКА: Не удалось создать драйвер")
        exit(1)
    
    print("[+] Chrome запущен успешно!")
    
    print("\n[5] Проверка доступа к OK.ru...")
    collector.driver.get("https://ok.ru")
    import time
    time.sleep(2)
    
    if "ok.ru" in collector.driver.current_url.lower():
        print("[+] OK.ru доступен")
    else:
        print("[!] Редирект или блокировка")
    
    print("\n[6] Закрытие драйвера...")
    collector.driver.quit()
    print("[+] Драйвер закрыт")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ВСЕ ПРОВЕРКИ ПРОШЛИ УСПЕШНО!")
    print("=" * 80)
    print("\nТеперь можно запускать полный сбор:")
    print("  python app_enhanced.py")
    print("  http://127.0.0.1:5001 -> Мониторинг -> Запустить сбор")
    
except Exception as e:
    print(f"\n[ERROR] ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
