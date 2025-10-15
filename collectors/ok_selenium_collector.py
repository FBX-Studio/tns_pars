"""
Коллектор для OK.ru через Selenium (обход ограничений API)
"""
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
from utils.webdriver_helper import create_edge_driver
import logging
import time
import random

logger = logging.getLogger(__name__)

class OKSeleniumCollector:
    """Коллектор постов из OK.ru через Selenium (для обхода ограничений API)"""
    
    def __init__(self, sentiment_analyzer=None):
        # Используем hardcoded ключевые слова для избежания проблем с кодировкой
        self.keywords = ['ТНС энерго НН', 'ТНС энерго', 'энергосбыт', 'ТНС']
        self.driver = None
        self.sentiment_analyzer = sentiment_analyzer
        
    def _init_driver(self, headless=True):
        """Инициализация Selenium WebDriver"""
        logger.info("[OK-SELENIUM] Запуск WebDriver...")
        self.driver = create_edge_driver(headless=headless)
        
        if self.driver:
            logger.info("[OK-SELENIUM] ✓ WebDriver запущен")
            return True
        else:
            logger.error("[OK-SELENIUM] Ошибка инициализации WebDriver")
            return False
    
    def _close_driver(self):
        """Закрытие WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("[OK-SELENIUM] WebDriver закрыт")
            except:
                pass
    
    def _is_relevant(self, text):
        """Проверка релевантности"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        exclude = ['газпром', 'т плюс', 'вакансия']
        if any(e in text_lower for e in exclude):
            return False
        
        return any(k.lower() in text_lower for k in self.keywords)
    
    def search_ok(self, query, max_results=20):
        """Поиск в OK.ru через Selenium"""
        results = []
        
        try:
            search_url = f"https://ok.ru/search?st.query={query}&st.typ=GROUPS"
            logger.info(f"[OK-SELENIUM] Поиск: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Парсим результаты поиска групп
            groups = soup.find_all('div', class_='ugrid_i')[:10]
            
            logger.info(f"[OK-SELENIUM] Найдено групп: {len(groups)}")
            
            for group in groups:
                try:
                    link_elem = group.find('a', class_='ucard_lk')
                    if not link_elem:
                        continue
                    
                    group_url = 'https://ok.ru' + link_elem['href']
                    
                    # Переходим в группу и собираем посты
                    posts = self._get_group_posts(group_url, max_per_group=3)
                    results.extend(posts)
                    
                    if len(results) >= max_results:
                        break
                    
                except Exception as e:
                    logger.debug(f"[OK-SELENIUM] Ошибка парсинга группы: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"[OK-SELENIUM] Ошибка поиска: {e}")
            return results
    
    def _get_group_posts(self, group_url, max_per_group=5):
        """Сбор постов из группы"""
        posts = []
        
        try:
            logger.info(f"[OK-SELENIUM] Сбор постов из группы: {group_url}")
            
            self.driver.get(group_url)
            time.sleep(random.uniform(2, 4))
            
            # Скроллим вниз для загрузки постов
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Ищем посты
            post_elements = soup.find_all('div', class_='feed-w')[:max_per_group]
            
            for post_elem in post_elements:
                try:
                    # Текст поста
                    text_elem = post_elem.find('div', class_='media-text_cnt_tx')
                    if not text_elem:
                        continue
                    
                    text = text_elem.get_text(strip=True)
                    
                    if not self._is_relevant(text):
                        continue
                    
                    # Ссылка на пост
                    link_elem = post_elem.find('a', class_='media-text_lk')
                    post_url = 'https://ok.ru' + link_elem['href'] if link_elem else group_url
                    
                    # Автор
                    author_elem = post_elem.find('a', class_='emphased')
                    author = author_elem.get_text(strip=True) if author_elem else 'OK User'
                    
                    posts.append({
                        'source': 'ok',
                        'source_id': f"ok_selenium_{hash(post_url)}",
                        'author': author,
                        'author_id': None,
                        'text': text[:500],
                        'url': post_url,
                        'published_date': datetime.now(),
                        'is_comment': False
                    })
                    
                    logger.info(f"[OK-SELENIUM] ✓ Пост: {text[:50]}...")
                    
                except Exception as e:
                    logger.debug(f"[OK-SELENIUM] Ошибка парсинга поста: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"[OK-SELENIUM] Ошибка сбора постов: {e}")
        
        return posts
    
    def collect(self, collect_comments=False):
        """Основной метод сбора"""
        all_posts = []
        
        logger.info("[OK-SELENIUM] Запуск сбора из OK.ru через Selenium")
        
        if not self._init_driver(headless=True):
            logger.error("[OK-SELENIUM] Не удалось запустить WebDriver")
            return all_posts
        
        try:
            for keyword in self.keywords[:3]:  # Первые 3 ключевых слова
                logger.info(f"[OK-SELENIUM] Поиск по: {keyword}")
                
                posts = self.search_ok(keyword, max_results=10)
                all_posts.extend(posts)
                
                time.sleep(random.uniform(3, 5))
            
            logger.info(f"[OK-SELENIUM] Собрано постов: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[OK-SELENIUM] Ошибка сбора: {e}")
        
        finally:
            self._close_driver()
        
        return all_posts
