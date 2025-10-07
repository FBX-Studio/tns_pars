"""
Тест ML моделей для анализа тональности
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from analyzers.ml_sentiment_analyzer import MLSentimentAnalyzer
import time

print("="*70)
print("ТЕСТ ML МОДЕЛЕЙ ДЛЯ АНАЛИЗА ТОНАЛЬНОСТИ")
print("="*70)

# Тестовые тексты
test_texts = {
    'positive': [
        "ТНС энерго отлично справляется с обслуживанием, персонал вежливый и профессиональный!",
        "Быстро решили проблему с электричеством, спасибо большое!",
        "Рекомендую ТНС энерго, качественный сервис и адекватные тарифы."
    ],
    'negative': [
        "ТНС энерго ужасная компания, постоянные отключения и грубые сотрудники.",
        "Не рекомендую, мошенники! Насчитали лишние деньги.",
        "Кошмар, неделю без света, никто не помогает. Безобразие!"
    ],
    'neutral': [
        "ТНС энерго - энергоснабжающая компания в Нижнем Новгороде.",
        "Оплатил счет за электроэнергию в офисе ТНС энерго.",
        "Информация о тарифах ТНС энерго доступна на сайте."
    ]
}

print("\n📋 Инициализация анализатора...")
print("-"*70)

try:
    # Автоматический выбор лучшей модели
    analyzer = MLSentimentAnalyzer(model_type='auto')
    
    model_info = analyzer.get_model_info()
    print(f"✓ Модель: {model_info['model_type']}")
    print(f"✓ Описание: {model_info['description']}")
    print(f"✓ Загружена: {'Да' if model_info['model_loaded'] else 'Нет'}")
    
except Exception as e:
    print(f"✗ Ошибка инициализации: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("ТЕСТИРОВАНИЕ НА ПРИМЕРАХ")
print("="*70)

def sentiment_emoji(label):
    """Эмодзи для тональности"""
    if label == 'positive':
        return '😊 ПОЗИТИВНО'
    elif label == 'negative':
        return '😠 НЕГАТИВНО'
    else:
        return '😐 НЕЙТРАЛЬНО'

def score_bar(score):
    """Визуализация score"""
    normalized = (score + 1) / 2  # От 0 до 1
    bar_length = 20
    filled = int(normalized * bar_length)
    bar = '█' * filled + '░' * (bar_length - filled)
    return bar

total_tests = 0
correct = 0

for expected_sentiment, texts in test_texts.items():
    print(f"\n{'='*70}")
    print(f"ТЕСТ: Ожидаемая тональность = {expected_sentiment.upper()}")
    print('='*70)
    
    for i, text in enumerate(texts, 1):
        print(f"\n{i}. Текст:")
        print(f"   \"{text}\"")
        print()
        
        start_time = time.time()
        result = analyzer.analyze(text)
        elapsed = time.time() - start_time
        
        print(f"   Результат: {sentiment_emoji(result['sentiment_label'])}")
        print(f"   Score: {result['sentiment_score']:.3f} {score_bar(result['sentiment_score'])}")
        print(f"   Уверенность: {result['confidence']:.1%}")
        print(f"   Время: {elapsed*1000:.1f}ms")
        print(f"   Модель: {result['model']}")
        
        total_tests += 1
        if result['sentiment_label'] == expected_sentiment:
            correct += 1
            print("   ✓ Правильно")
        else:
            print(f"   ✗ Неправильно (ожидалось {expected_sentiment})")

print("\n" + "="*70)
print("ИТОГИ ТЕСТИРОВАНИЯ")
print("="*70)
print(f"Всего тестов: {total_tests}")
print(f"Правильно: {correct}")
print(f"Точность: {correct/total_tests*100:.1f}%")
print(f"Модель: {analyzer.model_type}")

print("\n" + "="*70)
print("СРАВНЕНИЕ МОДЕЛЕЙ")
print("="*70)

print("\nЕсли хотите протестировать другие модели:")
print()
print("# RuBERT (лучшая точность)")
print("analyzer = MLSentimentAnalyzer(model_type='rubert')")
print()
print("# Dostoevsky (быстрая)")
print("analyzer = MLSentimentAnalyzer(model_type='dostoevsky')")
print()
print("# VADER (для соцсетей)")
print("analyzer = MLSentimentAnalyzer(model_type='vader')")
print()
print("# TextBlob (простая)")
print("analyzer = MLSentimentAnalyzer(model_type='textblob')")
print()
print("# Словарный (fallback)")
print("analyzer = MLSentimentAnalyzer(model_type='dictionary')")

print("\n" + "="*70)
print("ИНТЕГРАЦИЯ В СИСТЕМУ")
print("="*70)
print("\nДля интеграции в систему мониторинга:")
print()
print("1. Откройте async_monitor_websocket.py")
print("2. Замените импорт:")
print("   from analyzers.sentiment_analyzer import SentimentAnalyzer")
print("   на:")
print("   from analyzers.ml_sentiment_analyzer import MLSentimentAnalyzer as SentimentAnalyzer")
print()
print("3. Перезапустите систему:")
print("   python app_enhanced.py")
print()
print("✅ ML модель будет автоматически использоваться!")

print("\n" + "="*70)
print("✅ ТЕСТ ЗАВЕРШЕН!")
print("="*70)
