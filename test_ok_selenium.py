"""
Тест OK Selenium коллектора
"""
from collectors.ok_selenium_collector import OKSeleniumCollector
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("=" * 70)
    print("ТЕСТ: OK.ru через Selenium (обход ограничений API)")
    print("=" * 70)
    
    collector = OKSeleniumCollector()
    
    print("\n🔍 Начало сбора...")
    posts = collector.collect()
    
    print("\n" + "=" * 70)
    print(f"✅ РЕЗУЛЬТАТ: Найдено {len(posts)} постов")
    print("=" * 70)
    
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post['author']}")
        print(f"   Текст: {post['text'][:100]}...")
        print(f"   URL: {post['url']}")
        print(f"   Дата: {post['published_date']}")

if __name__ == '__main__':
    main()
