"""
Простая проверка без спецсимволов
"""
from app_enhanced import app
from models import Review

with app.app_context():
    total = Review.query.count()
    positive = Review.query.filter_by(sentiment_label='positive').count()
    negative = Review.query.filter_by(sentiment_label='negative').count()
    neutral = Review.query.filter_by(sentiment_label='neutral').count()
    neutral_zero = Review.query.filter_by(sentiment_label='neutral', sentiment_score=0.0).count()
    
    print("="*60)
    print("CURRENT DATABASE STATUS")
    print("="*60)
    print(f"Total records: {total}")
    print(f"Positive: {positive} ({positive/total*100:.1f}%)")
    print(f"Negative: {negative} ({negative/total*100:.1f}%)")
    print(f"Neutral: {neutral} ({neutral/total*100:.1f}%)")
    print(f"  with score=0.0: {neutral_zero}")
    print("="*60)
    
    print("\nLast 5 records:")
    latest = Review.query.order_by(Review.id.desc()).limit(5).all()
    for r in latest:
        print(f"ID {r.id}: {r.sentiment_label} ({r.sentiment_score:.3f}) - {r.source}")
    
    print("\n" + "="*60)
    
    if neutral_zero > total * 0.9:
        print("PROBLEM: Most records have score=0.0")
        print("Need to run: python reanalyze_all_sentiment.py")
    elif positive > 0 or negative > 0:
        print("OK: Sentiment is working!")
    else:
        print("PROBLEM: No positive/negative sentiment found")
