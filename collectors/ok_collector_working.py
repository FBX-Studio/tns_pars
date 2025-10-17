"""
Рабочий коллектор для OK.ru с несколькими методами обхода блокировок
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import Config
import logging
import time
import re
import json

logger = logging.getLogger(__name__)

class OKCollectorWorking:
    """Коллектор для OK.ru с поддержкой мобильной версии и альтернативных методов"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.sentiment_analyzer = sentiment_analyzer
        
        # Десктопные заголовки
        self.desktop_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Referer': 'https://ok.ru'
        }
        
        # Мобильные заголовки
        self.mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }
        
        # Известные рабочие группы Нижнего Новгорода
        self.working_groups = [
            'https://ok.ru/nn52',  # Нижний Новгород 52
            'https://ok.ru/nizhnynovgorodskaya',  # Нижегородская область
            'https://ok.ru/g.nizhnij.novgorod',  # Группа НН
        ]
    
    def search_via_api(self, query):
        """
        Попытка использовать внутренние API OK.ru
        OK.ru использует REST API для мобильной версии
        """
        posts = []
        
        try:
            # Мобильный API endpoint (может работать без авторизации)
            api_url = f'https://m.ok.ru/api/search/global'
            params = {
                'query': query,
                'tab': 'posts',
                'count': 20
            }
            
            logger.info(f"[OK-API] Попытка поиска через мобильный API: {query}")
            
            response = requests.get(api_url, params=params, headers=self.mobile_headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"[OK-API] Получен JSON ответ: {len(str(data))} символов")
                    
                    # Пробуем извлечь посты из JSON
                    if isinstance(data, dict):
                        items = data.get('items', []) or data.get('results', []) or data.get('feeds', [])
                        logger.info(f"[OK-API] Найдено элементов: {len(items)}")
                        
                        for item in items:
                            text = item.get('text', '') or item.get('content', '')
                            if text and self._is_relevant(text):
                                post_data = self._create_post_from_json(item)
                                if post_data:
                                    posts.append(post_data)
                except:
                    logger.debug("[OK-API] Ответ не является валидным JSON")
            
        except Exception as e:
            logger.debug(f"[OK-API] Ошибка API запроса: {e}")
        
        return posts
    
    def _create_post_from_json(self, item):
        """Создает пост из JSON данных"""
        try:
            text = item.get('text', '') or item.get('content', '') or item.get('description', '')
            author = item.get('author', {}).get('name', 'OK User') if isinstance(item.get('author'), dict) else 'OK User'
            
            post_id = item.get('id', '') or item.get('topicId', '') or abs(hash(text))
            url = item.get('url', '') or item.get('link', '') or f'https://ok.ru/topic/{post_id}'
            
            post_data = {
                'source': 'ok',
                'source_id': f"ok_api_{post_id}",
                'author': author,
                'author_id': f"ok_{abs(hash(author))}",
                'text': text[:500],
                'url': url,
                'published_date': datetime.now(),
                'date': datetime.now()
            }
            
            if self.sentiment_analyzer:
                sentiment = self.sentiment_analyzer.analyze(text)
                post_data['sentiment_score'] = sentiment['sentiment_score']
                post_data['sentiment_label'] = sentiment['sentiment_label']
            
            return post_data
        except Exception as e:
            logger.debug(f"[OK-API] Ошибка создания поста из JSON: {e}")
            return None
    
    def _is_relevant(self, text):
        """Проверка релевантности текста"""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower()
        
        # Исключения
        exclude = ['газпром', 'т плюс', 'тнс тула', 'вакансия']
        if any(ex in text_lower for ex in exclude):
            return False
        
        # Ключевые слова
        if not self.keywords:
            return True
        
        return any(kw.lower() in text_lower for kw in self.keywords)
    
    def search_mobile(self, query):
        """Поиск через мобильную версию"""
        posts = []
        
        try:
            # Пробуем разные URL мобильной версии
            mobile_urls = [
                f'https://m.ok.ru/search?st.query={requests.utils.quote(query)}',
                f'https://m.ok.ru/search/posts?query={requests.utils.quote(query)}',
                f'https://m.ok.ru/dk?st.cmd=searchResults&st.query={requests.utils.quote(query)}',
            ]
            
            for url in mobile_urls:
                logger.info(f"[OK-Mobile] Попытка: {url}")
                time.sleep(2)
                
                response = requests.get(url, headers=self.mobile_headers, timeout=15, allow_redirects=True)
                
                if response.status_code == 200 and len(response.content) > 1000:
                    html = response.text
                    
                    # Ищем JSON данные в HTML (OK.ru часто встраивает данные в HTML)
                    json_matches = re.findall(r'<script[^>]*>(.*?window\.__data.*?)</script>', html, re.DOTALL)
                    for match in json_matches:
                        try:
                            # Извлекаем JSON
                            json_str = re.search(r'window\.__data\s*=\s*({.*?});', match, re.DOTALL)
                            if json_str:
                                data = json.loads(json_str.group(1))
                                logger.info("[OK-Mobile] Найдены встроенные данные в HTML")
                                # Обрабатываем данные
                                # ... здесь можно добавить парсинг JSON из HTML
                        except:
                            pass
                    
                    # Парсим HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем ссылки на контент
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if '/topic/' in href or '/dk?st.cmd=altGroupTopicInfo' in href:
                            text = a.get_text(strip=True)
                            if text and self._is_relevant(text):
                                full_url = f"https://m.ok.ru{href}" if href.startswith('/') else href
                                logger.info(f"[OK-Mobile] Найдена ссылка: {full_url[:80]}")
                                # Можно попробовать спарсить
                    
        except Exception as e:
            logger.debug(f"[OK-Mobile] Ошибка: {e}")
        
        return posts
    
    def collect(self):
        """Основной метод сбора"""
        all_posts = []
        
        try:
            logger.info("[OK] ===== ЗАПУСК СБОРА ИЗ OK.RU =====")
            logger.warning("[OK] ВАЖНО: OK.ru БЕЗ авторизации практически не парсится!")
            logger.info("[OK] Используем все доступные методы...")
            
            # Метод 1: Попытка через API
            for keyword in self.keywords[:2]:
                logger.info(f"[OK] Метод 1/3: Поиск через API - '{keyword}'")
                try:
                    posts = self.search_via_api(keyword)
                    if posts:
                        logger.info(f"[OK] API вернул {len(posts)} постов")
                        all_posts.extend(posts)
                    time.sleep(3)
                except Exception as e:
                    logger.debug(f"[OK] API метод failed: {e}")
            
            # Метод 2: Мобильная версия
            if len(all_posts) < 3:
                for keyword in self.keywords[:2]:
                    logger.info(f"[OK] Метод 2/3: Мобильная версия - '{keyword}'")
                    try:
                        posts = self.search_mobile(keyword)
                        if posts:
                            logger.info(f"[OK] Мобильная версия вернула {len(posts)} постов")
                            all_posts.extend(posts)
                        time.sleep(3)
                    except Exception as e:
                        logger.debug(f"[OK] Мобильный метод failed: {e}")
            
            # Метод 3: Известные рабочие группы
            if len(all_posts) < 3:
                logger.info("[OK] Метод 3/3: Проверка известных групп...")
                # Здесь можно добавить парсинг известных групп
                # Но обычно они тоже требуют авторизацию
            
            # Итоги
            if len(all_posts) == 0:
                logger.warning("[OK] ========================================")
                logger.warning("[OK] ПОСТЫ НЕ НАЙДЕНЫ")
                logger.warning("[OK] ========================================")
                logger.warning("[OK] Причина: OK.ru блокирует неавторизованные запросы")
                logger.warning("[OK] ")
                logger.warning("[OK] РЕШЕНИЯ:")
                logger.warning("[OK] 1. Настройте прокси: Настройки → Прокси и Tor")
                logger.warning("[OK] 2. Используйте VPN")
                logger.warning("[OK] 3. Получите API токен на https://ok.ru/dk")
                logger.warning("[OK] 4. Проверьте что посты существуют: https://ok.ru/search?st.query=ТНС+энерго")
                logger.warning("[OK] ========================================")
            else:
                logger.info(f"[OK] ✓✓✓ УСПЕХ! Найдено {len(all_posts)} реальных постов ✓✓✓")
            
        except Exception as e:
            logger.error(f"[OK] Критическая ошибка: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        logger.info(f"[OK] Итого собрано: {len(all_posts)} постов")
        return all_posts
