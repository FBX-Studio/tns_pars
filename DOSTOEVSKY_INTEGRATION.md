# Интеграция анализа тональности

## Описание

В систему интегрирован **автоматический анализ тональности** с поддержкой нескольких движков:
1. **Dostoevsky** (рекомендуется) - FastText модель для русского языка
2. **SentimentAnalyzer** (fallback) - словарный анализатор

**⚠️ ВАЖНО:** Dostoevsky требует компиляции C++ и работает на **Python 3.9-3.11**. На Python 3.13 используется fallback на SentimentAnalyzer.

## Особенности

✅ **Автоматический анализ** - все новости анализируются сразу после сбора
✅ **Fallback механизм** - автоматическое переключение если Dostoevsky недоступен
✅ **Батч-обработка** - эффективная обработка множества текстов
✅ **Детальные результаты** - определяет positive, negative, neutral с уверенностью

## Установка

### ⚠️ Требования для Dostoevsky

- Python 3.9, 3.10 или 3.11 (НЕ 3.13!)
- C++ компилятор (Visual Studio на Windows)
- ~2 ГБ свободного места для моделей

### Автоматическая установка (рекомендуется)

```bash
python install_dostoevsky.py
```

Скрипт:
1. Установит библиотеку `dostoevsky`
2. Загрузит предобученные модели (~1-2 ГБ)
3. Проверит корректность установки

### Ручная установка

```bash
# 1. Установка библиотеки
pip install dostoevsky

# 2. Загрузка моделей
python -m dostoevsky download fasttext-social-network-model
```

## Как это работает

### 1. Сбор новостей

Когда новость собирается из источника (VK, OK, News, Zen):

```python
# Новость собрана
article = {
    'text': 'Отличный сервис ТНС энерго!',
    'source': 'vk',
    ...
}
```

### 2. Автоматический анализ тональности

```python
# Автоматически выполняется анализ
if self.sentiment_analyzer:
    sentiment = self.sentiment_analyzer.analyze(article['text'])
    article['sentiment_score'] = sentiment['sentiment_score']  # -1.0 до 1.0
    article['sentiment_label'] = sentiment['sentiment_label']  # positive/negative/neutral
```

### 3. Сохранение в базу данных

Результаты сохраняются в поля:
- `sentiment_score` (float) - от -1.0 (очень негативно) до 1.0 (очень позитивно)
- `sentiment_label` (string) - 'positive', 'negative' или 'neutral'

### 4. Отображение в интерфейсе

Новости отображаются с индикаторами тональности:
- 🟢 Positive - зеленый
- 🔴 Negative - красный
- ⚪ Neutral - серый

## Интегрированные коллекторы

| Коллектор | Статус | Описание |
|-----------|--------|----------|
| `news_collector.py` | ✅ | RSS новости, Google News, Yandex News |
| `vk_collector.py` | ✅ | Посты и комментарии ВКонтакте |
| `ok_api_collector.py` | ✅ | Посты из Одноклассников |
| `telegram_collector.py` | ⏳ | Telegram каналы (в планах) |
| `zen_collector.py` | ⏳ | Яндекс.Дзен (в планах) |

## Архитектура

```
┌─────────────────────┐
│   Источники         │
│  (VK, OK, News)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Collectors         │
│  (сбор данных)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DostoevskyAnalyzer  │◄─── Анализ сразу
│  (анализ текста)    │     после сбора
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Database          │
│ (sentiment_score,   │
│  sentiment_label)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Web Interface     │
│  (отображение с     │
│   тональностью)     │
└─────────────────────┘
```

## API анализатора

### Базовое использование

```python
from analyzers.dostoevsky_analyzer import DostoevskyAnalyzer

# Инициализация
analyzer = DostoevskyAnalyzer()

# Анализ одного текста
result = analyzer.analyze("Отличное обслуживание!")

print(result)
# {
#     'sentiment_score': 0.85,
#     'sentiment_label': 'positive',
#     'confidence': 0.90,
#     'details': {
#         'positive': 0.90,
#         'negative': 0.05,
#         'neutral': 0.05,
#         'speech': 0.0,
#         'skip': 0.0
#     }
# }
```

### Батч-обработка

```python
# Анализ нескольких текстов (эффективнее)
texts = [
    "Отличный сервис!",
    "Ужасное обслуживание",
    "Всё нормально"
]

results = analyzer.analyze_batch(texts)
```

## Примеры результатов

### Позитивный текст
```
Текст: "Отличный сервис ТНС энерго! Быстро подключили, вежливые операторы"
Результат:
  - sentiment_score: 0.82
  - sentiment_label: positive
  - confidence: 0.88
```

### Негативный текст
```
Текст: "Ужасное обслуживание! Никому не рекомендую"
Результат:
  - sentiment_score: -0.91
  - sentiment_label: negative
  - confidence: 0.93
```

### Нейтральный текст
```
Текст: "ТНС энерго работает в Нижнем Новгороде"
Результат:
  - sentiment_score: 0.02
  - sentiment_label: neutral
  - confidence: 0.65
```

## Fallback механизм

Если Dostoevsky не установлен или не загружен:
1. Система автоматически переключится на стандартный `SentimentAnalyzer`
2. Работа продолжится без прерывания
3. В логах появится предупреждение

```python
try:
    self.sentiment_analyzer = DostoevskyAnalyzer()
except Exception as e:
    logger.warning(f"Не удалось загрузить Dostoevsky: {e}")
    self.sentiment_analyzer = SentimentAnalyzer()  # Fallback
```

## Производительность

- **Скорость**: ~100-200 текстов/сек на CPU
- **Память**: ~500 МБ для моделей
- **Точность**: ~85-90% на русскоязычных отзывах

## Тестирование

Запустите тест для проверки работы:

```bash
python -c "
from analyzers.dostoevsky_analyzer import DostoevskyAnalyzer

analyzer = DostoevskyAnalyzer()

test_texts = [
    'Отличный сервис ТНС!',
    'Ужасное обслуживание',
    'Всё нормально'
]

for text in test_texts:
    result = analyzer.analyze(text)
    print(f'{text}: {result[\"sentiment_label\"]} ({result[\"sentiment_score\"]:.2f})')
"
```

## Устранение неполадок

### Ошибка: "No module named 'dostoevsky'"
```bash
pip install dostoevsky
```

### Ошибка: "Model not found"
```bash
python -m dostoevsky download fasttext-social-network-model
```

### Модели не загружаются
Проверьте:
1. Наличие интернета
2. Свободное место на диске (~2 ГБ)
3. Права на запись в директорию пользователя

### Медленная работа
Используйте батч-обработку вместо анализа по одному тексту:
```python
# Медленно
for text in texts:
    result = analyzer.analyze(text)

# Быстро
results = analyzer.analyze_batch(texts)
```

## Дополнительная информация

- **Библиотека**: https://github.com/bureaucratic-labs/dostoevsky
- **Документация**: https://github.com/bureaucratic-labs/dostoevsky
- **Модель**: FastText Social Network Model
- **Язык**: Русский

## Планы развития

- [ ] Интеграция в Telegram коллектор
- [ ] Интеграция в Zen коллектор
- [ ] Фильтрация по тональности в веб-интерфейсе
- [ ] Экспорт отчетов по тональности
- [ ] Уведомления о негативных отзывах
