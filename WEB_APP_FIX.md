# 🔧 Исправление ошибки веб-приложения

## ❌ Ошибка: `TypeError: Failed to fetch` / `ERR_CONNECTION_RESET`

Эта ошибка возникает когда:
1. Сервер перезагружается слишком часто
2. WebSocket соединения зависают
3. Много TIME_WAIT соединений

---

## ✅ Решение

### **Вариант 1: Быстрое исправление (рекомендуется)**

```bash
# 1. Остановите все процессы Python
taskkill /F /IM python.exe

# 2. Подождите 5 секунд

# 3. Запустите заново
python app_enhanced.py
```

---

### **Вариант 2: Использовать простое приложение без WebSocket**

Если WebSocket вызывает проблемы, используйте обычное приложение:

```bash
# Вместо app_enhanced.py используйте app.py (без WebSocket)
python app.py
```

**Откройте:** `http://localhost:5000`

---

### **Вариант 3: Использовать скрипт исправления**

```bash
python fix_web_app.py
```

Этот скрипт автоматически:
- ✓ Остановит зависшие процессы
- ✓ Проверит доступность модулей
- ✓ Перезапустит приложение

---

### **Вариант 4: Использовать командную строку (вместо веб-интерфейса)**

Если веб-интерфейс не нужен, используйте прямой запуск:

```bash
# Полный сбор
python final_collection.py

# Быстрый сбор
python final_collection.py --no-zen --no-ok

# С комментариями
python final_collection.py --comments
```

---

## 🔍 Диагностика

### **Проверить, занят ли порт 5000:**

```bash
netstat -ano | findstr :5000
```

**Если порт занят:**
```bash
# Найдите PID процесса (последний столбец)
# Остановите процесс:
taskkill /F /PID <PID>
```

---

### **Проверить доступность модулей:**

```bash
python -c "from flask import Flask; from flask_socketio import SocketIO; print('OK')"
```

**Если ошибка:**
```bash
pip install flask flask-socketio
```

---

### **Проверить базу данных:**

```bash
python -c "from models import Review; from app import app; app.app_context().push(); print(f'Записей: {Review.query.count()}')"
```

---

## 🚀 Альтернативные способы запуска

### **1. Использовать Gunicorn (Linux/Mac):**

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet app_enhanced:app
```

### **2. Использовать Waitress (Windows):**

```bash
pip install waitress
waitress-serve --host 0.0.0.0 --port 5000 app_enhanced:app
```

### **3. Изменить порт:**

В `.env`:
```env
FLASK_PORT=8000  # Вместо 5000
```

Затем:
```bash
python app_enhanced.py
# Откройте: http://localhost:8000
```

---

## ⚙️ Настройка для стабильности

### **Отключить auto-reload в production:**

В `app_enhanced.py` (в конце файла):
```python
if __name__ == '__main__':
    socketio.run(
        app,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=False,  # Было True - отключить для production
        use_reloader=False  # Отключить auto-reload
    )
```

### **Увеличить timeout для WebSocket:**

В `app_enhanced.py` (после создания socketio):
```python
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=120,  # Добавить
    ping_interval=25   # Добавить
)
```

---

## 📝 Логи для отладки

### **Включить подробные логи:**

```bash
set FLASK_ENV=development
set FLASK_DEBUG=1
python app_enhanced.py
```

### **Сохранить логи в файл:**

```bash
python app_enhanced.py > app.log 2>&1
```

---

## ✅ Чек-лист после исправления

- [ ] Все процессы Python остановлены
- [ ] Порт 5000 свободен
- [ ] Модули Flask и SocketIO установлены
- [ ] База данных доступна
- [ ] Приложение запускается без ошибок
- [ ] Браузер может подключиться

---

## 🆘 Если ничего не помогло

### **Используйте командную строку вместо веб-интерфейса:**

```bash
# Это работает всегда:
python final_collection.py
```

### **Или создайте issue с логами:**

```bash
# Соберите информацию:
python --version
pip list | findstr flask
netstat -ano | findstr :5000
```

---

## 📚 Документация

- `START_HERE.md` - быстрый старт
- `TELEGRAM_OK_IMPROVEMENTS.md` - улучшения коллекторов
- `COLLECTORS_STATUS.md` - статус всех коллекторов

---

**Обновлено:** 2025-01-09  
**Статус:** ✅ Решение найдено  
**Рекомендация:** Используйте Вариант 1 или командную строку
