"""
Тестирование анализатора тональности
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from analyzers.sentiment_analyzer import SentimentAnalyzer

def test_sentiment_analyzer():
    print("\n" + "="*60)
    print("ТЕСТ АНАЛИЗАТОРА ТОНАЛЬНОСТИ")
    print("="*60)
    
    analyzer = SentimentAnalyzer()
    
    if analyzer.use_dostoevsky:
        print("✓ Используется Dostoevsky")
    else:
        print("✓ Используется Rule-Based анализатор (встроенный)")
    
    test_cases = [
        # Позитивные
        ("Отличный сервис ТНС Энерго, быстро помогли!", "positive"),
        ("Спасибо за оперативное подключение электричества", "positive"),
        ("Очень довольны работой компании, рекомендуем!", "positive"),
        
        # Негативные
        ("Ужасная компания, постоянные проблемы с оплатой", "negative"),
        ("Не могу дозвониться, поддержка не отвечает", "negative"),
        ("Завышенные счета, грабеж какой-то!", "negative"),
        
        # Нейтральные
        ("Передал показания счетчика", "neutral"),
        ("Подключение электричества в новом доме", "neutral"),
        ("Тариф изменился с 1 января", "neutral"),
    ]
    
    print("\n" + "-"*60)
    print("ТЕСТОВЫЕ ПРИМЕРЫ:")
    print("-"*60)
    
    correct = 0
    total = len(test_cases)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        result = analyzer.analyze(text)
        predicted = result.get('sentiment_label', 'neutral')
        is_correct = predicted == expected
        
        if is_correct:
            correct += 1
            status = "✓"
        else:
            status = "✗"
        
        print(f"\n{i}. {status} Текст: {text[:60]}...")
        print(f"   Ожидалось: {expected}")
        print(f"   Получено: {predicted}")
        
        if 'sentiment_score' in result:
            print(f"   Score: {result['sentiment_score']:.3f}")
        if 'confidence' in result:
            print(f"   Уверенность: {result['confidence']:.3f}")
    
    print("\n" + "="*60)
    print(f"ТОЧНОСТЬ: {correct}/{total} ({100*correct/total:.1f}%)")
    print("="*60)
    
    return analyzer

if __name__ == "__main__":
    analyzer = test_sentiment_analyzer()
    
    print("\n" + "-"*60)
    print("ВАШИ ТЕКСТЫ ДЛЯ ПРОВЕРКИ:")
    print("-"*60)
    print("Введите текст для анализа (или 'exit' для выхода)")
    
    while True:
        try:
            text = input("\nТекст: ").strip()
            if text.lower() in ['exit', 'quit', 'q', 'выход']:
                break
            
            if not text:
                continue
            
            result = analyzer.analyze(text)
            print(f"  → Тональность: {result.get('sentiment_label', 'N/A')}")
            print(f"  → Score: {result.get('sentiment_score', 0):.3f}")
            if 'confidence' in result:
                print(f"  → Уверенность: {result['confidence']:.3f}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Ошибка: {e}")
    
    print("\nЗавершение тестирования.")
