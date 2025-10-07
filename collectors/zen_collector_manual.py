"""
Коллектор для Яндекс.Дзен по списку каналов (вручную)
Парсит RSS ленты конкретных каналов Дзена
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import time
import re
import feedparser

logger = logging.getLogger(__name__)

class ZenCollectorManual:
    """Коллектор статей из указанных каналов Яндекс.Дзен"""
    
    def __init__(self):
        self.channels = Config.DZEN_CHANNELS
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }
        
    def _is_relevant(self, text):
        """Проверка релевантности текста"""
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def _normalize_channel_url(self, channel):
        """Нормализация URL канала"""
        channel = channel.strip()
        
        # Если это уже полная ссылка
        if channel.startswith('http'):
            return channel
        
        # Если это ID канала
        if channel.startswith('id/'):
            return f'https://dzen.ru/{channel}'
        
        # Если просто ID
        return f'https://dzen.ru/id/{channel}'
    
    def parse_channel_rss(self, channel_url):
        """Парсинг RSS канала Дзен"""
        articles = []
        
        try:
            # RSS лента Дзен имеет формат: https://dzen.ru/id/CHANNEL_ID/rss
            if not channel_url.endswith('/rss'):
                rss_url = f"{channel_url.rstrip('/')}/rss"
            else:
                rss_url = channel_url
            
            logger.info(f"[DZEN-MANUAL] Парсинг канала: {rss_url}")
            
            # Пробуем через feedparser
            try:
                feed = feedparser.parse(rss_url)
                
                if not feed.entries:
                    logger.warning(f"[DZEN-MANUAL] Канал пуст: {rss_url}")
                    return []
                
                logger.info(f"[DZEN-MANUAL] Найдено статей: {len(feed.entries)}")
                
                for entry in feed.entries[:20]:  # Берем последние 20 статей
                    try:
                        title = entry.get('title', '')
                        description = entry.get('summary', entry.get('description', ''))
                        link = entry.get('link', '')
                        
                        # Извлекаем чистый текст из HTML описания
                        if description:
                            soup_desc = BeautifulSoup(description, 'html.parser')
                            description = soup_desc.get_text(strip=True)
                        
                        full_text = f"{title}\n\n{description}"
                        
                        # Проверяем релевантность
                        if not self._is_relevant(full_text):
                            continue
                        
                        # Парсим дату
                        pub_date = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                pub_date = datetime(*entry.published_parsed[:6])
                            except:
                                pass
                        
                        # Извлекаем ID статьи из URL
                        article_id = link.split('/a/')[-1] if '/a/' in link else abs(hash(link))
                        if '?' in str(article_id):
                            article_id = str(article_id).split('?')[0]
                        
                        date_str = pub_date.strftime('%Y%m%d')
                        
                        # Извлекаем автора (канал)
                        author = entry.get('author', 'Яндекс.Дзен')
                        
                        articles.append({
                            'source': 'zen',
                            'source_id': f"dzen_{article_id}_{date_str}",
                            'author': author,
                            'author_id': author.lower().replace(' ', '_').replace('.', '_'),
                            'text': full_text[:500],
                            'url': link,
                            'published_date': pub_date,
                            'date': pub_date
                        })
                        
                        logger.info(f"[DZEN-MANUAL] Релевантная: {title[:60]}...")
                        
                    except Exception as e:
                        logger.debug(f"[DZEN-MANUAL] Ошибка обработки статьи: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"[DZEN-MANUAL] Ошибка feedparser: {e}")
                # Пробуем вручную через requests
                return self._parse_channel_manual(rss_url)
            
        except Exception as e:
            logger.error(f"[DZEN-MANUAL] Ошибка парсинга канала {channel_url}: {e}")
        
        return articles
    
    def _parse_channel_manual(self, rss_url):
        """Ручной парсинг RSS если feedparser не работает"""
        articles = []
        
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"[DZEN-MANUAL] Статус {response.status_code} для {rss_url}")
                return []
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            logger.info(f"[DZEN-MANUAL] Найдено статей (вручную): {len(items)}")
            
            for item in items[:20]:
                try:
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    link_tag = item.find('link')
                    pubdate_tag = item.find('pubDate')
                    author_tag = item.find('author') or item.find('dc:creator')
                    
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    author = author_tag.get_text(strip=True) if author_tag else 'Яндекс.Дзен'
                    
                    # Очистка HTML из описания
                    if description:
                        soup_desc = BeautifulSoup(description, 'html.parser')
                        description = soup_desc.get_text(strip=True)
                    
                    full_text = f"{title}\n\n{description}"
                    
                    # Проверяем релевантность
                    if not self._is_relevant(full_text):
                        continue
                    
                    # Парсим дату
                    pub_date = datetime.now()
                    if pubdate_tag:
                        try:
                            from email.utils import parsedate_to_datetime
                            pub_date = parsedate_to_datetime(pubdate_tag.get_text(strip=True))
                        except:
                            pass
                    
                    # Извлекаем ID статьи
                    article_id = link.split('/a/')[-1] if '/a/' in link else abs(hash(link))
                    if '?' in str(article_id):
                        article_id = str(article_id).split('?')[0]
                    
                    date_str = pub_date.strftime('%Y%m%d')
                    
                    articles.append({
                        'source': 'zen',
                        'source_id': f"dzen_{article_id}_{date_str}",
                        'author': author,
                        'author_id': author.lower().replace(' ', '_').replace('.', '_'),
                        'text': full_text[:500],
                        'url': link,
                        'published_date': pub_date,
                        'date': pub_date
                    })
                    
                    logger.info(f"[DZEN-MANUAL] Релевантная: {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[DZEN-MANUAL] Ошибка обработки item: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"[DZEN-MANUAL] Ошибка ручного парсинга: {e}")
        
        return articles
    
    def collect(self):
        """Сбор статей из указанных каналов Дзена"""
        all_posts = []
        
        try:
            if not self.channels or (len(self.channels) == 1 and not self.channels[0].strip()):
                logger.warning("[DZEN-MANUAL] Список каналов пуст. Добавьте каналы в .env файл (DZEN_CHANNELS)")
                return []
            
            logger.info(f"[DZEN-MANUAL] Запуск сбора из {len(self.channels)} каналов Дзен")
            
            for channel in self.channels:
                if not channel.strip():
                    continue
                
                channel_url = self._normalize_channel_url(channel)
                logger.info(f"[DZEN-MANUAL] Обработка канала: {channel_url}")
                
                posts = self.parse_channel_rss(channel_url)
                all_posts.extend(posts)
                
                time.sleep(2)  # Задержка между каналами
            
            logger.info(f"[DZEN-MANUAL] Всего найдено релевантных статей: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[DZEN-MANUAL] Ошибка сбора: {e}")
        
        return all_posts
