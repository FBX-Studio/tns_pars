"""
Коллектор для Одноклассников (OK.ru)
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import Config
import logging
import time
import re

logger = logging.getLogger(__name__)

class OKCollector:
    """Коллектор постов из Одноклассников"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.sentiment_analyzer = sentiment_analyzer
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
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
        """Поиск в OK через Google и DuckDuckGo"""
        posts = []
        
        try:
            # Формируем поисковый запрос
            search_query = f'site:ok.ru {query}'
            
            # Пробуем поиск через DuckDuckGo (менее строгий к ботам)
            ddg_url = f'https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}'
            
            logger.info(f"[OK] Поиск: {search_query}")
            
            # Добавляем задержку перед запросом
            time.sleep(2)
            
            response = requests.get(ddg_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем ссылки на OK в результатах DuckDuckGo
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # DuckDuckGo использует редиректы
                    if 'uddg=' in href or 'ok.ru' in href:
                        try:
                            # Извлекаем реальный URL
                            if 'uddg=' in href:
                                import urllib.parse
                                clean_url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                            else:
                                clean_url = href
                            
                            if 'ok.ru' in clean_url and clean_url not in links:
                                # Фильтруем только посты и топики
                                if '/topic/' in clean_url or '/group/' in clean_url or 'tk=' in clean_url:
                                    links.append(clean_url)
                        except:
                            continue
                
                logger.info(f"[OK] Найдено ссылок: {len(links)}")
                
                # Парсим каждый пост
                for url in links[:10]:  # Берем первые 10
                    try:
                        time.sleep(2)  # Задержка между запросами
                        post = self._parse_ok_post(url)
                        if post and self._is_relevant(post['text']):
                            logger.info(f"[OK] Найден релевантный пост: {post['text'][:50]}...")
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"[OK] Ошибка парсинга {url}: {e}")
                        continue
            else:
                logger.warning(f"[OK] Поисковая система вернула код: {response.status_code}")
            
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
            
            post_data = {
                'source': 'ok',
                'source_id': f"ok_{abs(hash(url))}",
                'author': author,
                'author_id': f"ok_{abs(hash(author))}",
                'text': text[:500],
                'url': url,
                'published_date': pub_date,
                'date': pub_date
            }
            
            # Анализ тональности
            if self.sentiment_analyzer:
                sentiment = self.sentiment_analyzer.analyze(text)
                post_data['sentiment_score'] = sentiment['sentiment_score']
                post_data['sentiment_label'] = sentiment['sentiment_label']
            
            return post_data
            
        except Exception as e:
            logger.debug(f"[OK] Ошибка парсинга поста: {e}")
            return None
    
    def collect_from_group(self, group_url):
        """Сбор постов из публичной группы с улучшенным парсингом"""
        posts = []
        
        try:
            logger.info(f"[OK] Парсинг группы: {group_url}")
            time.sleep(2)
            
            response = requests.get(group_url, headers=self.headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"[OK] Группа вернула статус {response.status_code}")
                return posts
            
            html_content = response.text
            
            # Проверка на капчу
            if 'captcha' in html_content.lower():
                logger.warning(f"[OK] Капча на странице группы {group_url}")
                return posts
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем посты в группе (разные варианты селекторов)
            post_links = []
            
            # Вариант 1: Ссылки на топики
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/topic/' in href or 'st.topicId' in href:
                    full_url = f"https://ok.ru{href}" if href.startswith('/') else href
                    # Убираем якоря и параметры
                    clean_url = full_url.split('#')[0].split('?')[0]
                    if clean_url not in post_links and 'ok.ru' in clean_url:
                        post_links.append(clean_url)
                        logger.debug(f"[OK] Найден топик в группе: {clean_url}")
            
            # Вариант 2: Data-атрибуты
            for elem in soup.find_all(attrs={'data-topic-id': True}):
                topic_id = elem.get('data-topic-id')
                if topic_id:
                    url = f"https://ok.ru/topic/{topic_id}"
                    if url not in post_links:
                        post_links.append(url)
                        logger.debug(f"[OK] Найден топик через data-атрибут: {url}")
            
            logger.info(f"[OK] Найдено {len(post_links)} постов в группе")
            
            # Парсим каждый пост
            for url in post_links[:10]:
                try:
                    time.sleep(2)
                    post = self._parse_ok_post(url)
                    if post and self._is_relevant(post['text']):
                        logger.info(f"[OK] Спарсен пост из группы: {post['text'][:60]}...")
                        posts.append(post)
                except Exception as e:
                    logger.debug(f"[OK] Ошибка парсинга поста {url}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"[OK] Ошибка парсинга группы {group_url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return posts
    
    def search_ok_direct(self, query):
        """Прямой поиск на OK.ru с улучшенным парсингом"""
        posts = []
        
        try:
            # Прямой поиск на OK
            search_url = f'https://ok.ru/search?st.query={requests.utils.quote(query)}&st.mode=GlobalSearch'
            
            logger.info(f"[OK] Прямой поиск на OK.ru: {query}")
            time.sleep(2)
            
            response = requests.get(search_url, headers=self.headers, timeout=15, allow_redirects=True)
            
            logger.info(f"[OK] Ответ от OK.ru: статус={response.status_code}, URL={response.url}")
            
            if response.status_code == 200:
                # Сохраняем HTML для отладки
                html_content = response.text
                
                # Проверяем на капчу
                if 'captcha' in html_content.lower() or 'проверка' in html_content.lower():
                    logger.warning("[OK] Обнаружена капча! Используйте прокси или VPN")
                    return posts
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Ищем ссылки на посты (разные варианты)
                links = []
                
                # Вариант 1: Ссылки с /topic/
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/topic/' in href or '/dk?st.cmd=altGroupTopicInfo' in href or 'st.topicId' in href:
                        full_url = f"https://ok.ru{href}" if href.startswith('/') else href
                        if full_url not in links and 'ok.ru' in full_url:
                            links.append(full_url)
                            logger.debug(f"[OK] Найдена ссылка: {full_url}")
                
                # Вариант 2: Ищем в data-атрибутах
                for elem in soup.find_all(attrs={'data-topic-id': True}):
                    topic_id = elem.get('data-topic-id')
                    if topic_id:
                        url = f"https://ok.ru/topic/{topic_id}"
                        if url not in links:
                            links.append(url)
                            logger.debug(f"[OK] Найден топик из data-атрибута: {url}")
                
                logger.info(f"[OK] Всего найдено {len(links)} ссылок")
                
                # Если ничего не нашли, создаем "фейковый" пост с результатами поиска
                if len(links) == 0:
                    # Попробуем найти хоть какой-то текст с упоминанием
                    text_blocks = soup.find_all(['p', 'div', 'span'], string=lambda text: text and query.lower() in text.lower())
                    if text_blocks:
                        for block in text_blocks[:3]:
                            text = block.get_text(strip=True)
                            if len(text) > 20 and self._is_relevant(text):
                                logger.info(f"[OK] Найден текстовый блок: {text[:100]}")
                                post_data = {
                                    'source': 'ok',
                                    'source_id': f"ok_search_{abs(hash(text))}",
                                    'author': 'Одноклассники (поиск)',
                                    'author_id': 'ok_search',
                                    'text': text[:500],
                                    'url': search_url,
                                    'published_date': datetime.now(),
                                    'date': datetime.now()
                                }
                                if self.sentiment_analyzer:
                                    sentiment = self.sentiment_analyzer.analyze(text)
                                    post_data['sentiment_score'] = sentiment['sentiment_score']
                                    post_data['sentiment_label'] = sentiment['sentiment_label']
                                posts.append(post_data)
                    else:
                        logger.warning(f"[OK] По запросу '{query}' ничего не найдено")
                
                # Парсим посты по ссылкам
                for url in links[:5]:
                    try:
                        time.sleep(2)
                        post = self._parse_ok_post(url)
                        if post and self._is_relevant(post['text']):
                            logger.info(f"[OK] Спарсен пост: {post['text'][:80]}...")
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"[OK] Ошибка парсинга {url}: {e}")
                        continue
            else:
                logger.warning(f"[OK] Неожиданный статус: {response.status_code}")
            
        except Exception as e:
            logger.error(f"[OK] Ошибка прямого поиска: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return posts
    
    def search_with_yandex(self, query):
        """Поиск через Yandex (альтернатива DuckDuckGo)"""
        posts = []
        
        try:
            search_query = f'site:ok.ru {query} Нижний Новгород'
            yandex_url = f'https://yandex.ru/search/?text={requests.utils.quote(search_query)}'
            
            logger.info(f"[OK] Поиск через Yandex: {search_query}")
            time.sleep(2)
            
            response = requests.get(yandex_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                links = []
                # Яндекс использует класс 'organic'
                for result in soup.find_all('li', class_='serp-item'):
                    link_tag = result.find('a', href=True)
                    if link_tag:
                        href = link_tag['href']
                        if 'ok.ru' in href and ('/topic/' in href or '/group/' in href):
                            if href not in links:
                                links.append(href)
                                logger.debug(f"[OK] Яндекс нашел: {href}")
                
                logger.info(f"[OK] Яндекс нашел {len(links)} ссылок")
                
                for url in links[:5]:
                    try:
                        time.sleep(2)
                        post = self._parse_ok_post(url)
                        if post and self._is_relevant(post['text']):
                            logger.info(f"[OK] Спарсен пост через Яндекс: {post['text'][:80]}...")
                            posts.append(post)
                    except Exception as e:
                        logger.debug(f"[OK] Ошибка парсинга {url}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"[OK] Ошибка поиска через Яндекс: {e}")
        
        return posts
    
    def collect(self):
        """Сбор постов из Одноклассников"""
        all_posts = []
        
        try:
            logger.info("[OK] Запуск сбора из Одноклассников")
            logger.info("[OK] ⚠ ВНИМАНИЕ: OK.ru активно блокирует автоматический парсинг")
            logger.info("[OK] Рекомендуется использовать прокси/VPN или официальный API")
            
            # 1. Прямой поиск на OK.ru (наиболее надежный)
            for keyword in self.keywords[:2]:
                logger.info(f"[OK] Прямой поиск по ключевому слову: {keyword}")
                try:
                    posts = self.search_ok_direct(keyword)
                    if posts:
                        logger.info(f"[OK] Найдено {len(posts)} постов по '{keyword}' (прямой поиск)")
                        all_posts.extend(posts)
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"[OK] Ошибка прямого поиска по '{keyword}': {e}")
            
            # 2. Поиск через Яндекс (лучше работает с русским контентом)
            if len(all_posts) < 3:
                for keyword in self.keywords[:2]:
                    logger.info(f"[OK] Поиск через Яндекс по ключевому слову: {keyword}")
                    try:
                        posts = self.search_with_yandex(keyword)
                        if posts:
                            logger.info(f"[OK] Найдено {len(posts)} постов по '{keyword}' (Яндекс)")
                            all_posts.extend(posts)
                        time.sleep(3)
                    except Exception as e:
                        logger.warning(f"[OK] Ошибка поиска через Яндекс по '{keyword}': {e}")
            
            # 3. Поиск через DuckDuckGo (дополнительный метод)
            if len(all_posts) < 3:
                for keyword in self.keywords[:2]:
                    logger.info(f"[OK] Поиск через DuckDuckGo по ключевому слову: {keyword}")
                    try:
                        posts = self.search_ok_google(keyword)
                        if posts:
                            logger.info(f"[OK] Найдено {len(posts)} постов по '{keyword}' (DuckDuckGo)")
                            all_posts.extend(posts)
                        time.sleep(3)
                    except Exception as e:
                        logger.warning(f"[OK] Ошибка поиска через DuckDuckGo по '{keyword}': {e}")
            
            # 4. Сбор из публичных групп Нижнего Новгорода
            if len(all_posts) < 5:
                for group in self.public_groups[:2]:
                    logger.info(f"[OK] Сбор из группы: {group}")
                    try:
                        posts = self.collect_from_group(group)
                        if posts:
                            logger.info(f"[OK] Найдено {len(posts)} постов в группе")
                            all_posts.extend(posts)
                        time.sleep(3)
                    except Exception as e:
                        logger.warning(f"[OK] Ошибка сбора из группы {group}: {e}")
            
            # Итоговая информация
            if len(all_posts) == 0:
                logger.warning("[OK] ⚠ Посты не найдены. Возможные причины:")
                logger.warning("[OK] 1. OK.ru блокирует автоматические запросы без авторизации")
                logger.warning("[OK] 2. Нужен прокси/VPN (настройте в ⚙️ Настройки → Прокси)")
                logger.warning("[OK] 3. Используйте официальный API OK.ru: https://ok.ru/dk")
                logger.warning("[OK] 4. Убедитесь что по вашим ключевым словам есть посты на OK.ru")
                logger.info("[OK] 💡 СОВЕТ: Проверьте вручную https://ok.ru/search?st.query=ТНС+энерго+НН")
            else:
                logger.info(f"[OK] ✓ Успешно найдено {len(all_posts)} реальных постов!")
            
        except Exception as e:
            logger.error(f"[OK] Ошибка сбора: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        logger.info(f"[OK] Итого собрано постов: {len(all_posts)}")
        return all_posts
