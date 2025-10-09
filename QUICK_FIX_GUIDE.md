# 🚀 Быстрое исправление проблем коллекторов

## ⚠️ КРИТИЧЕСКИЕ ПРОБЛЕМЫ В ТЕКУЩЕЙ КОНФИГУРАЦИИ

### 🔴 Проблема #1: Telegram FloodWait

**Симптомы:**
- Ошибка "FloodWait" в логах
- Telegram блокирует запросы на 5-300 секунд
- Сбор останавливается

**Причина:**
- В `.env` указано **60+ каналов** - это слишком много!

**Решение:**
```bash
# 1. Откройте .env
# 2. Замените TELEGRAM_CHANNELS на:
TELEGRAM_CHANNELS=@moynizhny,@bez_cenz_nn,@today_nn,@nizhniy_smi,@nn52signal,@nn_obl,@nnzhest,@nn_ru,@newsnnru,@nizhny_novgorod_news

# Или скопируйте оптимизированную конфигурацию:
copy .env.optimized .env
```

**Дополнительно:**
```python
# В telegram_user_collector.py строка 321:
await asyncio.sleep(10)  # Было 3 - увеличить до 10
```

---

### 🔴 Проблема #2: Медленный сбор новостей

**Симптомы:**
- Сбор занимает 30+ минут
- Много таймаутов

**Причина:**
- В `.env` указано **40+ сайтов**

**Решение:**
```bash
# В .env оставить только топ-10:
NEWS_SITES=https://nn.ru,https://www.vn.ru,https://www.pravda-nn.ru,https://www.nn52.ru,https://nnews.nnov.ru,https://www.newsnn.ru,https://www.niann.ru,https://www.ontvtime.ru,https://www.bornews52.ru,https://www.gorby.ru
```

---

### 🔴 Проблема #3: OK API дает мало данных

**Симптомы:**
- OK находит 0-5 постов
- Ошибка "No data found"

**Причина:**
- OK API не поддерживает публичный поиск

**Решение - использовать Selenium:**
```bash
# Тест нового коллектора:
python test_ok_selenium.py

# Интеграция в систему:
# В final_collection.py строка 57:
# Заменить:
from collectors.ok_api_collector import OKAPICollector
# На:
from collectors.ok_selenium_collector import OKSeleniumCollector as OKAPICollector
```

---

## ✅ БЫСТРЫЕ ИСПРАВЛЕНИЯ

### 1️⃣ Применить оптимизированную конфигурацию

```bash
# Windows:
copy .env.optimized .env

# Linux/Mac:
cp .env.optimized .env

# Перезапустить:
python final_collection.py
```

### 2️⃣ Увеличить интервал мониторинга

```bash
# В .env изменить:
MONITORING_INTERVAL_MINUTES=60  # Было 30
```

### 3️⃣ Отключить бесплатные прокси

```bash
# В .env изменить:
USE_FREE_PROXIES=False  # Было True
```

### 4️⃣ Использовать быстрые режимы

```bash
# Быстрый сбор (без медленных источников):
python final_collection.py --no-zen --no-ok

# Время: 5-7 минут вместо 15-20
```

---

## 🎯 ОПТИМАЛЬНЫЕ НАСТРОЙКИ

### Конфигурация .env:

```env
# Telegram - 10 каналов
TELEGRAM_CHANNELS=@moynizhny,@bez_cenz_nn,@today_nn,@nizhniy_smi,@nn52signal,@nn_obl,@nnzhest,@nn_ru,@newsnnru,@nizhny_novgorod_news

# News - 10 сайтов
NEWS_SITES=https://nn.ru,https://www.vn.ru,https://www.pravda-nn.ru,https://www.nn52.ru,https://nnews.nnov.ru,https://www.newsnn.ru,https://www.niann.ru,https://www.ontvtime.ru,https://www.bornews52.ru,https://www.gorby.ru

# Мониторинг - 60 минут
MONITORING_INTERVAL_MINUTES=60

# Прокси - отключить
USE_FREE_PROXIES=False
```

### График запусков:

