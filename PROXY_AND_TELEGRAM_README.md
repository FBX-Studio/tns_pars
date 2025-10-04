# 🚀 Парсинг через прокси и Telegram User API

## 📋 Что было добавлено

### ✅ Поддержка прокси для всех коллекторов:
- **Web scraping** (BeautifulSoup) - HTTP/HTTPS/SOCKS/Tor
- **VK API** - HTTP/HTTPS/SOCKS/Tor
- **Telegram User API** (Telethon) - SOCKS5/Tor

### ✅ Поддержка Tor Browser:
- Простая настройка через `.env`
- Автоматическая анонимизация всего трафика
- Работает на Windows/Linux/Mac

### ✅ Telegram User API (Telethon):
- Парсинг любых публичных каналов
- Не требуется добавление бота
- Доступ к истории сообщений

---

## 🎯 Быстрый старт

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Настройте Tor Browser (опционально, но рекомендуется)

**Скачайте Tor Browser:**
- https://www.torproject.org/download/

**Запустите Tor Browser и добавьте в `.env`:**

Windows:
```bash
USE_TOR=True
TOR_PROXY=socks5h://127.0.0.1:9150
TOR_HOST=127.0.0.1
TOR_PORT=9150
```

Linux/Mac:
```bash
USE_TOR=True
TOR_PROXY=socks5h://127.0.0.1:9050
TOR_HOST=127.0.0.1
TOR_PORT=9050
```

### 3. Настройте Telegram User API

**Получите API credentials на https://my.telegram.org:**

1. Войдите с номером телефона
2. API Development Tools → Create application
3. Скопируйте `api_id` и `api_hash`

**Добавьте в `.env`:**
```bash
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef
TELEGRAM_PHONE=+79991234567
TELEGRAM_CHANNELS=@breakingmash,@rbc_news,@nnov_news
```

### 4. Первая авторизация в Telegram

```bash
python setup_telegram.py
```

Введите код, который придет в Telegram.

### 5. Запустите парсинг

```bash
python run.py
```

✅ **Готово!** Парсинг работает через Tor и собирает данные из Telegram каналов.

---

## 📚 Подробные инструкции

### Парсинг через прокси:
📄 **PROXY_SETUP_QUICK_GUIDE.md** - полная инструкция по настройке прокси

Включает:
- Настройка Tor Browser
- Использование бесплатных прокси
- Платные SOCKS5 прокси
- Устранение проблем

### Парсинг Telegram:
📄 **TELEGRAM_USER_API_GUIDE.md** - детальная инструкция по Telegram User API

Включает:
- Получение API credentials
- Первая авторизация
- Какие каналы можно парсить
- Использование прокси для Telegram
- Решение типичных проблем

---

## ⚙️ Примеры конфигураций

### Конфигурация 1: Только Tor (рекомендуется)

```bash
# .env
USE_TOR=True
TOR_PROXY=socks5h://127.0.0.1:9050
TOR_HOST=127.0.0.1
TOR_PORT=9050

TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash_here
TELEGRAM_PHONE=+79991234567
TELEGRAM_CHANNELS=@breakingmash,@nnov_news
```

**Использует Tor для:** Web scraping, VK, Telegram

---

### Конфигурация 2: Без прокси

```bash
# .env
# Просто не указывайте настройки прокси

TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash_here
TELEGRAM_PHONE=+79991234567
TELEGRAM_CHANNELS=@breakingmash,@nnov_news
```

**Парсинг через ваш обычный IP**

---

### Конфигурация 3: Платный SOCKS5 прокси

```bash
# .env
SOCKS_PROXY=socks5://user:pass@proxy.example.com:1080

TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash_here
TELEGRAM_PHONE=+79991234567
TELEGRAM_CHANNELS=@breakingmash,@nnov_news
```

---

## 🔍 Какие каналы Telegram можно парсить?

### ✅ Можно:
- Любые публичные каналы (@channel_name)
- Группы, в которых вы состоите
- Новостные каналы

### ❌ Нельзя:
- Закрытые/приватные каналы (без приглашения)
- Каналы, где вас забанили

### 📌 Примеры каналов для мониторинга:

