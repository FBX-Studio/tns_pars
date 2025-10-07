"""
Тест ручного коллектора Дзен (по списку каналов)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from collectors.zen_collector_manual import ZenCollectorManual
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

print("="*60)
print("Тест коллектора Яндекс.Дзен (ручной список каналов)")
print("="*60)

collector = ZenCollectorManual()

print(f"\nНастроенные каналы: {len(collector.channels)}")
if collector.channels:
    for i, channel in enumerate(collector.channels, 1):
        if channel.strip():
            print(f"  {i}. {channel}")
else:
    print("\n⚠ ВНИМАНИЕ: Список каналов пуст!")
    print("\nДобавьте каналы в .env файл:")
    print("  DZEN_CHANNELS=id1,id2,id3")
    print("\nПодробнее смотрите в файле: DZEN_CHANNELS_GUIDE.md")
    print("\n" + "="*60)
    sys.exit(0)

print("\n" + "-"*60)
print("Начинаем сбор...")
print("-"*60 + "\n")

posts = collector.collect()

print("\n" + "="*60)
print(f"Всего найдено релевантных статей: {len(posts)}")
print("="*60)

if posts:
    print("\nПервые 5 статей:\n")
    for i, post in enumerate(posts[:5], 1):
        print(f"{i}. Автор: {post.get('author', 'N/A')}")
        print(f"   Текст: {post.get('text', '')[:150]}...")
        print(f"   URL: {post['url']}")
        print(f"   Дата: {post.get('published_date', 'N/A')}")
        print()
else:
    print("\n❌ Релевантные статьи не найдены.")
    print("\nВозможные причины:")
    print("  1. Каналы не содержат статей с ключевыми словами")
    print("  2. RSS ленты каналов пусты")
    print("  3. Неправильные ID каналов")
    print("\nПопробуйте:")
    print("  - Добавить другие каналы")
    print("  - Проверить что RSS работает: https://dzen.ru/id/CHANNEL_ID/rss")
