import vk_api
from datetime import datetime, timedelta
from config import Config
from utils.language_detector import LanguageDetector
import time
import logging

logger = logging.getLogger(__name__)

class VKCollector:
    def __init__(self):
        self.access_token = Config.VK_ACCESS_TOKEN
        self.keywords = Config.COMPANY_KEYWORDS
        self.max_comments = Config.MAX_COMMENTS_PER_REQUEST
        self.language_detector = LanguageDetector()
        self.proxies = self._setup_proxy()
        
        if self.access_token:
            try:
                # Setup VK session with proxy support
                session_params = {'token': self.access_token}
                
                # VK API uses requests session internally
                if self.proxies:
                    import requests
                    session = requests.Session()
                    session.proxies.update(self.proxies)
                    self.vk_session = vk_api.VkApi(**session_params, session=session)
                else:
                    self.vk_session = vk_api.VkApi(**session_params)
                
                self.vk = self.vk_session.get_api()
            except Exception as e:
                logger.error(f"Error initializing VK API: {e}")
                self.vk = None
        else:
            self.vk = None
            logger.warning("VK_ACCESS_TOKEN not configured")
    
    def _setup_proxy(self):
        """Setup proxy configuration for VK API"""
        proxies = {}
        
        # Check for Tor proxy
        use_tor = Config.get('USE_TOR', '').lower() == 'true'
        if use_tor:
            tor_proxy = Config.get('TOR_PROXY', 'socks5h://127.0.0.1:9050')
            proxies['http'] = tor_proxy
            proxies['https'] = tor_proxy
            logger.info(f"Using Tor proxy for VK: {tor_proxy}")
            return proxies
        
        # Check for SOCKS proxy
        socks_proxy = Config.get('SOCKS_PROXY', '')
        if socks_proxy:
            proxies['http'] = socks_proxy
            proxies['https'] = socks_proxy
            logger.info(f"Using SOCKS proxy for VK: {socks_proxy}")
            return proxies
        
        # Check for HTTP/HTTPS proxies
        http_proxy = Config.get('HTTP_PROXY', '')
        https_proxy = Config.get('HTTPS_PROXY', '')
        
        if http_proxy:
            proxies['http'] = http_proxy
            logger.info(f"Using HTTP proxy for VK: {http_proxy}")
        if https_proxy:
            proxies['https'] = https_proxy
            logger.info(f"Using HTTPS proxy for VK: {https_proxy}")
        
        return proxies if proxies else None
    
    def _is_russian(self, text):
        if not Config.LANGUAGE_FILTER_ENABLED:
            return True
        return self.language_detector.is_russian(text)
    
    def _is_nizhny_region(self, text, geo_data=None):
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
    
    def search_posts(self, query, count=100):
        if not self.vk:
            logger.warning("VK API not initialized")
            return []
        
        try:
            results = self.vk.newsfeed.search(
                q=query,
                count=min(count, 200),
                extended=1
            )
            
            posts = []
            for item in results.get('items', []):
                text = item.get('text', '')
                
                if not self._is_relevant_to_company(text):
                    continue
                
                if not self._is_nizhny_region(text) or not self._is_russian(text):
                    continue
                
                post = {
                    'source_id': f"vk_post_{item['owner_id']}_{item['id']}",
                    'author': self._get_author_name(item, results),
                    'author_id': str(item.get('owner_id', '')),
                    'text': text,
                    'url': f"https://vk.com/wall{item['owner_id']}_{item['id']}",
                    'published_date': datetime.fromtimestamp(item.get('date', 0)),
                    'source': 'vk'
                }
                posts.append(post)
            
            return posts
        except Exception as e:
            logger.error(f"Error searching VK posts: {e}")
            return []
    
    def get_wall_comments(self, owner_id, post_id, count=100):
        if not self.vk:
            return []
        
        try:
            comments = self.vk.wall.getComments(
                owner_id=owner_id,
                post_id=post_id,
                count=min(count, 100),
                extended=1,
                need_likes=1
            )
            
            result = []
            for comment in comments.get('items', []):
                text = comment.get('text', '')
                if text and self._is_relevant_to_company(text) and self._is_nizhny_region(text) and self._is_russian(text):
                    result.append({
                        'source_id': f"vk_comment_{owner_id}_{post_id}_{comment['id']}",
                        'author': self._get_comment_author(comment, comments),
                        'author_id': str(comment.get('from_id', '')),
                        'text': text,
                        'url': f"https://vk.com/wall{owner_id}_{post_id}?reply={comment['id']}",
                        'published_date': datetime.fromtimestamp(comment.get('date', 0)),
                        'source': 'vk'
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error getting VK comments: {e}")
            return []
    
    def monitor_groups(self, group_ids):
        all_posts = []
        
        for group_id in group_ids:
            if not group_id.strip():
                continue
            
            try:
                posts = self.vk.wall.get(
                    owner_id=f"-{group_id}" if not group_id.startswith('-') else group_id,
                    count=100
                )
                
                for post in posts.get('items', []):
                    text = post.get('text', '')
                    
                    if self._is_relevant_to_company(text) and self._is_nizhny_region(text) and self._is_russian(text):
                        all_posts.append({
                            'source_id': f"vk_post_{post['owner_id']}_{post['id']}",
                            'author': f"Group {group_id}",
                            'author_id': str(post.get('owner_id', '')),
                            'text': text,
                            'url': f"https://vk.com/wall{post['owner_id']}_{post['id']}",
                            'published_date': datetime.fromtimestamp(post.get('date', 0)),
                            'source': 'vk'
                        })
                
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error monitoring group {group_id}: {e}")
        
        return all_posts
    
    def collect(self):
        all_reviews = []
        
        search_queries = [
            'ТНС энерго Нижний Новгород',
            'ТНС энерго НН',
            'энергосбыт Нижний Новгород'
        ]
        
        for query in search_queries:
            logger.info(f"Searching VK for: {query}")
            posts = self.search_posts(query, count=self.max_comments)
            all_reviews.extend(posts)
            time.sleep(1)
        
        if Config.VK_GROUP_IDS:
            logger.info(f"Monitoring VK groups: {Config.VK_GROUP_IDS}")
            group_posts = self.monitor_groups(Config.VK_GROUP_IDS)
            all_reviews.extend(group_posts)
        
        logger.info(f"Collected {len(all_reviews)} reviews from VK")
        return all_reviews
    
    def _get_author_name(self, item, results):
        """Get author name from extended results"""
        owner_id = item.get('owner_id')
        if owner_id > 0:
            profiles = results.get('profiles', [])
            for profile in profiles:
                if profile['id'] == owner_id:
                    return f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
        else:
            groups = results.get('groups', [])
            for group in groups:
                if group['id'] == abs(owner_id):
                    return group.get('name', 'Unknown')
        return 'Unknown'
    
    def _get_comment_author(self, comment, comments):
        """Get comment author name"""
        from_id = comment.get('from_id')
        if from_id > 0:
            profiles = comments.get('profiles', [])
            for profile in profiles:
                if profile['id'] == from_id:
                    return f"{profile.get('first_name', '')} {profile.get('last_name', '')}"
        return 'Unknown'