**Новости Нижнего Новгорода:**
```bash
TELEGRAM_CHANNELS=@nnov_news,@nizhnynovgorod_official,@life_nn,@nnrus52
```

**Общероссийские новости:**
```bash
TELEGRAM_CHANNELS=@breakingmash,@rbc_news,@rian_ru,@tass_agency
```

---

## 🛠️ Устранение проблем

### Проблема: Tor не подключается

✅ **Решение:**
1. Убедитесь, что Tor Browser запущен
2. Проверьте порт в `.env`: Windows - 9150, Linux - 9050
3. Перезапустите Tor Browser

---

### Проблема: Telegram код не приходит

✅ **Решение:**
1. Проверьте номер телефона в `.env` (формат: +79991234567)
2. Убедитесь, что номер зарегистрирован в Telegram
3. Проверьте Telegram на вашем телефоне

---

### Проблема: FloodWaitError в Telegram

✅ **Решение:**
1. Подождите указанное время (обычно несколько минут)
2. Используйте Tor/прокси
3. Уменьшите частоту мониторинга в `.env`:
   ```bash
   MONITORING_INTERVAL_MINUTES=60
   ```

---

### Проблема: Прокси не работает

✅ **Решение:**
1. Проверьте формат: `socks5://host:port` или `http://host:port`
2. Убедитесь, что прокси активен
3. Попробуйте другой прокси

---

## 📊 Что изменилось в коде

### Файлы, которые были обновлены:

1. **`config.py`** - добавлены настройки прокси и Tor
2. **`collectors/web_collector.py`** - поддержка прокси для web scraping
3. **`collectors/vk_collector.py`** - поддержка прокси для VK API
4. **`collectors/telegram_user_collector.py`** - поддержка прокси для Telegram
5. **`requirements.txt`** - добавлены telethon, PySocks
6. **`.env.example`** - примеры настроек прокси и Telegram

### Новые файлы:

1. **`TELEGRAM_USER_API_GUIDE.md`** - детальная инструкция по Telegram
2. **`PROXY_SETUP_QUICK_GUIDE.md`** - инструкция по настройке прокси
3. **`PROXY_AND_TELEGRAM_README.md`** - этот файл (краткая сводка)

---

## 🎓 Дополнительные материалы

### Официальная документация:

- **Tor Project**: https://www.torproject.org/
- **Telethon**: https://docs.telethon.dev/
- **Telegram API**: https://core.telegram.org/api
- **My Telegram**: https://my.telegram.org/

### Списки бесплатных прокси:

- https://www.freeproxylists.net/
- https://hidemy.name/ru/proxy-list/
- https://www.proxyscrape.com/free-proxy-list

---

## ⚠️ Важные замечания

### Безопасность:
- Не делитесь своими API credentials
- Не коммитьте `.env` в Git
- Храните `telegram_session.session` в безопасности
- Используйте прокси/Tor для анонимности

### Лимиты:
- **Telegram**: не более 20 запросов/сек
- **VK API**: ограничения по количеству запросов
- **Веб-сайты**: могут использовать защиту от ботов

### Рекомендации:
- Начните с Tor Browser
- Делайте паузы между запросами
- Не парсите слишком часто (интервал 30+ минут)
- Соблюдайте Terms of Service каждого сервиса

---

## 📞 Поддержка

Если у вас возникли вопросы:

1. Прочитайте **TELEGRAM_USER_API_GUIDE.md**
2. Прочитайте **PROXY_SETUP_QUICK_GUIDE.md**
3. Проверьте раздел "Устранение проблем"
4. Посмотрите логи в консоли

---

## ✅ Чек-лист для запуска

- [ ] Установлены зависимости: `pip install -r requirements.txt`
- [ ] Скачан и запущен Tor Browser
- [ ] Настроен `.env` с Tor параметрами
- [ ] Получены API credentials на my.telegram.org
- [ ] Добавлены в `.env`: API_ID, API_HASH, PHONE
- [ ] Выполнена первая авторизация: `python setup_telegram.py`
- [ ] Указаны каналы в `TELEGRAM_CHANNELS`
- [ ] Запущен парсинг: `python run.py`

**Готово!** Система работает.

---

**Версия**: 1.0  
**Дата обновления**: 2024  
**См. также**: README.md, PROJECT_SUMMARY.txt
