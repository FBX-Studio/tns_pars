"""
Быстрый тест ML анализатора
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from analyzers.ml_sentiment_analyzer import MLSentimentAnalyzer

print("="*70)
print("БЫСТРЫЙ ТЕСТ ML АНАЛИЗАТОРА")
print("="*70)

print("\n1. Инициализация...")
analyzer = MLSentimentAnalyzer(model_type='auto')

model_info = analyzer.get_model_info()
print(f"✓ Модель: {model_info['model_type']}")
print(f"✓ Описание: {model_info['description']}")

print("\n2. Тестовые примеры:")

tests = [
    ("ТНС энерго отлично работает!", "positive"),
    ("Ужасная компания, не рекомендую.", "negative"),
    ("ТНС энерго - энергоснабжающая компания.", "neutral")
]

for text, expected in tests:
    result = analyzer.analyze(text)
    status = "✓" if result['sentiment_label'] == expected else "✗"
    print(f"\n{status} \"{text}\"")
    print(f"   Результат: {result['sentiment_label']} (score: {result['sentiment_score']:.2f}, уверенность: {result['confidence']:.0%})")
    print(f"   Модель: {result['model']}")

print("\n" + "="*70)
print("✅ ТЕСТ ЗАВЕРШЕН!")
print("="*70)
