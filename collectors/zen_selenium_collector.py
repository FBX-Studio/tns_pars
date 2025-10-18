"""
Коллектор для Яндекс.Дзен через Selenium (обход капчи)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import time
import random

logger = logging.getLogger(__name__)

class ZenSeleniumCollector:
    """Коллектор статей из Яндекс.Дзен через Selenium"""
    
    def __init__(self, sentiment_analyzer=None):
        # Используем hardcoded ключевые слова для избежания проблем с кодировкой
        self.keywords = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт', 'ТНС']
        self.driver = None
        self.sentiment_analyzer = sentiment_analyzer  # Для совместимости с app_enhanced.py
        
    def _init_driver(self, headless=True):
        """Инициализация Selenium WebDriver"""
        try:
            logger.info("[ZEN-Selenium] Запуск Chrome WebDriver...")
            
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless=new')
            
            # Уникальная директория для профиля (избегаем конфликтов)
            import tempfile
            import os
            import shutil
            user_data_dir = os.path.join(tempfile.gettempdir(), f'zen_selenium_chrome_{os.getpid()}')
            
            # Очищаем старую директорию если есть
            if os.path.exists(user_data_dir):
                try:
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                except:
                    pass
            
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Базовые настройки с улучшенной стабильностью
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--lang=ru-RU')
            
            # Стабилизация Chrome
            chrome_options.add_argument('--remote-debugging-port=0')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            
            # Отключение логов
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Создаем драйвер
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Скрываем признаки webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Устанавливаем таймаут
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("[ZEN-Selenium] ✓ Chrome WebDriver запущен")
            return True
            
        except Exception as e:
            logger.error(f"[ZEN-Selenium] Ошибка инициализации WebDriver: {e}")
            return False
    
    def _close_driver(self):
        """Закрытие WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("[SELENIUM] WebDriver закрыт")
            except:
                pass
    
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
    
    def search_yandex(self, query, max_results=10):
        """Поиск в Яндексе через Selenium"""
        results = []
        
        try:
            search_url = f"https://yandex.ru/search/?text={query}+site%3Adzen.ru"
            logger.info(f"[SELENIUM] Открытие страницы поиска: {search_url}")
            
            self.driver.get(search_url)
            
            # Ждем загрузки результатов
            time.sleep(random.uniform(2, 4))
            
            # Проверяем на капчу
            if 'showcaptcha' in self.driver.current_url or 'Обнаружены подозрительные запросы' in self.driver.page_source:
                logger.warning("[SELENIUM] Яндекс показал капчу - ждем 5 секунд")
                time.sleep(5)
                
                # Проверяем снова
                if 'showcaptcha' in self.driver.current_url:
                    logger.error("[SELENIUM] Капча не пропала - прерываем")
                    return results
            
            # Парсим результаты поиска
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Ищем результаты
            search_results = soup.find_all('li', class_='serp-item')
            
            logger.info(f"[SELENIUM] Найдено результатов поиска: {len(search_results)}")
            
            for result in search_results[:max_results]:
                try:
                    # Ссылка
                    link_elem = result.find('a', class_='Link')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    
                    url = link_elem['href']
                    
                    # Фильтруем только dzen.ru
                    if 'dzen.ru' not in url:
                        continue
                    
                    # Заголовок
                    title_elem = result.find('h2')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Описание
                    desc_elem = result.find('div', class_='VanillaReact')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    text = f"{title} {description}"
                    
                    if self._is_relevant(text):
                        results.append({
                            'url': url,
                            'title': title,
                            'description': description,
                            'text': text
                        })
                        logger.info(f"[SELENIUM] ✓ Релевантная статья: {title[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"[SELENIUM] Ошибка парсинга результата: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"[SELENIUM] Ошибка поиска: {e}")
            return results
    
    def parse_dzen_comments(self, article_url):
        """Парсинг комментариев из статьи Дзена"""
        comments = []
        
        try:
            logger.info(f"[ZEN-Comments] Парсинг комментариев: {article_url}")
            
            # Открываем статью
            self.driver.get(article_url)
            time.sleep(random.uniform(2, 3))
            
            # Скроллим вниз для загрузки комментариев
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            
            # Ищем кнопку "Показать все комментарии" и кликаем
            try:
                show_comments_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Показать')]")
                show_comments_button.click()
                time.sleep(2)
            except:
                pass  # Кнопки может не быть
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Ищем комментарии по различным селекторам
            comment_selectors = [
                {'class': 'comment'},
                {'class': 'mg-comment'},
                {'class': 'comments-item'},
                {'data-testid': 'comment'},
                {'class': 'comment-item'},
            ]
            
            for selector in comment_selectors:
                comment_elements = soup.find_all(['div', 'li', 'article'], selector)
                
                if comment_elements:
                    logger.info(f"[ZEN-Comments] Найдено элементов по селектору {selector}: {len(comment_elements)}")
                    
                    for elem in comment_elements[:30]:  # Максимум 30 комментариев
                        try:
                            # Текст комментария
                            text_elem = elem.find('div', class_='text') or elem.find('p') or elem
                            text = text_elem.get_text(strip=True)
                            
                            if not text or len(text) < 5:
                                continue
                            
                            # Автор
                            author_elem = elem.find('a', class_='user') or elem.find('span', class_='author')
                            author = author_elem.get_text(strip=True) if author_elem else 'Дзен пользователь'
                            
                            # Создаем комментарий
                            comment_data = {
                                'source': 'dzen',
                                'source_id': f"dzen_comment_{abs(hash(text[:50]))}",
                                'author': author[:100],
                                'author_id': f"dzen_{abs(hash(author))}",
                                'text': text[:500],
                                'url': article_url,
                                'published_date': datetime.now(),
                                'date': datetime.now(),
                                'is_comment': True,
                                'parent_source_id': f"dzen_{hash(article_url)}"
                            }
                            
                            # Анализ тональности если доступен
                            if self.sentiment_analyzer:
                                try:
                                    sentiment = self.sentiment_analyzer.analyze(text)
                                    comment_data['sentiment_score'] = sentiment.get('sentiment_score', 0)
                                    comment_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                                except:
                                    pass
                            
                            comments.append(comment_data)
                            
                        except Exception as e:
                            logger.debug(f"[ZEN-Comments] Ошибка парсинга комментария: {e}")
                            continue
                    
                    if comments:
                        break  # Нашли рабочий селектор
            
            logger.info(f"[ZEN-Comments] Собрано комментариев: {len(comments)}")
            
        except Exception as e:
            logger.warning(f"[ZEN-Comments] Ошибка парсинга комментариев: {e}")
        
        return comments
    
    def parse_article(self, url):
        """Парсинг отдельной статьи Дзена"""
        try:
            logger.info(f"[SELENIUM] Парсинг статьи: {url}")
            
            self.driver.get(url)
            time.sleep(random.uniform(2, 3))
            
            # Проверка на капчу
            if 'showcaptcha' in self.driver.current_url:
                logger.warning("[SELENIUM] Капча на странице статьи")
                return None
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Заголовок
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Текст статьи
            article_text = ''
            
            # Пробуем разные селекторы
            content_selectors = [
                {'name': 'div', 'class_': 'article-render'},
                {'name': 'div', 'class_': 'content'},
                {'name': 'article'},
                {'name': 'div', 'class_': 'text'}
            ]
            
            for selector in content_selectors:
                content_elem = soup.find(**selector)
                if content_elem:
                    article_text = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # Дата публикации
            date_elem = soup.find('time')
            published_date = None
            if date_elem and 'datetime' in date_elem.attrs:
                try:
                    published_date = datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00'))
                except:
                    pass
            
            # Автор
            author = ''
            author_elem = soup.find('a', class_='author')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            full_text = f"{title} {article_text}"
            
            if not full_text or len(full_text) < 50:
                logger.warning(f"[SELENIUM] Статья слишком короткая: {url}")
                return None
            
            return {
                'url': url,
                'title': title,
                'text': full_text,
                'author': author,
                'published_date': published_date or datetime.now()
            }
            
        except Exception as e:
            logger.error(f"[SELENIUM] Ошибка парсинга статьи {url}: {e}")
            return None
    
    def collect(self, collect_comments=False):
        """Основной метод сбора данных с поддержкой комментариев"""
        all_articles = []
        
        logger.info("[ZEN-SELENIUM] Начало сбора данных из Яндекс.Дзен через Selenium")
        if collect_comments:
            logger.info("[ZEN-SELENIUM] Режим: СТАТЬИ + КОММЕНТАРИИ")
        else:
            logger.info("[ZEN-SELENIUM] Режим: ТОЛЬКО СТАТЬИ")
        
        # Инициализация драйвера
        if not self._init_driver(headless=True):
            logger.error("[ZEN-SELENIUM] Не удалось инициализировать WebDriver")
            return all_articles
        
        try:
            # Поиск по ключевым словам
            for keyword in self.keywords:
                logger.info(f"[ZEN-SELENIUM] Поиск по ключевому слову: {keyword}")
                
                search_results = self.search_yandex(keyword, max_results=5)
                logger.info(f"[ZEN-SELENIUM] Найдено результатов: {len(search_results)}")
                
                # Парсим каждую найденную статью
                for result in search_results:
                    article = self.parse_article(result['url'])
                    
                    if article:
                        # Добавляем данные для базы
                        review_data = {
                            'source': 'dzen',
                            'source_id': f"dzen_{hash(article['url'])}",
                            'author': article.get('author', 'Unknown'),
                            'author_id': None,
                            'text': article['text'],
                            'url': article['url'],
                            'published_date': article.get('published_date'),
                            'is_comment': False
                        }
                        
                        # Анализ тональности
                        if self.sentiment_analyzer:
                            try:
                                sentiment = self.sentiment_analyzer.analyze(article['text'])
                                review_data['sentiment_score'] = sentiment.get('sentiment_score', 0)
                                review_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                            except Exception as e:
                                logger.debug(f"[ZEN-SELENIUM] Ошибка анализа тональности: {e}")
                        
                        all_articles.append(review_data)
                        logger.info(f"[ZEN-SELENIUM] ✓ Статья добавлена: {article['title'][:50]}...")
                    
                    # Задержка между статьями
                    time.sleep(random.uniform(1, 3))
                
                # Задержка между ключевыми словами
                time.sleep(random.uniform(2, 4))
            
            # Сбор комментариев если нужно
            if collect_comments and len(all_articles) > 0:
                logger.info("[ZEN-SELENIUM] Начинаем сбор комментариев...")
                comments_total = 0
                
                for article in all_articles[:10]:  # Комментарии для первых 10 статей
                    try:
                        article_url = article.get('url')
                        if article_url:
                            comments = self.parse_dzen_comments(article_url)
                            if comments:
                                all_articles.extend(comments)
                                comments_total += len(comments)
                                logger.info(f"[ZEN-Comments] Добавлено {len(comments)} комментариев к статье")
                            time.sleep(random.uniform(2, 3))  # Задержка между статьями
                    except Exception as e:
                        logger.debug(f"[ZEN-Comments] Ошибка сбора комментариев: {e}")
                        continue
                
                logger.info(f"[ZEN-SELENIUM] ✓ Собрано комментариев: {comments_total}")
            
            # Итоги
            posts_count = len([p for p in all_articles if not p.get('is_comment')])
            comments_count = len([p for p in all_articles if p.get('is_comment')])
            
            logger.info(f"[ZEN-SELENIUM] Сбор завершен")
            logger.info(f"[ZEN-SELENIUM] Статей: {posts_count}")
            if comments_count > 0:
                logger.info(f"[ZEN-SELENIUM] Комментариев: {comments_count}")
            logger.info(f"[ZEN-SELENIUM] ИТОГО: {len(all_articles)} записей")
            
        except Exception as e:
            logger.error(f"[ZEN-SELENIUM] Ошибка при сборе: {e}")
        
        finally:
            self._close_driver()
            
            # Очищаем временную директорию
            try:
                import tempfile
                import shutil
                import os
                user_data_dir = os.path.join(tempfile.gettempdir(), f'zen_selenium_chrome_{os.getpid()}')
                if os.path.exists(user_data_dir):
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                    logger.debug("[ZEN-SELENIUM] Временная директория очищена")
            except:
                pass
        
        return all_articles
