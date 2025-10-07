import os
from dotenv import load_dotenv

# Загружаем .env с явным указанием кодировки UTF-8
load_dotenv(encoding='utf-8')

class Config:
    VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN', '')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///reviews.db')
    
    # Ключевые слова для мониторинга (с явной поддержкой UTF-8)
    # Hardcoded значения гарантируют правильное отображение
    COMPANY_KEYWORDS = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт', 'ТНС', 'TNS']
    
    # Попытка загрузить из .env (если там правильная кодировка)
    _keywords = os.getenv('COMPANY_KEYWORDS', '')
    if _keywords and _keywords.strip():
        try:
            loaded_keywords = [k.strip() for k in _keywords.split(',')]
            # Проверяем что загруженные значения содержат кириллицу
            if any('а' <= c <= 'я' or 'А' <= c <= 'Я' for keyword in loaded_keywords for c in keyword):
                COMPANY_KEYWORDS = loaded_keywords
        except:
            pass  # Используем hardcoded значения
    
    VK_GROUP_IDS = os.getenv('VK_GROUP_IDS', '').split(',') if os.getenv('VK_GROUP_IDS') else []
    VK_SEARCH_QUERY = os.getenv('VK_SEARCH_QUERY', 'ТНС энерго НН')
    
    TELEGRAM_CHANNELS = os.getenv('TELEGRAM_CHANNELS', '').split(',') if os.getenv('TELEGRAM_CHANNELS') else []
    
    NEWS_SITES = os.getenv('NEWS_SITES', 'https://nn.ru,https://www.vn.ru').split(',')
    
    # Яндекс.Дзен каналы
    DZEN_CHANNELS = os.getenv('DZEN_CHANNELS', '').split(',') if os.getenv('DZEN_CHANNELS') else []
    
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key_change_in_production')
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    MONITORING_INTERVAL_MINUTES = int(os.getenv('MONITORING_INTERVAL_MINUTES', 30))
    MAX_COMMENTS_PER_REQUEST = int(os.getenv('MAX_COMMENTS_PER_REQUEST', 100))
    
    BLOCK_WORDS = os.getenv('BLOCK_WORDS', '').split(',') if os.getenv('BLOCK_WORDS') else []
    NEGATIVE_THRESHOLD = float(os.getenv('NEGATIVE_THRESHOLD', -0.5))
    
    GEO_FILTER_ENABLED = os.getenv('GEO_FILTER_ENABLED', 'True') == 'True'
    GEO_KEYWORDS = os.getenv('GEO_KEYWORDS', 'Нижний Новгород,Нижегородск,НН,Nizhny Novgorod,нижний новгород,нижегородск').split(',')
    
    LANGUAGE_FILTER_ENABLED = os.getenv('LANGUAGE_FILTER_ENABLED', 'True') == 'True'
    ALLOWED_LANGUAGES = os.getenv('ALLOWED_LANGUAGES', 'ru').split(',')
    
    # Proxy settings
    USE_FREE_PROXIES = os.getenv('USE_FREE_PROXIES', 'True')
    HTTP_PROXY = os.getenv('HTTP_PROXY', '')
    HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')
    SOCKS_PROXY = os.getenv('SOCKS_PROXY', '')
    
    # Tor Browser settings
    USE_TOR = os.getenv('USE_TOR', 'False')
    TOR_PROXY = os.getenv('TOR_PROXY', 'socks5h://127.0.0.1:9050')
    TOR_HOST = os.getenv('TOR_HOST', '127.0.0.1')
    TOR_PORT = os.getenv('TOR_PORT', '9050')
    
    # Telegram User API settings (Telethon)
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID', '')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
    
    # OK API (Одноклассники)
    OK_APP_ID = os.getenv('OK_APP_ID', '')
    OK_PUBLIC_KEY = os.getenv('OK_PUBLIC_KEY', '')
    OK_SECRET_KEY = os.getenv('OK_SECRET_KEY', '')
    OK_ACCESS_TOKEN = os.getenv('OK_ACCESS_TOKEN', '')
    OK_GROUP_IDS = os.getenv('OK_GROUP_IDS', '')
    
    @classmethod
    def get(cls, key, default=''):
        return getattr(cls, key, default)
