"""
Тестирование анализатора тональности с RuSentiment
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from analyzers.sentiment_analyzer import SentimentAnalyzer
import time

def test_rusentiment_analyzer():
    print("\n" + "="*70)
    print("ТЕСТ АНАЛИЗАТОРА ТОНАЛЬНОСТИ С RuSentiment")
    print("="*70)
    
    print("\nИнициализация анализатора...")
    start_time = time.time()
    analyzer = SentimentAnalyzer()
    init_time = time.time() - start_time
    
    # Получаем информацию об анализаторе
    info = analyzer.get_analyzer_info()
    
    print(f"\n{'='*70}")
    print(f"ИСПОЛЬЗУЕМЫЙ АНАЛИЗАТОР: {info['name']}")
    print(f"{'='*70}")
    print(f"  Тип:         {info['type']}")
    print(f"  Модель:      {info['model']}")
    print(f"  Язык:        {info['language']}")
    print(f"  Точность:    {info['accuracy']}")
    print(f"  Скорость:    {info['speed']}")
    print(f"  Описание:    {info['description']}")
    print(f"  Время инициализации: {init_time:.2f} сек")
    print(f"{'='*70}")
    
    test_cases = [
        # Позитивные
        ("Отличный сервис ТНС Энерго, быстро помогли!", "positive"),
        ("Спасибо за оперативное подключение электричества", "positive"),
        ("Очень довольны работой компании, рекомендуем!", "positive"),
        ("Качественное обслуживание, всё на высоте", "positive"),
        ("Быстро решили проблему, молодцы!", "positive"),
        
        # Негативные
        ("Ужасная компания, постоянные проблемы с оплатой", "negative"),
        ("Не могу дозвониться, поддержка не отвечает", "negative"),
        ("Завышенные счета, грабеж какой-то!", "negative"),
        ("Отключили свет без предупреждения", "negative"),
        ("Хамское отношение операторов", "negative"),
        
        # Нейтральные
        ("Передал показания счетчика", "neutral"),
        ("Подключение электричества в новом доме", "neutral"),
        ("Тариф изменился с 1 января", "neutral"),
        ("Офис работает с 9 до 18", "neutral"),
    ]
    
    print("\n" + "-"*70)
    print("ТЕСТОВЫЕ ПРИМЕРЫ:")
    print("-"*70)
    
    correct = 0
    total = len(test_cases)
    total_time = 0
    
    for i, (text, expected) in enumerate(test_cases, 1):
        start_time = time.time()
        result = analyzer.analyze(text)
        analysis_time = time.time() - start_time
        total_time += analysis_time
        
        predicted = result.get('sentiment_label', 'neutral')
        is_correct = predicted == expected
        
        if is_correct:
            correct += 1
            status = "✓"
        else:
            status = "✗"
        
        print(f"\n{i}. {status} [{analysis_time*1000:.1f}ms] Текст: {text[:50]}...")
        print(f"   Ожидалось: {expected:8} | Получено: {predicted:8} | Score: {result.get('sentiment_score', 0):+.3f} | Уверенность: {result.get('confidence', 0):.3f}")
        
        # Показываем детали для неправильных предсказаний
        if not is_correct and 'raw_result' in result:
            print(f"   Raw: {result['raw_result']}")
    
    avg_time = total_time / total if total > 0 else 0
    
    print("\n" + "="*70)
    print(f"ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*70)
    print(f"  Точность:         {correct}/{total} ({100*correct/total:.1f}%)")
    print(f"  Среднее время:    {avg_time*1000:.1f} мс на текст")
    print(f"  Общее время:      {total_time:.2f} сек")
    print(f"  Анализатор:       {info['name']}")
    print("="*70)
    
    # Сравнение с ожидаемой точностью
    expected_accuracy = {
        'rusentiment': 85,
        'dostoevsky': 80,
        'rule_based': 70
    }
    
    current_expected = expected_accuracy.get(analyzer.analyzer_type, 70)
    actual_accuracy = 100 * correct / total
    
    if actual_accuracy >= current_expected:
        print(f"\n✓ Точность соответствует ожиданиям (>= {current_expected}%)")
    else:
        print(f"\n⚠ Точность ниже ожиданий (< {current_expected}%)")
    
    return analyzer

def test_real_world_examples():
    """Тест на реальных примерах из соцсетей"""
    print("\n" + "="*70)
    print("ТЕСТ НА РЕАЛЬНЫХ ПРИМЕРАХ")
    print("="*70)
    
    analyzer = SentimentAnalyzer()
    
    real_examples = [
        "ТНС Энерго опять счет неправильный прислали, уже надоело разбираться",
        "Наконец-то подключили свет! Спасибо бригаде за оперативную работу",
        "Позвонил в поддержку, быстро объяснили как передать показания",
        "Третий день без электричества, никто не реагирует на заявки",
        "Удобный личный кабинет, легко оплачивать счета онлайн",
    ]
    
    for i, text in enumerate(real_examples, 1):
        result = analyzer.analyze(text)
        print(f"\n{i}. {text}")
        print(f"   → Тональность: {result['sentiment_label']:8} | Score: {result['sentiment_score']:+.3f} | Уверенность: {result['confidence']:.3f}")

if __name__ == "__main__":
    try:
        analyzer = test_rusentiment_analyzer()
        test_real_world_examples()
        
        print("\n" + "-"*70)
        print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("-"*70)
        print("Введите текст для анализа (или 'exit' для выхода)")
        
        while True:
            try:
                text = input("\nТекст: ").strip()
                if text.lower() in ['exit', 'quit', 'q', 'выход']:
                    break
                
                if not text:
                    continue
                
                start_time = time.time()
                result = analyzer.analyze(text)
                analysis_time = time.time() - start_time
                
                print(f"  → Тональность: {result.get('sentiment_label', 'N/A')}")
                print(f"  → Score: {result.get('sentiment_score', 0):+.3f}")
                print(f"  → Уверенность: {result.get('confidence', 0):.3f}")
                print(f"  → Анализатор: {result.get('analyzer', 'N/A')}")
                print(f"  → Время: {analysis_time*1000:.1f} мс")
                
                if 'raw_result' in result:
                    print(f"  → Raw: {result['raw_result']}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Ошибка: {e}")
        
        print("\nЗавершение тестирования.")
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
