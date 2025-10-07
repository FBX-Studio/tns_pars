"""
Коллектор для Яндекс.Дзен через поиск Google
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import time
import random
import re

logger = logging.getLogger(__name__)

class ZenCollector:
    """Коллектор статей из Яндекс.Дзен через Google поиск"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        # Полные заголовки для обхода блокировки Яндекса
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
        
        # Список бесплатных прокси (будем обновлять динамически)
        self.proxies_list = []
        
        # Сессия для сохранения cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
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
    
    def _get_free_proxies(self):
        """Получение списка бесплатных прокси"""
        try:
            response = requests.get(
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                self.proxies_list = [f'http://{p.strip()}' for p in proxies if p.strip()][:10]
                logger.info(f"[ZEN] Загружено прокси: {len(self.proxies_list)}")
        except Exception as e:
            logger.warning(f"[ZEN] Не удалось загрузить прокси: {e}")
            self.proxies_list = []
    
    def _make_request(self, url, max_retries=3):
        """Выполнение запроса с использованием сессии и обхода блокировки"""
        from config import Config
        
        # Проверяем настройки Tor
        use_tor = Config.get('USE_TOR', '').lower() == 'true'
        tor_proxy = Config.get('TOR_PROXY', 'socks5h://127.0.0.1:9150')
        
        # Добавляем рефферер для имитации перехода с Яндекса
        if 'yandex.ru' in url:
            self.session.headers['Referer'] = 'https://yandex.ru/'
        
        # Если включен Tor - используем его
        if use_tor:
            proxies = {'http': tor_proxy, 'https': tor_proxy}
            logger.debug(f"[ZEN] Используем Tor: {tor_proxy}")
        else:
            proxies = None
        
        # Сначала пробуем через сессию (сохраняет cookies)
        try:
            response = self.session.get(url, timeout=20, allow_redirects=True, proxies=proxies)
            
            # Проверяем не капча ли это
            if 'showcaptcha' in response.url or 'captcha' in response.text.lower():
                logger.warning("[ZEN] Яндекс показал капчу")
                if use_tor:
                    logger.info("[ZEN] Пробуем получить новый IP через Tor...")
                    time.sleep(5)
                else:
                    logger.warning("[ZEN] Рекомендуется включить Tor (USE_TOR=True в .env)")
                    time.sleep(3)
            elif response.status_code == 200:
                return response
        except Exception as e:
            logger.debug(f"[ZEN] Прямое подключение не удалось: {e}")
            pass
        
        # Если не получилось, пробуем с прокси
        if not self.proxies_list:
            self._get_free_proxies()
        
        for attempt in range(max_retries):
            if self.proxies_list:
                proxy = random.choice(self.proxies_list)
                try:
                    response = self.session.get(
                        url,
                        proxies={'http': proxy, 'https': proxy},
                        timeout=20,
                        allow_redirects=True
                    )
                    if response.status_code == 200 and 'captcha' not in response.url:
                        return response
                except:
                    self.proxies_list.remove(proxy)
            time.sleep(1)
        
        # Последняя попытка без прокси
        return self.session.get(url, timeout=20, allow_redirects=True)
    
    def _warm_up_session(self):
        """Прогрев сессии - получение cookies от Яндекса"""
        try:
            # Сначала заходим на главную Яндекса
            logger.debug("[ZEN] Прогрев сессии - заход на главную Яндекса")
            self.session.get('https://yandex.ru/', timeout=10)
            time.sleep(1)
            return True
        except:
            return False
    
    def search_dzen_yandex(self, query):
        """Поиск статей Дзен через Яндекс"""
        articles = []
        
        try:
            # Прогреваем сессию перед первым запросом
            if not self.session.cookies:
                self._warm_up_session()
            
            # Поиск в Яндексе по Дзену с ключевым словом
            search_query = f'dzen.ru {query}'
            yandex_url = f'https://yandex.ru/search/?text={requests.utils.quote(search_query)}&lr=47'  # lr=47 - Нижний Новгород
            
            logger.info(f"[ZEN] Поиск в Яндекс: {search_query}")
            
            response = self._make_request(yandex_url)
            
            # Проверяем ответ
            if not response:
                logger.error("[ZEN] Не удалось получить ответ от Яндекса")
                return []
            
            logger.debug(f"[ZEN] Ответ получен, статус: {response.status_code}, длина: {len(response.content)}")
            
            # Проверяем на капчу
            if 'showcaptcha' in response.url:
                logger.error("[ZEN] Яндекс требует капчу - невозможно продолжить")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем ссылки на Дзен из результатов Яндекса
            dzen_links = set()
            
            # Яндекс использует другую структуру - ищем прямые ссылки
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Прямые ссылки на dzen.ru
                if href.startswith('https://dzen.ru/a/') or href.startswith('http://dzen.ru/a/'):
                    clean_url = href.split('?')[0]  # Убираем параметры
                    if clean_url not in dzen_links:
                        dzen_links.add(clean_url)
                        logger.info(f"[ZEN] Найдена статья (прямая): {clean_url}")
                
                # Редиректы через yandex
                elif 'dzen.ru/a/' in href:
                    try:
                        # Извлекаем URL из редиректа
                        if 'url=' in href:
                            clean_url = href.split('url=')[1].split('&')[0]
                        else:
                            clean_url = href
                        
                        # Декодируем URL-encoded символы
                        from urllib.parse import unquote
                        clean_url = unquote(clean_url)
                        
                        # Проверяем что это статья Дзен
                        if 'dzen.ru/a/' in clean_url:
                            clean_url = clean_url.split('?')[0]
                            if clean_url.startswith('http') and clean_url not in dzen_links:
                                dzen_links.add(clean_url)
                                logger.info(f"[ZEN] Найдена статья (редирект): {clean_url}")
                    except Exception as e:
                        logger.debug(f"[ZEN] Ошибка парсинга ссылки: {e}")
                        pass
            
            logger.info(f"[ZEN] Всего найдено ссылок: {len(dzen_links)}")
            
            # Если ничего не найдено - сохраним HTML для отладки
            if len(dzen_links) == 0:
                debug_file = f'yandex_search_debug_{query.replace(" ", "_")}.html'
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.debug(f"[ZEN] HTML сохранен в {debug_file} для отладки")
                except:
                    pass
            
            # Для каждой ссылки извлекаем метаданные из Яндекса
            for link in list(dzen_links)[:20]:  # Ограничение 20 статей
                try:
                    # Извлекаем заголовок из результатов Яндекса
                    title = ''
                    description = ''
                    
                    # Ищем результат поиска содержащий эту ссылку
                    for li in soup.find_all('li', class_=re.compile('serp-item|organic')):
                        # Проверяем есть ли ссылка в этом результате
                        li_html = str(li)
                        if link in li_html or link.replace('https://', '') in li_html:
                            # Заголовок обычно в h2 или в элементе с классом title
                            h2 = li.find('h2')
                            if h2:
                                title = h2.get_text(strip=True)
                            else:
                                # Альтернативный поиск заголовка
                                title_elem = li.find('a', class_=re.compile('link|organic__url'))
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                            
                            # Описание в div с классом text или snippet
                            text_div = li.find('div', class_=re.compile('text-container|organic__text|snippet'))
                            if text_div:
                                description = text_div.get_text(strip=True)
                            
                            if title:
                                break
                    
                    if not title:
                        # Если не нашли заголовок, пропускаем
                        continue
                    
                    full_text = f"{title}\n\n{description}"
                    
                    # Проверяем релевантность
                    if not self._is_relevant(full_text):
                        continue
                    
                    # Извлекаем ID статьи из URL
                    article_id = link.split('/a/')[-1] if '/a/' in link else abs(hash(link))
                    
                    pub_date = datetime.now()
                    date_str = pub_date.strftime('%Y%m%d')
                    
                    articles.append({
                        'source': 'zen',
                        'source_id': f"dzen_{article_id}_{date_str}",
                        'author': 'Яндекс.Дзен',
                        'author_id': 'yandex_dzen',
                        'text': full_text[:500],
                        'url': link,
                        'published_date': pub_date,
                        'date': pub_date
                    })
                    
                    logger.info(f"[ZEN] Добавлена: {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[ZEN] Ошибка обработки ссылки {link}: {e}")
                    continue
            
            logger.info(f"[ZEN] Релевантных статей: {len(articles)}")
            
        except Exception as e:
            logger.error(f"[ZEN] Ошибка поиска: {e}")
        
        return articles
    
    def parse_dzen_comments(self, article_url):
        """Parse comments from Dzen article"""
        comments = []
        
        try:
            logger.info(f"[ZEN] Parsing comments from: {article_url}")
            
            response = self._make_request(article_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Яндекс.Дзен использует React и динамическую загрузку
            # Комментарии часто загружаются через API или находятся в data-атрибутах
            
            # Попытка найти комментарии по селекторам
            comment_selectors = [
                {'class': 'comment'},
                {'class': 'comments-item'},
                {'data-testid': 'comment'},
                {'class': 'mg-comment'},
            ]
            
            for selector in comment_selectors:
                comment_elements = soup.find_all(['div', 'li', 'article'], selector)
                
                if comment_elements:
                    for elem in comment_elements[:30]:  # Limit comments
                        try:
                            comment_text = elem.get_text(strip=True)
                            
                            if not comment_text or len(comment_text) < 10:
                                continue
                            
                            # Extract author
                            author_elem = elem.find(['span', 'a', 'div'], class_=lambda x: x and 'author' in x.lower())
                            author = author_elem.get_text(strip=True) if author_elem else 'Аноним'
                            
                            comment = {
                                'text': comment_text,
                                'author': author,
                                'published_date': datetime.now(),
                                'source': 'zen_comment',
                                'url': article_url
                            }
                            
                            comments.append(comment)
                            
                        except Exception as e:
                            logger.debug(f"[ZEN] Error parsing comment: {e}")
                            continue
                    
                    if comments:
                        break
            
            logger.info(f"[ZEN] Found {len(comments)} comments")
            
        except Exception as e:
            logger.warning(f"[ZEN] Error parsing comments: {e}")
        
        return comments
    
    def collect(self, collect_comments=False):
        """Сбор статей из Яндекс.Дзен"""
        all_posts = []
        
        try:
            logger.info("[ZEN] Запуск сбора из Яндекс.Дзен через Яндекс поиск")
            
            # Поиск по первым 2 ключевым словам
            for keyword in self.keywords[:2]:
                logger.info(f"[ZEN] Поиск по ключевому слову: {keyword}")
                posts = self.search_dzen_yandex(keyword)
                
                # Collect comments if requested
                if collect_comments:
                    for post in posts:
                        if post.get('url'):
                            comments = self.parse_dzen_comments(post['url'])
                            
                            for comment in comments:
                                comment['parent_source_id'] = post['source_id']
                                comment['parent_url'] = post['url']
                                comment['source_id'] = f"{post['source_id']}_comment_{hash(comment['text'])}"
                                comment['is_comment'] = True
                                all_posts.append(comment)
                            
                            time.sleep(1)
                        
                        post['is_comment'] = False
                
                all_posts.extend(posts)
                time.sleep(2)  # Задержка между запросами
            
            logger.info(f"[ZEN] Всего найдено релевантных элементов: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[ZEN] Ошибка сбора: {e}")
        
        return all_posts
