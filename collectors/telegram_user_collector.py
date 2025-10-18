from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest, GetRepliesRequest
from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameNotOccupiedError
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import logging
import asyncio
import os
import time

logger = logging.getLogger(__name__)

class TelegramUserCollector:
    """Telegram collector using User API (Telethon) - can read any public channel"""
    
    def __init__(self, sentiment_analyzer=None):
        self.api_id = Config.get('TELEGRAM_API_ID', '')
        self.api_hash = Config.get('TELEGRAM_API_HASH', '')
        self.phone = Config.get('TELEGRAM_PHONE', '')
        self.keywords = Config.COMPANY_KEYWORDS
        self.channels = Config.TELEGRAM_CHANNELS
        self.language_detector = LanguageDetector()
        self.sentiment_analyzer = sentiment_analyzer
        self.client = None
        
        # Session file - используем уникальное имя для избежания блокировки
        import os
        import time
        self.session_file = f'telegram_session_{int(time.time())}'
        self.main_session = 'telegram_session'
        
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
            import shutil
            
            # Копируем основную сессию если она существует
            if os.path.exists(f'{self.main_session}.session'):
                try:
                    shutil.copy2(f'{self.main_session}.session', f'{self.session_file}.session')
                    logger.info(f"[TELEGRAM] Скопирована сессия из {self.main_session}")
                except Exception as e:
                    logger.warning(f"[TELEGRAM] Не удалось скопировать сессию: {e}")
            
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
    
    async def get_message_replies(self, channel, message):
        """Get replies (comments) for a specific message"""
        replies = []
        
        try:
            if not message.replies or message.replies.replies == 0:
                return []
            
            # Get replies for this message
            result = await self.client(GetRepliesRequest(
                peer=channel,
                msg_id=message.id,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            for reply in result.messages:
                if not reply.message:
                    continue
                
                reply_text = reply.message
                
                # Basic filters for replies
                if not self._is_russian(reply_text):
                    continue
                
                replies.append({
                    'text': reply_text,
                    'author': reply.post_author or f'User_{reply.from_id.user_id if reply.from_id else "unknown"}',
                    'author_id': str(reply.from_id.user_id if reply.from_id else 0),
                    'published_date': reply.date,
                    'source': 'telegram_comment'
                })
            
            logger.debug(f"Found {len(replies)} replies for message {message.id}")
            
        except Exception as e:
            logger.debug(f"Error getting replies for message {message.id}: {e}")
        
        return replies
    
    async def get_channel_messages(self, channel_username, limit=200, collect_comments=False):
        """Get messages from a channel with flood wait handling"""
        messages = []
        
        try:
            # Get the channel entity with flood wait handling
            try:
                channel = await self.client.get_entity(channel_username)
            except FloodWaitError as e:
                logger.warning(f"⏰ Flood wait для {channel_username}: нужно подождать {e.seconds} секунд")
                if e.seconds < 300:  # Если меньше 5 минут - ждем
                    logger.info(f"Ожидание {e.seconds} секунд...")
                    await asyncio.sleep(e.seconds + 5)
                    channel = await self.client.get_entity(channel_username)
                else:
                    logger.error(f"❌ Слишком долгое ожидание ({e.seconds}с), пропускаем канал")
                    return messages
            except (ChannelPrivateError, UsernameNotOccupiedError) as e:
                logger.warning(f"⚠️ Канал {channel_username} недоступен: {e}")
                return messages
            
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
                
                msg_data = {
                    'source_id': f"telegram_{channel.id}_{message.id}",
                    'author': channel.title or channel_username,
                    'author_id': str(channel.id),
                    'text': text,
                    'url': f"https://t.me/{channel_username.replace('@', '')}/{message.id}",
                    'published_date': message.date,
                    'source': 'telegram',
                    'is_comment': False
                }
                
                # Анализ тональности если доступен
                if self.sentiment_analyzer:
                    try:
                        sentiment = self.sentiment_analyzer.analyze(text)
                        msg_data['sentiment_score'] = sentiment.get('sentiment_score', 0)
                        msg_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                    except Exception as e:
                        logger.debug(f"Error analyzing message sentiment: {e}")
                
                messages.append(msg_data)
                
                # Collect comments/replies if requested
                if collect_comments:
                    replies = await self.get_message_replies(channel, message)
                    
                    for reply in replies:
                        reply['parent_source_id'] = msg_data['source_id']
                        reply['parent_url'] = msg_data['url']
                        reply['source_id'] = f"{msg_data['source_id']}_reply_{hash(reply['text'])}"
                        reply['url'] = msg_data['url']
                        reply['is_comment'] = True
                        
                        # Анализ тональности для комментария
                        if self.sentiment_analyzer:
                            try:
                                sentiment = self.sentiment_analyzer.analyze(reply['text'])
                                reply['sentiment_score'] = sentiment.get('sentiment_score', 0)
                                reply['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                            except Exception as e:
                                logger.debug(f"Error analyzing reply sentiment: {e}")
                        
                        messages.append(reply)
                    
                    if replies:
                        await asyncio.sleep(1)  # Увеличено с 0.3 до 1 сек
                
            logger.info(f"Found {len(messages)} relevant items from {channel_username}")
            
        except Exception as e:
            logger.error(f"Error getting messages from {channel_username}: {e}")
        
        return messages
    
    async def search_in_channels(self, collect_comments=False):
        """Search for keywords in configured channels"""
        if not await self.init_client():
            return []
        
        all_messages = []
        
        try:
            for channel in self.channels:
                if not channel.strip():
                    continue
                
                logger.info(f"Searching Telegram channel: {channel}")
                try:
                    messages = await self.get_channel_messages(channel, limit=100, collect_comments=collect_comments)
                    all_messages.extend(messages)
                except FloodWaitError as e:
                    logger.error(f"❌ Flood wait для {channel}: {e.seconds} секунд. Пропускаем оставшиеся каналы.")
                    break  # Прекращаем сбор, чтобы не усугублять
                
                # Увеличенная задержка между каналами (защита от FloodWait)
                await asyncio.sleep(10)  # 10 секунд для безопасности
            
        except Exception as e:
            logger.error(f"Error searching Telegram channels: {e}")
        finally:
            if self.client:
                await self.client.disconnect()
            
            # Удаляем временную сессию
            try:
                import glob
                for f in glob.glob(f'{self.session_file}*'):
                    os.remove(f)
                    logger.debug(f"[TELEGRAM] Удалён временный файл: {f}")
            except Exception as e:
                logger.debug(f"[TELEGRAM] Ошибка удаления временных файлов: {e}")
        
        logger.info(f"Total items collected from Telegram: {len(all_messages)}")
        return all_messages
    
    def collect(self, collect_comments=False, save_to_db=False):
        """
        Сбор сообщений из Telegram каналов
        
        Args:
            collect_comments: Собирать ли ответы (комментарии)
            save_to_db: Сохранять ли напрямую в БД через CommentHelper
        
        Returns:
            Список сообщений
        """
        logger.info("[TELEGRAM] Запуск сбора...")
        
        messages = asyncio.run(self.search_in_channels(collect_comments=collect_comments))
        
        # Если нужно сохранять в БД с правильной привязкой комментариев
        if save_to_db and messages:
            try:
                from utils.comment_helper import CommentHelper
                
                # Группируем посты и комментарии
                posts_dict = {}  # {source_id: post_data}
                comments_dict = {}  # {parent_source_id: [comments]}
                
                for msg in messages:
                    # Проверяем является ли это комментарием (ответом)
                    if msg.get('is_comment'):
                        parent_id = msg.get('parent_source_id', msg.get('parent_url', ''))
                        if parent_id:
                            if parent_id not in comments_dict:
                                comments_dict[parent_id] = []
                            # Убираем временные поля
                            msg.pop('parent_source_id', None)
                            msg.pop('parent_url', None)
                            comments_dict[parent_id].append(msg)
                    else:
                        # Это пост
                        posts_dict[msg['source_id']] = msg
                
                # Сохраняем посты с комментариями
                saved_count = 0
                comment_count = 0
                
                for source_id, post_data in posts_dict.items():
                    comments = comments_dict.get(source_id, [])
                    
                    saved_post, saved_comments = CommentHelper.save_post_with_comments(
                        post_data, comments, None
                    )
                    
                    if saved_post:
                        saved_count += 1
                        comment_count += len(saved_comments)
                
                logger.info(f"[TELEGRAM] ✓ Сохранено постов: {saved_count}, комментариев: {comment_count}")
                
            except Exception as e:
                logger.error(f"[TELEGRAM] Ошибка при сохранении: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"[TELEGRAM] Собрано сообщений: {len(messages)}")
        return messages
