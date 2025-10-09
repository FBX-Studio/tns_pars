# ❓ Почему нет данных из Дзена и Одноклассников

## 🔍 Диагностика проблемы

### **Проблема 1: OK Selenium не работает**

**Ошибка:** `[WinError 193] %1 не является приложением Win32`

**Причина:** ChromeDriver установлен неправильно или несовместим

---

## ✅ Решения

### **Вариант 1: Использовать API вместо Selenium (быстро)**

OK API работает, но дает меньше данных:

```bash
# В final_collection.py или run_collection_once.py временно отключить OK Selenium
# Система автоматически вернется к OK API
```

**Запустить:**
```bash
python final_collection.py
```

---

### **Вариант 2: Исправить ChromeDriver (рекомендуется)**

#### **Шаг 1: Проверить Chrome**
```bash
# Откройте Chrome и перейдите:
chrome://version/

# Запомните версию (например: 131.0.6778.86)
```

#### **Шаг 2: Удалить старый ChromeDriver**
```bash
# Удалите папку:
C:\Users\kiruh\.wdm\drivers\chromedriver
```

#### **Шаг 3: Переустановить ChromeDriver**
```bash
pip uninstall webdriver-manager
pip install webdriver-manager
```

#### **Шаг 4: Протестировать**
```bash
python test_ok_selenium.py
```

---

### **Вариант 3: Отключить Selenium источники временно**

```bash
# Собрать только работающие источники:
python final_collection.py --no-zen --no-ok

# Время: 10-15 минут
# Источники: VK, Telegram, News
```

---

## 📊 Почему нет данных?

### **Дзен (Яндекс.Дзен):**

**Причины:**
1. **ChromeDriver не работает** (та же ошибка что и OK)
2. **Нет статей с ключевыми словами** за последние дни
3. **Яндекс блокирует** (капча)

**Решение:**
```bash
# 1. Исправить ChromeDriver (см. выше)

# 2. Проверить ключевые слова
# В .env:
COMPANY_KEYWORDS=ТНС энерго НН,ТНС энерго,энергосбыт

# 3. Тест Дзена:
python test_zen_selenium.py
```

---

### **Одноклассники:**

**Причины:**
1. **OK Selenium не работает** (ChromeDriver)
2. **OK API очень ограничен** (нет публичного поиска)
3. **Нужно добавить группы** в OK_GROUP_IDS

**Решение:**

#### **Способ 1: Добавить группы OK вручную**

```env
# В .env добавьте ID групп Нижнего Новгорода:
OK_GROUP_IDS=70000002593972,53038442348715,57917644668973

# Как найти ID группы:
# 1. Откройте группу на ok.ru
# 2. Скопируйте ID из URL: ok.ru/group/12345678
# 3. Добавьте в .env
```

#### **Способ 2: Использовать OK API (ограниченно)**

OK API собирает только из:
- Вашей личной ленты (посты друзей)
- Указанных групп (OK_GROUP_IDS)

```bash
# Подпишитесь на новостные группы НН в OK.ru
# Затем запустите:
python final_collection.py
```

#### **Способ 3: Исправить OK Selenium**

```bash
# 1. Исправить ChromeDriver (см. выше)
# 2. Протестировать:
python test_ok_selenium.py
```

---

## 🔧 Быстрое исправление ChromeDriver

### **Windows (автоматически):**

```bash
# Удалить кэш:
rmdir /S /Q "%USERPROFILE%\.wdm"

# Переустановить:
pip install --force-reinstall webdriver-manager

# Тест:
python test_zen_selenium.py
```

---

### **Вручную (если автоматически не работает):**

#### **Шаг 1: Скачать ChromeDriver**

1. Узнайте версию Chrome: `chrome://version/`
2. Скачайте подходящий ChromeDriver:
   - https://googlechromelabs.github.io/chrome-for-testing/
   - Выберите версию = версии Chrome
   - Скачайте `chromedriver-win64.zip`

#### **Шаг 2: Установить**

```bash
# 1. Распакуйте chromedriver.exe
# 2. Скопируйте в C:\Windows\System32\
# Или в папку Python: C:\Python\Scripts\
```

#### **Шаг 3: Проверить**

```bash
chromedriver --version
# Должно показать версию
```

#### **Шаг 4: Изменить код**

В `collectors/ok_selenium_collector.py` и `collectors/zen_selenium_collector.py`:

```python
# Было:
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=chrome_options)

# Стало (использовать системный chromedriver):
self.driver = webdriver.Chrome(options=chrome_options)
```

---

## 📈 Что работает сейчас?

| Источник | Статус | Данных за запуск |
|----------|--------|------------------|
| **VK** | ✅ Работает | 50-100 |
| **Telegram** | ✅ Работает | 100-200 (93 канала) |
| **News** | ✅ Работает | 20-50 |
| **Дзен** | ⚠️ ChromeDriver | 0 (нужно исправить) |
| **OK** | ⚠️ ChromeDriver | 0 (нужно исправить) |

---

## 🚀 Рекомендации

### **Краткосрочное решение (сейчас):**

```bash
# Собирать без Дзена и OK:
python final_collection.py --no-zen --no-ok

# Время: 10-15 минут
# Данных: 100-300 записей
```

---

### **Долгосрочное решение:**

1. ✅ Исправить ChromeDriver (см. инструкцию выше)
2. ✅ Добавить группы OK в `OK_GROUP_IDS`
3. ✅ Протестировать Selenium коллекторы:
   ```bash
   python test_zen_selenium.py
   python test_ok_selenium.py
   ```

---

## 🔍 Проверка после исправления

### **Тест 1: ChromeDriver**
```bash
chromedriver --version
# Должен показать версию
```

### **Тест 2: Selenium**
```bash
python -c "from selenium import webdriver; driver = webdriver.Chrome(); print('OK'); driver.quit()"
```

### **Тест 3: Дзен**
```bash
python test_zen_selenium.py
# Должен найти 5-20 статей
```

### **Тест 4: OK**
```bash
python test_ok_selenium.py
# Должен найти 10-30 постов
```

### **Тест 5: Полный сбор**
```bash
python final_collection.py
# Должны быть данные из всех источников
```

---

## 📚 Дополнительно

### **Альтернатива Selenium - использовать API:**

Если ChromeDriver не исправляется, можно:

1. **OK:** Добавить больше групп в `OK_GROUP_IDS`
2. **Дзен:** Использовать RSS или ручной парсинг

Или просто собирать без этих источников:
```bash
python final_collection.py --no-zen --no-ok
```

VK + Telegram + News дают достаточно данных (100-300 записей).

---

**Обновлено:** 2025-01-09  
**Статус:** ⚠️ Требуется исправить ChromeDriver  
**Решение:** См. инструкции выше
