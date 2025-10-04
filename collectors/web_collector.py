import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
from utils.language_detector import LanguageDetector
from utils.proxy_manager import ProxyManager
import logging
import time
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class WebCollector:
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.news_sites = Config.NEWS_SITES
        self.language_detector = LanguageDetector()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Настройка прокси
        self.use_free_proxies = Config.get('USE_FREE_PROXIES', 'True').lower() == 'true'
        self.proxy_manager = ProxyManager() if self.use_free_proxies else None
        self.current_proxy = None
        
        # Инициализируем прокси при создании
        if not self.use_free_proxies:
            self.current_proxy = self._setup_static_proxy()
        else:
            logger.info("Free proxy mode enabled. Proxies will be fetched automatically.")
    
    def _setup_static_proxy(self):
        """Setup static proxy configuration from .env"""
        proxies = {}
        
        # Check for Tor proxy
        use_tor = Config.get('USE_TOR', '').lower() == 'true'
        if use_tor:
            tor_proxy = Config.get('TOR_PROXY', 'socks5h://127.0.0.1:9050')
            proxies['http'] = tor_proxy
            proxies['https'] = tor_proxy
            logger.info(f"Using Tor proxy: {tor_proxy}")
            return proxies
        
        # Check for SOCKS proxy (has priority)
        socks_proxy = Config.get('SOCKS_PROXY', '')
        if socks_proxy:
            proxies['http'] = socks_proxy
            proxies['https'] = socks_proxy
            logger.info(f"Using SOCKS proxy: {socks_proxy}")
            return proxies
        
        # Check for HTTP/HTTPS proxies
        http_proxy = Config.get('HTTP_PROXY', '')
        https_proxy = Config.get('HTTPS_PROXY', '')
        
        if http_proxy:
            proxies['http'] = http_proxy
            logger.info(f"Using HTTP proxy: {http_proxy}")
        if https_proxy:
            proxies['https'] = https_proxy
            logger.info(f"Using HTTPS proxy: {https_proxy}")
        
        return proxies if proxies else None
    
    def _get_proxy(self):
        """Get proxy for request (free or static)"""
        if self.use_free_proxies and self.proxy_manager:
            proxy = self.proxy_manager.get_random_proxy()
            if proxy:
                logger.debug(f"Using free proxy: {proxy.get('http', 'Unknown')}")
                return proxy
            logger.warning("No free proxies available, trying without proxy")
            return None
        return self.current_proxy
    
    def _request_with_retry(self, url, max_retries=3):
        """Make request with retry logic and proxy rotation"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                proxy = self._get_proxy()
                
                logger.debug(f"Attempt {attempt + 1}/{max_retries} for {url}")
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    proxies=proxy, 
                    timeout=10
                )
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Если используем бесплатные прокси и запрос провалился, удаляем прокси
                if self.use_free_proxies and proxy and self.proxy_manager:
                    self.proxy_manager.remove_proxy(proxy)
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_exception
    
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
    
    def scrape_page(self, url):
        """Scrape a single page for mentions"""
        try:
            response = self._request_with_retry(url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            
            for tag in soup.find_all(['article', 'div'], class_=lambda x: x and ('news' in x.lower() or 'article' in x.lower() or 'post' in x.lower())):
                text_content = tag.get_text(separator=' ', strip=True)
                
                if self._is_relevant_to_company(text_content) and self._is_nizhny_region(text_content) and self._is_russian(text_content):
                    title = tag.find(['h1', 'h2', 'h3', 'h4'])
                    title_text = title.get_text(strip=True) if title else ''
                    
                    link_tag = tag.find('a', href=True)
                    article_url = urljoin(url, link_tag['href']) if link_tag else url
                    
                    date_tag = tag.find(['time', 'span'], class_=lambda x: x and 'date' in x.lower())
                    published_date = None
                    if date_tag:
                        try:
                            date_str = date_tag.get('datetime') or date_tag.get_text(strip=True)
                            published_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            published_date = datetime.now()
                    else:
                        published_date = datetime.now()
                    
                    articles.append({
                        'source_id': f"web_{hash(article_url)}",
                        'author': urlparse(url).netloc,
                        'author_id': urlparse(url).netloc,
                        'text': f"{title_text}\n\n{text_content[:500]}",
                        'url': article_url,
                        'published_date': published_date,
                        'source': 'web'
                    })
            
            if not articles:
                full_text = soup.get_text(separator=' ', strip=True)
                if self._is_relevant_to_company(full_text) and self._is_nizhny_region(full_text) and self._is_russian(full_text):
                    title = soup.find('title')
                    title_text = title.get_text(strip=True) if title else 'No title'
                    
                    articles.append({
                        'source_id': f"web_{hash(url)}",
                        'author': urlparse(url).netloc,
                        'author_id': urlparse(url).netloc,
                        'text': f"{title_text}\n\n{full_text[:500]}",
                        'url': url,
                        'published_date': datetime.now(),
                        'source': 'web'
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
    
    def search_yandex_news(self, query):
        articles = []
        try:
            search_url = f"https://news.yandex.ru/search?text={query} Нижний Новгород"
            response = self._request_with_retry(search_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.find_all('div', class_='story'):
                title_tag = item.find('h2')
                link_tag = item.find('a', href=True)
                snippet_tag = item.find('div', class_='story__text')
                
                if title_tag and link_tag:
                    title = title_tag.get_text(strip=True)
                    url = link_tag['href']
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    full_text = f"{title}\n\n{snippet}"
                    if self._is_nizhny_region(full_text) and self._is_russian(full_text):
                        articles.append({
                            'source_id': f"web_{hash(url)}",
                            'author': 'Yandex News',
                            'author_id': 'yandex_news',
                            'text': full_text,
                            'url': url,
                            'published_date': datetime.now(),
                            'source': 'web'
                        })
        except Exception as e:
            logger.error(f"Error searching Yandex News: {e}")
        
        return articles
    
    def collect(self):
        all_articles = []
        
        for site in self.news_sites:
            if not site.strip():
                continue
            
            logger.info(f"Scraping website: {site}")
            articles = self.scrape_page(site)
            all_articles.extend(articles)
            time.sleep(2)
        
        search_queries = ['ТНС энерго Нижний Новгород', 'энергосбыт Нижний Новгород']
        for query in search_queries:
            logger.info(f"Searching Yandex News for: {query}")
            news_articles = self.search_yandex_news(query)
            all_articles.extend(news_articles)
            time.sleep(2)
        
        logger.info(f"Collected {len(all_articles)} articles from web")
        return all_articles
