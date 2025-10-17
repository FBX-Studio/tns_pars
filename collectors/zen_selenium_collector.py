"""
Коллектор для Яндекс.Дзен через Selenium (обход капчи)
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
from utils.webdriver_helper import create_edge_driver, hide_webdriver_signature
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
        logger.info("[SELENIUM] Запуск WebDriver...")
        self.driver = create_edge_driver(headless=headless)
        
        if self.driver:
            hide_webdriver_signature(self.driver)
            logger.info("[SELENIUM] ✓ WebDriver запущен")
            return True
        else:
            logger.error("[SELENIUM] Ошибка инициализации WebDriver")
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
        """Основной метод сбора данных"""
        all_articles = []
        
        logger.info("[ZEN-SELENIUM] Начало сбора данных из Яндекс.Дзен через Selenium")
        
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
                        
                        all_articles.append(review_data)
                        logger.info(f"[ZEN-SELENIUM] ✓ Статья добавлена: {article['title'][:50]}...")
                    
                    # Задержка между статьями
                    time.sleep(random.uniform(1, 3))
                
                # Задержка между ключевыми словами
                time.sleep(random.uniform(2, 4))
            
            logger.info(f"[ZEN-SELENIUM] Сбор завершен. Всего статей: {len(all_articles)}")
            
        except Exception as e:
            logger.error(f"[ZEN-SELENIUM] Ошибка при сборе: {e}")
        
        finally:
            self._close_driver()
        
        return all_articles
