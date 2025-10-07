"""
Тест Дзен коллектора с прокси
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True, encoding='utf-8')

from collect_dzen_duckduckgo import DzenDuckDuckGoCollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*70)
print("ТЕСТ ДЗЕН КОЛЛЕКТОРА С ПРОКСИ")
print("="*70)

print("\n📋 Шаг 1: Инициализация коллектора с прокси...")
print("-"*70)

try:
    collector = DzenDuckDuckGoCollector(use_proxy=True)
    print("✓ Коллектор создан")
    print(f"✓ Режим прокси: {'Включен' if collector.use_proxy else 'Выключен'}")
    if collector.use_proxy and collector.proxy_manager:
        print(f"✓ Загружено прокси: {len(collector.proxy_manager.proxies)}")
except Exception as e:
    print(f"✗ Ошибка инициализации: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("📋 Шаг 2: Сбор статей из Дзен...")
print("-"*70)

try:
    articles = collector.collect()
    
    print("\n" + "="*70)
    print(f"✅ Результат: Найдено статей: {len(articles)}")
    print("="*70)
    
    if articles:
        print("\nПримеры статей:\n")
        for i, article in enumerate(articles[:5], 1):
            print(f"{i}. {article['text'][:100]}...")
            print(f"   URL: {article['url']}")
            print(f"   Автор: {article['author']}")
            print(f"   Дата: {article['published_date']}")
            print()
    else:
        print("\n⚠️ Релевантных статей не найдено.")
        print("\nВозможные причины:")
        print("- В Дзен нет статей с ключевыми словами")
        print("- Прокси не работают")
        print("- DuckDuckGo все еще блокирует")
        
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ Тест завершен!")
print("="*70)
