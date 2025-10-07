"""
Легкая версия коллектора новостей через Google News с поддержкой прокси
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import random
import time

logger = logging.getLogger(__name__)

class NewsCollectorLight:
    """Коллектор новостей через Google News RSS с прокси"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.sentiment_analyzer = sentiment_analyzer
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }
        
        # Google News RSS для региона Нижний Новгород
        self.search_query = ' OR '.join(self.keywords)
        
        # Список бесплатных прокси (будем обновлять динамически)
        self.proxies_list = []
    
    def _extract_real_url(self, google_news_url):
        """Извлечение реального URL из Google News редиректа"""
        try:
            # Google News использует редирект, пробуем получить реальный URL
            if 'news.google.com' in google_news_url:
                # Пробуем запросить с редиректом
                response = requests.head(google_news_url, allow_redirects=True, timeout=5)
                if response.url != google_news_url:
                    return response.url
        except:
            pass
        return google_news_url
    
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
        
        # Проверяем исключения
        for exclude in exclude_patterns:
            if exclude in text_lower:
                return False
        
        # Ключевые слова - проверяем каждое
        if not self.keywords:
            logger.warning("[NEWS-LIGHT] Нет ключевых слов для фильтрации!")
            return True  # Если нет ключевых слов, берём всё
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _get_free_proxies(self):
        """Получение списка бесплатных прокси"""
        try:
            # Используем бесплатный API для получения прокси
            response = requests.get(
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                self.proxies_list = [f'http://{p.strip()}' for p in proxies if p.strip()][:20]  # Берем первые 20
                logger.info(f"[NEWS] Загружено прокси: {len(self.proxies_list)}")
        except Exception as e:
            logger.warning(f"[NEWS] Не удалось загрузить прокси: {e}")
            self.proxies_list = []
    
    def _make_request(self, url, max_retries=3):
        """Выполнение запроса с использованием прокси"""
        # Если нет прокси, пробуем загрузить
        if not self.proxies_list:
            self._get_free_proxies()
        
        # Сначала пробуем без прокси
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response
        except:
            pass
        
        # Если не получилось, пробуем с прокси
        for attempt in range(max_retries):
            if self.proxies_list:
                proxy = random.choice(self.proxies_list)
                try:
                    logger.debug(f"[NEWS] Попытка {attempt+1} с прокси {proxy}")
                    response = requests.get(
                        url,
                        headers=self.headers,
                        proxies={'http': proxy, 'https': proxy},
                        timeout=10
                    )
                    if response.status_code == 200:
                        return response
                except Exception as e:
                    logger.debug(f"[NEWS] Прокси {proxy} не работает: {e}")
                    # Удаляем нерабочий прокси
                    self.proxies_list.remove(proxy)
            
            time.sleep(1)
        
        # Последняя попытка без прокси
        return requests.get(url, headers=self.headers, timeout=10)
    
    def collect(self):
        """Сбор новостей через Google News RSS"""
        articles = []
        
        try:
            # Формируем запрос для Google News (русскоязычные новости о Нижнем Новгороде)
            # Ищем по ключевым словам
            query = '+'.join(self.keywords[0].split())  # Берем первое ключевое слово
            google_news_url = f'https://news.google.com/rss/search?q={query}+Нижний+Новгород&hl=ru&gl=RU&ceid=RU:ru'
            
            logger.info(f"[NEWS] Поиск в Google News")
            logger.info(f"[NEWS] Ключевые слова: {', '.join(self.keywords) if self.keywords else 'НЕ НАСТРОЕНЫ'}")
            logger.info(f"[NEWS] URL: {google_news_url}")
            
            response = self._make_request(google_news_url)
            
            logger.info(f"[NEWS] Парсинг Google News feed... (статус: {response.status_code})")
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            if not items:
                logger.warning("[NEWS] Нет элементов 'item' в XML, пробуем как HTML...")
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('item')
            
            total_items = len(items)
            logger.info(f"[NEWS] Найдено новостей в Google News: {total_items}")
            
            if total_items == 0:
                logger.error("[NEWS] RSS не содержит новостей!")
                return []
            
            logger.info(f"[NEWS] Обработка новостей...")
            
            items_found = 0
            relevant_count = 0
            
            for item in items:
                items_found += 1
                if items_found > 100:  # Увеличен лимит для Google News
                    break
                
                try:
                    title_tag = item.find('title')
                    desc_tag = item.find('description')
                    link_tag = item.find('link')
                    pubdate_tag = item.find('pubDate')
                    
                    # Извлекаем чистый заголовок
                    title = title_tag.get_text(strip=True) if title_tag else ''
                    
                    # Парсим description для извлечения чистого текста без HTML тегов
                    description = ''
                    if desc_tag:
                        desc_content = desc_tag.get_text(strip=True)
                        # Удаляем HTML теги из description
                        desc_soup = BeautifulSoup(desc_content, 'html.parser')
                        description = desc_soup.get_text(strip=True)
                        
                        # Если в description есть заголовок в ссылке, извлекаем его
                        a_tag = BeautifulSoup(desc_content, 'html.parser').find('a')
                        if a_tag and a_tag.get_text(strip=True):
                            clean_title = a_tag.get_text(strip=True)
                            if len(clean_title) > len(title):  # Если в ссылке более полный заголовок
                                title = clean_title
                    
                    # Получаем ссылку
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    if not title and not description:
                        logger.debug(f"[NEWS] Пропуск: нет заголовка и описания")
                        continue
                    
                    full_text = f"{title} {description}"
                    
                    # Google News уже фильтрует по ключевым словам, но проверяем на исключения
                    if self._is_relevant(full_text):
                        relevant_count += 1
                        logger.info(f"[NEWS] Релевантная: {title[:60]}...")
                        
                        # Парсим дату публикации
                        pub_date = datetime.now()
                        if pubdate_tag:
                            try:
                                from email.utils import parsedate_to_datetime
                                pub_date = parsedate_to_datetime(pubdate_tag.get_text(strip=True))
                            except:
                                pass
                        
                        # Извлекаем реальный URL (не Google редирект)
                        real_url = self._extract_real_url(link)
                        
                        # Определяем источник из description (там указан источник)
                        source_name = 'Google News'
                        # В description Google News добавляет источник после тире или в font теге
                        if description:
                            # Ищем название источника в конце description
                            parts = description.split('\xa0')  # Разделитель в Google News
                            if len(parts) > 1:
                                source_name = parts[-1].strip()
                            else:
                                # Пробуем из URL
                                if 'nn.ru' in real_url:
                                    source_name = 'НИА Нижний Новгород'
                                elif 'vn.ru' in real_url:
                                    source_name = 'Ведомости Нижний Новгород'
                                elif 'pravda-nn.ru' in real_url:
                                    source_name = 'Правда НН'
                                elif 'niann.ru' in real_url:
                                    source_name = 'НИАН'
                        
                        # Очищаем текст от HTML сущностей и лишних символов
                        clean_text = title
                        if description:
                            # Убираем название источника из текста
                            desc_clean = description.split(source_name)[0].strip()
                            if desc_clean and desc_clean != title:
                                clean_text = f"{title}\n\n{desc_clean[:300]}"
                        
                        # Генерируем уникальный source_id с учетом даты
                        # Это позволяет одной статье появляться раз в день
                        date_str = pub_date.strftime('%Y%m%d') if pub_date else datetime.now().strftime('%Y%m%d')
                        
                        article = {
                            'source': 'news',
                            'source_id': f"gnews_{abs(hash(real_url))}_{date_str}",
                            'author': source_name,
                            'author_id': source_name.lower().replace(' ', '_').replace('.', '_'),
                            'text': clean_text,
                            'url': real_url,  # Используем реальный URL
                            'published_date': pub_date,
                            'date': pub_date  # Добавляем для фильтрации по периоду
                        }
                        
                        # Анализ тональности
                        if self.sentiment_analyzer:
                            sentiment = self.sentiment_analyzer.analyze(clean_text)
                            article['sentiment_score'] = sentiment['sentiment_score']
                            article['sentiment_label'] = sentiment['sentiment_label']
                        
                        articles.append(article)
                    else:
                        logger.debug(f"[NEWS] Не релевантна (исключение): {title[:40]}...")
                    
                except Exception as e:
                    logger.warning(f"[NEWS] Ошибка обработки item: {e}")
                    continue
            
            logger.info(f"[NEWS] Обработано новостей: {items_found}/{total_items}")
            logger.info(f"[NEWS] Релевантных: {relevant_count}")
            logger.info(f"[NEWS] Возвращаем статей: {len(articles)}")
            
        except requests.Timeout:
            logger.warning("[NEWS] Таймаут при подключении к Google News")
        except requests.RequestException as e:
            logger.error(f"[NEWS] Ошибка запроса: {e}")
        except Exception as e:
            logger.error(f"[NEWS] Неожиданная ошибка: {e}", exc_info=True)
        
        return articles
