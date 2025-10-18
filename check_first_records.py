"""
Проверка первых записей в базе
"""
from app_enhanced import app
from models import Review

with app.app_context():
    print("="*70)
    print("ПЕРВЫЕ 10 ЗАПИСЕЙ В БАЗЕ (должны быть пересчитаны)")
    print("="*70)
    
    first = Review.query.order_by(Review.id.asc()).limit(10).all()
    
    for r in first:
        print(f"\nID: {r.id}")
        print(f"Источник: {r.source}")
        print(f"Тональность: {r.sentiment_label} (score: {r.sentiment_score:.3f})")
        print(f"Текст: {r.text[:80]}...")
    
    print("\n" + "="*70)
    print("ПРОВЕРКА СТАРЫХ ЗАПИСЕЙ (ID 1-57)")
    print("="*70)
    
    old_records = Review.query.filter(Review.id <= 57).all()
    
    positive_old = sum(1 for r in old_records if r.sentiment_label == 'positive')
    negative_old = sum(1 for r in old_records if r.sentiment_label == 'negative')
    neutral_old = sum(1 for r in old_records if r.sentiment_label == 'neutral')
    
    print(f"\nСтарые записи (ID 1-57): {len(old_records)}")
    print(f"  Позитивных: {positive_old}")
    print(f"  Негативных: {negative_old}")
    print(f"  Нейтральных: {neutral_old}")
    
    if positive_old > 0 or negative_old > 0:
        print("\nВЫВОД: Старые записи ИМЕЮТ правильную тональность!")
    else:
        print("\nВЫВОД: Старые записи НЕ имеют тональности (нужен пересчет)")
    
    print("\n" + "="*70)
    print("ПРОВЕРКА НОВЫХ ЗАПИСЕЙ (ID > 57)")
    print("="*70)
    
    new_records = Review.query.filter(Review.id > 57).all()
    
    if new_records:
        positive_new = sum(1 for r in new_records if r.sentiment_label == 'positive')
        negative_new = sum(1 for r in new_records if r.sentiment_label == 'negative')
        neutral_new = sum(1 for r in new_records if r.sentiment_label == 'neutral')
        
        print(f"\nНовые записи (ID > 57): {len(new_records)}")
        print(f"  Позитивных: {positive_new}")
        print(f"  Негативных: {negative_new}")
        print(f"  Нейтральных: {neutral_new}")
        
        # Показываем примеры новых
        print("\nПримеры новых записей:")
        for r in new_records[:5]:
            print(f"  ID {r.id}: {r.sentiment_label} ({r.sentiment_score:.3f})")
        
        if negative_new > 0:
            print("\nВЫВОД: Новые записи ПОЛУЧАЮТ тональность!")
        else:
            print("\nВЫВОД: Новые записи НЕ получают тональность!")
    else:
        print("\nНовых записей нет")
    
    print("="*70)
