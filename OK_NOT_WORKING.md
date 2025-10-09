# ❌ Почему OK Selenium не работает

## 🔍 Проблемы

### **1. SSL ошибки (не критично)**
```
ERROR:net\socket\ssl_client_socket_impl.cc:902] handshake failed
```
**Это нормально!** Chrome показывает эти ошибки, но они не мешают работе Selenium.

---

### **2. OK не находит посты (критично)**

**Причины:**

#### **A. Проблема с кодировкой ключевых слов**
```python
Keywords: ['��� ������ ��', '��� ������', ...]  # Кракозябры!
```

**Решение:**
```python
# В ok_selenium_collector.py изменить:
# Вместо:
self.keywords = Config.COMPANY_KEYWORDS

# Использовать hardcoded:
self.keywords = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт']
```

#### **B. OK.ru блокирует поиск**
OK.ru может блокировать автоматические поиски через Selenium.

#### **C. Нет релевантных постов**
В OK просто может не быть постов с ключевыми словами за последние дни.

---

## ✅ Решения

### **Решение 1: Использовать OK API вместо Selenium (рекомендуется)**

OK API работает стабильно, хоть и дает меньше данных:

```bash
# В final_collection.py использовать API:
python final_collection.py --no-ok  # Отключить OK совсем

# Или оставить API (он включен по умолчанию если Selenium не работает)
```

**Что даст OK API:**
- Посты из вашей личной ленты
- Посты из групп в `OK_GROUP_IDS`
- 5-20 постов (меньше чем Selenium, но стабильно)

---

### **Решение 2: Добавить группы OK вручную**

```env
# В .env добавьте ID групп Нижнего Новгорода:
OK_GROUP_IDS=70000002593972,53038442348715,57917644668973,53546227925099

# Как найти ID группы:
# 1. Откройте группу на ok.ru (например "Новости Нижнего Новгорода")
# 2. Скопируйте ID из URL: ok.ru/group/12345678
# 3. Добавьте в .env
```

**Затем:**
```bash
python final_collection.py
```

OK API будет собирать из этих групп.

---

### **Решение 3: Исправить кодировку в ok_selenium_collector.py**

Отредактируйте файл `collectors/ok_selenium_collector.py`:

```python
# Строка 12-13:
def __init__(self, sentiment_analyzer=None):
    # Вместо:
    # self.keywords = Config.COMPANY_KEYWORDS
    
    # Использовать hardcoded:
    self.keywords = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт', 'ТНС']
    self.driver = None
    self.sentiment_analyzer = sentiment_analyzer
```

**Затем протестировать:**
```bash
python test_ok_selenium.py
```

---

### **Решение 4: Отключить OK полностью**

Если OK не критичен, просто отключите:

```bash
python final_collection.py --no-ok
```

Вы всё равно получите 100-250 записей из:
- VK (50-100)
- Telegram (100-150 из 93 каналов)
- News (20-50)
- Дзен (10-20 если работает)

---

## 📊 Сравнение вариантов OK

| Метод | Данных | Стабильность | Рекомендация |
|-------|--------|--------------|--------------|
| **OK API** | 5-20 | ✅ Высокая | ⭐ Использовать |
| **OK Selenium** | 20-50 | ⚠️ Средняя | Если исправить |
| **Без OK** | 0 | ✅ Без проблем | Если не нужен |

---

## 🚀 Рекомендованная конфигурация

### **Вариант 1: OK API + группы (лучший)**

```env
# В .env:
OK_GROUP_IDS=70000002593972,53038442348715,57917644668973
```

```bash
python final_collection.py
```

**Что получите:**
- VK: 50-100
- Telegram: 100-150
- News: 20-50
- Дзен: 10-20
- OK API: 5-20
- **Итого: 185-340 записей**

---

### **Вариант 2: Без OK (самый быстрый)**

```bash
python final_collection.py --no-ok
```

**Время:** 15-20 минут  
**Данных:** 180-320 записей

---

### **Вариант 3: Исправить OK Selenium**

1. Исправить кодировку (см. Решение 3)
2. Протестировать: `python test_ok_selenium.py`
3. Если работает: `python final_collection.py`

---

## 🔧 Быстрое исправление кодировки

```bash
# Скопируйте и вставьте в PowerShell:
$file = "C:\tns_pars\collectors\ok_selenium_collector.py"
$content = Get-Content $file -Encoding UTF8 -Raw
$content = $content -replace "self.keywords = Config.COMPANY_KEYWORDS", "self.keywords = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт', 'ТНС']"
Set-Content $file $content -Encoding UTF8
Write-Host "OK Selenium fixed!"
```

**Затем тест:**
```bash
python test_ok_selenium.py
```

---

## ✅ Итог

**Рекомендация:** 
1. **Используйте OK API** (работает стабильно)
2. **Добавьте группы** в `OK_GROUP_IDS`
3. **Или отключите OK:** `python final_collection.py --no-ok`

**OK Selenium** - необязателен, API дает достаточно данных.

---

**Обновлено:** 2025-01-09  
**Статус:** ⚠️ OK Selenium имеет проблемы, используйте OK API  
**Рекомендация:** `python final_collection.py` (будет использовать API автоматически)
