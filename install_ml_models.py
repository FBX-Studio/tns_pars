"""
Установка ML моделей для анализа тональности
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("="*70)
print("УСТАНОВКА ML МОДЕЛЕЙ ДЛЯ АНАЛИЗА ТОНАЛЬНОСТИ")
print("="*70)

models = {
    'RuBERT': {
        'packages': ['transformers', 'torch', 'torchvision'],
        'description': 'Лучшая точность для русского языка (BERT)',
        'size': '~500MB',
        'speed': 'Медленная',
        'accuracy': '★★★★★'
    },
    'Dostoevsky': {
        'packages': ['dostoevsky'],
        'description': 'Быстрая модель для русского (FastText)',
        'size': '~50MB',
        'speed': 'Быстрая',
        'accuracy': '★★★★☆'
    },
    'VADER': {
        'packages': ['vaderSentiment'],
        'description': 'Хорошо для соцсетей (английский)',
        'size': '~1MB',
        'speed': 'Очень быстрая',
        'accuracy': '★★★☆☆'
    },
    'TextBlob': {
        'packages': ['textblob'],
        'description': 'Простая модель (мультиязычная)',
        'size': '~5MB',
        'speed': 'Быстрая',
        'accuracy': '★★☆☆☆'
    }
}

print("\n📊 Доступные модели:\n")
for i, (name, info) in enumerate(models.items(), 1):
    print(f"{i}. {name}")
    print(f"   Описание: {info['description']}")
    print(f"   Размер: {info['size']}")
    print(f"   Скорость: {info['speed']}")
    print(f"   Точность: {info['accuracy']}")
    print(f"   Пакеты: {', '.join(info['packages'])}")
    print()

print("="*70)
print("РЕКОМЕНДАЦИЯ")
print("="*70)
print()
print("Для русского языка лучше всего:")
print("1. RuBERT - максимальная точность (если есть ресурсы)")
print("2. Dostoevsky - хороший баланс скорости и точности")
print()
print("Если нужна скорость:")
print("3. Dostoevsky - самая быстрая для русского")
print()

choice = input("\nУстановить ВСЕ модели? (y/n): ").lower()

if choice == 'y':
    print("\n" + "="*70)
    print("УСТАНОВКА МОДЕЛЕЙ")
    print("="*70)
    
    all_packages = set()
    for info in models.values():
        all_packages.update(info['packages'])
    
    for package in all_packages:
        print(f"\n[{package}] Установка...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ])
            print(f"✓ {package} установлен")
        except subprocess.CalledProcessError:
            print(f"✗ Ошибка установки {package}")
    
    # Дополнительная инициализация для досtoevsky
    if 'dostoevsky' in all_packages:
        print("\n[Dostoevsky] Загрузка модели...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'dostoevsky', 'download', 'fasttext-social-network-model'
            ])
            print("✓ Dostoevsky модель загружена")
        except:
            print("✗ Ошибка загрузки Dostoevsky модели (загрузится автоматически при первом использовании)")
    
    print("\n" + "="*70)
    print("✅ УСТАНОВКА ЗАВЕРШЕНА!")
    print("="*70)
    print("\nТеперь запустите тест:")
    print("python test_ml_sentiment.py")
    
else:
    print("\nВыберите модели для установки:")
    print("1 - RuBERT")
    print("2 - Dostoevsky (рекомендуется)")
    print("3 - VADER")
    print("4 - TextBlob")
    print("0 - Отмена")
    
    selected = input("\nВведите номера через запятую (например: 2,3): ").strip()
    
    if selected and selected != '0':
        model_list = list(models.keys())
        selected_indices = [int(x.strip()) - 1 for x in selected.split(',') if x.strip().isdigit()]
        
        packages_to_install = set()
        for idx in selected_indices:
            if 0 <= idx < len(model_list):
                model_name = model_list[idx]
                packages_to_install.update(models[model_name]['packages'])
                print(f"✓ Выбрана модель: {model_name}")
        
        if packages_to_install:
            print("\n" + "="*70)
            print("УСТАНОВКА ВЫБРАННЫХ МОДЕЛЕЙ")
            print("="*70)
            
            for package in packages_to_install:
                print(f"\n[{package}] Установка...")
                try:
                    subprocess.check_call([
                        sys.executable, '-m', 'pip', 'install', package
                    ])
                    print(f"✓ {package} установлен")
                except subprocess.CalledProcessError:
                    print(f"✗ Ошибка установки {package}")
            
            print("\n" + "="*70)
            print("✅ УСТАНОВКА ЗАВЕРШЕНА!")
            print("="*70)
            print("\nТеперь запустите тест:")
            print("python test_ml_sentiment.py")
    else:
        print("\nУстановка отменена.")

print("\n" + "="*70)
print("АЛЬТЕРНАТИВА: Ручная установка")
print("="*70)
print("\nДля RuBERT:")
print("pip install transformers torch")
print("\nДля Dostoevsky (рекомендуется):")
print("pip install dostoevsky")
print("python -m dostoevsky download fasttext-social-network-model")
print("\nДля VADER:")
print("pip install vaderSentiment")
print("\nДля TextBlob:")
print("pip install textblob")
print("="*70)
