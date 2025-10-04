"""
Улучшенный коллектор новостей с поддержкой RSS, прокси и множества источников
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
from utils.language_detector import LanguageDetector
from utils.proxy_manager import ProxyManager
import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, quote

try:
    import feedparser
    HAS_FEEDPARSER = True
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"feedparser not available: {e}, using BeautifulSoup for RSS")
    HAS_FEEDPARSER = False

logger = logging.getLogger(__name__)

class NewsCollector:
    """Продвинутый коллектор новостей с RSS и веб-скрапингом"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.language_detector = LanguageDetector()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Настройка прокси
        self.use_free_proxies = Config.get('USE_FREE_PROXIES', 'True').lower() == 'true'
        self.proxy_manager = ProxyManager() if self.use_free_proxies else None
        self.current_proxy = None
        
        if not self.use_free_proxies:
            self.current_proxy = self._setup_static_proxy()
        
        # RSS feeds для новостей Нижнего Новгорода
        self.rss_feeds = [
            'https://nn.ru/rss.xml',
            'https://www.nn52.ru/rss',
            'https://www.niann.ru/rss/',
        ]
        
        # Поисковые запросы для Google News
        self.search_queries = [
            'ТНС энерго Нижний Новгород',
            'энергосбыт Нижний Новгород',
            'ТНС энерго НН отзывы'
        ]
    
    def _setup_static_proxy(self):
        """Setup static proxy from config"""
        proxies = {}
        
        use_tor = Config.get('USE_TOR', '').lower() == 'true'
        if use_tor:
            tor_proxy = Config.get('TOR_PROXY', 'socks5h://127.0.0.1:9050')
            proxies['http'] = tor_proxy
            proxies['https'] = tor_proxy
            logger.info(f"Using Tor proxy: {tor_proxy}")
            return proxies
        
        socks_proxy = Config.get('SOCKS_PROXY', '')
        if socks_proxy:
            proxies['http'] = socks_proxy
            proxies['https'] = socks_proxy
            logger.info(f"Using SOCKS proxy: {socks_proxy}")
            return proxies
        
        http_proxy = Config.get('HTTP_PROXY', '')
        https_proxy = Config.get('HTTPS_PROXY', '')
        
        if http_proxy:
            proxies['http'] = http_proxy
        if https_proxy:
            proxies['https'] = https_proxy
        
        return proxies if proxies else None
    
    def _get_proxy(self):
        """Get proxy for request"""
        if self.use_free_proxies and self.proxy_manager:
            proxy = self.proxy_manager.get_random_proxy()
            if proxy:
                return proxy
            logger.warning("No free proxies available")
        return self.current_proxy
    
    def _request_with_retry(self, url, max_retries=3, timeout=15, use_proxy=True):
        """Make HTTP request with retry and proxy rotation"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                proxy = self._get_proxy() if use_proxy else None
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    proxies=proxy, 
                    timeout=timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if self.use_free_proxies and proxy and self.proxy_manager:
                    self.proxy_manager.remove_proxy(proxy)
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        raise last_exception
    
    def _is_relevant(self, text):
        """Check if text is relevant to company"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Исключения
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс', 'росатом',
            'тнс тула', 'тнс великий новгород', 'тнс ярославль',
            'вакансия', 'вакансии', 'требуется', 'резюме'
        ]
        
        if any(exclude in text_lower for exclude in exclude_patterns):
            return False
        
        # Расширенные ключевые паттерны (более гибкие)
        main_patterns = [
            'тнс энерго нн',
            'тнс энерго нижний',
            'тнс энерго нижегородск',
            'тнс нн',
            'тнс нижний новгород',
            # Добавляем более общие паттерны
            'тнс энерго',  # Может быть с упоминанием НН рядом
            'энергосбыт нижний',
            'энергосбыт нн',
        ]
        
        # Проверяем основные паттерны
        has_main_pattern = any(pattern in text_lower for pattern in main_patterns)
        
        # Или проверяем комбинацию: ТНС/энергосбыт + Нижний/НН/Нижегородск
        has_company = any(word in text_lower for word in ['тнс', 'энергосбыт'])
        has_region = any(word in text_lower for word in ['нижний новгород', 'нижегородск', ' нн ', 'нн,', 'нн.'])
        
        return has_main_pattern or (has_company and has_region)
    
    def _is_russian(self, text):
        """Check if text is in Russian"""
        if not Config.LANGUAGE_FILTER_ENABLED:
            return True
        return self.language_detector.is_russian(text)
    
    def _is_nizhny_region(self, text):
        """Check if text mentions Nizhny Novgorod region"""
        if not Config.GEO_FILTER_ENABLED:
            return True
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in Config.GEO_KEYWORDS)
    
    def collect_from_rss(self, feed_url):
        """Collect news from RSS feed"""
        articles = []
        
        try:
            logger.info(f"Parsing RSS feed: {feed_url}")
            
            if HAS_FEEDPARSER:
                # Используем feedparser если доступен
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:50]:
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    full_text = f"{title} {description}"
                    
                    if not self._is_relevant(full_text):
                        continue
                    if not self._is_nizhny_region(full_text):
                        continue
                    if not self._is_russian(full_text):
                        continue
                    
                    published_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_date = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    
                    articles.append({
                        'source_id': f"rss_{hash(link)}",
                        'author': urlparse(feed_url).netloc,
                        'author_id': urlparse(feed_url).netloc,
                        'text': f"{title}\n\n{description[:500]}",
                        'url': link,
                        'published_date': published_date,
                        'source': 'news'
                    })
            else:
                # Альтернативный парсинг через BeautifulSoup
                response = self._request_with_retry(feed_url)
                soup = BeautifulSoup(response.content, 'xml') or BeautifulSoup(response.content, 'html.parser')
                
                for item in soup.find_all('item')[:50]:
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    link_tag = item.find('link')
                    
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    full_text = f"{title} {description}"
                    
                    if not self._is_relevant(full_text):
                        continue
                    if not self._is_nizhny_region(full_text):
                        continue
                    if not self._is_russian(full_text):
                        continue
                    
                    articles.append({
                        'source_id': f"rss_{hash(link)}",
                        'author': urlparse(feed_url).netloc,
                        'author_id': urlparse(feed_url).netloc,
                        'text': f"{title}\n\n{description[:500]}",
                        'url': link,
                        'published_date': datetime.now(),
                        'source': 'news'
                    })
            
            logger.info(f"Found {len(articles)} relevant articles from {feed_url}")
            
        except Exception as e:
            logger.error(f"Error parsing RSS {feed_url}: {e}")
        
        return articles
    
    def search_google_news(self, query):
        """Search Google News (через RSS)"""
        articles = []
        
        try:
            # Правильно кодируем URL, используя quote для параметра запроса
            encoded_query = quote(f"{query} Нижний Новгород")
            search_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ru&gl=RU&ceid=RU:ru"
            
            logger.info(f"Searching Google News: {query}")
            
            if HAS_FEEDPARSER:
                feed = feedparser.parse(search_url)
                
                for entry in feed.entries[:20]:
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    link = entry.get('link', '')
                    
                    full_text = f"{title} {description}"
                    
                    if not self._is_relevant(full_text):
                        continue
                    
                    published_date = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_date = datetime(*entry.published_parsed[:6])
                        except:
                            pass
                    
                    articles.append({
                        'source_id': f"google_news_{hash(link)}",
                        'author': 'Google News',
                        'author_id': 'google_news',
                        'text': f"{title}\n\n{description[:500]}",
                        'url': link,
                        'published_date': published_date,
                        'source': 'news'
                    })
            else:
                # Альтернативный парсинг
                response = self._request_with_retry(search_url)
                soup = BeautifulSoup(response.content, 'xml') or BeautifulSoup(response.content, 'html.parser')
                
                for item in soup.find_all('item')[:20]:
                    title_tag = item.find('title')
                    link_tag = item.find('link')
                    
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    if not self._is_relevant(title):
                        continue
                    
                    articles.append({
                        'source_id': f"google_news_{hash(link)}",
                        'author': 'Google News',
                        'author_id': 'google_news',
                        'text': title,
                        'url': link,
                        'published_date': datetime.now(),
                        'source': 'news'
                    })
            
            logger.info(f"Found {len(articles)} articles from Google News for '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
        
        return articles
    
    def search_yandex_news_rss(self, query):
        """Search Yandex News через RSS (бесплатный)"""
        articles = []
        
        try:
            # Yandex News RSS (бесплатный) - кодируем запрос
            encoded_query = quote(query)
            search_url = f"https://news.yandex.ru/yandsearch?cl4url=&lang=ru&lr=47&rpt=nnews2&text={encoded_query}"
            
            logger.info(f"Searching Yandex News: {query}")
            
            # Увеличенный таймаут и без прокси для Яндекса (они блокируют публичные прокси)
            response = self._request_with_retry(search_url, timeout=30, use_proxy=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Парсим результаты Yandex News
            for item in soup.find_all('div', class_='story')[:20]:
                title_tag = item.find('h2', class_='story__title')
                link_tag = item.find('a', class_='story__title-link')
                text_tag = item.find('div', class_='story__text')
                
                if not title_tag or not link_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                link = link_tag.get('href', '')
                description = text_tag.get_text(strip=True) if text_tag else ''
                
                full_text = f"{title} {description}"
                
                if not self._is_relevant(full_text):
                    continue
                
                articles.append({
                    'source_id': f"yandex_news_{hash(link)}",
                    'author': 'Yandex News',
                    'author_id': 'yandex_news',
                    'text': f"{title}\n\n{description[:500]}",
                    'url': link,
                    'published_date': datetime.now(),
                    'source': 'news'
                })
            
            logger.info(f"Found {len(articles)} articles from Yandex News for '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching Yandex News: {e}")
        
        return articles
    
    def collect(self):
        """Main collection method"""
        all_articles = []
        
        logger.info("=" * 60)
        logger.info("Starting news collection")
        logger.info("=" * 60)
        
        # 1. RSS feeds
        for feed_url in self.rss_feeds:
            articles = self.collect_from_rss(feed_url)
            all_articles.extend(articles)
            time.sleep(2)
        
        # 2. Google News
        for query in self.search_queries:
            articles = self.search_google_news(query)
            all_articles.extend(articles)
            time.sleep(3)  # Задержка между запросами
        
        # 3. Yandex News
        for query in self.search_queries:
            articles = self.search_yandex_news_rss(query)
            all_articles.extend(articles)
            time.sleep(5)  # Увеличенная задержка для Яндекса
        
        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
