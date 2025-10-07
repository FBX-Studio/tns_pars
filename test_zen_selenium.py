"""
Тест Selenium-коллектора для Дзен
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from collectors.zen_collector_selenium import ZenCollectorSelenium
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("Тестируем Дзен коллектор с Selenium...")
print("-" * 60)

collector = ZenCollectorSelenium()
posts = collector.collect()

print("-" * 60)
print(f"\nВсего найдено: {len(posts)}")

if posts:
    print("\nПервые 5 статей:")
    for i, post in enumerate(posts[:5], 1):
        print(f"\n{i}. {post.get('text', '')[:150]}...")
        print(f"   URL: {post['url']}")
        print(f"   Source ID: {post['source_id']}")
else:
    print("\nСтатьи не найдены")
