"""
Скрипт для установки и настройки Dostoevsky
"""
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command):
    """Выполнение команды с выводом в реальном времени"""
    logger.info(f"Выполнение: {command}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Команда завершилась с ошибкой (код {process.returncode})")
            return False
        
        logger.info("✓ Команда выполнена успешно")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("Установка и настройка Dostoevsky")
    logger.info("=" * 60)
    
    # Шаг 1: Установка библиотеки
    logger.info("\n[1/2] Установка библиотеки dostoevsky...")
    if not run_command(f"{sys.executable} -m pip install dostoevsky"):
        logger.error("Не удалось установить dostoevsky")
        return False
    
    # Шаг 2: Загрузка моделей
    logger.info("\n[2/2] Загрузка предобученных моделей...")
    logger.info("Это может занять несколько минут...")
    
    if not run_command(f"{sys.executable} -m dostoevsky download fasttext-social-network-model"):
        logger.error("Не удалось загрузить модели")
        logger.info("\nПопробуйте загрузить модели вручную:")
        logger.info(f"  {sys.executable} -m dostoevsky download fasttext-social-network-model")
        return False
    
    # Шаг 3: Проверка установки
    logger.info("\n[3/3] Проверка установки...")
    try:
        from dostoevsky.tokenization import RegexTokenizer
        from dostoevsky.models import FastTextSocialNetworkModel
        
        logger.info("Инициализация модели...")
        tokenizer = RegexTokenizer()
        model = FastTextSocialNetworkModel(tokenizer=tokenizer)
        
        logger.info("Тестирование на примере...")
        test_texts = [
            "Отличный сервис, быстро и качественно!",
            "Ужасное обслуживание, больше никогда",
            "Всё нормально, ничего особенного"
        ]
        
        results = model.predict(test_texts, k=2)
        
        logger.info("\nРезультаты тестирования:")
        for text, result in zip(test_texts, results):
            logger.info(f"  Текст: {text}")
            logger.info(f"  Результат: {result}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Dostoevsky успешно установлен и настроен!")
        logger.info("=" * 60)
        logger.info("\nТеперь можно запустить приложение:")
        logger.info("  python app_enhanced.py")
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Ошибка при проверке установки: {e}")
        logger.error("\nПопробуйте:")
        logger.error("1. Переустановить библиотеку: pip uninstall dostoevsky && pip install dostoevsky")
        logger.error("2. Загрузить модели заново: python -m dostoevsky download fasttext-social-network-model")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nНеожиданная ошибка: {e}")
        sys.exit(1)
