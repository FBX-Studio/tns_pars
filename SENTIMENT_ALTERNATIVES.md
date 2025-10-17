# Альтернативы Dostoevsky для анализа тональности

## ✅ Текущее состояние
Ваш проект **уже имеет встроенный fallback** - если `dostoevsky` недоступен, используется простой rule-based анализатор на основе словарей (см. `analyzers/sentiment_analyzer.py`). Он работает сейчас и содержит специфичные для ТНС Энерго ключевые слова.

## 🔄 Альтернативы для установки

### 1. ⭐ **TextBlob (с переводом)** - Простое решение
**Установка:**
```bash
pip install textblob textblob-ru
python -m textblob.download_corpora
```

**Плюсы:**
- Простая установка (без C++ компиляции)
- Работает для русского и английского
- Легкий API

**Минусы:**
- Требует перевода для точности на русском
- Медленнее dostoevsky

**Пример использования:**
```python
from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # от -1 до 1
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    return 'neutral'
```

---

### 2. ⭐⭐ **VADER (с переводом)** - Для социальных сетей
**Установка:**
```bash
pip install vaderSentiment googletrans==3.1.0a0
```

**Плюсы:**
- Отлично для соцсетей (эмодзи, сленг)
- Без компиляции
- Быстрый

**Минусы:**
- Для английского (нужен перевод)
- Перевод может снизить точность

**Пример:**
```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googletrans import Translator

translator = Translator()
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    # Переводим на английский
    translated = translator.translate(text, src='ru', dest='en').text
    scores = analyzer.polarity_scores(translated)
    return scores['compound']  # от -1 до 1
```

---

### 3. ⭐⭐⭐ **RuSentiment** - Русский язык, легкая установка
**Установка:**
```bash
pip install transformers torch
```

**Плюсы:**
- Нативно для русского
- Без компиляции C++
- Хорошая точность

**Минусы:**
- Требует ~500 MB для модели
- Медленнее rule-based

**Пример:**
```python
from transformers import pipeline

classifier = pipeline("sentiment-analysis", 
                     model="blanchefort/rubert-base-cased-sentiment")

def analyze_sentiment(text):
    result = classifier(text[:512])[0]  # max 512 символов
    label = result['label']  # POSITIVE, NEGATIVE, NEUTRAL
    score = result['score']
    return label.lower(), score
```

---

### 4. ⭐⭐⭐⭐ **Natasha** - Современное NLP для русского
**Установка:**
```bash
pip install natasha razdel
```

**Плюсы:**
- Специально для русского
- Без компиляции
- Легковесная

**Минусы:**
- Нет встроенного sentiment analysis
- Нужно строить свой классификатор

---

### 5. 🚫 **Dostoevsky (для информации)**
**Требует:**
- Microsoft Visual C++ 14.0+ Build Tools
- ИЛИ Python 3.11/3.12 (есть pre-built wheels)

**Установка Build Tools:**
1. Скачать: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Установить "Desktop development with C++"
3. Затем: `pip install dostoevsky`

---

## 📊 Рекомендации

### Для вашего проекта (ТНС Энерго):

**1. Оставить как есть (Rule-Based) ✅ РЕКОМЕНДУЕТСЯ**
- У вас уже есть специализированный анализатор
- Содержит специфичные для энергосбыта слова
- Работает без зависимостей
- Быстрый и предсказуемый

**2. Добавить RuSentiment как опцию**
```bash
pip install transformers torch
```
Модифицировать `sentiment_analyzer.py`:
```python
def __init__(self):
    try:
        # Попытка 1: Dostoevsky
        from dostoevsky.tokenization import RegexTokenizer
        # ...
    except:
        try:
            # Попытка 2: RuSentiment
            from transformers import pipeline
            self.model = pipeline("sentiment-analysis", 
                                 model="blanchefort/rubert-base-cased-sentiment")
            self.use_transformers = True
        except:
            # Попытка 3: Rule-based (fallback)
            self._init_simple_analyzer()
```

**3. Улучшить Rule-Based анализатор**
- Добавить больше специфичных слов
- Использовать веса для слов
- Учитывать отрицания (не хорошо = плохо)

---

## 💡 Итоговые рекомендации

### Быстрое решение (5 минут):
**Ничего не делать** - ваш rule-based анализатор уже работает!

### Среднее решение (30 минут):
**Установить RuSentiment:**
```bash
pip install transformers torch
```

### Полное решение (1-2 часа):
**Установить Visual C++ Build Tools + Dostoevsky:**
1. Установить Build Tools
2. `pip install dostoevsky`
3. `python -m dostoevsky download fasttext-social-network-model`

---

## 🧪 Тестирование текущего анализатора

Создайте файл `test_sentiment.py`:
```python
from analyzers.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()

test_texts = [
    "Отличный сервис ТНС Энерго, быстро помогли!",
    "Ужасная компания, постоянные проблемы",
    "Передал показания счетчика",
]

for text in test_texts:
    result = analyzer.analyze(text)
    print(f"Текст: {text}")
    print(f"Результат: {result}")
    print("-" * 50)
```

Запустите:
```bash
python test_sentiment.py
```

Если работает - **дополнительных действий не требуется!**
