"""
Улучшенный коллектор новостей с поддержкой RSS, прокси и множества источников
С интегрированным анализом тональности через Dostoevsky
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
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class NewsCollector:
    """Продвинутый коллектор новостей с RSS и веб-скрапингом"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.language_detector = LanguageDetector()
        self.sentiment_analyzer = sentiment_analyzer
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Отключаем прокси для новостей - они блокируют
        self.use_free_proxies = False
        self.proxy_manager = None
        self.current_proxy = None
        
        # Рабочие RSS feeds
        self.rss_feeds = []
        
        # Поисковые запросы для Google News (работает!)
        self.search_queries = [
            'ТНС энерго Нижний Новгород',
            'энергосбыт Нижний Новгород',
            'ТНС энерго НН отзывы'
        ]
    
    def _request_with_retry(self, url, max_retries=2, timeout=15):
        """Make HTTP request with retry"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=self.headers,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False  # Игнорировать SSL для RSS
                )
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        raise last_exception
    
    def _company_keywords(self):
        patterns = [kw.lower() for kw in getattr(Config, 'COMPANY_KEYWORDS', []) if kw]
        if not patterns:
            patterns = ['тнс энерго', 'тнс энерго нн', 'тнс нн', 'энергосбыт']
        return patterns
    
    def _is_relevant(self, text):
        """Check if text is relevant to company"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Исключаем нерелевантное
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс', 'росатом',
            'тнс тула', 'тнс великий новгород', 'тнс ярославль',
            'вакансия', 'вакансии', 'требуется', 'резюме'
        ]
        if any(exclude in text_lower for exclude in exclude_patterns):
            return False
        
        # Проверяем ключевые слова компании
        company_match = any(pattern in text_lower for pattern in self._company_keywords())
        if not company_match:
            # Дополнительные паттерны
            fallback_patterns = ['тнс', 'энерго', 'энергосбыт', 'электроэнерг', 'свет отключ']
            company_match = any(pattern in text_lower for pattern in fallback_patterns)
        
        return company_match
    
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
        geo_match = any(keyword.lower() in text_lower for keyword in Config.GEO_KEYWORDS)
        if geo_match:
            return True
        # Комбинированные токены
        combined_tokens = ['тнс энерго нн', 'тнсэнерго нн', 'энергосбыт нн', 'нижний', 'нижегородск']
        return any(token in text_lower for token in combined_tokens)
    
    def search_google_news(self, query):
        """Search Google News через RSS (работает!)"""
        articles = []
        
        try:
            # URL-кодируем запрос
            encoded_query = quote(f"{query} Нижний Новгород")
            search_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ru&gl=RU&ceid=RU:ru"
            
            logger.info(f"Searching Google News: {query}")
            
            response = self._request_with_retry(search_url, timeout=10)
            
            # Парсим XML
            soup = BeautifulSoup(response.content, 'xml')
            if not soup.find_all('item'):
                soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('item')[:20]  # Берем больше новостей
            
            for item in items:
                try:
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    link_tag = item.find('link')
                    pub_date_tag = item.find('pubDate')
                    
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    full_text = f"{title} {description}"
                    
                    if not self._is_relevant(full_text):
                        continue
                    
                    if not self._is_nizhny_region(full_text):
                        continue
                    
                    published_date = datetime.now()
                    if pub_date_tag:
                        try:
                            from email.utils import parsedate_to_datetime
                            published_date = parsedate_to_datetime(pub_date_tag.get_text(strip=True))
                        except:
                            pass
                    
                    article = {
                        'source_id': f"google_news_{hash(link)}",
                        'author': 'Google News',
                        'author_id': 'google_news',
                        'text': f"{title}\n\n{description[:500]}",
                        'url': link,
                        'published_date': published_date,
                        'source': 'news'
                    }
                    
                    # Анализ тональности
                    if self.sentiment_analyzer:
                        sentiment = self.sentiment_analyzer.analyze(article['text'])
                        article['sentiment_score'] = sentiment['sentiment_score']
                        article['sentiment_label'] = sentiment['sentiment_label']
                    
                    articles.append(article)
                    logger.debug(f"Found relevant article: {title[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"Error parsing article: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} articles from Google News for '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
        
        return articles
    
    def collect_from_newsnn(self):
        """Collect from NewsNN RSS (работает!)"""
        articles = []
        
        try:
            feed_url = 'https://newsnn.ru/rss/'
            logger.info(f"Parsing NewsNN RSS feed")
            
            response = self._request_with_retry(feed_url, timeout=10)
            
            soup = BeautifulSoup(response.content, 'xml')
            if not soup.find_all('item'):
                soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('item')[:50]  # Берем больше для фильтрации
            
            for item in items:
                try:
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    link_tag = item.find('link')
                    
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    full_text = f"{title} {description}"
                    
                    # Проверяем релевантность
                    if not self._is_relevant(full_text):
                        continue
                    
                    if not self._is_russian(full_text):
                        continue
                    
                    article = {
                        'source_id': f"newsnn_{hash(link)}",
                        'author': 'NewsNN',
                        'author_id': 'newsnn.ru',
                        'text': f"{title}\n\n{description[:500]}",
                        'url': link,
                        'published_date': datetime.now(),
                        'source': 'news'
                    }
                    
                    # Анализ тональности
                    if self.sentiment_analyzer:
                        sentiment = self.sentiment_analyzer.analyze(article['text'])
                        article['sentiment_score'] = sentiment['sentiment_score']
                        article['sentiment_label'] = sentiment['sentiment_label']
                    
                    articles.append(article)
                    logger.debug(f"Found relevant NewsNN article: {title[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"Error parsing NewsNN article: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} relevant articles from NewsNN")
            
        except Exception as e:
            logger.error(f"Error parsing NewsNN: {e}")
        
        return articles
    
    def parse_article_comments(self, article_url):
        """Parse comments from article page"""
        comments = []
        
        try:
            logger.info(f"Parsing comments from: {article_url}")
            
            # Пропускаем Google News ссылки - они редиректы
            if 'news.google.com' in article_url:
                return comments
            
            response = self._request_with_retry(article_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем комментарии
            comment_selectors = [
                {'class': 'comment'},
                {'class': 'comment-item'},
                {'class': 'comment-body'},
                {'class': 'comment-content'},
                {'class': 'user-comment'},
                {'id': 'comments'},
                {'class': 'comments'},
                {'class': 'comment-list'},
            ]
            
            for selector in comment_selectors:
                comment_elements = soup.find_all('div', selector) or soup.find_all('li', selector)
                
                if comment_elements:
                    for elem in comment_elements[:20]:  # Ограничиваем количество
                        try:
                            # Извлекаем текст
                            text_elem = elem.find(['p', 'div'], class_=lambda x: x and ('text' in x.lower() or 'content' in x.lower()))
                            if not text_elem:
                                text_elem = elem
                            
                            comment_text = text_elem.get_text(strip=True)
                            
                            if not comment_text or len(comment_text) < 10:
                                continue
                            
                            # Извлекаем автора
                            author_elem = elem.find(['span', 'a', 'div'], class_=lambda x: x and ('author' in x.lower() or 'user' in x.lower()))
                            author = author_elem.get_text(strip=True) if author_elem else 'Anonymous'
                            
                            comment = {
                                'text': comment_text[:500],  # Ограничиваем длину
                                'author': author,
                                'published_date': datetime.now(),
                                'source': 'news_comment',
                                'url': article_url
                            }
                            
                            comments.append(comment)
                            
                        except Exception as e:
                            logger.debug(f"Error parsing comment: {e}")
                            continue
                    
                    if comments:
                        break
            
            if comments:
                logger.info(f"Found {len(comments)} comments")
            
        except Exception as e:
            logger.debug(f"Error parsing comments from {article_url}: {e}")
        
        return comments
    
    def collect(self):
        """Main collection method"""
        all_articles = []
        
        logger.info("=" * 60)
        logger.info("Starting news collection")
        logger.info("=" * 60)
        
        # 1. Google News (основной источник - работает!)
        for query in self.search_queries[:2]:  # Берем первые 2 запроса
            try:
                articles = self.search_google_news(query)
                all_articles.extend(articles)
                time.sleep(1)  # Небольшая задержка между запросами
            except Exception as e:
                logger.error(f"Google News search failed for '{query}': {e}")
        
        # 2. NewsNN RSS (дополнительный источник)
        try:
            articles = self.collect_from_newsnn()
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"NewsNN collection failed: {e}")
        
        # Удаляем дубликаты по URL
        unique_articles = {}
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in unique_articles:
                unique_articles[url] = article
        
        all_articles = list(unique_articles.values())
        
        logger.info(f"Total unique articles collected: {len(all_articles)}")
        return all_articles
    
    def collect_with_comments(self):
        """Collect articles with comments"""
        articles = self.collect()
        all_data = []
        
        logger.info(f"Collecting comments for {len(articles)} articles")
        
        for article in articles:
            all_data.append(article)
            
            # Парсим комментарии для каждой статьи
            if article.get('url'):
                comments = self.parse_article_comments(article['url'])
                
                # Добавляем ссылку на статью к комментариям
                for comment in comments:
                    comment['parent_url'] = article['url']
                    comment['parent_source_id'] = article['source_id']
                    comment['source_id'] = f"{article['source_id']}_comment_{hash(comment['text'])}"
                    comment['is_comment'] = True
                    
                    # Анализ тональности для комментария
                    if self.sentiment_analyzer:
                        sentiment = self.sentiment_analyzer.analyze(comment['text'])
                        comment['sentiment_score'] = sentiment['sentiment_score']
                        comment['sentiment_label'] = sentiment['sentiment_label']
                
                all_data.extend(comments)
        
        logger.info(f"Total items (articles + comments): {len(all_data)}")
        return all_data
