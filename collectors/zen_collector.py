import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import time
import logging
import json
import re

logger = logging.getLogger(__name__)

class ZenCollector:
    """Collector for Yandex Zen articles"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.language_detector = LanguageDetector()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
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
        """Check if text is relevant to TNS Energo Nizhny Novgorod"""
        text_lower = text.lower()
        
        # Exclude patterns
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс', 'росатом', 'энергосбыт плюс',
            'энергосбыт луганск', 'энергосбыт волга', 'энергосбыт тюмень',
            'тнс тула', 'тнс великий новгород', 'тнс ярославль',
            'вакансия', 'вакансии', 'требуется'
        ]
        
        if any(exclude in text_lower for exclude in exclude_patterns):
            return False
        
        # Main patterns
        main_patterns = [
            'тнс энерго нн',
            'тнс энерго нижний',
            'тнс энерго нижегородск',
            'тнс нн',
            'тнс нижний новгород',
            'энергосбыт нижний новгород'
        ]
        
        return any(pattern in text_lower for pattern in main_patterns)
    
    def search_zen(self, query, max_articles=50):
        """Search Yandex Zen for articles matching query"""
        articles = []
        
        try:
            # Yandex Zen search URL
            search_url = f"https://dzen.ru/search?text={requests.utils.quote(query)}"
            
            logger.info(f"Searching Yandex Zen: {query}")
            
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find article links
            # Yandex Zen uses dynamic loading, so we try to extract from script tags
            scripts = soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Article':
                        title = data.get('headline', '')
                        description = data.get('description', '')
                        text = f"{title}. {description}"
                        
                        if not self._is_relevant_to_company(text):
                            continue
                        
                        if not self._is_nizhny_region(text) or not self._is_russian(text):
                            continue
                        
                        article = {
                            'source_id': f"zen_{data.get('url', '').split('/')[-1]}",
                            'author': data.get('author', {}).get('name', 'Unknown'),
                            'author_id': None,
                            'text': text,
                            'url': data.get('url', ''),
                            'published_date': self._parse_date(data.get('datePublished')),
                            'source': 'zen'
                        }
                        articles.append(article)
                        
                        if len(articles) >= max_articles:
                            break
                except json.JSONDecodeError:
                    continue
            
            # Alternative: try to find article cards in HTML
            if not articles:
                article_cards = soup.find_all(['article', 'div'], class_=re.compile(r'article|card|item'))
                
                for card in article_cards[:max_articles]:
                    try:
                        title_elem = card.find(['h1', 'h2', 'h3', 'a'])
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        
                        # Get link
                        link_elem = card.find('a', href=True)
                        url = link_elem['href'] if link_elem else ''
                        if url and not url.startswith('http'):
                            url = f"https://dzen.ru{url}"
                        
                        # Get description
                        desc_elem = card.find(['p', 'div'], class_=re.compile(r'description|snippet|summary'))
                        description = desc_elem.get_text(strip=True) if desc_elem else ''
                        
                        text = f"{title}. {description}"
                        
                        if not self._is_relevant_to_company(text):
                            continue
                        
                        if not self._is_nizhny_region(text) or not self._is_russian(text):
                            continue
                        
                        article = {
                            'source_id': f"zen_{url.split('/')[-1] if url else hash(text)}",
                            'author': 'Unknown',
                            'author_id': None,
                            'text': text,
                            'url': url,
                            'published_date': datetime.now() - timedelta(days=1),
                            'source': 'zen'
                        }
                        articles.append(article)
                        
                        if len(articles) >= max_articles:
                            break
                    except Exception as e:
                        logger.debug(f"Error parsing article card: {e}")
                        continue
            
            logger.info(f"Found {len(articles)} articles from Yandex Zen for '{query}'")
            
        except Exception as e:
            logger.error(f"Error searching Yandex Zen: {e}")
        
        time.sleep(3)  # Rate limiting
        return articles
    
    def _parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return datetime.now() - timedelta(days=1)
        
        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try other common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d.%m.%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
            except:
                pass
        
        return datetime.now() - timedelta(days=1)
    
    def collect(self):
        """Collect articles from Yandex Zen"""
        all_articles = []
        
        # Search queries
        queries = [
            "ТНС энерго Нижний Новгород",
            "ТНС энерго НН",
            "энергосбыт Нижний Новгород"
        ]
        
        for query in queries:
            articles = self.search_zen(query, max_articles=20)
            all_articles.extend(articles)
        
        # Remove duplicates by source_id
        seen = set()
        unique_articles = []
        for article in all_articles:
            if article['source_id'] not in seen:
                seen.add(article['source_id'])
                unique_articles.append(article)
        
        logger.info(f"Total unique articles collected from Yandex Zen: {len(unique_articles)}")
        return unique_articles
