"""
Проверка базы данных
"""
from models import db, Review
from app_enhanced import app
from datetime import datetime, timedelta

app.app_context().push()

print("=" * 80)
print("СТАТИСТИКА БАЗЫ ДАННЫХ")
print("=" * 80)

total = Review.query.count()
print(f"\nВсего записей: {total}")

today = datetime.now().date()
today_count = Review.query.filter(db.func.date(Review.collected_date) == today).count()
print(f"Сегодня собрано: {today_count}")

yesterday = today - timedelta(days=1)
yesterday_count = Review.query.filter(db.func.date(Review.collected_date) == yesterday).count()
print(f"Вчера собрано: {yesterday_count}")

print("\nПо источникам:")
print("-" * 80)

vk = Review.query.filter_by(source='vk').count()
ok = Review.query.filter_by(source='ok').count()
dzen = Review.query.filter_by(source='dzen').count()
telegram = Review.query.filter_by(source='telegram').count()
news = Review.query.filter_by(source='news').count()

print(f"VK:       {vk}")
print(f"OK:       {ok}")
print(f"Дзен:     {dzen}")
print(f"Telegram: {telegram}")
print(f"News:     {news}")

print("\nПоследние записи:")
print("-" * 80)

last_records = Review.query.order_by(Review.collected_date.desc()).limit(5).all()

for i, record in enumerate(last_records, 1):
    print(f"{i}. [{record.source}] {record.collected_date} - {record.text[:60]}...")

print("\nПоследняя запись по источникам:")
print("-" * 80)

for source in ['vk', 'ok', 'dzen', 'telegram', 'news']:
    last = Review.query.filter_by(source=source).order_by(Review.collected_date.desc()).first()
    if last:
        print(f"{source:10} - {last.collected_date}")
    else:
        print(f"{source:10} - НЕТ ЗАПИСЕЙ")

print("\n" + "=" * 80)

# Проверка пустых источников
empty_sources = []
if vk == 0:
    empty_sources.append("VK")
if ok == 0:
    empty_sources.append("OK.ru")
if dzen == 0:
    empty_sources.append("Дзен")

if empty_sources:
    print("!!! ВНИМАНИЕ: Нет записей из источников:")
    for src in empty_sources:
        print(f"  - {src}")
    print("\nЗапустите сбор через веб-интерфейс:")
    print("  http://127.0.0.1:5002 → Мониторинг → Запустить сбор")
else:
    print("OK: Все источники имеют записи")

print("=" * 80)
