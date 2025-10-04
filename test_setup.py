"""
Скрипт для проверки правильности установки и настройки системы
"""
import sys
import os

def check_python_version():
    """Проверка версии Python"""
    print("Проверка версии Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} - требуется Python 3.8+")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\nПроверка зависимостей...")
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'requests',
        'bs4',
        'vk_api',
        'telegram',
        'sklearn',
        'numpy',
        'nltk',
        'dostoevsky',
        'schedule',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - не установлен")
            missing.append(package)
    
    if missing:
        print(f"\nУстановите недостающие пакеты:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Проверка файла .env"""
    print("\nПроверка конфигурации...")
    if not os.path.exists('.env'):
        print("✗ Файл .env не найден")
        print("Создайте .env на основе .env.example:")
        print("copy .env.example .env  (Windows)")
        print("cp .env.example .env    (Linux/Mac)")
        return False
    
    print("✓ Файл .env существует")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    vk_token = os.getenv('VK_ACCESS_TOKEN', '')
    tg_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    keywords = os.getenv('COMPANY_KEYWORDS', '')
    
    if vk_token:
        print("✓ VK_ACCESS_TOKEN настроен")
    else:
        print("⚠ VK_ACCESS_TOKEN не настроен (сбор из VK не будет работать)")
    
    if tg_token:
        print("✓ TELEGRAM_BOT_TOKEN настроен")
    else:
        print("⚠ TELEGRAM_BOT_TOKEN не настроен (сбор из Telegram не будет работать)")
    
    if keywords:
        print(f"✓ COMPANY_KEYWORDS: {keywords}")
    else:
        print("⚠ COMPANY_KEYWORDS не настроены")
    
    return True

def check_database():
    """Проверка базы данных"""
    print("\nПроверка базы данных...")
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✓ База данных инициализирована")
        return True
    except Exception as e:
        print(f"✗ Ошибка инициализации БД: {e}")
        return False

def check_sentiment_model():
    """Проверка модели sentiment analysis"""
    print("\nПроверка модели анализа тональности...")
    try:
        from dostoevsky.tokenization import RegexTokenizer
        from dostoevsky.models import FastTextSocialNetworkModel
        
        tokenizer = RegexTokenizer()
        model = FastTextSocialNetworkModel(tokenizer=tokenizer)
        
        test_text = "Это тестовый текст"
        result = model.predict([test_text])
        
        print("✓ Модель загружена успешно")
        return True
    except Exception as e:
        print(f"✗ Ошибка загрузки модели: {e}")
        print("\nУстановите модель:")
        print("python -m dostoevsky download fasttext-social-network-model")
        return False

def check_collectors():
    """Проверка сборщиков"""
    print("\nПроверка сборщиков данных...")
    try:
        from collectors.vk_collector import VKCollector
        from collectors.telegram_collector import TelegramCollector
        from collectors.web_collector import WebCollector
        
        vk = VKCollector()
        tg = TelegramCollector()
        web = WebCollector()
        
        print("✓ VK Collector")
        print("✓ Telegram Collector")
        print("✓ Web Collector")
        return True
    except Exception as e:
        print(f"✗ Ошибка инициализации сборщиков: {e}")
        return False

def check_analyzers():
    """Проверка анализаторов"""
    print("\nПроверка анализаторов...")
    try:
        from analyzers.sentiment_analyzer import SentimentAnalyzer
        from analyzers.moderator import Moderator
        
        analyzer = SentimentAnalyzer()
        moderator = Moderator()
        
        print("✓ Sentiment Analyzer")
        print("✓ Moderator")
        return True
    except Exception as e:
        print(f"✗ Ошибка инициализации анализаторов: {e}")
        return False

def run_full_test():
    """Полный тест системы"""
    print("\n" + "="*60)
    print("Тест работоспособности системы")
    print("="*60 + "\n")
    
    try:
        from analyzers.sentiment_analyzer import SentimentAnalyzer
        from analyzers.moderator import Moderator
        
        analyzer = SentimentAnalyzer()
        moderator = Moderator()
        
        test_reviews = [
            "Отличный сервис ТНС энерго! Всё быстро подключили.",
            "Ужасная компания, постоянные проблемы с электричеством.",
            "Передал показания через сайт, всё нормально."
        ]
        
        print("Тестирование анализа отзывов:\n")
        for i, text in enumerate(test_reviews, 1):
            print(f"Отзыв {i}: {text}")
            
            sentiment = analyzer.analyze(text)
            print(f"  Тональность: {sentiment['sentiment_label']}")
            print(f"  Оценка: {sentiment['sentiment_score']:.2f}")
            
            keywords = analyzer.extract_keywords(text)
            print(f"  Ключевые слова: {', '.join(keywords)}")
            
            status, reason, manual = moderator.moderate(text, sentiment['sentiment_score'])
            print(f"  Модерация: {status}")
            if reason:
                print(f"  Причина: {reason}")
            print()
        
        print("✓ Тест пройден успешно!")
        return True
    except Exception as e:
        print(f"✗ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("ПРОВЕРКА УСТАНОВКИ СИСТЕМЫ МОНИТОРИНГА ТНС ЭНЕРГО НН")
    print("="*60)
    
    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies),
        ("Конфигурация", check_env_file),
        ("База данных", check_database),
        ("Модель sentiment", check_sentiment_model),
        ("Сборщики", check_collectors),
        ("Анализаторы", check_analyzers),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Критическая ошибка в {name}: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for (name, _), result in zip(checks, results):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nПройдено: {passed}/{total}")
    
    if all(results):
        print("\n✓ Все проверки пройдены! Система готова к работе.")
        print("\nДля запуска выполните:")
        print("  python app.py          (Web-интерфейс)")
        print("  python monitor.py      (Мониторинг)")
        print("или:")
        print("  python run.py          (Запуск всего)")
        
        response = input("\nЗапустить тестирование работы системы? (y/n): ")
        if response.lower() == 'y':
            run_full_test()
    else:
        print("\n✗ Некоторые проверки не прошли. Исправьте ошибки перед запуском.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
