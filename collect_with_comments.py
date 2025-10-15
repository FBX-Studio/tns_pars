"""
Скрипт для тестирования сбора постов с комментариями
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import logging
from flask import Flask
from models import db
from config import Config
from analyzers.sentiment_analyzer import SentimentAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройка Flask приложения для работы с БД
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_vk_with_comments():
    """Тест сбора VK с комментариями"""
    print("\n" + "="*70)
    print("ТЕСТ: VK с комментариями")
    print("="*70)
    
    with app.app_context():
        try:
            from collectors.vk_collector import VKCollector
            from utils.comment_helper import CommentHelper
            
            print("\n1. Инициализация VK коллектора...")
            analyzer = SentimentAnalyzer()
            collector = VKCollector(sentiment_analyzer=analyzer)
            
            print(f"   Анализатор: {analyzer.get_analyzer_info()['name']}")
            
            print("\n2. Запуск сбора с комментариями...")
            print("   (save_to_db=True, collect_comments=True)")
            
            # Сбор с комментариями и сохранением в БД
            results = collector.collect(collect_comments=True, save_to_db=True)
            
            print(f"\n3. Собрано постов: {len(results)}")
            
            # Проверяем что сохранилось
            print("\n4. Проверка БД...")
            total_comments = CommentHelper.get_all_comments_count()
            
            from models import Review
            total_posts = Review.query.filter_by(is_comment=False, source='vk').count()
            
            print(f"   Постов в БД (VK): {total_posts}")
            print(f"   Комментариев в БД (все): {total_comments}")
            
            # Показываем пример
            if total_posts > 0:
                print("\n5. Пример поста с комментариями:")
                post = Review.query.filter_by(is_comment=False, source='vk').first()
                
                comments = CommentHelper.get_post_comments(post.id)
                stats = CommentHelper.get_comment_stats(post.id)
                
                print(f"\n   Пост ID: {post.id}")
                print(f"   Текст: {post.text[:80]}...")
                print(f"   Комментариев: {stats['total']}")
                print(f"   Позитивных: {stats['positive']}")
                print(f"   Негативных: {stats['negative']}")
                print(f"   Средняя тональность: {stats['avg_sentiment']:+.2f}")
                
                if comments:
                    print(f"\n   Примеры комментариев:")
                    for i, comment in enumerate(comments[:3], 1):
                        print(f"   {i}. {comment.author}: {comment.text[:60]}...")
                        print(f"      Тональность: {comment.sentiment_label} ({comment.sentiment_score:+.2f})")
            
            print("\n" + "="*70)
            print("✓ ТЕСТ VK ЗАВЕРШЕН")
            print("="*70)
            return True
            
        except Exception as e:
            print(f"\n✗ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_telegram_with_comments():
    """Тест сбора Telegram с комментариями"""
    print("\n" + "="*70)
    print("ТЕСТ: Telegram с комментариями")
    print("="*70)
    
    with app.app_context():
        try:
            from collectors.telegram_user_collector import TelegramUserCollector
            from utils.comment_helper import CommentHelper
            
            print("\n1. Инициализация Telegram коллектора...")
            collector = TelegramUserCollector()
            
            print("\n2. Запуск сбора с комментариями...")
            print("   (save_to_db=True, collect_comments=True)")
            
            # Сбор с комментариями и сохранением в БД
            results = collector.collect(collect_comments=True, save_to_db=True)
            
            print(f"\n3. Собрано сообщений: {len(results)}")
            
            # Проверяем что сохранилось
            print("\n4. Проверка БД...")
            total_comments = CommentHelper.get_all_comments_count()
            
            from models import Review
            total_posts = Review.query.filter_by(is_comment=False, source='telegram').count()
            
            print(f"   Постов в БД (Telegram): {total_posts}")
            print(f"   Комментариев в БД (все): {total_comments}")
            
            # Показываем пример
            if total_posts > 0:
                print("\n5. Пример поста с комментариями:")
                post = Review.query.filter_by(is_comment=False, source='telegram').first()
                
                comments = CommentHelper.get_post_comments(post.id)
                stats = CommentHelper.get_comment_stats(post.id)
                
                print(f"\n   Пост ID: {post.id}")
                print(f"   Канал: {post.author}")
                print(f"   Текст: {post.text[:80]}...")
                print(f"   Комментариев: {stats['total']}")
                
                if comments:
                    print(f"\n   Примеры ответов:")
                    for i, comment in enumerate(comments[:3], 1):
                        print(f"   {i}. {comment.text[:60]}...")
            
            print("\n" + "="*70)
            print("✓ ТЕСТ TELEGRAM ЗАВЕРШЕН")
            print("="*70)
            return True
            
        except Exception as e:
            print(f"\n✗ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            return False

def show_final_stats():
    """Показать итоговую статистику"""
    print("\n" + "="*70)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("="*70)
    
    with app.app_context():
        try:
            from utils.comment_helper import CommentHelper
            from models import Review
            
            # Общая статистика
            total_posts = Review.query.filter_by(is_comment=False).count()
            total_comments = CommentHelper.get_all_comments_count()
            
            print(f"\nВсего постов: {total_posts}")
            print(f"Всего комментариев: {total_comments}")
            print(f"Среднее комментариев на пост: {total_comments / total_posts:.2f}" if total_posts > 0 else "Среднее: 0")
            
            # По источникам
            print("\nПо источникам:")
            sources = db.session.query(
                Review.source,
                db.func.sum(db.case((Review.is_comment == False, 1), else_=0)).label('posts'),
                db.func.sum(db.case((Review.is_comment == True, 1), else_=0)).label('comments')
            ).group_by(Review.source).all()
            
            for source, posts, comments in sources:
                print(f"  {source:12} - Постов: {posts:4}, Комментариев: {comments:4}")
            
            # По тональности комментариев
            print("\nТональность комментариев:")
            sentiments = db.session.query(
                Review.sentiment_label,
                db.func.count(Review.id).label('count')
            ).filter_by(is_comment=True).group_by(Review.sentiment_label).all()
            
            for label, count in sentiments:
                print(f"  {(label or 'neutral'):10} - {count:4}")
            
            print("\n" + "="*70)
            
        except Exception as e:
            print(f"\n✗ ОШИБКА: {e}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ СБОРА КОММЕНТАРИЕВ")
    print("="*70)
    print("\nЭтот скрипт протестирует:")
    print("  1. VK коллектор с комментариями")
    print("  2. Telegram коллектор с комментариями")
    print("  3. Сохранение в БД через CommentHelper")
    print("  4. API endpoints")
    
    # Создаем таблицы если нужно
    with app.app_context():
        db.create_all()
        print("\n✓ БД инициализирована")
    
    results = {}
    
    # Запрашиваем что тестировать
    print("\n" + "-"*70)
    print("Выберите что протестировать:")
    print("  1 - VK с комментариями")
    print("  2 - Telegram с комментариями")
    print("  3 - Оба")
    print("  0 - Только показать статистику")
    
    try:
        choice = input("\nВаш выбор (1/2/3/0): ").strip()
        
        if choice == '1':
            results['VK'] = test_vk_with_comments()
        elif choice == '2':
            results['Telegram'] = test_telegram_with_comments()
        elif choice == '3':
            results['VK'] = test_vk_with_comments()
            results['Telegram'] = test_telegram_with_comments()
        
        # Показываем итоговую статистику
        show_final_stats()
        
        if results:
            print("\n" + "="*70)
            print("РЕЗУЛЬТАТЫ ТЕСТОВ")
            print("="*70)
            for name, success in results.items():
                status = "✓ УСПЕШНО" if success else "✗ ОШИБКА"
                print(f"{name}: {status}")
            print("="*70)
        
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
    except Exception as e:
        print(f"\n✗ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
