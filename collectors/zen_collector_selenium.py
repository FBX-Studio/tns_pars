"""
Коллектор для Яндекс.Дзен через Selenium (обход капчи)
"""
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from datetime import datetime
from config import Config
import logging
import time
import re

logger = logging.getLogger(__name__)

class ZenCollectorSelenium:
    """Коллектор статей из Яндекс.Дзен через Selenium"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.driver = None
        
    def _setup_driver(self):
        """Настройка Edge драйвера"""
        edge_options = Options()
        
        # Headless режим (без окна браузера)
        edge_options.add_argument('--headless=new')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-gpu')
        
        # Имитация реального браузера
        edge_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')
        edge_options.add_argument('--window-size=1920,1080')
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        
        # Отключение логов
        edge_options.add_argument('--log-level=3')
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            
            # Скрываем WebDriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("[ZEN-SELENIUM] Edge драйвер запущен")
            return True
        except Exception as e:
            logger.error(f"[ZEN-SELENIUM] Ошибка запуска драйвера: {e}")
            return False
    
    def _close_driver(self):
        """Закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("[ZEN-SELENIUM] Драйвер закрыт")
            except:
                pass
    
    def _is_relevant(self, text):
        """Проверка релевантности текста"""
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def search_dzen_yandex(self, query):
        """Поиск статей Дзен через Яндекс с Selenium"""
        articles = []
        
        try:
            # Формируем поисковый запрос
            search_query = f'dzen.ru {query}'
            yandex_url = f'https://yandex.ru/search/?text={search_query}&lr=47'
            
            logger.info(f"[ZEN-SELENIUM] Поиск: {search_query}")
            
            # Загружаем страницу
            self.driver.get(yandex_url)
            
            # Ждем загрузки результатов (макс 10 сек)
            wait = WebDriverWait(self.driver, 10)
            
            # Проверяем на капчу
            if 'showcaptcha' in self.driver.current_url:
                logger.warning("[ZEN-SELENIUM] Яндекс показал капчу")
                return []
            
            # Ждем появления результатов
            time.sleep(2)  # Даем время на полную загрузку
            
            # Ищем ссылки на dzen.ru
            dzen_links = set()
            
            # Находим все ссылки на странице
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            for link_elem in links:
                try:
                    href = link_elem.get_attribute('href')
                    if href and 'dzen.ru/a/' in href:
                        # Очищаем URL
                        clean_url = href.split('?')[0]
                        if clean_url not in dzen_links:
                            dzen_links.add(clean_url)
                            logger.debug(f"[ZEN-SELENIUM] Найдена статья: {clean_url}")
                except:
                    continue
            
            logger.info(f"[ZEN-SELENIUM] Найдено ссылок: {len(dzen_links)}")
            
            # Для каждой ссылки извлекаем заголовок из результатов поиска
            for link_url in list(dzen_links)[:20]:  # Ограничение 20 статей
                try:
                    # Ищем элемент результата, содержащий эту ссылку
                    title = ''
                    description = ''
                    
                    # Пробуем найти заголовок рядом со ссылкой
                    xpath_query = f"//a[contains(@href, '{link_url}')]/ancestor::li//h2 | //a[contains(@href, '{link_url}')]/ancestor::div[contains(@class, 'organic')]//h2"
                    
                    try:
                        title_elem = self.driver.find_element(By.XPATH, xpath_query)
                        title = title_elem.text.strip()
                    except:
                        # Альтернативный поиск
                        try:
                            link_elem = self.driver.find_element(By.XPATH, f"//a[contains(@href, '{link_url}')]")
                            title = link_elem.text.strip()
                        except:
                            pass
                    
                    if not title:
                        continue
                    
                    # Ищем описание
                    try:
                        desc_xpath = f"//a[contains(@href, '{link_url}')]/ancestor::li//div[contains(@class, 'text')] | //a[contains(@href, '{link_url}')]/ancestor::div[contains(@class, 'organic')]//div[contains(@class, 'text')]"
                        desc_elem = self.driver.find_element(By.XPATH, desc_xpath)
                        description = desc_elem.text.strip()
                    except:
                        pass
                    
                    full_text = f"{title}\n\n{description}"
                    
                    # Проверяем релевантность
                    if not self._is_relevant(full_text):
                        continue
                    
                    # Извлекаем ID статьи из URL
                    article_id = link_url.split('/a/')[-1] if '/a/' in link_url else abs(hash(link_url))
                    
                    pub_date = datetime.now()
                    date_str = pub_date.strftime('%Y%m%d')
                    
                    articles.append({
                        'source': 'zen',
                        'source_id': f"dzen_{article_id}_{date_str}",
                        'author': 'Яндекс.Дзен',
                        'author_id': 'yandex_dzen',
                        'text': full_text[:500],
                        'url': link_url,
                        'published_date': pub_date,
                        'date': pub_date
                    })
                    
                    logger.info(f"[ZEN-SELENIUM] Добавлена: {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[ZEN-SELENIUM] Ошибка обработки ссылки: {e}")
                    continue
            
            logger.info(f"[ZEN-SELENIUM] Релевантных статей: {len(articles)}")
            
        except Exception as e:
            logger.error(f"[ZEN-SELENIUM] Ошибка поиска: {e}")
        
        return articles
    
    def collect(self):
        """Сбор статей из Яндекс.Дзен"""
        all_posts = []
        
        try:
            # Запускаем драйвер
            if not self._setup_driver():
                logger.error("[ZEN-SELENIUM] Не удалось запустить драйвер")
                return []
            
            logger.info("[ZEN-SELENIUM] Запуск сбора из Яндекс.Дзен")
            
            # Поиск по первым 2 ключевым словам
            for keyword in self.keywords[:2]:
                logger.info(f"[ZEN-SELENIUM] Поиск по ключевому слову: {keyword}")
                posts = self.search_dzen_yandex(keyword)
                all_posts.extend(posts)
                time.sleep(3)  # Задержка между запросами
            
            logger.info(f"[ZEN-SELENIUM] Всего найдено релевантных статей: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[ZEN-SELENIUM] Ошибка сбора: {e}")
        finally:
            # Обязательно закрываем драйвер
            self._close_driver()
        
        return all_posts
