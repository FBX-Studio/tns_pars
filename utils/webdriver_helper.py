"""
Helper для инициализации WebDriver с fallback логикой
"""
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import logging

logger = logging.getLogger(__name__)

def create_edge_driver(headless=True):
    """
    Создает Edge WebDriver с автоматическим fallback
    
    Args:
        headless: Запускать в headless режиме (без окна)
    
    Returns:
        WebDriver instance или None при ошибке
    """
    edge_options = Options()
    
    if headless:
        edge_options.add_argument('--headless=new')
    
    # Базовые настройки
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('--disable-dev-shm-usage')
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    edge_options.add_argument('--window-size=1920,1080')
    
    # Отключение загрузки изображений для скорости
    prefs = {'profile.managed_default_content_settings.images': 2}
    edge_options.add_experimental_option('prefs', prefs)
    
    # Метод 1: Попробовать webdriver-manager (если есть интернет)
    try:
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        logger.info("[WEBDRIVER] Попытка загрузки EdgeDriver через webdriver-manager...")
        driver_path = EdgeChromiumDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
        logger.info("[WEBDRIVER] ✓ WebDriver запущен через webdriver-manager")
        return driver
    except Exception as e:
        logger.debug(f"[WEBDRIVER] webdriver-manager недоступен: {e}")
    
    # Метод 2: Selenium 4+ может автоматически найти Edge без указания пути
    try:
        logger.info("[WEBDRIVER] Попытка запуска Edge без явного пути...")
        driver = webdriver.Edge(options=edge_options)
        logger.info("[WEBDRIVER] ✓ WebDriver запущен напрямую")
        return driver
    except Exception as e:
        logger.error(f"[WEBDRIVER] Не удалось запустить Edge: {e}")
        return None

def hide_webdriver_signature(driver):
    """
    Скрывает признаки автоматизации в WebDriver
    
    Args:
        driver: WebDriver instance
    """
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
    except Exception as e:
        logger.debug(f"[WEBDRIVER] Не удалось скрыть webdriver signature: {e}")
