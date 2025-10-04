from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class TelegramUserCollector:
    """Telegram collector using User API (Telethon) - can read any public channel"""
    
    def __init__(self):
        self.api_id = Config.get('TELEGRAM_API_ID', '')
        self.api_hash = Config.get('TELEGRAM_API_HASH', '')
        self.phone = Config.get('TELEGRAM_PHONE', '')
        self.keywords = Config.COMPANY_KEYWORDS
        self.channels = Config.TELEGRAM_CHANNELS
        self.language_detector = LanguageDetector()
        self.client = None
        
        # Session file
        self.session_file = 'telegram_session'
        
        if not self.api_id or not self.api_hash:
            logger.warning("TELEGRAM_API_ID and TELEGRAM_API_HASH not configured")
            logger.info("Visit https://my.telegram.org to get API credentials")
    
    def _is_russian(self, text):
        if not Config.LANGUAGE_FILTER_ENABLED:
            return True
        return self.language_detector.is_russian(text)
    
    def _is_nizhny_region(self, text):
        if not Config.GEO_FILTER_ENABLED:
            return True
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in Config.GEO_KEYWORDS)
    
    def _is_relevant_to_company(self, text):
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Исключаем конкурентов и нерелевантные упоминания
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс', 'росатом', 'энергосбыт плюс',
            'энергосбыт луганск', 'энергосбыт волга', 'энергосбыт тюмень',
            'тнс тула', 'тнс великий новгород', 'тнс ярославль',
            'вакансия', 'вакансии', 'требуется', 'резюме'
        ]
        
        if any(exclude in text_lower for exclude in exclude_patterns):
            return False
        
        # Расширенные паттерны поиска (более гибкие)
        main_patterns = [
            'тнс энерго',  # Более общий паттерн
            'тнс нн',
            'тнсэнерго',
            'тнс-энерго'
        ]
        
        has_tns = any(pattern in text_lower for pattern in main_patterns)
        
        # Если нашли ТНС, проверяем что это про Нижний
        if has_tns:
            nizhny_patterns = ['нижний', 'нижегородск', 'нн', 'н.новгород', 'н новгород']
            # Проверяем наличие упоминания Нижнего в тексте (более мягкая проверка)
            has_nizhny = any(pattern in text_lower for pattern in nizhny_patterns)
            return has_nizhny or 'энерго нн' in text_lower
        
        # Также ищем упоминания энергосбыта в контексте Нижнего
        if 'энергосбыт' in text_lower:
            nizhny_patterns = ['нижний новгород', 'нижегородск', 'нн ', ' нн', 'нн,', 'нн.']
            return any(pattern in text_lower for pattern in nizhny_patterns)
        
        return False
    
    def _setup_proxy(self):
        """Setup proxy configuration for Telegram (Telethon)"""
        proxy_config = None
        
        # Check for Tor proxy
        use_tor = Config.get('USE_TOR', '').lower() == 'true'
        if use_tor:
            tor_host = Config.get('TOR_HOST', '127.0.0.1')
            tor_port = int(Config.get('TOR_PORT', '9050'))
            logger.info(f"Using Tor proxy for Telegram: socks5://{tor_host}:{tor_port}")
            return ('socks5', tor_host, tor_port)
        
        # Check for SOCKS proxy
        socks_proxy = Config.get('SOCKS_PROXY', '')
        if socks_proxy:
            # Parse proxy URL: socks5://host:port
            try:
                from urllib.parse import urlparse
                parsed = urlparse(socks_proxy)
                proxy_type = parsed.scheme if parsed.scheme else 'socks5'
                host = parsed.hostname if parsed.hostname else '127.0.0.1'
                port = parsed.port if parsed.port else 1080
                logger.info(f"Using SOCKS proxy for Telegram: {proxy_type}://{host}:{port}")
                return (proxy_type, host, port)
            except Exception as e:
                logger.error(f"Error parsing SOCKS proxy: {e}")
        
        # HTTP/HTTPS proxies are not natively supported by Telethon for Telegram MTProto
        http_proxy = Config.get('HTTP_PROXY', '')
        if http_proxy:
            logger.warning("HTTP proxies are not recommended for Telegram. Consider using SOCKS5 proxy instead.")
        
        return proxy_config
    
    async def init_client(self):
        """Initialize Telegram client"""
        if not self.api_id or not self.api_hash:
            return False
        
        try:
            proxy = self._setup_proxy()
            
            # Create Telegram client with optional proxy
            self.client = TelegramClient(
                self.session_file, 
                int(self.api_id), 
                self.api_hash,
                proxy=proxy
            )
            
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                logger.error("Telegram authorization required. Please run setup script first.")
                return False
            
            logger.info("Telegram client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {e}")
            return False
    
    async def get_channel_messages(self, channel_username, limit=200):
        """Get messages from a channel"""
        messages = []
        
        try:
            # Get the channel entity
            channel = await self.client.get_entity(channel_username)
            
            # Get messages from the last 30 days (увеличен период)
            offset_date = datetime.now() - timedelta(days=30)
            
            # Get channel history
            result = await self.client(GetHistoryRequest(
                peer=channel,
                offset_id=0,
                offset_date=offset_date,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            for message in result.messages:
                if not message.message:
                    continue
                
                text = message.message
                
                # Apply filters
                if not self._is_relevant_to_company(text):
                    continue
                if not self._is_nizhny_region(text):
                    continue
                if not self._is_russian(text):
                    continue
                
                messages.append({
                    'source_id': f"telegram_{channel.id}_{message.id}",
                    'author': channel.title or channel_username,
                    'author_id': str(channel.id),
                    'text': text,
                    'url': f"https://t.me/{channel_username.replace('@', '')}/{message.id}",
                    'published_date': message.date,
                    'source': 'telegram'
                })
                
            logger.info(f"Found {len(messages)} relevant messages from {channel_username}")
            
        except Exception as e:
            logger.error(f"Error getting messages from {channel_username}: {e}")
        
        return messages
    
    async def search_in_channels(self):
        """Search for keywords in configured channels"""
        if not await self.init_client():
            return []
        
        all_messages = []
        
        try:
            for channel in self.channels:
                if not channel.strip():
                    continue
                
                logger.info(f"Searching Telegram channel: {channel}")
                messages = await self.get_channel_messages(channel, limit=100)
                all_messages.extend(messages)
                
                # Small delay to avoid rate limits
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error searching Telegram channels: {e}")
        finally:
            if self.client:
                await self.client.disconnect()
        
        logger.info(f"Total messages collected from Telegram: {len(all_messages)}")
        return all_messages
    
    def collect(self):
        """Synchronous wrapper for async collect"""
        return asyncio.run(self.search_in_channels())
