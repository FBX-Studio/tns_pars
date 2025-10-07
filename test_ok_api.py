"""
Тест коллектора OK API
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True, encoding='utf-8')

from collectors.ok_api_collector import OKAPICollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*70)
print("ТЕСТ OK API КОЛЛЕКТОРА")
print("="*70)

# Создаем коллектор
collector = OKAPICollector()

# Проверка конфигурации
print("\n📋 Проверка конфигурации:")
print("-"*70)
print(f"APP_ID: {'✓ Настроен' if collector.app_id else '✗ НЕ НАСТРОЕН'}")
print(f"PUBLIC_KEY: {'✓ Настроен' if collector.public_key else '✗ НЕ НАСТРОЕН'}")
print(f"SECRET_KEY: {'✓ Настроен' if collector.secret_key else '✗ НЕ НАСТРОЕН'}")
print(f"ACCESS_TOKEN: {'✓ Настроен' if collector.access_token else '✗ НЕ НАСТРОЕН'}")
print(f"Ключевых слов: {len(collector.keywords)}")

if not collector.access_token:
    print("\n" + "="*70)
    print("❌ ОШИБКА: Access Token не настроен!")
    print("="*70)
    print("\nЗапустите скрипт для получения токена:")
    print("python ok_get_token.py")
    print("\nИли см. инструкцию: OK_API_COMPLETE_GUIDE.md")
    sys.exit(1)

print("\n" + "="*70)
print("🚀 Запуск сбора...")
print("="*70)

# Собираем посты
posts = collector.collect()

print("\n" + "="*70)
print(f"✅ Результат: Найдено постов: {len(posts)}")
print("="*70)

if posts:
    print("\nПримеры постов:\n")
    for i, post in enumerate(posts[:5], 1):
        print(f"{i}. {post['text'][:100]}...")
        print(f"   Автор: {post['author']}")
        print(f"   URL: {post['url']}")
        print(f"   Дата: {post['published_date']}")
        print()
else:
    print("\n⚠️ Релевантных постов не найдено.")
    print("\nВозможные причины:")
    print("- В ленте нет постов с ключевыми словами")
    print("- Проверьте настройки фильтрации")
    print("- Попробуйте расширить список ключевых слов")

print("\n" + "="*70)
print("✅ Тест завершен!")
print("="*70)
