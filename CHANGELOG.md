# Changelog

## [Новое] Парсинг комментариев к новостям

### Добавлено
- **Парсинг комментариев к новостям** из всех источников
- **Связь комментариев с родительскими новостями** через `parent_id`
- **Поддержка комментариев в Telegram** (ответы/replies к сообщениям)
- **Парсинг комментариев с новостных сайтов** (универсальные селекторы)
- **Комментарии к статьям Яндекс.Дзен**

### Изменено
- **models.py**: Добавлены поля `parent_id`, `is_comment` и relationship для комментариев
- **final_collection.py**: Флаг `--comments` для включения парсинга комментариев
- **run_collection_once.py**: Поддержка сохранения комментариев с правильной связью
- **collectors/news_collector.py**: Методы `parse_article_comments()` и `collect_with_comments()`
- **collectors/telegram_user_collector.py**: Метод `get_message_replies()` для парсинга ответов
- **collectors/zen_collector.py**: Метод `parse_dzen_comments()` для комментариев Дзен

### Новые файлы
- **migrate_database.py**: Миграция БД для добавления новых колонок
- **test_comments_collection.py**: Тестовый скрипт для проверки парсинга
- **COMMENTS_PARSING.md**: Подробная документация по парсингу комментариев

### Использование

```bash
# Быстрый сбор (без комментариев)
python final_collection.py

# Полный сбор (с комментариями)
python final_collection.py --comments

# Выборочный сбор
python final_collection.py --comments --no-vk --no-zen

# Тестирование
python test_comments_collection.py
```

### База данных

После обновления обязательно выполните миграцию:
```bash
python migrate_database.py
```

Это добавит поля `parent_id` и `is_comment` в таблицу `reviews`.

### API изменения

```python
# News Collector
from collectors.news_collector import NewsCollector
collector = NewsCollector()

# Без комментариев
articles = collector.collect()

# С комментариями
data = collector.collect_with_comments()

# Telegram Collector
from collectors.telegram_user_collector import TelegramUserCollector
collector = TelegramUserCollector()

# С комментариями
data = collector.collect(collect_comments=True)

# Zen Collector
from collectors.zen_collector import ZenCollector
collector = ZenCollector()

# С комментариями
data = collector.collect(collect_comments=True)
```

### Примечания
- Парсинг комментариев значительно увеличивает время сбора
- Рекомендуется использовать для периодического полного анализа
- Для ежедневного мониторинга достаточно быстрого режима без комментариев
