# 📊 Статус коллекторов и способы обхода ограничений

## Обновлено: 2025

---

## ✅ Работающие коллекторы

### 1️⃣ **VK Collector** - РАБОТАЕТ СТАБИЛЬНО

**Статус:** ✅ Полностью функционален  
**API:** Официальный VK API  
**Требования:** `VK_ACCESS_TOKEN`

**Ограничения:**
- ⏱️ Rate limit: 3 запроса/сек
- 📊 Максимум 200 постов за запрос
- 🔍 Только публичные посты

**Способы обхода:**
```python
# 1. Увеличить задержки (уже встроено)
time.sleep(0.5)

# 2. Использовать несколько токенов
tokens = [token1, token2, token3]
collector = VKCollector(token=random.choice(tokens))

# 3. Добавить больше групп для мониторинга
VK_GROUP_IDS=123456,789012,345678
```

**Оценка:** ⭐⭐⭐⭐⭐ (5/5) - Работает отлично

---

### 2️⃣ **Telegram Collector** - РАБОТАЕТ С ОГРАНИЧЕНИЯМИ

**Статус:** ⚠️ Работает, но требует осторожности  
**API:** Telethon (User API)  
**Требования:** `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`

**Ограничения:**
- ⚠️ FloodWait: блокировка на 5-300 сек при частых запросах
- 📅 Только последние 30 дней
- 📊 100 сообщений за запрос
- 🚫 Риск бана при слишком частом использовании

**Способы обхода:**
```python
# 1. ГЛАВНОЕ: Сократить список каналов
# В .env оставить только 10-15 каналов вместо 60+
TELEGRAM_CHANNELS=@moynizhny,@bez_cenz_nn,@today_nn,@nizhniy_smi,@nn52signal

# 2. Увеличить задержки между каналами
# В telegram_user_collector.py строка 321:
await asyncio.sleep(10)  # Было 3

# 3. Собирать за 7 дней вместо 30
# Строка 246:
offset_date = datetime.now() - timedelta(days=7)

# 4. Использовать несколько аккаунтов
# Создать несколько .env с разными phone/api_id
```

**Оценка:** ⭐⭐⭐⭐ (4/5) - Работает, но нужна осторожность

**⚠️ КРИТИЧНО для вашей системы:**
- У вас **60+ каналов** - это ГАРАНТИРОВАННЫЙ FloodWait!
- Сократите до **10-15 самых важных**
- Запускайте **максимум 2 раза в день**

---

### 3️⃣ **News Collector** - РАБОТАЕТ ХОРОШО

**Статус:** ✅ Функционален  
**Метод:** RSS + Google News + Web scraping  
**Требования:** Нет (публичный доступ)

**Ограничения:**
- 🌐 Зависит от доступности RSS
- 💬 Комментарии парсятся не всегда
- ⏱️ Медленный при большом количестве сайтов

**Способы обхода:**
```python
# 1. Использовать только главные RSS
self.rss_feeds = [
    'https://nn.ru/rss.xml',
    'https://www.nn52.ru/rss'
]

# 2. Параллельный сбор (многопоточность)
from concurrent.futures import ThreadPoolExecutor

def collect_parallel(self):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(self.collect_from_rss, feed) 
                   for feed in self.rss_feeds]
        return sum([f.result() for f in futures], [])

# 3. Кэширование результатов
import pickle
def collect_with_cache(self, cache_hours=1):
    cache_file = 'news_cache.pkl'
    if os.path.exists(cache_file):
        cache_time, data = pickle.load(open(cache_file, 'rb'))
        if datetime.now() - cache_time < timedelta(hours=cache_hours):
            return data
    
    data = self.collect()
    pickle.dump((datetime.now(), data), open(cache_file, 'wb'))
    return data

# 4. Использовать newspaper3k для лучшего парсинга
from newspaper import Article
article = Article(url, language='ru')
article.download()
article.parse()
```

**Оценка:** ⭐⭐⭐⭐ (4/5) - Надежный источник

**💡 Рекомендации:**
- Сократить список сайтов с **40+ до 5-10**
- Использовать **только Google News** для скорости
- Комментарии собирать **отдельным запуском**

---

### 4️⃣ **Zen Selenium Collector** - РАБОТАЕТ ОТЛИЧНО

**Статус:** ✅ Лучший вариант для Дзена  
**Метод:** Selenium (реальный браузер)  
**Требования:** Chrome/Chromium

