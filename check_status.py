from models import Review, db
from app import app

with app.app_context():
    total = Review.query.count()
    vk = Review.query.filter_by(source='vk').count()
    tg = Review.query.filter_by(source='telegram').count()
    news = Review.query.filter(Review.source.in_(['news', 'web'])).count()
    
    pos = Review.query.filter_by(sentiment_label='positive').count()
    neg = Review.query.filter_by(sentiment_label='negative').count()
    neu = Review.query.filter_by(sentiment_label='neutral').count()
    
    print("=" * 50)
    print("ИТОГОВАЯ СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    print(f"Всего записей: {total}")
    print(f"\nПо источникам:")
    print(f"  VK: {vk}")
    print(f"  Telegram: {tg}")
    print(f"  Новости: {news}")
    print(f"\nПо тональности:")
    print(f"  Позитивные: {pos}")
    print(f"  Негативные: {neg}")
    print(f"  Нейтральные: {neu}")
    print("=" * 50)
