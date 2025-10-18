"""
Тестовый скрипт для проверки авторизации на OK.ru
"""
import os
from dotenv import load_dotenv
import logging

# Загружаем .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 80)
print("ТЕСТ АВТОРИЗАЦИИ OK.RU")
print("=" * 80)

# Проверяем наличие логина и пароля
ok_login = os.getenv('OK_LOGIN', '')
ok_password = os.getenv('OK_PASSWORD', '')

print(f"\nЛогин: {ok_login}")
print(f"Пароль: {'*' * len(ok_password) if ok_password else '(не указан)'}")

if not ok_login or not ok_password:
    print("\n[!] ОШИБКА: Логин или пароль не указаны в .env")
    print("    Добавьте OK_LOGIN и OK_PASSWORD в файл .env")
    exit(1)

print("\n[+] Учетные данные найдены")
print("\nИнициализация Selenium...")

try:
    from collectors.ok_selenium_collector import OKSeleniumCollector
    
    collector = OKSeleniumCollector()
    print("[+] Коллектор создан")
    
    # Инициализация драйвера
    print("\n[*] Запуск Chrome WebDriver...")
    collector.driver = collector._setup_driver()
    
    if not collector.driver:
        print("[!] ОШИБКА: Не удалось создать драйвер")
        exit(1)
    
    print("[+] WebDriver запущен")
    
    # Попытка авторизации
    print("\n[*] Попытка авторизации на OK.ru...")
    print(f"    Логин: {ok_login}")
    
    success = collector.login()
    
    if success:
        print("\n" + "=" * 80)
        print("✓✓✓ АВТОРИЗАЦИЯ УСПЕШНА! ✓✓✓")
        print("=" * 80)
        print("\n[+] Cookies сохранены в ok_cookies.pkl")
        print("[+] При следующем запуске авторизация будет автоматической")
        print("\n[*] Теперь можно запустить полный сбор:")
        print("    python app_enhanced.py")
        print("    http://127.0.0.1:5001 → Мониторинг → Запустить сбор")
    else:
        print("\n" + "=" * 80)
        print("✗✗✗ АВТОРИЗАЦИЯ НЕ УДАЛАСЬ ✗✗✗")
        print("=" * 80)
        print("\n[!] Возможные причины:")
        print("    1. Неверный логин или пароль")
        print("    2. OK.ru показывает капчу")
        print("    3. Требуется подтверждение по SMS")
        print("\n[*] Проверьте скриншот: ok_login_failed.png")
        print("[*] Проверьте логин и пароль в .env файле")
    
    # Закрываем браузер
    print("\n[*] Закрытие браузера...")
    collector.driver.quit()
    print("[+] Готово")
    
except Exception as e:
    print(f"\n[!] ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
