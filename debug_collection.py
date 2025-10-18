"""
Детальная диагностика: что происходит при сборе и сохранении
"""
import logging
from app_enhanced import app
from models import db, Review
from analyzers.sentiment_analyzer import SentimentAnalyzer
from collectors.news_collector import NewsCollector

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_collection():
    """Детальная диагностика процесса сбора"""
    
    print("\n" + "="*80)
    print("ДЕТАЛЬНАЯ ДИАГНОСТИКА ПРОЦЕССА СБОРА И СОХРАНЕНИЯ")
    print("="*80)
    
    with app.app_context():
        # Шаг 1: Проверка БД ДО
        count_before = Review.query.count()
        print(f"\n[1] Записей в БД ДО сбора: {count_before}")
        
        # Шаг 2: Создание анализатора
        print("\n[2] Создание sentiment_analyzer...")
        sentiment_analyzer = SentimentAnalyzer()
        info = sentiment_analyzer.get_analyzer_info()
        print(f"    ✓ Тип: {info['type']}")
        print(f"    ✓ Название: {info['name']}")
        
        # Тест анализатора
        print("\n[3] Тест анализатора на примере:")
        test_text = "Ужасный сервис! Отвратительное обслуживание!"
        test_result = sentiment_analyzer.analyze(test_text)
        print(f"    Текст: {test_text}")
        print(f"    Результат: {test_result['sentiment_label']} (score: {test_result['sentiment_score']:.3f})")
        
        if test_result['sentiment_label'] == 'neutral' and test_result['sentiment_score'] == 0.0:
            print("    ✗ ПРОБЛЕМА: Анализатор НЕ работает!")
            return
        else:
            print("    ✓ Анализатор работает корректно")
        
        # Шаг 3: Создание коллектора С анализатором
        print("\n[4] Создание news_collector С sentiment_analyzer...")
        news_collector = NewsCollector(sentiment_analyzer=sentiment_analyzer)
        
        # ВАЖНАЯ ПРОВЕРКА
        if news_collector.sentiment_analyzer is None:
            print("    ✗ КРИТИЧЕСКАЯ ОШИБКА: sentiment_analyzer НЕ передан!")
            return
        else:
            print(f"    ✓ sentiment_analyzer передан: {type(news_collector.sentiment_analyzer)}")
        
        # Шаг 4: Сбор (ограничено)
        print("\n[5] Запуск сбора (1 запрос)...")
        news_collector.search_queries = news_collector.search_queries[:1]
        
        articles = news_collector.collect()
        
        print(f"\n[6] Результат сбора: {len(articles)} статей")
        
        if not articles:
            print("    ⚠ Статьи не найдены")
            return
        
        # Шаг 5: Проверка тональности В СОБРАННЫХ ДАННЫХ
        print("\n[7] ПРОВЕРКА ТОНАЛЬНОСТИ В СОБРАННЫХ ДАННЫХ:")
        print("-" * 80)
        
        problems = []
        
        for i, article in enumerate(articles[:3], 1):
            has_sentiment_score = 'sentiment_score' in article
            has_sentiment_label = 'sentiment_label' in article
            
            print(f"\nСтатья {i}:")
            print(f"  source_id: {article.get('source_id', 'отсутствует')}")
            print(f"  Текст: {article.get('text', '')[:60]}...")
            print(f"  Есть sentiment_score: {has_sentiment_score}")
            print(f"  Есть sentiment_label: {has_sentiment_label}")
            
            if has_sentiment_score and has_sentiment_label:
                score = article['sentiment_score']
                label = article['sentiment_label']
                print(f"  ✓ sentiment_score: {score:.3f}")
                print(f"  ✓ sentiment_label: {label}")
                
                if score == 0.0 and label == 'neutral':
                    print(f"  ⚠ Возможно ложный нейтральный")
            else:
                print(f"  ✗ ТОНАЛЬНОСТЬ ОТСУТСТВУЕТ В ДАННЫХ!")
                problems.append(f"Статья {i} без тональности")
        
        if problems:
            print("\n" + "="*80)
            print("✗ ПРОБЛЕМА НАЙДЕНА: Коллектор НЕ добавляет тональность!")
            print("="*80)
            for p in problems:
                print(f"  - {p}")
            
            print("\nВОЗМОЖНЫЕ ПРИЧИНЫ:")
            print("  1. В коллекторе НЕ вызывается sentiment_analyzer.analyze()")
            print("  2. Анализатор есть, но результат не добавляется в article")
            print("  3. Ошибка при анализе (проверьте логи выше)")
            return
        
        # Шаг 6: Сохранение в БД
        print("\n" + "="*80)
        print("[8] СОХРАНЕНИЕ В БАЗУ ДАННЫХ")
        print("="*80)
        
        saved_count = 0
        
        for i, article in enumerate(articles, 1):
            # Проверка дубликата
            existing = Review.query.filter_by(source_id=article['source_id']).first()
            if existing:
                print(f"\nСтатья {i}: ДУБЛИКАТ (пропускаем)")
                continue
            
            print(f"\nСтатья {i}: Сохраняем...")
            
            # Если по какой-то причине нет тональности - анализируем снова
            if 'sentiment_label' not in article or not article.get('sentiment_label'):
                print("  ⚠ Тональность отсутствует - анализируем...")
                sentiment = sentiment_analyzer.analyze(article['text'])
                article['sentiment_score'] = sentiment['sentiment_score']
                article['sentiment_label'] = sentiment['sentiment_label']
                print(f"  → Результат: {article['sentiment_label']} ({article['sentiment_score']:.3f})")
            
            # Создаем запись
            review = Review(
                source=article['source'],
                source_id=article['source_id'],
                author=article.get('author'),
                author_id=article.get('author_id'),
                text=article['text'],
                url=article.get('url'),
                published_date=article.get('published_date'),
                sentiment_score=article.get('sentiment_score', 0.0),
                sentiment_label=article.get('sentiment_label', 'neutral')
            )
            
            print(f"  Сохраняем с тональностью: {review.sentiment_label} ({review.sentiment_score:.3f})")
            
            db.session.add(review)
            saved_count += 1
        
        # Коммит
        try:
            db.session.commit()
            print(f"\n✓ Коммит успешен: {saved_count} записей")
        except Exception as e:
            print(f"\n✗ ОШИБКА при коммите: {e}")
            db.session.rollback()
            return
        
        # Шаг 7: Проверка что сохранилось
        print("\n" + "="*80)
        print("[9] ПРОВЕРКА БАЗЫ ДАННЫХ ПОСЛЕ СОХРАНЕНИЯ")
        print("="*80)
        
        count_after = Review.query.count()
        print(f"\nВсего записей: {count_after} (было {count_before})")
        print(f"Добавлено: {count_after - count_before}")
        
        # Проверяем последнюю запись
        if saved_count > 0:
            latest = Review.query.order_by(Review.id.desc()).first()
            
            print(f"\nПоследняя сохраненная запись:")
            print(f"  ID: {latest.id}")
            print(f"  source_id: {latest.source_id}")
            print(f"  sentiment_label: {latest.sentiment_label}")
            print(f"  sentiment_score: {latest.sentiment_score}")
            print(f"  Текст: {latest.text[:60]}...")
            
            if latest.sentiment_label == 'neutral' and latest.sentiment_score == 0.0:
                print(f"\n  ✗ ПРОБЛЕМА: Запись сохранилась с neutral/0.0!")
            else:
                print(f"\n  ✓ Тональность сохранена правильно!")
        
        # Итоговая статистика
        print("\n" + "="*80)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("="*80)
        
        total = Review.query.count()
        positive = Review.query.filter_by(sentiment_label='positive').count()
        negative = Review.query.filter_by(sentiment_label='negative').count()
        neutral = Review.query.filter_by(sentiment_label='neutral').count()
        
        print(f"\nВсего: {total}")
        print(f"Позитивных: {positive} ({positive/total*100:.1f}%)")
        print(f"Негативных: {negative} ({negative/total*100:.1f}%)")
        print(f"Нейтральных: {neutral} ({neutral/total*100:.1f}%)")
        
        if positive == 0 and negative == 0:
            print("\n✗ ВСЕ НЕЙТРАЛЬНЫЕ - ПРОБЛЕМА НЕ РЕШЕНА!")
        else:
            print("\n✓ ТОНАЛЬНОСТЬ ОПРЕДЕЛЯЕТСЯ!")

if __name__ == '__main__':
    try:
        debug_collection()
    except Exception as e:
        logger.error(f"\n✗ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
