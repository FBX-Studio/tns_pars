from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramCollector:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.keywords = Config.COMPANY_KEYWORDS
        self.channels = Config.TELEGRAM_CHANNELS
        self.language_detector = LanguageDetector()
        self.bot = None
        
        if self.bot_token:
            try:
                self.bot = Bot(token=self.bot_token)
            except Exception as e:
                logger.error(f"Error initializing Telegram Bot: {e}")
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not configured")
    
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
        text_lower = text.lower()
        
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс', 'росатом', 'энергосбыт плюс',
            'энергосбыт луганск', 'энергосбыт волга', 'энергосбыт тюмень',
            'тнс тула', 'тнс великий новгород', 'тнс ярославль',
            'вакансия', 'вакансии', 'требуется'
        ]
        
        if any(exclude in text_lower for exclude in exclude_patterns):
            return False
        
        main_patterns = [
            'тнс энерго нн',
            'тнс энерго нижний',
            'тнс энерго нижегородск',
            'тнс нн',
            'тнс нижний новгород'
        ]
        
        return any(pattern in text_lower for pattern in main_patterns)
    
    async def get_channel_messages(self, channel_username, limit=100):
        if not self.bot:
            return []
        
        messages = []
        try:
            updates = await self.bot.get_updates(limit=limit)
            
            for update in updates:
                if update.channel_post:
                    post = update.channel_post
                    text = post.text or post.caption or ''
                    
                    if self._is_relevant_to_company(text) and self._is_nizhny_region(text) and self._is_russian(text):
                        messages.append({
                            'source_id': f"telegram_{post.chat.id}_{post.message_id}",
                            'author': post.chat.title or post.chat.username or 'Unknown',
                            'author_id': str(post.chat.id),
                            'text': text,
                            'url': f"https://t.me/{channel_username}/{post.message_id}",
                            'published_date': post.date,
                            'source': 'telegram'
                        })
        except TelegramError as e:
            logger.error(f"Telegram API error for {channel_username}: {e}")
        except Exception as e:
            logger.error(f"Error getting Telegram messages: {e}")
        
        return messages
    
    async def search_in_channels(self):
        """Search for keywords in configured channels"""
        all_messages = []
        
        for channel in self.channels:
            if not channel.strip():
                continue
            
            logger.info(f"Searching Telegram channel: {channel}")
            messages = await self.get_channel_messages(channel)
            all_messages.extend(messages)
            await asyncio.sleep(1)
        
        return all_messages
    
    def collect(self):
        """Main collection method (sync wrapper)"""
        if not self.bot:
            logger.warning("Telegram bot not initialized")
            return []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            all_messages = loop.run_until_complete(self.search_in_channels())
            loop.close()
            
            logger.info(f"Collected {len(all_messages)} messages from Telegram")
            return all_messages
        except Exception as e:
            logger.error(f"Error in Telegram collection: {e}")
            return []
