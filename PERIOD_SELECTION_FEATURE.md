# Функция выбора периода парсинга

## Описание

Добавлена возможность выбирать период, за который собираются отзывы при парсинге.

## 🎯 Возможности

### Доступные периоды:
- **За последний час** - собирает отзывы за последние 60 минут
- **За последний день** - собирает отзывы за последние 24 часа (по умолчанию)
- **За последнюю неделю** - собирает отзывы за последние 7 дней
- **За последний месяц** - собирает отзывы за последние 30 дней
- **За всё время** - собирает все доступные отзывы без ограничения

## 📍 Где находится

На странице **Dashboard** (главная страница) в разделе "Управление системой" над кнопкой "Запустить сбор".

## 🎨 Внешний вид

```
⚙️ Управление системой

Ключевые слова: ТНС энерго НН, ТНС энерго, энергосбыт, ТНС

Период парсинга:
[Выпадающий список ▼]
   - За последний час
   - За последний день ✓
   - За последнюю неделю
   - За последний месяц
   - За всё время

[▶ Запустить сбор]  [🗑️ Очистить отзывы]  [🗑️ Очистить логи]  [⚠️ Очистить всё]
```

## 🔧 Как работает

### 1. Выбор периода
Пользователь выбирает период из выпадающего списка перед запуском сбора.

### 2. Подтверждение
При нажатии "Запустить сбор" появляется диалог:
```
Запустить сбор отзывов за последний день?
[OK] [Отмена]
```

### 3. Процесс сбора
- Система собирает данные из всех источников (VK, Telegram, Новости)
- Фильтрует отзывы по выбранному периоду
- Показывает прогресс в реальном времени

### 4. Отображение прогресса
```
Прогресс сбора:

VK:
  Сбор данных из источника... 25%
  Отфильтровано: 45 из 120 (период: day) 45%
  Получено записей: 45 50%
  Обработано: 45/45 90%
  ✓ Завершено: добавлено 12 новых отзывов

Telegram:
  Сбор данных из источника... 25%
  ...
```

## 💻 Техническая реализация

### Frontend (dashboard_enhanced.html)

#### HTML:
```html
<div style="margin: 1.5rem 0;">
    <label>Период парсинга:</label>
    <select id="period-select">
        <option value="hour">За последний час</option>
        <option value="day" selected>За последний день</option>
        <option value="week">За последнюю неделю</option>
        <option value="month">За последний месяц</option>
        <option value="all">За всё время</option>
    </select>
</div>
```

#### JavaScript:
```javascript
function startMonitoring() {
    const period = document.getElementById('period-select').value;
    const periodText = document.getElementById('period-select').options[...].text;
    
    fetch('/api/monitoring/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ period: period })
    })
    ...
}
```

### Backend (app_enhanced.py)

#### API Endpoint:
```python
@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    data = request.get_json() or {}
    period = data.get('period', 'day')  # По умолчанию - день
    
    monitoring_state['period'] = period
    monitor = AsyncReviewMonitorWebSocket(socketio, period=period)
    
    thread = threading.Thread(target=monitor.run_collection_sync)
    thread.start()
    
    period_text = {
        'hour': 'за последний час',
        'day': 'за последний день',
        ...
    }.get(period, 'за выбранный период')
    
    return jsonify({
        'success': True,
        'message': f'Мониторинг запущен {period_text}'
    })
```

### Monitor (async_monitor_websocket.py)

#### Инициализация:
```python
class AsyncReviewMonitorWebSocket:
    def __init__(self, socketio, period='day'):
        self.period = period
        self.since_date = self._calculate_since_date(period)
        ...
```

#### Вычисление даты:
```python
def _calculate_since_date(self, period):
    now = datetime.utcnow()
    
    if period == 'hour':
        return now - timedelta(hours=1)
    elif period == 'day':
        return now - timedelta(days=1)
    elif period == 'week':
        return now - timedelta(weeks=1)
    elif period == 'month':
        return now - timedelta(days=30)
    else:  # 'all'
        return None
```