```
06:00 - Быстрый сбор: python final_collection.py --no-zen --no-ok
12:00 - Полный сбор:  python final_collection.py
18:00 - Быстрый сбор: python final_collection.py --no-zen --no-ok
00:00 - Только Дзен:  python test_zen_selenium.py
```

---

## 📊 Ожидаемые результаты после оптимизации

| Показатель | Было | Стало | Улучшение |
|------------|------|-------|-----------|
| **Время сбора** | 30-40 мин | 10-15 мин | ⬇️ **60%** |
| **FloodWait** | Часто | Редко | ⬇️ **90%** |
| **Записей/запуск** | 50-100 | 100-200 | ⬆️ **100%** |
| **Стабильность** | ⚠️ Нестабильно | ✅ Стабильно | ⬆️ |

---

## 🔧 Тестирование после исправлений

```bash
# 1. Проверить конфигурацию
cat .env | grep TELEGRAM_CHANNELS
cat .env | grep NEWS_SITES
cat .env | grep MONITORING_INTERVAL

# 2. Тест быстрого сбора
python final_collection.py --no-zen --no-ok

# 3. Тест полного сбора
python final_collection.py

# 4. Тест OK Selenium
python test_ok_selenium.py

# 5. Проверить результаты
python -c "from models import Review; from app import app; app.app_context().push(); print(f'Всего записей: {Review.query.count()}')"
```

---

## 📚 Дополнительные улучшения (опционально)

### Параллельный сбор (в 2-3 раза быстрее):

```python
# Создать файл: parallel_collection.py
from concurrent.futures import ThreadPoolExecutor
from collectors.vk_collector import VKCollector
from collectors.telegram_user_collector import TelegramUserCollector
from collectors.news_collector import NewsCollector

def collect_parallel():
    collectors = {
        'vk': VKCollector(),
        'telegram': TelegramUserCollector(),
        'news': NewsCollector()
    }
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(c.collect) 
                   for name, c in collectors.items()}
        
        results = {}
        for name, future in futures.items():
            results[name] = future.result()
    
    return sum(results.values(), [])

if __name__ == '__main__':
    data = collect_parallel()
    print(f"Собрано: {len(data)} записей")
```

### Кэширование новостей:

```python
# В news_collector.py добавить:
import pickle
from datetime import datetime, timedelta

def collect_with_cache(self, cache_hours=1):
    cache_file = 'news_cache.pkl'
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cache_time, data = pickle.load(f)
            if datetime.now() - cache_time < timedelta(hours=cache_hours):
                logger.info(f"Используем кэш ({len(data)} статей)")
                return data
    
    data = self.collect()
    with open(cache_file, 'wb') as f:
        pickle.dump((datetime.now(), data), f)
    return data
```

---

## ✅ Чек-лист

- [ ] Скопировать `.env.optimized` в `.env`
- [ ] Проверить количество каналов Telegram (должно быть 10-15)
- [ ] Проверить количество сайтов News (должно быть 10-15)
- [ ] Установить `MONITORING_INTERVAL_MINUTES=60`
- [ ] Отключить `USE_FREE_PROXIES=False`
- [ ] Протестировать `test_ok_selenium.py`
- [ ] Запустить тестовый сбор
- [ ] Проверить логи на наличие ошибок
- [ ] Настроить расписание запусков

---

## 🆘 Если проблемы остались

**Telegram FloodWait:**
- Увеличьте задержки в `telegram_user_collector.py` (строка 321)
- Уменьшите количество каналов еще больше (до 5)
- Запускайте только 1 раз в день

**Медленный сбор:**
- Используйте `--no-zen --no-ok` для быстрого режима
- Уменьшите количество сайтов до 5
- Используйте параллельный сбор

**OK не находит данных:**
- Используйте OK Selenium вместо API
- Добавьте больше групп в `OK_GROUP_IDS`
- Или отключите OK: `python final_collection.py --no-ok`

---

**Обновлено:** 2025  
**Статус:** ✅ Все проблемы имеют решения  
**Поддержка:** См. `COLLECTORS_STATUS.md` для подробностей
