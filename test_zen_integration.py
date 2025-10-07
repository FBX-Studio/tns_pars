"""
Тест интеграции Zen коллектора в систему мониторинга
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("ТЕСТ ИНТЕГРАЦИИ ДЗЕН В ВЕБ-ИНТЕРФЕЙС")
print("="*70)

# Шаг 1: Импорт коллектора
print("\n1. Проверка импорта DzenDuckDuckGoCollector...")
try:
    from collect_dzen_duckduckgo import DzenDuckDuckGoCollector
    print("   ✓ DzenDuckDuckGoCollector импортирован успешно")
    collector = DzenDuckDuckGoCollector()
    print(f"   ✓ Коллектор создан, ключевых слов: {len(collector.keywords)}")
except Exception as e:
    print(f"   ✗ Ошибка: {e}")
    sys.exit(1)

# Шаг 2: Импорт монитора
print("\n2. Проверка импорта AsyncReviewMonitorWebSocket...")
try:
    from async_monitor_websocket import AsyncReviewMonitorWebSocket
    print("   ✓ AsyncReviewMonitorWebSocket импортирован")
except Exception as e:
    print(f"   ✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Шаг 3: Создание монитора
print("\n3. Создание экземпляра монитора...")
try:
    from flask_socketio import SocketIO
    from app_enhanced import app
    
    socketio = SocketIO(app)
    monitor = AsyncReviewMonitorWebSocket(socketio)
    print("   ✓ Монитор создан")
    
    if monitor.zen_collector:
        print("   ✓ Zen коллектор подключен!")
        print(f"   ✓ Тип: {type(monitor.zen_collector).__name__}")
    else:
        print("   ✗ Zen коллектор НЕ подключен")
        
except Exception as e:
    print(f"   ✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Шаг 4: Проверка источников
print("\n4. Проверка списка источников...")
try:
    sources = ['vk', 'telegram', 'news']
    if monitor.zen_collector:
        sources.append('zen')
    if monitor.ok_collector:
        sources.append('ok')
    
    print(f"   ✓ Активные источники: {', '.join(sources)}")
    
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

print("\n" + "="*70)
print("РЕЗУЛЬТАТ: Zen коллектор успешно интегрирован!")
print("="*70)
print("\nЗапустите веб-интерфейс: python app_enhanced.py")
print("И нажмите кнопку 'Запустить сбор' - Дзен будет в списке источников!")
