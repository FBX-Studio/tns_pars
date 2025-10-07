"""
Коллектор для Одноклассников (OK.ru)
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import time
import re

logger = logging.getLogger(__name__)

class OKCollector:
    """Коллектор постов из Одноклассников"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }
        
        # Публичные группы Нижнего Новгорода
        self.public_groups = [
            'https://ok.ru/nizhnynovgorod',
            'https://ok.ru/nizhniynovgorod',
            'https://ok.ru/nnov',
            'https://ok.ru/nn52',
        ]
    
    def _is_relevant(self, text):
        """Проверка релевантности текста"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Исключения
        exclude_patterns = [
            'газпром', 'т плюс', 'т-плюс',
            'тнс тула', 'тнс ярославль',
            'вакансия', 'требуется'
        ]
        
        for exclude in exclude_patterns:
            if exclude in text_lower:
                return False
        
        # Ключевые слова
        if not self.keywords:
            return True
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def search_ok_google(self, query):
        """Поиск в OK через Google"""
        posts = []
        
        try:
            # Используем Google для поиска в OK
            google_query = f'site:ok.ru {query} Нижний Новгород'
            google_url = f'https://www.google.com/search?q={google_query}&num=30'
            
            logger.info(f"[OK] Поиск через Google: {google_query}")
            
            response = requests.get(google_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем ссылки на OK
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'ok.ru' in href and ('/topic/' in href or '/group/' in href):
                        # Извлекаем чистый URL
                        if href.startswith('/url?q='):
                            clean_url = href.split('/url?q=')[1].split('&')[0]
                            if clean_url not in links:
                                links.append(clean_url)
                
                logger.info(f"[OK] Найдено ссылок: {len(links)}")
                
                # Парсим каждый пост
                for url in links[:15]:  # Берем первые 15
                    try:
                        time.sleep(1)  # Задержка между запросами
                        post = self._parse_ok_post(url)
                        if post and self._is_relevant(post['text']):
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"[OK] Ошибка парсинга {url}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"[OK] Ошибка поиска: {e}")
        
        return posts
    
    def _parse_ok_post(self, url):
        """Парсинг отдельного поста OK"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем текст поста
            text = ''
            text_block = soup.find('div', class_='media-text_cnt')
            if text_block:
                text = text_block.get_text(strip=True)
            
            # Если не нашли текст, ищем в других местах
            if not text:
                # Пробуем найти в мета-тегах
                meta_desc = soup.find('meta', {'property': 'og:description'})
                if meta_desc:
                    text = meta_desc.get('content', '')
            
            # Извлекаем автора/группу
            author = 'OK.ru'
            author_tag = soup.find('a', class_='mctc_name')
            if author_tag:
                author = author_tag.get_text(strip=True)
            else:
                # Пробуем из мета-тегов
                meta_site = soup.find('meta', {'property': 'og:site_name'})
                if meta_site:
                    author = meta_site.get('content', 'OK.ru')
            
            # Извлекаем дату
            pub_date = datetime.now()
            date_tag = soup.find('time')
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                # Парсим относительные даты ("2 часа назад", "вчера" и т.д.)
                try:
                    if 'час' in date_text:
                        hours = int(re.findall(r'\d+', date_text)[0])
                        from datetime import timedelta
                        pub_date = datetime.now() - timedelta(hours=hours)
                    elif 'дн' in date_text or 'день' in date_text:
                        days = int(re.findall(r'\d+', date_text)[0]) if re.findall(r'\d+', date_text) else 1
                        from datetime import timedelta
                        pub_date = datetime.now() - timedelta(days=days)
                except:
                    pass
            
            if not text:
                return None
            
            return {
                'source': 'ok',
                'source_id': f"ok_{abs(hash(url))}",
                'author': author,
                'author_id': f"ok_{abs(hash(author))}",
                'text': text[:500],
                'url': url,
                'published_date': pub_date,
                'date': pub_date
            }
            
        except Exception as e:
            logger.debug(f"[OK] Ошибка парсинга поста: {e}")
            return None
    
    def collect_from_group(self, group_url):
        """Сбор постов из публичной группы"""
        posts = []
        
        try:
            logger.info(f"[OK] Парсинг группы: {group_url}")
            
            response = requests.get(group_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем посты в группе
            post_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/topic/' in href:
                    full_url = f"https://ok.ru{href}" if href.startswith('/') else href
                    if full_url not in post_links:
                        post_links.append(full_url)
            
            logger.info(f"[OK] Найдено постов в группе: {len(post_links)}")
            
            # Парсим каждый пост
            for url in post_links[:10]:  # Берем первые 10 постов
                time.sleep(1)
                post = self._parse_ok_post(url)
                if post and self._is_relevant(post['text']):
                    posts.append(post)
            
        except Exception as e:
            logger.warning(f"[OK] Ошибка парсинга группы {group_url}: {e}")
        
        return posts
    
    def collect(self):
        """Сбор постов из Одноклассников"""
        all_posts = []
        
        try:
            logger.info("[OK] Запуск сбора из Одноклассников")
            
            # 1. Поиск через Google по ключевым словам
            for keyword in self.keywords[:2]:  # Берем первые 2 ключевых слова
                logger.info(f"[OK] Поиск по ключевому слову: {keyword}")
                posts = self.search_ok_google(keyword)
                all_posts.extend(posts)
                time.sleep(2)
            
            # 2. Сбор из публичных групп
            for group in self.public_groups[:2]:  # Берем первые 2 группы
                posts = self.collect_from_group(group)
                all_posts.extend(posts)
                time.sleep(2)
            
            logger.info(f"[OK] Всего найдено постов: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[OK] Ошибка сбора: {e}")
        
        return all_posts
