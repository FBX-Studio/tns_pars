"""
Тест анализатора тональности
"""
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("=" * 80)
print("ТЕСТ АНАЛИЗАТОРА ТОНАЛЬНОСТИ")
print("=" * 80)

# Инициализация анализатора
print("\n[1] Инициализация анализатора...")
try:
    from analyzers.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    print(f"[+] Анализатор создан")
    
    # Получаем информацию об анализаторе
    info = analyzer.get_analyzer_info()
    print(f"[+] Тип: {info['type']}")
    print(f"[+] Название: {info.get('name', 'Unknown')}")
    print(f"[+] Точность: {info.get('accuracy', 'Unknown')}")
    
except Exception as e:
    print(f"[!] ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Тестовые тексты
print("\n[2] Тестирование анализа...")
print("-" * 80)

test_texts = [
    # Позитивные
    ("Отличный сервис! Быстро подключили, все работает стабильно. Спасибо ТНС Энерго!", "positive"),
    ("Вежливые операторы, помогли разобраться с показаниями счетчика. Рекомендую!", "positive"),
    
    # Негативные
    ("Ужасный сервис! Постоянные отключения света, не дозвониться в поддержку. Кошмар!", "negative"),
    ("Огромные счета за электричество. Грабительские тарифы. Обман и беспредел!", "negative"),
    
    # Нейтральные
    ("Передал показания счетчика через личный кабинет.", "neutral"),
    ("ТНС Энерго - энергосбытовая компания.", "neutral"),
]

success_count = 0
total_count = len(test_texts)

for text, expected_sentiment in test_texts:
    print(f"\nТекст: '{text[:70]}...'")
    print(f"Ожидается: {expected_sentiment}")
    
    try:
        result = analyzer.analyze(text)
        
        detected_sentiment = result.get('sentiment_label', 'unknown')
        score = result.get('sentiment_score', 0)
        confidence = result.get('confidence', 0)
        
        print(f"Обнаружено: {detected_sentiment}")
        print(f"Score: {score:.3f}")
        print(f"Уверенность: {confidence:.3f}")
        
        if detected_sentiment == expected_sentiment:
            print("[+] УСПЕХ - совпадает с ожиданием")
            success_count += 1
        else:
            print("[!] ВНИМАНИЕ - не совпадает с ожиданием")
        
    except Exception as e:
        print(f"[!] ОШИБКА анализа: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print(f"РЕЗУЛЬТАТЫ: {success_count}/{total_count} успешных тестов ({success_count/total_count*100:.0f}%)")
print("=" * 80)

# Тест получения результата
print("\n[3] Тест формата результата...")
sample_text = "Хороший сервис"
result = analyzer.analyze(sample_text)

required_keys = ['sentiment_score', 'sentiment_label', 'confidence', 'analyzer']
print(f"Проверка наличия ключей в результате:")
for key in required_keys:
    if key in result:
        print(f"  [+] {key}: {result[key]}")
    else:
        print(f"  [!] {key}: ОТСУТСТВУЕТ")

print("\n" + "=" * 80)
if success_count == total_count:
    print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
elif success_count >= total_count * 0.7:
    print("[WARNING] Большинство тестов пройдено, но есть ошибки")
else:
    print("[ERROR] Много ошибок в анализе тональности")
print("=" * 80)
