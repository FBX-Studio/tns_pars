"""
Тест парсинга Яндекс.Дзен через Tor
"""
import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка настроек Tor
from config import Config

logger.info("=" * 70)
logger.info("ТЕСТ ПАРСИНГА ЯНДЕКС.ДЗЕН ЧЕРЕЗ TOR")
logger.info("=" * 70)

# Проверяем настройки
use_tor = Config.get('USE_TOR', '').lower() == 'true'
tor_proxy = Config.get('TOR_PROXY', 'socks5h://127.0.0.1:9150')
tor_host = Config.get('TOR_HOST', '127.0.0.1')
tor_port = Config.get('TOR_PORT', '9150')

logger.info(f"Настройки Tor:")
logger.info(f"  USE_TOR: {use_tor}")
logger.info(f"  TOR_PROXY: {tor_proxy}")
logger.info(f"  TOR_HOST: {tor_host}")
logger.info(f"  TOR_PORT: {tor_port}")

if not use_tor:
    logger.error("❌ USE_TOR=False - Tor не включен!")
    logger.info("Включите в .env: USE_TOR=True")
    sys.exit(1)

logger.info("✅ Tor включен в настройках")
logger.info("")

# Проверяем подключение к Tor
logger.info("Проверка подключения к Tor...")
import socket

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((tor_host, int(tor_port)))
    sock.close()
    
    if result == 0:
        logger.info(f"✅ Tor слушает на {tor_host}:{tor_port}")
    else:
        logger.error(f"❌ Tor НЕ доступен на {tor_host}:{tor_port}")
        logger.error("Убедитесь что Tor Browser запущен!")
        sys.exit(1)
except Exception as e:
    logger.error(f"❌ Ошибка проверки Tor: {e}")
    sys.exit(1)

logger.info("")

# Проверяем IP через Tor
logger.info("Проверка IP адреса через Tor...")
try:
    import requests
    
    # Запрос БЕЗ Tor
    logger.info("Получение IP без Tor...")
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        real_ip = response.json().get('ip', 'Unknown')
        logger.info(f"  Ваш реальный IP: {real_ip}")
    except:
        logger.warning("  Не удалось получить реальный IP")
        real_ip = "Unknown"
    
    # Запрос ЧЕРЕЗ Tor
    logger.info("Получение IP через Tor...")
    proxies = {
        'http': tor_proxy,
        'https': tor_proxy
    }
    
    response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=30)
    tor_ip = response.json().get('ip', 'Unknown')
    logger.info(f"  IP через Tor: {tor_ip}")
    
    if real_ip != "Unknown" and tor_ip != "Unknown" and real_ip != tor_ip:
        logger.info("✅ Tor работает! IP адреса отличаются")
    elif tor_ip != "Unknown":
        logger.info("✅ Подключение через Tor установлено")
    else:
        logger.warning("⚠️ Tor может не работать корректно")
        
except Exception as e:
    logger.error(f"❌ Ошибка проверки IP через Tor: {e}")
    logger.error("Возможно Tor не подключен к сети (застрял на bootstrap)")
    logger.info("\nПопробуйте настроить мосты в Tor Browser:")
    logger.info("  Settings → Connection → Bridges → obfs4")
    sys.exit(1)

logger.info("")
logger.info("=" * 70)
logger.info("ЗАПУСК ПАРСИНГА ДЗЕНА")
logger.info("=" * 70)

# Импортируем коллектор
try:
    from collectors.zen_collector import ZenCollector
    logger.info("✅ ZenCollector импортирован")
except Exception as e:
    logger.error(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Создаем коллектор
logger.info("")
logger.info("Создание коллектора...")
collector = ZenCollector()
logger.info("✅ Коллектор создан")

# Запускаем сбор
logger.info("")
logger.info("Запуск сбора данных из Дзена...")
logger.info("Это может занять 1-2 минуты...")
logger.info("")

try:
    articles = collector.collect(collect_comments=False)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("РЕЗУЛЬТАТЫ")
    logger.info("=" * 70)
    logger.info(f"✅ Найдено статей: {len(articles)}")
    
    if articles:
        logger.info("")
        logger.info("Первые 3 статьи:")
        for i, article in enumerate(articles[:3], 1):
            logger.info(f"\n{i}. {article.get('text', '')[:100]}...")
            logger.info(f"   URL: {article.get('url', 'N/A')}")
            logger.info(f"   Дата: {article.get('published_date', 'N/A')}")
    else:
        logger.warning("⚠️ Статьи не найдены")
        logger.info("\nВозможные причины:")
        logger.info("  1. Яндекс показал капчу (даже через Tor)")
        logger.info("  2. Нет статей по ключевым словам")
        logger.info("  3. Проблема с парсингом страниц")
        
except Exception as e:
    logger.error(f"❌ Ошибка при сборе: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

logger.info("")
logger.info("=" * 70)
logger.info("ТЕСТ ЗАВЕРШЕН")
logger.info("=" * 70)
