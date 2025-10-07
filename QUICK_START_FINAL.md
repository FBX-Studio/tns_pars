# ⚡ Quick Start - Финальная версия

## 🎯 **ГОТОВЫЕ КОМАНДЫ:**

### **1. Полный сбор (РЕКОМЕНДУЕТСЯ)**
```bash
python final_collection.py --zen-selenium
```
**Собирает:** VK + Telegram + Новости + Дзен (Selenium) + OK  
**Время:** 5-7 минут  
**Надежность:** ✅ Высокая

---

### **2. Только Дзен (Selenium)**
```bash
python collect_zen_selenium.py
```
**Собирает:** Только Яндекс.Дзен через Selenium  
**Время:** 2-3 минуты  
**Надежность:** ✅ 100% (обходит капчу)

---

### **3. Быстрый сбор (без Дзена)**
```bash
python collect_safe_sources.py
```
**Собирает:** VK + Новости  
**Время:** 1-2 минуты  
**Надежность:** ✅ 100%

---

### **4. Тестирование Дзена**
```bash
python test_zen_selenium.py
```
**Тестирует** Selenium парсер без сохранения в БД

---

## 📊 **ПРОВЕРКА РЕЗУЛЬТАТОВ:**

```bash
python check_status.py
```

Показывает:
- Сколько записей в базе
- Распределение по источникам
- Последние добавленные

---

## 🔧 **НАСТРОЙКИ:**

### **В .env:**
```env
# Дзен через Selenium (не требует прокси)
USE_TOR=False
USE_FREE_PROXIES=True

# Интервал мониторинга
MONITORING_INTERVAL_MINUTES=240  # 4 часа
```

---

## ⚠️ **ВАЖНО:**

### **Telegram:**
- ⏰ Если FloodWait - подождите 3-4 часа
- Используйте `--no-telegram` если заблокирован

### **Яндекс.Дзен:**
- ✅ **Используйте Selenium** (флаг `--zen-selenium`)
- ❌ Обычный метод показывает капчу

### **Частота:**
- Запускайте **максимум 2-3 раза в день**
- Не чаще чем раз в 4 часа

---

## 📋 **ПРИМЕРЫ:**

### **Утренний сбор (09:00):**
```bash
python collect_safe_sources.py
```
Быстро: VK + Новости

### **Вечерний сбор (18:00):**
```bash
python collect_zen_selenium.py
```
Дзен через Selenium

### **Полный сбор (раз в день):**
```bash
python final_collection.py --zen-selenium --no-ok
```
Всё кроме OK

### **С комментариями (раз в неделю):**
```bash
python final_collection.py --zen-selenium --comments
```
Всё + комментарии

---

## 🎯 **ЧТО РАБОТАЕТ:**

| Источник | Команда | Время | Статус |
|----------|---------|-------|--------|
| **Дзен (Selenium)** | `python collect_zen_selenium.py` | 2-3 мин | ✅ Работает |
| **VK + Новости** | `python collect_safe_sources.py` | 1-2 мин | ✅ Работает |
| **Полный сбор** | `python final_collection.py --zen-selenium` | 5-7 мин | ✅ Работает |

---

## 📚 **ДОКУМЕНТАЦИЯ:**

- `FINAL_STATUS.md` - полный статус системы
- `SELENIUM_INTEGRATION.md` - интеграция Selenium
- `SELENIUM_SUCCESS.md` - результаты тестов
- `QUICK_START_FINAL.md` - эта шпаргалка

---

## ✅ **ГОТОВО!**

**Система полностью рабочая и готова к использованию!**

Используйте:
```bash
python collect_zen_selenium.py
```

Для ежедневного сбора из Яндекс.Дзен! 🚀
