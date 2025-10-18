"""
Проверка последних записей в базе
"""
from app_enhanced import app
from models import Review

with app.app_context():
    print("="*70)
    print("ПОСЛЕДНИЕ 10 ЗАПИСЕЙ В БАЗЕ")
    print("="*70)
    
    latest = Review.query.order_by(Review.id.desc()).limit(10).all()
    
    for r in latest:
        print(f"\nID: {r.id}")
        print(f"Источник: {r.source}")
        print(f"Тональность: {r.sentiment_label} (score: {r.sentiment_score:.3f})")
        print(f"Текст: {r.text[:80]}...")
    
    print("\n" + "="*70)
    print("СТАТИСТИКА ТОНАЛЬНОСТИ")
    print("="*70)
    
    total = Review.query.count()
    positive = Review.query.filter_by(sentiment_label='positive').count()
    negative = Review.query.filter_by(sentiment_label='negative').count()
    neutral = Review.query.filter_by(sentiment_label='neutral').count()
    none_or_empty = Review.query.filter(
        (Review.sentiment_label == None) | (Review.sentiment_label == '')
    ).count()
    
    print(f"\nВсего записей: {total}")
    print(f"Позитивных: {positive} ({positive/total*100:.1f}%)")
    print(f"Негативных: {negative} ({negative/total*100:.1f}%)")
    print(f"Нейтральных: {neutral} ({neutral/total*100:.1f}%)")
    
    if none_or_empty > 0:
        print(f"БЕЗ тональности: {none_or_empty} ({none_or_empty/total*100:.1f}%)")
        print("\n⚠ ВНИМАНИЕ: Есть записи без тональности!")
    else:
        print("\n✓ ВСЕ ЗАПИСИ ИМЕЮТ ТОНАЛЬНОСТЬ!")
    
    print("="*70)
