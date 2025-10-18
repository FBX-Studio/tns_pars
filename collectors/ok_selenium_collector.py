"""
Selenium коллектор для OK.ru с поддержкой прокси, авторизации и комментариев
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
import pickle
import os

logger = logging.getLogger(__name__)

class OKSeleniumCollector:
    """Коллектор OK.ru через Selenium (обход всех блокировок) + авторизация + комментарии"""
    
    def __init__(self, sentiment_analyzer=None):
        self.keywords = Config.COMPANY_KEYWORDS
        self.sentiment_analyzer = sentiment_analyzer
        self.driver = None
        self.max_retries = 2
        self.cookies_file = 'ok_cookies.pkl'
        self.is_authenticated = False
        
        # Учетные данные из .env
        self.ok_login = os.getenv('OK_LOGIN', '')
        self.ok_password = os.getenv('OK_PASSWORD', '')
        
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
            
            # Уникальная директория для профиля (избегаем конфликтов)
            import tempfile
            import shutil
            user_data_dir = os.path.join(tempfile.gettempdir(), f'ok_selenium_chrome_{os.getpid()}')
            
            # Очищаем старую директорию если есть
            if os.path.exists(user_data_dir):
                try:
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                except:
                    pass
            
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Headless режим с улучшенной стабильностью
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
            
            # Стабилизация Chrome
            chrome_options.add_argument('--remote-debugging-port=0')  # Динамический выбор порта
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-breakpad')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
            chrome_options.add_argument('--force-color-profile=srgb')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--mute-audio')
            
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
    
    def save_cookies(self):
        """Сохранение cookies для повторного использования"""
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'wb') as f:
                    pickle.dump(cookies, f)
                logger.info("[OK-Auth] Cookies сохранены")
                return True
        except Exception as e:
            logger.warning(f"[OK-Auth] Ошибка сохранения cookies: {e}")
        return False
    
    def load_cookies(self):
        """Загрузка сохраненных cookies"""
        try:
            if os.path.exists(self.cookies_file) and self.driver:
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                # Сначала откроем OK.ru
                self.driver.get("https://ok.ru")
                self._random_delay(2, 3)
                
                # Загружаем cookies
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                
                # Обновляем страницу
                self.driver.refresh()
                self._random_delay(2, 3)
                
                # Проверяем авторизацию
                if self.check_auth():
                    logger.info("[OK-Auth] ✓ Авторизация через cookies успешна")
                    self.is_authenticated = True
                    return True
                else:
                    logger.warning("[OK-Auth] Cookies устарели")
                    os.remove(self.cookies_file)
        except Exception as e:
            logger.warning(f"[OK-Auth] Ошибка загрузки cookies: {e}")
        return False
    
    def check_auth(self):
        """Проверка авторизации"""
        try:
            if not self.driver:
                return False
            
            # Ищем элементы, которые есть только у авторизованных пользователей
            page_source = self.driver.page_source
            
            # Признаки авторизации
            if 'toolbar_uprofile' in page_source or 'topPanel_logout' in page_source:
                return True
            
            # Проверяем URL профиля
            try:
                profile_link = self.driver.find_element(By.CSS_SELECTOR, 'a[data-l="t,userPage"]')
                if profile_link:
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.debug(f"[OK-Auth] Ошибка проверки авторизации: {e}")
            return False
    
    def login(self):
        """Авторизация на OK.ru"""
        try:
            if not self.ok_login or not self.ok_password:
                logger.warning("[OK-Auth] Логин или пароль не указаны в .env")
                logger.info("[OK-Auth] Добавьте OK_LOGIN и OK_PASSWORD в файл .env")
                return False
            
            if not self.driver:
                logger.error("[OK-Auth] Драйвер не инициализирован")
                return False
            
            logger.info("[OK-Auth] Попытка авторизации...")
            
            # Открываем страницу входа
            self.driver.get("https://ok.ru")
            self._random_delay(2, 3)
            
            # Ищем поле логина
            try:
                login_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "field_email"))
                )
                login_input.clear()
                login_input.send_keys(self.ok_login)
                logger.info("[OK-Auth] Логин введен")
                self._random_delay(1, 2)
            except:
                logger.warning("[OK-Auth] Поле логина не найдено, пробуем альтернативный метод")
                try:
                    login_input = self.driver.find_element(By.NAME, "st.email")
                    login_input.clear()
                    login_input.send_keys(self.ok_login)
                except Exception as e:
                    logger.error(f"[OK-Auth] Не удалось найти поле логина: {e}")
                    return False
            
            # Ищем поле пароля
            try:
                password_input = self.driver.find_element(By.ID, "field_password")
                password_input.clear()
                password_input.send_keys(self.ok_password)
                logger.info("[OK-Auth] Пароль введен")
                self._random_delay(1, 2)
            except:
                try:
                    password_input = self.driver.find_element(By.NAME, "st.password")
                    password_input.clear()
                    password_input.send_keys(self.ok_password)
                except Exception as e:
                    logger.error(f"[OK-Auth] Не удалось найти поле пароля: {e}")
                    return False
            
            # Нажимаем кнопку входа
            try:
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Войти']")
                submit_button.click()
                logger.info("[OK-Auth] Кнопка входа нажата")
            except:
                # Пробуем отправить форму через Enter
                password_input.send_keys(Keys.RETURN)
                logger.info("[OK-Auth] Форма отправлена через Enter")
            
            # Ждем загрузки
            self._random_delay(3, 5)
            
            # Проверяем успешность авторизации
            if self.check_auth():
                logger.info("[OK-Auth] ✓✓✓ Авторизация успешна!")
                self.is_authenticated = True
                
                # Сохраняем cookies
                self.save_cookies()
                
                return True
            else:
                logger.warning("[OK-Auth] Авторизация не удалась")
                # Сохраняем скриншот для отладки
                try:
                    self.driver.save_screenshot('ok_login_failed.png')
                    logger.info("[OK-Auth] Скриншот сохранен: ok_login_failed.png")
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"[OK-Auth] Ошибка авторизации: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def parse_post_comments(self, post_url):
        """Парсинг комментариев к посту"""
        comments = []
        
        try:
            if not self.driver:
                return comments
            
            logger.info(f"[OK-Comments] Парсинг комментариев: {post_url}")
            
            # Открываем пост
            self.driver.get(post_url)
            self._random_delay(2, 3)
            
            # Скроллим вниз для загрузки комментариев
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            self._random_delay(1, 2)
            
            # Получаем HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем комментарии по различным селекторам
            comment_selectors = [
                {'class': 'comments_lst'},
                {'class': 'comments-item'},
                {'class': 'media-text_cnt'},
                {'data-tsid': 'comments_lst'},
            ]
            
            for selector in comment_selectors:
                comment_elements = soup.find_all(['div', 'li'], selector)
                
                if comment_elements:
                    logger.info(f"[OK-Comments] Найдено элементов по селектору {selector}: {len(comment_elements)}")
                    
                    for elem in comment_elements[:30]:  # Максимум 30 комментариев
                        try:
                            # Текст комментария
                            text_elem = elem.find('div', class_='media-text_cnt') or elem.find(class_='comments_text')
                            if not text_elem:
                                continue
                            
                            text = text_elem.get_text(strip=True)
                            if not text or len(text) < 5:
                                continue
                            
                            # Автор
                            author_elem = elem.find('a', class_='user-name') or elem.find(class_='comments_author')
                            author = author_elem.get_text(strip=True) if author_elem else 'OK User'
                            
                            # Создаем комментарий
                            comment_data = {
                                'source': 'ok',
                                'source_id': f"ok_comment_{abs(hash(text[:50]))}",
                                'author': author[:100],
                                'author_id': f"ok_{abs(hash(author))}",
                                'text': text[:500],
                                'url': post_url,
                                'published_date': datetime.now(),
                                'date': datetime.now(),
                                'is_comment': True,
                                'parent_source_id': post_url.split('/')[-1] if '/' in post_url else post_url
                            }
                            
                            # Анализ тональности
                            if self.sentiment_analyzer:
                                sentiment = self.sentiment_analyzer.analyze(text)
                                comment_data['sentiment_score'] = sentiment['sentiment_score']
                                comment_data['sentiment_label'] = sentiment['sentiment_label']
                            
                            comments.append(comment_data)
                            
                        except Exception as e:
                            logger.debug(f"[OK-Comments] Ошибка парсинга комментария: {e}")
                            continue
                    
                    if comments:
                        break  # Нашли рабочий селектор
            
            logger.info(f"[OK-Comments] Собрано комментариев: {len(comments)}")
            
        except Exception as e:
            logger.warning(f"[OK-Comments] Ошибка парсинга комментариев: {e}")
        
        return comments
    
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
                        try:
                            sentiment = self.sentiment_analyzer.analyze(text)
                            post_data['sentiment_score'] = sentiment.get('sentiment_score', 0)
                            post_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                        except Exception as e:
                            logger.debug(f"[OK-Selenium] Ошибка анализа тональности: {e}")
                    
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
    
    def collect(self, collect_comments=False):
        """Основной метод сбора с поддержкой авторизации и комментариев"""
        all_posts = []
        
        try:
            logger.info("[OK-Selenium] ================================================")
            logger.info("[OK-Selenium] ЗАПУСК SELENIUM КОЛЛЕКТОРА ДЛЯ OK.RU")
            if collect_comments:
                logger.info("[OK-Selenium] Режим: ПОСТЫ + КОММЕНТАРИИ")
            else:
                logger.info("[OK-Selenium] Режим: ТОЛЬКО ПОСТЫ")
            logger.info("[OK-Selenium] ================================================")
            
            # Инициализация драйвера
            self.driver = self._setup_driver()
            if not self.driver:
                logger.error("[OK-Selenium] Не удалось создать драйвер")
                return all_posts
            
            # Попытка авторизации (если нужны комментарии или просто для доступа)
            if collect_comments or self.ok_login:
                logger.info("[OK-Selenium] Попытка авторизации...")
                
                # Сначала пробуем через сохраненные cookies
                if self.load_cookies():
                    logger.info("[OK-Selenium] ✓ Авторизация через cookies успешна")
                elif self.ok_login and self.ok_password:
                    # Если cookies не сработали - логинимся
                    if self.login():
                        logger.info("[OK-Selenium] ✓ Авторизация через логин/пароль успешна")
                    else:
                        logger.warning("[OK-Selenium] Авторизация не удалась")
                        if collect_comments:
                            logger.warning("[OK-Selenium] Комментарии недоступны без авторизации")
                else:
                    logger.info("[OK-Selenium] Учетные данные не указаны (OK_LOGIN, OK_PASSWORD)")
            
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
            
            # Сбор комментариев если нужно и есть авторизация
            if collect_comments and len(all_posts) > 0 and self.is_authenticated:
                logger.info("[OK-Selenium] Начинаем сбор комментариев...")
                comments_total = 0
                
                for post in all_posts[:10]:  # Комментарии для первых 10 постов
                    try:
                        post_url = post.get('url')
                        if post_url:
                            comments = self.parse_post_comments(post_url)
                            if comments:
                                all_posts.extend(comments)
                                comments_total += len(comments)
                                logger.info(f"[OK-Comments] Добавлено {len(comments)} комментариев к посту")
                            time.sleep(2)  # Задержка между постами
                    except Exception as e:
                        logger.debug(f"[OK-Comments] Ошибка сбора комментариев: {e}")
                        continue
                
                logger.info(f"[OK-Selenium] ✓ Собрано комментариев: {comments_total}")
            elif collect_comments and not self.is_authenticated:
                logger.warning("[OK-Selenium] Комментарии не собраны: требуется авторизация")
                logger.info("[OK-Selenium] Добавьте OK_LOGIN и OK_PASSWORD в .env файл")
            
            # Итоги
            logger.info("[OK-Selenium] ================================================")
            if len(all_posts) > 0:
                posts_count = len([p for p in all_posts if not p.get('is_comment')])
                comments_count = len([p for p in all_posts if p.get('is_comment')])
                logger.info(f"[OK-Selenium] ✓✓✓ УСПЕХ!")
                logger.info(f"[OK-Selenium] Собрано постов: {posts_count}")
                if comments_count > 0:
                    logger.info(f"[OK-Selenium] Собрано комментариев: {comments_count}")
                logger.info(f"[OK-Selenium] ИТОГО: {len(all_posts)} записей")
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
        
        finally:
            # Закрываем драйвер
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("[OK-Selenium] Драйвер закрыт")
                except:
                    pass
            
            # Очищаем временную директорию
            try:
                import tempfile
                import shutil
                user_data_dir = os.path.join(tempfile.gettempdir(), f'ok_selenium_chrome_{os.getpid()}')
                if os.path.exists(user_data_dir):
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                    logger.debug("[OK-Selenium] Временная директория очищена")
            except:
                pass
        
        return all_posts