#### Фильтрация:
```python
async def collect_from_source_async(self, source_name, collector):
    reviews = await loop.run_in_executor(None, collector.collect)
    
    # Фильтрация по периоду
    if self.since_date:
        initial_count = len(reviews)
        reviews = [r for r in reviews if self._is_within_period(r)]
        self.emit_progress(source_name, 'filtering',
            f'Отфильтровано: {len(reviews)} из {initial_count} (период: {self.period})'
        )
    ...
```

#### Проверка периода:
```python
def _is_within_period(self, review_data):
    if not self.since_date:
        return True  # Период 'all'
    
    # Поиск даты в различных полях
    date_fields = ['date', 'created_date', 'collected_date', ...]
    
    for field in date_fields:
        if field in review_data and review_data[field]:
            # Парсинг даты (timestamp, string, datetime)
            review_date = parse_date(review_data[field])
            if review_date:
                return review_date >= self.since_date
    
    return True  # Если дата не найдена - пропускаем
```

## 📊 Примеры использования

### Пример 1: Срочный мониторинг
```
Цель: Проверить последние отзывы после публикации важной новости

1. Выбрать: "За последний час"
2. Нажать "Запустить сбор"
3. Система соберет только отзывы за последний час
```

### Пример 2: Ежедневный отчет
```
Цель: Собрать отзывы за вчерашний день

1. Выбрать: "За последний день" (по умолчанию)
2. Нажать "Запустить сбор"
3. Получить отзывы за 24 часа
```

### Пример 3: Недельная аналитика
```
Цель: Проанализировать тренды за неделю

1. Выбрать: "За последнюю неделю"
2. Нажать "Запустить сбор"
3. Собрать все отзывы за 7 дней
```

### Пример 4: Полный анализ
```
Цель: Собрать всю историю отзывов

1. Выбрать: "За всё время"
2. Нажать "Запустить сбор"
3. Система соберет все доступные отзывы
```

## ⚡ Производительность

### Оптимизация:
- Фильтрация происходит **после** сбора данных
- Коллекторы собирают данные с API обычным образом
- Фильтр убирает устаревшие записи перед анализом

### Время выполнения:
- **Час:** ~30-60 сек (мало данных)
- **День:** ~1-2 мин (стандартный объем)
- **Неделя:** ~3-5 мин (большой объем)
- **Месяц:** ~5-10 мин (очень большой объем)
- **Всё время:** зависит от количества данных в источниках

## 🔍 Логирование

При фильтрации в логах отображается:
```
[VK] filtering: Отфильтровано: 45 из 120 (период: day)
[TELEGRAM] filtering: Отфильтровано: 12 из 89 (период: day)
[NEWS] filtering: Отфильтровано: 8 из 34 (период: day)
```

## 📝 Файлы, затронутые изменениями

1. **templates/dashboard_enhanced.html**
   - Добавлен dropdown для выбора периода
   - Обновлена функция `startMonitoring()`

2. **app_enhanced.py**
   - Обновлен endpoint `/api/monitoring/start`
   - Добавлен прием параметра `period`
   - Передача параметра в AsyncReviewMonitorWebSocket

3. **async_monitor_websocket.py**
   - Добавлен параметр `period` в `__init__`
   - Добавлен метод `_calculate_since_date()`
   - Добавлен метод `_is_within_period()`
   - Добавлена фильтрация в `collect_from_source_async()`

## 🎉 Результат

Теперь пользователи могут:
- ✅ Выбирать точный период сбора отзывов
- ✅ Экономить время на обработке
- ✅ Фокусироваться на актуальных данных
- ✅ Создавать отчеты за конкретные периоды
- ✅ Избегать дубликатов при регулярном мониторинге

---

**Дата создания:** 07.01.2025  
**Версия:** 1.0  
**Разработчик:** FBX Studio
