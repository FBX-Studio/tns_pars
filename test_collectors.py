"""
Тестирование Selenium коллекторов
"""
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Установка UTF-8 для консоли Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_ok_collector():
    """Тест OK.ru коллектора"""
    print("\n" + "="*60)
    print("ТЕСТ 1: OK.ru Selenium Collector")
    print("="*60)
    
    try:
        from collectors.ok_selenium_collector import OKSeleniumCollector
        
        collector = OKSeleniumCollector()
        print("✓ OKSeleniumCollector создан")
        
        # Запускаем сбор (с ограничением времени)
        results = collector.collect()
        
        print(f"\n✓ Сбор завершен. Собрано постов: {len(results)}")
        
        if results:
            print("\nПримеры собранных постов:")
            for i, post in enumerate(results[:3], 1):
                print(f"\n{i}. Источник: {post.get('source')}")
                print(f"   Автор: {post.get('author', 'Unknown')}")
                print(f"   Текст: {post.get('text', '')[:100]}...")
                print(f"   URL: {post.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zen_selenium_collector():
    """Тест Яндекс.Дзен коллектора (zen_selenium_collector)"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Яндекс.Дзен Selenium Collector")
    print("="*60)
    
    try:
        from collectors.zen_selenium_collector import ZenSeleniumCollector
        
        collector = ZenSeleniumCollector()
        print("✓ ZenSeleniumCollector создан")
        
        # Запускаем сбор
        results = collector.collect()
        
        print(f"\n✓ Сбор завершен. Собрано статей: {len(results)}")
        
        if results:
            print("\nПримеры собранных статей:")
            for i, article in enumerate(results[:3], 1):
                print(f"\n{i}. Источник: {article.get('source')}")
                print(f"   Автор: {article.get('author', 'Unknown')}")
                print(f"   Текст: {article.get('text', '')[:100]}...")
                print(f"   URL: {article.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zen_collector_selenium():
    """Тест Яндекс.Дзен коллектора (zen_collector_selenium)"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Яндекс.Дзен Collector Selenium")
    print("="*60)
    
    try:
        from collectors.zen_collector_selenium import ZenCollectorSelenium
        
        collector = ZenCollectorSelenium()
        print("✓ ZenCollectorSelenium создан")
        
        # Запускаем сбор
        results = collector.collect()
        
        print(f"\n✓ Сбор завершен. Собрано статей: {len(results)}")
        
        if results:
            print("\nПримеры собранных статей:")
            for i, article in enumerate(results[:3], 1):
                print(f"\n{i}. Источник: {article.get('source')}")
                print(f"   Автор: {article.get('author', 'Unknown')}")
                print(f"   Текст: {article.get('text', '')[:100]}...")
                print(f"   URL: {article.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ SELENIUM КОЛЛЕКТОРОВ")
    print("="*60)
    
    results = {
        "OK.ru": test_ok_collector(),
        "Zen Selenium": test_zen_selenium_collector(),
        "Zen Collector Selenium": test_zen_collector_selenium()
    }
    
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    for name, success in results.items():
        status = "✓ УСПЕШНО" if success else "✗ ОШИБКА"
        print(f"{name}: {status}")
    print("="*60)
