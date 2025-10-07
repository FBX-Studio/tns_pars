"""
Тест нового Дзен коллектора
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from collectors.zen_collector import ZenCollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("Тестируем Дзен коллектор...")
print("-" * 60)

collector = ZenCollector()
posts = collector.collect()

print("-" * 60)
print(f"\nВсего найдено: {len(posts)}")

if posts:
    print("\nПервые 3 статьи:")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post.get('text', '')[:100]}...")
        print(f"   URL: {post['url']}")
        print(f"   Source ID: {post['source_id']}")