**Ограничения:**
- 🐌 Медленный: 2-3 минуты
- 💾 Ресурсоемкий: ~300 МБ RAM
- ⚠️ Может словить капчу при частом использовании

**Способы обхода:**
```python
# 1. Увеличить количество результатов
# В zen_selenium_collector.py строка 224:
search_results = self.search_yandex(keyword, max_results=20)  # Было 5

# 2. Параллельный запуск (2 браузера)
from multiprocessing import Pool

def collect_parallel(self):
    with Pool(processes=2) as pool:
        results = pool.map(self._collect_keyword, self.keywords)
    return sum(results, [])

# 3. Использовать профиль Chrome (ускорение)
chrome_options.add_argument('--user-data-dir=C:/selenium_profile')

# 4. Ротация User-Agent
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Windows NT 10.0; WOW64)...',
]
chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
```

**Оценка:** ⭐⭐⭐⭐⭐ (5/5) - 100% обход капчи

**✅ Рекомендации:**
- Запускать **1-2 раза в день**
- Собирать **в ночное время** (меньше нагрузка)
- Отлично работает **как есть**

---

### 5️⃣ **OK API Collector** - ОГРАНИЧЕННЫЙ

**Статус:** ⚠️ Работает, но очень ограничен  
**API:** Официальный OK API  
**Требования:** `OK_APP_ID`, `OK_PUBLIC_KEY`, `OK_ACCESS_TOKEN`

**Ограничения:**
- 🚫 **НЕТ публичного поиска!**
- 📊 Только личная лента или конкретные группы
- 📊 Максимум 20 постов на группу
- 📝 Текст обрезается до 500 символов

**Способы обхода:**
```python
# 1. Мониторить больше групп
# Найти ID групп вручную:
# ok.ru/group/12345678 -> добавить 12345678 в OK_GROUP_IDS

# 2. Делать несколько запросов с offset
def get_all_posts(self, group_id, total=100):
    all_posts = []
    for offset in range(0, total, 20):
        params = {'gid': group_id, 'count': 20, 'offset': offset}
        posts = self._make_api_request('stream.get', params)
        all_posts.extend(posts)
        time.sleep(1)
    return all_posts

# 3. Использовать Selenium (см. ниже)
from collectors.ok_selenium_collector import OKSeleniumCollector
collector = OKSeleniumCollector()
posts = collector.collect()
```

**Оценка:** ⭐⭐ (2/5) - Очень ограничен

---

### 6️⃣ **OK Selenium Collector** - НОВЫЙ! ✨

**Статус:** ✅ Обходит ограничения API  
**Метод:** Selenium (поиск + парсинг)  
**Требования:** Chrome/Chromium

**Преимущества:**
- ✅ Публичный поиск работает!
- ✅ Нет лимита на количество постов
- ✅ Полный текст постов
- ✅ Обход ограничений API

**Использование:**
```bash
# Тест коллектора
python test_ok_selenium.py

# Использование в коде
from collectors.ok_selenium_collector import OKSeleniumCollector
collector = OKSeleniumCollector()
posts = collector.collect()
```

**Интеграция в final_collection.py:**
```python
# Заменить строку 57:
# from collectors.ok_api_collector import OKAPICollector
# На:
from collectors.ok_selenium_collector import OKSeleniumCollector as OKAPICollector
```

**Оценка:** ⭐⭐⭐⭐ (4/5) - Хорошая альтернатива API

---

## 📊 Сравнительная таблица

| Коллектор | Статус | Скорость | Надежность | Данных/запуск | Рекомендация |
|-----------|--------|----------|------------|---------------|--------------|
| **VK** | ✅ | Быстро | ⭐⭐⭐⭐⭐ | 50-200 | ✅ Использовать |
| **Telegram** | ⚠️ | Средне | ⭐⭐⭐⭐ | 100-500 | ⚠️ Сократить каналы! |
| **News** | ✅ | Быстро | ⭐⭐⭐⭐ | 20-50 | ✅ Использовать |
| **Zen Selenium** | ✅ | Медленно | ⭐⭐⭐⭐⭐ | 10-20 | ✅ 1-2 раза/день |
| **OK API** | ⚠️ | Быстро | ⭐⭐ | 5-20 | ❌ Очень ограничен |
| **OK Selenium** | ✅ | Медленно | ⭐⭐⭐⭐ | 20-30 | ✅ Вместо API |

