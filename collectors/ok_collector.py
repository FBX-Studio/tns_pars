import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import time
import logging
import re
import json

logger = logging.getLogger(__name__)

class OKCollector:
    """Collector for Odnoklassniki posts"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.language_detector = LanguageDetector()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        
        # OK API credentials (if available)
        self.application_key = Config.get('OK_APPLICATION_KEY', '')
        self.access_token = Config.get('OK_ACCESS_TOKEN', '')
        
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
    
    def search_ok_web(self, query, max_posts=50):
        """Search Odnoklassniki via web search"""
        posts = []
        
        try:
            # OK search URL
            search_url = f"https://ok.ru/search?st.query={requests.utils.quote(query)}&st.mode=Users"
            
            logger.info(f"Searching Odnoklassniki (web): {query}")
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find posts/discussions
                # OK structure may vary, looking for common patterns
                post_elements = soup.find_all(['div', 'article'], class_=re.compile(r'post|feed-item|card'))
                
                for elem in post_elements[:max_posts]:
                    try:
                        # Get text content
                        text_elem = elem.find(['div', 'p'], class_=re.compile(r'text|content|body'))
                        if not text_elem:
                            continue
                        
                        text = text_elem.get_text(strip=True)
                        
                        if not self._is_relevant_to_company(text):
                            continue
                        
                        if not self._is_nizhny_region(text) or not self._is_russian(text):
                            continue
                        
                        # Get author
                        author_elem = elem.find(['a', 'span'], class_=re.compile(r'author|username|name'))
                        author = author_elem.get_text(strip=True) if author_elem else 'Unknown'
                        
                        # Get link
                        link_elem = elem.find('a', href=True)
                        url = link_elem['href'] if link_elem else ''
                        if url and not url.startswith('http'):
                            url = f"https://ok.ru{url}"
                        
                        # Get post ID from URL or generate from text
                        post_id = url.split('/')[-1] if url else str(hash(text))
                        
                        post = {
                            'source_id': f"ok_{post_id}",
                            'author': author,
                            'author_id': None,
                            'text': text,
                            'url': url,
                            'published_date': datetime.now() - timedelta(days=1),
                            'source': 'ok'
                        }
                        posts.append(post)
                        
                        if len(posts) >= max_posts:
                            break
                    except Exception as e:
                        logger.debug(f"Error parsing OK post: {e}")
                        continue
                
                logger.info(f"Found {len(posts)} posts from Odnoklassniki for '{query}'")
            else:
                logger.warning(f"OK search returned status {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error searching Odnoklassniki: {e}")
        
        time.sleep(3)  # Rate limiting
        return posts
    
    def search_ok_groups(self, group_ids=None):
        """Search in specific OK groups"""
        posts = []
        
        if not group_ids:
            # Default groups for Nizhny Novgorod
            group_ids = Config.get('OK_GROUP_IDS', '').split(',')
            group_ids = [g.strip() for g in group_ids if g.strip()]
        
        if not group_ids:
            logger.info("No OK groups configured")
            return posts
        
        for group_id in group_ids:
            try:
                url = f"https://ok.ru/group/{group_id}"
                
                logger.info(f"Checking OK group: {group_id}")
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find posts in group feed
                    feed_posts = soup.find_all(['div', 'article'], class_=re.compile(r'feed-item|post|card'))
                    
                    for elem in feed_posts[:20]:  # Limit per group
                        try:
                            text_elem = elem.find(['div', 'p'], class_=re.compile(r'text|content|body'))
                            if not text_elem:
                                continue
                            
                            text = text_elem.get_text(strip=True)
                            
                            if not self._is_relevant_to_company(text):
                                continue
                            
                            if not self._is_nizhny_region(text) or not self._is_russian(text):
                                continue
                            
                            author_elem = elem.find(['a', 'span'], class_=re.compile(r'author|username'))
                            author = author_elem.get_text(strip=True) if author_elem else group_id
                            
                            link_elem = elem.find('a', href=True)
                            post_url = link_elem['href'] if link_elem else url
                            if post_url and not post_url.startswith('http'):
                                post_url = f"https://ok.ru{post_url}"
                            
                            post_id = post_url.split('/')[-1] if post_url else str(hash(text))
                            
                            post = {
                                'source_id': f"ok_group_{group_id}_{post_id}",
                                'author': author,
                                'author_id': group_id,
                                'text': text,
                                'url': post_url,
                                'published_date': datetime.now() - timedelta(days=1),
                                'source': 'ok'
                            }
                            posts.append(post)
                        except Exception as e:
                            logger.debug(f"Error parsing group post: {e}")
                            continue
                
                time.sleep(2)  # Rate limiting between groups
                
            except Exception as e:
                logger.error(f"Error checking OK group {group_id}: {e}")
        
        logger.info(f"Found {len(posts)} posts from OK groups")
        return posts
    
    def collect(self):
        """Collect posts from Odnoklassniki"""
        all_posts = []
        
        # Web search queries
        queries = [
            "ТНС энерго Нижний Новгород",
            "ТНС энерго НН",
            "энергосбыт Нижний Новгород"
        ]
        
        for query in queries:
            posts = self.search_ok_web(query, max_posts=15)
            all_posts.extend(posts)
        
        # Check specific groups if configured
        group_posts = self.search_ok_groups()
        all_posts.extend(group_posts)
        
        # Remove duplicates by source_id
        seen = set()
        unique_posts = []
        for post in all_posts:
            if post['source_id'] not in seen:
                seen.add(post['source_id'])
                unique_posts.append(post)
        
        logger.info(f"Total unique posts collected from Odnoklassniki: {len(unique_posts)}")
        return unique_posts
