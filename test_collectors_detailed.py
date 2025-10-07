"""
Детальная проверка работы коллекторов с выводом результатов
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_telegram_detailed():
    """Детальный тест Telegram"""
    logger.info("=" * 70)
    logger.info("ТЕСТ TELEGRAM КОЛЛЕКТОРА")
    logger.info("=" * 70)
    
    try:
        from collectors.telegram_user_collector import TelegramUserCollector
        collector = TelegramUserCollector()
        
        logger.info(f"Ключевые слова: {collector.keywords}")
        logger.info(f"Каналов настроено: {len(collector.channels)}")
        logger.info(f"Первые 5 каналов: {collector.channels[:5]}")
        
        logger.info("\nЗапуск сбора (первые 2 канала для теста)...")
        # Тестируем только первые 2 канала для скорости
        original_channels = collector.channels
        collector.channels = collector.channels[:2]
        
        results = collector.collect(collect_comments=False)
        
        logger.info(f"\n✓ Найдено сообщений: {len(results)}")
        
        if results:
            logger.info("\nПример найденного сообщения:")
            sample = results[0]
            logger.info(f"  Канал: {sample.get('author', 'N/A')}")
            logger.info(f"  Текст: {sample.get('text', '')[:100]}...")
            logger.info(f"  Дата: {sample.get('published_date', 'N/A')}")
            return True
        else:
            logger.warning("⚠ Сообщения не найдены!")
            logger.info("Возможные причины:")
            logger.info("  1. Фильтры слишком строгие (ключевые слова)")
            logger.info("  2. В каналах нет недавних упоминаний компании")
            logger.info("  3. Проблемы с Telegram API")
            return False
            
    except Exception as e:
        logger.error(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zen_detailed():
    """Детальный тест Дзен"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ ЯНДЕКС.ДЗЕН КОЛЛЕКТОРА")
    logger.info("=" * 70)
    
    try:
        from collectors.zen_collector import ZenCollector
        collector = ZenCollector()
        
        logger.info(f"Ключевые слова: {collector.keywords}")
        logger.info(f"Количество: {len(collector.keywords)}")
        
        logger.info("\nЗапуск сбора (первое ключевое слово для теста)...")
        # Тестируем только первое ключевое слово
        test_keyword = collector.keywords[0] if collector.keywords else "ТНС энерго"
        logger.info(f"Тестовое слово: {test_keyword}")
        
        results = collector.search_dzen_yandex(test_keyword)
        
        logger.info(f"\n✓ Найдено статей: {len(results)}")
        
        if results:
            logger.info("\nПример найденной статьи:")
            sample = results[0]
            logger.info(f"  Источник: {sample.get('author', 'N/A')}")
            logger.info(f"  Текст: {sample.get('text', '')[:100]}...")
            logger.info(f"  URL: {sample.get('url', 'N/A')}")
            return True
        else:
            logger.warning("⚠ Статьи не найдены!")
            logger.info("Возможные причины:")
            logger.info("  1. Яндекс показывает капчу")
            logger.info("  2. Структура страницы Яндекса изменилась")
            logger.info("  3. Нет статей по ключевым словам в Дзене")
            logger.info("  4. Фильтры слишком строгие")
            return False
            
    except Exception as e:
        logger.error(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ok_detailed():
    """Детальный тест OK"""
    logger.info("\n" + "=" * 70)
    logger.info("ТЕСТ ОДНОКЛАССНИКИ КОЛЛЕКТОРА")
    logger.info("=" * 70)
    
    try:
        from collectors.ok_api_collector import OKAPICollector
        collector = OKAPICollector()
        
        logger.info(f"Токен: {collector.access_token[:20] if collector.access_token else 'НЕ НАСТРОЕН'}...")
        logger.info(f"Ключевые слова: {collector.keywords}")
        
        logger.info("\nЗапуск сбора...")
        results = collector.collect()
        
        logger.info(f"\n✓ Найдено постов: {len(results)}")
        
        if results:
            logger.info("\nПример найденного поста:")
            sample = results[0]
            logger.info(f"  Автор: {sample.get('author', 'N/A')}")
            logger.info(f"  Текст: {sample.get('text', '')[:100]}...")
            logger.info(f"  URL: {sample.get('url', 'N/A')}")
            return True
        else:
            logger.warning("⚠ Посты не найдены!")
            logger.info("Возможные причины:")
            logger.info("  1. API OK не возвращает результаты по поиску")
            logger.info("  2. Фильтры слишком строгие")
            logger.info("  3. Нет постов по ключевым словам")
            logger.info("  4. Проблемы с токеном или правами доступа")
            return False
            
    except Exception as e:
        logger.error(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    logger.info("ДЕТАЛЬНАЯ ПРОВЕРКА КОЛЛЕКТОРОВ")
    logger.info("=" * 70)
    
    results = {
        'Telegram': test_telegram_detailed(),
        'Яндекс.Дзен': test_zen_detailed(),
        'Одноклассники': test_ok_detailed()
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГИ")
    logger.info("=" * 70)
    
    for name, found_data in results.items():
        status = "✓ НАШЕЛ ДАННЫЕ" if found_data else "⚠ ДАННЫЕ НЕ НАЙДЕНЫ"
        logger.info(f"{name}: {status}")
    
    found_count = sum(results.values())
    logger.info(f"\nКоллекторов нашло данные: {found_count}/3")
    
    if found_count == 0:
        logger.warning("\n⚠ НИ ОДИН КОЛЛЕКТОР НЕ НАШЕЛ ДАННЫЕ!")
        logger.info("\nВозможные общие причины:")
        logger.info("1. Фильтры слишком строгие (COMPANY_KEYWORDS, GEO_KEYWORDS)")
        logger.info("2. За последние 30 дней нет упоминаний компании")
        logger.info("3. Проблемы с API ключами")
        logger.info("\nРекомендации:")
        logger.info("- Проверьте .env файл")
        logger.info("- Расширьте ключевые слова")
        logger.info("- Увеличьте период поиска")

if __name__ == '__main__':
    main()
