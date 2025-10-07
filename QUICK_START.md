# 🚀 Быстрый старт с анализом тональности

## ✅ Интеграция завершена!

Анализ тональности уже интегрирован и готов к использованию. Все новости будут автоматически анализироваться при сборе.

## 📋 Что работает

✅ Автоматический анализ тональности всех новостей  
✅ Сохранение результатов в БД (sentiment_score, sentiment_label)  
✅ Fallback на SentimentAnalyzer (работает на Python 3.13)  
✅ Интеграция в коллекторы: news, vk, ok

## 🎯 Запуск

### 1. Запустите веб-приложение

```bash
python app_enhanced.py
```

### 2. Откройте браузер

```
http://localhost:5000
```

### 3. Запустите мониторинг

Нажмите кнопку "Запустить мониторинг" в веб-интерфейсе

### 4. Наблюдайте результаты

Новости будут собираться с автоматическим анализом тональности:
- 🟢 Positive (позитивные)
- 🔴 Negative (негативные)  
- ⚪ Neutral (нейтральные)

## 🔍 Проверка работы

### Посмотрите в БД

```python
from models import db, Review
from app_enhanced import app

with app.app_context():
    # Последние 5 новостей с тональностью
    reviews = Review.query.order_by(Review.collected_date.desc()).limit(5).all()
    for r in reviews:
        print(f"{r.sentiment_label}: {r.text[:50]}... (score: {r.sentiment_score})")
```

### Или через SQL

```sql
SELECT sentiment_label, sentiment_score, text 
FROM reviews 
ORDER BY collected_date DESC 
LIMIT 10;
```

## ⚙️ Настройка

### Используемый анализатор

Система автоматически выбирает анализатор при запуске:

```python
# В async_monitor_websocket.py
try:
    self.sentiment_analyzer = DostoevskyAnalyzer()  # Попытка загрузить
    logger.info("✓ Dostoevsky загружен")
except:
    self.sentiment_analyzer = SentimentAnalyzer()  # Fallback
    logger.info("✓ SentimentAnalyzer загружен")
```

### Текущая конфигурация

На Python 3.13: **SentimentAnalyzer** (словарный анализатор)

Для Dostoevsky нужен Python 3.9-3.11 + C++ компилятор.

## 📊 Примеры результатов

### Positive (позитив)
```
Текст: "Отличный сервис ТНС энерго! Быстро подключили"
sentiment_score: 0.75
sentiment_label: positive
```

### Negative (негатив)
```
Текст: "Ужасное обслуживание, долго ждал"
sentiment_score: -0.82
sentiment_label: negative
```

### Neutral (нейтрально)
```
Текст: "ТНС энерго работает в Нижнем Новгороде"
sentiment_score: 0.05
sentiment_label: neutral
```

## 🐛 Проблемы?

### Ошибка: "unexpected keyword argument 'sentiment_analyzer'"

**Решено!** Обновлены все коллекторы:
- ✅ news_collector.py
- ✅ news_collector_light.py
- ✅ vk_collector.py
- ✅ ok_api_collector.py

### Проверка версии Python

```bash
python --version
```

Если Python 3.13 - используется SentimentAnalyzer (это нормально!)

### Логи

Смотрите логи при запуске:
```
[MONITOR] Инициализация Dostoevsky анализатора...
[MONITOR] ✓ Dostoevsky анализатор загружен
```
или
```
[MONITOR] Не удалось загрузить Dostoevsky: ...
[MONITOR] Используем стандартный анализатор
```

## 📚 Документация

- **README_SENTIMENT.md** - полное описание интеграции
- **DOSTOEVSKY_INTEGRATION.md** - техническая документация
- **install_dostoevsky.py** - скрипт установки (для Python 3.9-3.11)

## ✨ Готово!

Просто запустите приложение и система начнет собирать новости с автоматическим анализом тональности! 🎉
