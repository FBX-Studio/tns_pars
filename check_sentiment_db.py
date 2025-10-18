"""
Проверка sentiment в базе данных
"""
import sqlite3
import os

db_path = 'instance/reviews.db'

print("=" * 80)
print("ПРОВЕРКА SENTIMENT В БАЗЕ ДАННЫХ")
print("=" * 80)

if not os.path.exists(db_path):
    print(f"\n[!] База данных не найдена: {db_path}")
    exit(1)

print(f"\n[+] База данных найдена: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем таблицы
print("\n[1] Проверка таблиц...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Таблицы: {[t[0] for t in tables]}")

# Проверяем структуру таблицы review
print("\n[2] Структура таблицы review...")
try:
    cursor.execute("PRAGMA table_info(review)")
    columns = cursor.fetchall()
    print("Колонки:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Проверяем наличие sentiment колонок
    col_names = [col[1] for col in columns]
    has_sentiment_score = 'sentiment_score' in col_names
    has_sentiment_label = 'sentiment_label' in col_names
    
    print(f"\n[+] sentiment_score: {'ДА' if has_sentiment_score else 'НЕТ'}")
    print(f"[+] sentiment_label: {'ДА' if has_sentiment_label else 'НЕТ'}")
    
except Exception as e:
    print(f"[!] Ошибка: {e}")

# Проверяем количество записей
print("\n[3] Статистика записей...")
cursor.execute("SELECT COUNT(*) FROM review")
total = cursor.fetchone()[0]
print(f"Всего записей: {total}")

# Проверяем записи с sentiment
cursor.execute("SELECT COUNT(*) FROM review WHERE sentiment_label IS NOT NULL")
with_sentiment = cursor.fetchone()[0]
print(f"С sentiment_label: {with_sentiment}")

cursor.execute("SELECT COUNT(*) FROM review WHERE sentiment_score IS NOT NULL")
with_score = cursor.fetchone()[0]
print(f"С sentiment_score: {with_score}")

# Распределение по тональности
print("\n[4] Распределение по тональности...")
cursor.execute("""
    SELECT sentiment_label, COUNT(*) as count 
    FROM review 
    WHERE sentiment_label IS NOT NULL 
    GROUP BY sentiment_label
""")
distribution = cursor.fetchall()
if distribution:
    for label, count in distribution:
        print(f"  {label}: {count}")
else:
    print("  [!] Нет записей с sentiment_label")

# Последние записи
print("\n[5] Последние 5 записей...")
cursor.execute("""
    SELECT id, source, sentiment_label, sentiment_score, 
           substr(text, 1, 50) as text_preview
    FROM review 
    ORDER BY id DESC 
    LIMIT 5
""")
recent = cursor.fetchall()
for row in recent:
    id, source, label, score, text = row
    print(f"\nID: {id}")
    print(f"Source: {source}")
    print(f"Sentiment: {label} (score: {score})")
    print(f"Text: {text}...")

# Проверяем источники
print("\n[6] Записи по источникам...")
cursor.execute("""
    SELECT source, 
           COUNT(*) as total,
           COUNT(sentiment_label) as with_sentiment
    FROM review 
    GROUP BY source
""")
by_source = cursor.fetchall()
for source, total, with_sent in by_source:
    percentage = (with_sent / total * 100) if total > 0 else 0
    print(f"  {source}: {total} записей, {with_sent} с sentiment ({percentage:.0f}%)")

conn.close()

print("\n" + "=" * 80)
if with_sentiment == 0:
    print("[ERROR] SENTIMENT НЕ ОПРЕДЕЛЯЕТСЯ")
    print("\nВозможные причины:")
    print("1. Анализатор не инициализируется в коллекторах")
    print("2. Записи были созданы до исправления")
    print("3. Ошибка при сохранении в базу")
    print("\nРекомендация: Запустить новый сбор данных")
elif with_sentiment < total:
    print(f"[WARNING] ЧАСТИЧНО РАБОТАЕТ ({with_sentiment}/{total})")
    print("\nСтарые записи без sentiment, новые - с sentiment")
else:
    print("[SUCCESS] ВСЕ ЗАПИСИ С SENTIMENT!")
print("=" * 80)
