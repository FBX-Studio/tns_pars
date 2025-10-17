"""
Selenium коллектор для OK.ru с поддержкой прокси
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import Config
import logging
import time
import random

logger = logging.getLogger(__name__)

class OKSeleniumCollector:
    """Коллектор OK.ru через Selenium (обход всех блокировок)"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.sentiment_analyzer = sentiment_analyzer
        self.driver = None
        self.max_retries = 2
        
    def _setup_driver(self, use_proxy=None):
        """Настройка Chrome драйвера"""
        try:
            chrome_options = Options()
            
            # Базовые настройки для обхода детекции
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
            
            # Headless режим (работает быстрее, но можно отключить для отладки)
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Язык
            chrome_options.add_argument('--lang=ru-RU')
            
            # Размер окна
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Прокси если указан
            if use_proxy:
                logger.info(f"[OK-Selenium] Использую прокси: {use_proxy}")
                chrome_options.add_argument(f'--proxy-server={use_proxy}')
            
            # Отключаем логи
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Создаем драйвер
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Скрываем признаки webdriver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Устанавливаем таймаут
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            logger.info("[OK-Selenium] ✓ Chrome драйвер успешно инициализирован")
            return driver
            
        except Exception as e:
            logger.error(f"[OK-Selenium] Ошибка создания драйвера: {e}")
            return None
    
    def _is_relevant(self, text):
        """Проверка релевантности"""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower()
        
        # Исключения
        exclude = ['газпром', 'т плюс', 'тнс тула', 'вакансия', 'требуется']
        if any(ex in text_lower for ex in exclude):
            return False
        
        # Ключевые слова
        if not self.keywords:
            return True
        
        return any(kw.lower() in text_lower for kw in self.keywords)
    
    def _random_delay(self, min_sec=1, max_sec=3):
        """Случайная задержка для имитации человека"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def search_with_selenium(self, query, proxy=None):
        """Поиск через Selenium"""
        posts = []
        driver = None
        
        try:
            logger.info(f"[OK-Selenium] Запуск поиска: {query}")
            
            # Создаем драйвер
            driver = self._setup_driver(use_proxy=proxy)
            if not driver:
                return posts
            
            # Формируем URL поиска
            search_url = f'https://ok.ru/search?st.query={query}&st.mode=GlobalSearch'
            
            logger.info(f"[OK-Selenium] Открываю: {search_url}")
            driver.get(search_url)
            
            # Ждем загрузки
            self._random_delay(3, 5)
            
            # Проверяем на капчу
            if 'captcha' in driver.page_source.lower():
                logger.warning("[OK-Selenium] ⚠ Обнаружена капча! Пробую подождать...")
                time.sleep(10)  # Ждем если капча автоматическая
            
            # Скроллим страницу (имитация человека)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self._random_delay(1, 2)
            
            # Получаем HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем результаты поиска
            # OK.ru использует разные классы, пробуем все
            selectors = [
                'div[class*="feed"]',
                'div[class*="post"]',
                'div[class*="topic"]',
                'div[class*="media"]',
                'article',
                'div[data-id]'
            ]
            
            found_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    logger.debug(f"[OK-Selenium] Найдено элементов по селектору '{selector}': {len(elements)}")
                    found_elements.extend(elements)
            
            logger.info(f"[OK-Selenium] Всего найдено элементов: {len(found_elements)}")
            
            # Парсим элементы
            for elem in found_elements[:20]:  # Берем первые 20
                try:
                    # Извлекаем текст
                    text = elem.get_text(strip=True, separator=' ')
                    
                    if not text or len(text) < 30:
                        continue
                    
                    # Проверяем релевантность
                    if not self._is_relevant(text):
                        continue
                    
                    # Ищем ссылку
                    link_tag = elem.find('a', href=True)
                    url = 'https://ok.ru'
                    if link_tag:
                        href = link_tag['href']
                        if href.startswith('http'):
                            url = href
                        elif href.startswith('/'):
                            url = f"https://ok.ru{href}"
                    
                    # Ищем автора
                    author = 'OK User'
                    author_elem = elem.find(class_=lambda x: x and ('author' in x.lower() or 'name' in x.lower() or 'user' in x.lower()))
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                    
                    # Создаем пост
                    post_data = {
                        'source': 'ok',
                        'source_id': f"ok_sel_{abs(hash(text[:100]))}",
                        'author': author[:100],
                        'author_id': f"ok_{abs(hash(author))}",
                        'text': text[:500],
                        'url': url,
                        'published_date': datetime.now(),
                        'date': datetime.now()
                    }
                    
                    # Анализ тональности
                    if self.sentiment_analyzer:
                        sentiment = self.sentiment_analyzer.analyze(text)
                        post_data['sentiment_score'] = sentiment['sentiment_score']
                        post_data['sentiment_label'] = sentiment['sentiment_label']
                    
                    posts.append(post_data)
                    logger.info(f"[OK-Selenium] ✓ Найден пост: {text[:80]}...")
                    
                except Exception as e:
                    logger.debug(f"[OK-Selenium] Ошибка парсинга элемента: {e}")
                    continue
            
            # Сохраняем скриншот для отладки
            try:
                screenshot_path = 'ok_selenium_screenshot.png'
                driver.save_screenshot(screenshot_path)
                logger.info(f"[OK-Selenium] Скриншот сохранен: {screenshot_path}")
            except:
                pass
            
        except TimeoutException:
            logger.warning("[OK-Selenium] Таймаут загрузки страницы")
        except Exception as e:
            logger.error(f"[OK-Selenium] Ошибка: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("[OK-Selenium] Драйвер закрыт")
                except:
                    pass
        
        return posts
    
    def get_free_proxies(self):
        """Получение списка бесплатных прокси"""
        proxies = []
        
        try:
            import requests
            
            logger.info("[OK-Selenium] Получение списка бесплатных прокси...")
            
            # Источник 1: geonode.com (самый надежный)
            try:
                url = 'https://proxylist.geonode.com/api/proxy-list?limit=10&page=1&sort_by=lastChecked&sort_type=desc&protocols=http,https'
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for proxy in data.get('data', [])[:5]:
                        ip = proxy.get('ip')
                        port = proxy.get('port')
                        protocol = proxy.get('protocols', ['http'])[0]
                        if ip and port:
                            proxy_url = f"{protocol}://{ip}:{port}"
                            proxies.append(proxy_url)
                            logger.debug(f"[OK-Selenium] Найден прокси: {proxy_url}")
            except Exception as e:
                logger.debug(f"[OK-Selenium] Ошибка получения прокси из geonode: {e}")
            
            # Источник 2: free-proxy-list.net
            if len(proxies) < 3:
                try:
                    url = 'https://www.proxy-list.download/api/v1/get?type=http'
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        proxy_list = response.text.strip().split('\n')
                        for proxy in proxy_list[:5]:
                            if proxy:
                                proxies.append(f"http://{proxy.strip()}")
                except Exception as e:
                    logger.debug(f"[OK-Selenium] Ошибка получения прокси из proxy-list.download: {e}")
            
            logger.info(f"[OK-Selenium] Получено {len(proxies)} прокси")
            
        except Exception as e:
            logger.warning(f"[OK-Selenium] Не удалось получить бесплатные прокси: {e}")
        
        return proxies
    
    def collect(self):
        """Основной метод сбора"""
        all_posts = []
        
        try:
            logger.info("[OK-Selenium] ================================================")
            logger.info("[OK-Selenium] ЗАПУСК SELENIUM КОЛЛЕКТОРА ДЛЯ OK.RU")
            logger.info("[OK-Selenium] ================================================")
            
            # Попытка 1: Без прокси
            logger.info("[OK-Selenium] Попытка 1: БЕЗ прокси")
            for keyword in self.keywords[:2]:
                try:
                    posts = self.search_with_selenium(keyword)
                    if posts:
                        logger.info(f"[OK-Selenium] ✓ Найдено {len(posts)} постов по '{keyword}'")
                        all_posts.extend(posts)
                        break  # Если нашли - хватит
                    time.sleep(3)
                except Exception as e:
                    logger.debug(f"[OK-Selenium] Ошибка без прокси: {e}")
            
            # Попытка 2: С бесплатными прокси
            if len(all_posts) == 0:
                logger.info("[OK-Selenium] Попытка 2: С БЕСПЛАТНЫМИ ПРОКСИ")
                free_proxies = self.get_free_proxies()
                
                if free_proxies:
                    logger.info(f"[OK-Selenium] Тестирую {len(free_proxies)} прокси...")
                    
                    for proxy in free_proxies[:3]:  # Пробуем первые 3
                        logger.info(f"[OK-Selenium] Пробую прокси: {proxy}")
                        
                        for keyword in self.keywords[:1]:  # Только первое ключевое слово
                            try:
                                posts = self.search_with_selenium(keyword, proxy=proxy)
                                if posts:
                                    logger.info(f"[OK-Selenium] ✓✓✓ УСПЕХ с прокси {proxy}! Найдено {len(posts)} постов")
                                    all_posts.extend(posts)
                                    break
                            except Exception as e:
                                logger.debug(f"[OK-Selenium] Прокси {proxy} не работает: {e}")
                                continue
                        
                        if len(all_posts) > 0:
                            break  # Нашли рабочий прокси
                        
                        time.sleep(2)
                else:
                    logger.warning("[OK-Selenium] Не удалось получить бесплатные прокси")
            
            # Итоги
            logger.info("[OK-Selenium] ================================================")
            if len(all_posts) > 0:
                logger.info(f"[OK-Selenium] ✓✓✓ УСПЕХ! Собрано {len(all_posts)} постов")
            else:
                logger.warning("[OK-Selenium] ПОСТОВ НЕ НАЙДЕНО")
                logger.warning("[OK-Selenium] Возможные причины:")
                logger.warning("[OK-Selenium] 1. OK.ru показывает капчу")
                logger.warning("[OK-Selenium] 2. Все прокси заблокированы")
                logger.warning("[OK-Selenium] 3. На странице нет постов по вашим ключевым словам")
                logger.info("[OK-Selenium] Рекомендации:")
                logger.info("[OK-Selenium] - Настройте Tor: Настройки → Прокси и Tor")
                logger.info("[OK-Selenium] - Используйте платные прокси")
                logger.info("[OK-Selenium] - Получите API токен OK.ru")
            logger.info("[OK-Selenium] ================================================")
            
        except Exception as e:
            logger.error(f"[OK-Selenium] Критическая ошибка: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return all_posts
