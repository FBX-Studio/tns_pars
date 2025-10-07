# Почему новости не сохраняются в базу данных

## Проблема

В логах видно:
```
INFO:collectors.news_collector_light:[NEWS] Релевантная: "ТНС Энерго НН" банкротит...
...
INFO:async_monitor_websocket:[NEWS] collected: Получено записей: 65
INFO:async_monitor_websocket:[NEWS] completed: Завершено! Добавлено: 0
```

**Найдено 65 новостей, но добавлено 0!**

## Причина

Все найденные новости **УЖЕ ЕСТЬ В БАЗЕ ДАННЫХ**.

### Проверка базы данных:
```
Всего записей: 63
Последние записи от: 2025-10-06 23:26:39
Источник: Google News
```

### Как проверяются дубликаты:

В файле `async_monitor_websocket.py` строка 193-199:
```python
existing = Review.query.filter_by(
    source_id=review_data['source_id']
).first()

if existing:
    continue  # Пропускаем дубликат
```

### Как генерируется source_id:

В файле `collectors/news_collector_light.py` строка 250:
```python
'source_id': f"gnews_{abs(hash(real_url))}"
```

**Проблема**: Google News возвращает одни и те же статьи каждый день!

URL статьи не меняется → hash(url) не меняется → source_id одинаковый → новость считается дубликатом.

## Решения

### Вариант 1: Очистить старые новости (БЫСТРО)

Удалить новости старше 1 дня:

```bash
python -c "from models import Review, db; from app_enhanced import app; from datetime import datetime, timedelta; app.app_context().push(); old_date = datetime.now() - timedelta(days=1); deleted = Review.query.filter(Review.collected_date < old_date).delete(); db.session.commit(); print(f'Udaleno: {deleted}')"
```

Или через веб-интерфейс: кнопка "Очистить отзывы"

### Вариант 2: Изменить генерацию source_id (ПРАВИЛЬНО)

Добавить дату/время в source_id чтобы одна и та же статья могла быть добавлена повторно:

**В `news_collector_light.py` изменить:**
```python
# Было:
'source_id': f"gnews_{abs(hash(real_url))}"

# Стало:
'source_id': f"gnews_{abs(hash(real_url))}_{pub_date.strftime('%Y%m%d')}"
```

Теперь одна статья может появляться раз в день.

### Вариант 3: Увеличить период фильтрации

Если вы запускаете сбор раз в неделю, измените логику чтобы собирать только **новые** статьи:

**В dashboard выбрать период:**
- "За последний час" - только свежие
- "За последний день" - за сутки

Но это не решит проблему полностью, т.к. Google News показывает старые статьи.

### Вариант 4: Добавить автоочистку старых записей

Добавить в конфигурацию автоматическую очистку записей старше N дней.

## Рекомендация

**Используйте Вариант 2** - измените генерацию source_id чтобы включить дату.

Тогда:
- Статья от 06.10.2025 → source_id = "gnews_12345_20251006"
- Та же статья от 07.10.2025 → source_id = "gnews_12345_20251007"
- **Обе будут сохранены!**

## Быстрое решение СЕЙЧАС

1. **Очистите базу данных новостей:**
```bash
# Через веб-интерфейс
http://localhost:5000
→ Кнопка "Очистить отзывы"
```

2. **Запустите сбор снова:**
```bash
→ Кнопка "Запустить сбор"
```

3. **Все 65 новостей будут добавлены!**

## Статистика текущего сбора

Согласно логам:
- **News (Google)**: найдено ~65, добавлено 0 (дубликаты)
- **OK**: найдено 0 (ошибка connection reset)
- **Zen**: найдено 0 (timeout при подключении к Яндекс.Новости)
- **VK**: ? (нужно посмотреть логи)
- **Telegram**: ? (нужно посмотреть логи)

## Исправим дополнительные проблемы

### OK collector - Connection Reset
```
ERROR:collectors.ok_collector:[OK] Ошибка поиска: Connection aborted
```
**Решение**: Добавить retry и увеличить timeout

### Zen collector - Timeout
```
ERROR:collectors.zen_collector:[ZEN] Ошибка парсинга RSS: Read timed out
```
**Решение**: Увеличить timeout с 10 до 20 секунд