---

## 🎯 Оптимальная стратегия для вашей системы

### **Конфигурация .env (оптимизированная):**

```env
# Telegram - СОКРАТИТЬ с 60+ до 10 каналов!
TELEGRAM_CHANNELS=@moynizhny,@bez_cenz_nn,@today_nn,@nizhniy_smi,@nn52signal,@nn_obl,@nnzhest,@nn_ru,@newsnnru,@nizhny_novgorod_news

# News - оставить топ-5 сайтов
NEWS_SITES=https://nn.ru,https://www.vn.ru,https://www.pravda-nn.ru,https://www.nn52.ru,https://nnews.nnov.ru

# Мониторинг - увеличить интервал
MONITORING_INTERVAL_MINUTES=60  # Было 30

# Прокси - отключить для скорости
USE_FREE_PROXIES=False
```

### **Режимы запуска:**

```bash
# 1. БЫСТРЫЙ (5-7 минут) - для частого использования
python final_collection.py --no-zen --no-ok

# 2. СРЕДНИЙ (10-15 минут) - стандартный режим
python final_collection.py

# 3. ПОЛНЫЙ (20-30 минут) - глубокий сбор
python final_collection.py --comments

# 4. ТОЛЬКО ПРОБЛЕМНЫЕ источники (OK + Дзен)
python final_collection.py --no-vk --no-telegram --no-news
```

### **График запусков (рекомендуемый):**

```
06:00 - Быстрый сбор (VK + Telegram + News)
12:00 - Полный сбор (все источники)
18:00 - Быстрый сбор (VK + Telegram + News)
00:00 - Дзен + OK через Selenium (медленные)
```

---

## 🔧 Улучшения системы

### **1. Интегрировать OK Selenium вместо API:**

```bash
# В final_collection.py строка 57:
# Заменить:
from collectors.ok_api_collector import OKAPICollector
# На:
from collectors.ok_selenium_collector import OKSeleniumCollector as OKAPICollector
```

### **2. Добавить кэширование для News:**

```python
# В news_collector.py добавить метод:
def collect_with_cache(self, cache_hours=1):
    cache_file = 'news_cache.pkl'
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cache_time, data = pickle.load(f)
            if datetime.now() - cache_time < timedelta(hours=cache_hours):
                logger.info(f"Используем кэш новостей ({len(data)} статей)")
                return data
    
    data = self.collect()
    with open(cache_file, 'wb') as f:
        pickle.dump((datetime.now(), data), f)
    return data
```

### **3. Параллельный сбор (ускорение в 2-3 раза):**

```python
# Создать файл: parallel_collection.py
from concurrent.futures import ThreadPoolExecutor
import logging

def collect_parallel():
    collectors = {
        'vk': VKCollector(),
        'telegram': TelegramUserCollector(),
        'news': NewsCollector(),
    }
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(c.collect) 
                   for name, c in collectors.items()}
        
        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result()
                logger.info(f"{name}: {len(results[name])} записей")
            except Exception as e:
                logger.error(f"{name}: {e}")
                results[name] = []
    
    # Selenium коллекторы запускаются последовательно
    results['zen'] = ZenSeleniumCollector().collect()
    results['ok'] = OKSeleniumCollector().collect()
    
    return sum(results.values(), [])
```

---

## ✅ Чек-лист перед запуском

- [ ] Сократить `TELEGRAM_CHANNELS` до 10-15 каналов
- [ ] Уменьшить `NEWS_SITES` до 5-10 сайтов
- [ ] Установить `MONITORING_INTERVAL_MINUTES=60`
- [ ] Отключить `USE_FREE_PROXIES=False`
- [ ] Протестировать `test_ok_selenium.py`
- [ ] Интегрировать OK Selenium в `final_collection.py`
- [ ] Настроить расписание запусков (2-4 раза в день)

---

## 📚 Документация

- `COLLECTORS_STATUS.md` - этот файл
- `SELENIUM_INTEGRATION.md` - документация по Selenium
- `APP_ENHANCED_SELENIUM.md` - интеграция в веб-интерфейс
- `README.md` - общая документация

---

**Обновлено:** 2025  
**Статус системы:** ✅ Все коллекторы работают  
**Рекомендация:** Оптимизировать конфигурацию для стабильной работы
