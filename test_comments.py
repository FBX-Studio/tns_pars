"""
Тест парсинга и сохранения комментариев
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models import db, Review
from utils.comment_helper import CommentHelper
from analyzers.sentiment_analyzer import SentimentAnalyzer
from datetime import datetime
import os

def setup_test_db():
    """Настройка тестовой БД"""
    from flask import Flask
    from config import Config
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_comments.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Удаляем старую БД
        if os.path.exists('test_comments.db'):
            os.remove('test_comments.db')
        
        # Создаем таблицы
        db.create_all()
    
    return app

def test_basic_comment_functionality():
    """Тест базовой функциональности комментариев"""
    print("\n" + "="*70)
    print("ТЕСТ 1: Базовая функциональность")
    print("="*70)
    
    app = setup_test_db()
    analyzer = SentimentAnalyzer()
    
    with app.app_context():
        # Тестовый пост
        post_data = {
            'source': 'test',
            'source_id': 'test_post_1',
            'author': 'Тестовый пользователь',
            'author_id': '12345',
            'text': 'Отличный сервис ТНС Энерго!',
            'url': 'https://test.com/post/1',
            'published_date': datetime.now()
        }
        
        # Тестовые комментарии
        comments_data = [
            {
                'source': 'test',
                'source_id': 'test_comment_1',
                'author': 'Комментатор 1',
                'text': 'Полностью согласен!',
                'url': 'https://test.com/post/1#comment1',
                'published_date': datetime.now()
            },
            {
                'source': 'test',
                'source_id': 'test_comment_2',
                'author': 'Комментатор 2',
                'text': 'Не согласен, были проблемы',
                'url': 'https://test.com/post/1#comment2',
                'published_date': datetime.now()
            },
            {
                'source': 'test',
                'source_id': 'test_comment_3',
                'author': 'Комментатор 3',
                'text': 'Нейтральный комментарий',
                'url': 'https://test.com/post/1#comment3',
                'published_date': datetime.now()
            }
        ]
        
        # Сохраняем пост с комментариями
        print("\n1. Сохранение поста с комментариями...")
        saved_post, saved_comments = CommentHelper.save_post_with_comments(
            post_data, comments_data, analyzer
        )
        
        if saved_post:
            print(f"   ✓ Пост сохранен: ID={saved_post.id}")
            print(f"   ✓ Комментариев сохранено: {len(saved_comments)}")
        else:
            print("   ✗ Ошибка сохранения поста")
            return False
        
        # Проверяем связи
        print("\n2. Проверка связей пост-комментарии...")
        for comment in saved_comments:
            if comment.parent_id == saved_post.id and comment.is_comment:
                print(f"   ✓ Комментарий ID={comment.id} привязан к посту ID={saved_post.id}")
            else:
                print(f"   ✗ Неправильная привязка комментария ID={comment.id}")
                return False
        
        # Получаем комментарии
        print("\n3. Получение комментариев к посту...")
        retrieved_comments = CommentHelper.get_post_comments(saved_post.id)
        print(f"   ✓ Получено комментариев: {len(retrieved_comments)}")
        
        if len(retrieved_comments) != len(saved_comments):
            print(f"   ✗ Количество не совпадает! Ожидалось {len(saved_comments)}, получено {len(retrieved_comments)}")
            return False
        
        # Статистика
        print("\n4. Статистика комментариев...")
        stats = CommentHelper.get_comment_stats(saved_post.id)
        print(f"   Всего: {stats['total']}")
        print(f"   Позитивных: {stats['positive']}")
        print(f"   Негативных: {stats['negative']}")
        print(f"   Нейтральных: {stats['neutral']}")
        print(f"   Средняя тональность: {stats['avg_sentiment']:+.3f}")
        
        if stats['total'] != len(saved_comments):
            print("   ✗ Статистика некорректна!")
            return False
        
        print("\n5. Проверка relationship...")
        # Через relationship
        comments_via_rel = saved_post.comments.all()
        print(f"   ✓ Через relationship получено: {len(comments_via_rel)} комментариев")
        
        if len(comments_via_rel) != len(saved_comments):
            print("   ✗ Relationship работает некорректно!")
            return False
        
        print("\n" + "="*70)
        print("✓ ТЕСТ 1 ПРОЙДЕН УСПЕШНО")
        print("="*70)
        return True

def test_multiple_posts():
    """Тест нескольких постов с комментариями"""
    print("\n" + "="*70)
    print("ТЕСТ 2: Несколько постов с комментариями")
    print("="*70)
    
    app = setup_test_db()
    analyzer = SentimentAnalyzer()
    
    with app.app_context():
        # Создаем 3 поста с комментариями
        for i in range(1, 4):
            post_data = {
                'source': 'test',
                'source_id': f'test_post_{i}',
                'author': f'Автор {i}',
                'text': f'Тестовый пост номер {i}',
                'url': f'https://test.com/post/{i}',
                'published_date': datetime.now()
            }
            
            comments_data = []
            for j in range(1, i+2):  # Пост 1 -> 2 комментария, пост 2 -> 3, пост 3 -> 4
                comments_data.append({
                    'source': 'test',
                    'source_id': f'test_post_{i}_comment_{j}',
                    'author': f'Комментатор {j}',
                    'text': f'Комментарий {j} к посту {i}',
                    'url': f'https://test.com/post/{i}#comment{j}',
                    'published_date': datetime.now()
                })
            
            saved_post, saved_comments = CommentHelper.save_post_with_comments(
                post_data, comments_data, analyzer
            )
            
            print(f"\nПост {i}:")
            print(f"  ID поста: {saved_post.id}")
            print(f"  Комментариев: {len(saved_comments)}")
        
        # Проверяем общее количество
        print("\nПроверка общих счетчиков...")
        total_posts = Review.query.filter_by(is_comment=False).count()
        total_comments = Review.query.filter_by(is_comment=True).count()
        
        print(f"  Всего постов: {total_posts} (ожидается: 3)")
        print(f"  Всего комментариев: {total_comments} (ожидается: 9)")
        
        if total_posts == 3 and total_comments == 9:
            print("\n" + "="*70)
            print("✓ ТЕСТ 2 ПРОЙДЕН УСПЕШНО")
            print("="*70)
            return True
        else:
            print("\n✗ ТЕСТ 2 ПРОВАЛЕН")
            return False

def test_posts_without_comments():
    """Тест постов без комментариев"""
    print("\n" + "="*70)
    print("ТЕСТ 3: Посты без комментариев")
    print("="*70)
    
    app = setup_test_db()
    analyzer = SentimentAnalyzer()
    
    with app.app_context():
        # Создаем 2 поста БЕЗ комментариев
        for i in range(1, 3):
            post_data = {
                'source': 'test',
                'source_id': f'test_post_no_comments_{i}',
                'author': f'Автор {i}',
                'text': f'Пост без комментариев {i}',
                'url': f'https://test.com/post_no_comments/{i}',
                'published_date': datetime.now()
            }
            
            saved_post, _ = CommentHelper.save_post_with_comments(
                post_data, [], analyzer
            )
            print(f"  Пост {i} сохранен: ID={saved_post.id}")
        
        # Создаем 1 пост С комментариями
        post_with_comments = {
            'source': 'test',
            'source_id': 'test_post_with_comments',
            'author': 'Автор',
            'text': 'Пост с комментариями',
            'url': 'https://test.com/post_with_comments',
            'published_date': datetime.now()
        }
        
        comments = [{
            'source': 'test',
            'source_id': 'test_comment',
            'author': 'Комментатор',
            'text': 'Комментарий',
            'url': 'https://test.com/post_with_comments#comment',
            'published_date': datetime.now()
        }]
        
        saved_post, saved_comments = CommentHelper.save_post_with_comments(
            post_with_comments, comments, analyzer
        )
        print(f"  Пост с комментариями сохранен: ID={saved_post.id}")
        
        # Получаем посты БЕЗ комментариев
        print("\nПоиск постов без комментариев...")
        posts_no_comments = CommentHelper.get_posts_without_comments()
        
        print(f"  Найдено постов без комментариев: {len(posts_no_comments)}")
        print(f"  Ожидается: 2")
        
        if len(posts_no_comments) == 2:
            for post in posts_no_comments:
                print(f"    - Пост ID={post.id}: {post.text[:30]}...")
            
            print("\n" + "="*70)
            print("✓ ТЕСТ 3 ПРОЙДЕН УСПЕШНО")
            print("="*70)
            return True
        else:
            print("\n✗ ТЕСТ 3 ПРОВАЛЕН")
            return False

def test_duplicate_prevention():
    """Тест предотвращения дубликатов"""
    print("\n" + "="*70)
    print("ТЕСТ 4: Предотвращение дубликатов")
    print("="*70)
    
    app = setup_test_db()
    analyzer = SentimentAnalyzer()
    
    with app.app_context():
        post_data = {
            'source': 'test',
            'source_id': 'test_duplicate_post',
            'author': 'Автор',
            'text': 'Тестовый пост',
            'url': 'https://test.com/duplicate',
            'published_date': datetime.now()
        }
        
        comment_data = {
            'source': 'test',
            'source_id': 'test_duplicate_comment',
            'author': 'Комментатор',
            'text': 'Тестовый комментарий',
            'url': 'https://test.com/duplicate#comment',
            'published_date': datetime.now()
        }
        
        # Первое сохранение
        print("\n1. Первое сохранение поста...")
        post1, comments1 = CommentHelper.save_post_with_comments(
            post_data, [comment_data], analyzer
        )
        print(f"   Пост ID: {post1.id}, Комментариев: {len(comments1)}")
        
        # Повторное сохранение (должны игнорироваться дубликаты)
        print("\n2. Повторное сохранение того же поста...")
        post2, comments2 = CommentHelper.save_post_with_comments(
            post_data, [comment_data], analyzer
        )
        print(f"   Пост ID: {post2.id}, Комментариев: {len(comments2)}")
        
        # Проверяем количество в БД
        total_posts = Review.query.filter_by(source_id='test_duplicate_post').count()
        total_comments = Review.query.filter_by(source_id='test_duplicate_comment').count()
        
        print(f"\n3. Проверка БД:")
        print(f"   Постов с source_id='test_duplicate_post': {total_posts} (ожидается: 1)")
        print(f"   Комментариев с source_id='test_duplicate_comment': {total_comments} (ожидается: 1)")
        
        if total_posts == 1 and total_comments == 1 and post1.id == post2.id:
            print("\n" + "="*70)
            print("✓ ТЕСТ 4 ПРОЙДЕН УСПЕШНО")
            print("="*70)
            return True
        else:
            print("\n✗ ТЕСТ 4 ПРОВАЛЕН")
            return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ КОММЕНТАРИЕВ")
    print("="*70)
    
    results = {
        "Базовая функциональность": test_basic_comment_functionality(),
        "Несколько постов": test_multiple_posts(),
        "Посты без комментариев": test_posts_without_comments(),
        "Предотвращение дубликатов": test_duplicate_prevention()
    }
    
    print("\n" + "="*70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✓ ПРОЙДЕН" if result else "✗ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nВсего тестов: {total}")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {total - passed}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("\n⚠️ ЕСТЬ ПРОВАЛЕННЫЕ ТЕСТЫ!")
    
    print("="*70)
    
    # Очистка
    if os.path.exists('test_comments.db'):
        os.remove('test_comments.db')
        print("\n✓ Тестовая БД удалена")
