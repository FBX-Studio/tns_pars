"""
Сбор новостей из Яндекс.Дзен через Google поиск
Обходит проблему с авторизацией RSS
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True, encoding='utf-8')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import Config
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DzenSearchCollector:
    """Коллектор статей из Дзен через Google Search"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        self.proxies_list = []
        self.current_proxy = None
    
    def _get_free_proxies(self):
        """Получение списка бесплатных прокси"""
        try:
            logger.info("[DZEN] Загрузка списка прокси...")
            response = requests.get(
                'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                self.proxies_list = [f'http://{p.strip()}' for p in proxies if p.strip()][:20]
                logger.info(f"[DZEN] Загружено прокси: {len(self.proxies_list)}")
                return True
        except Exception as e:
            logger.warning(f"[DZEN] Не удалось загрузить прокси: {e}")
        return False
    
    def _get_next_proxy(self):
        """Получить следующий прокси из списка"""
        if not self.proxies_list:
            self._get_free_proxies()
        
        if self.proxies_list:
            import random
            self.current_proxy = random.choice(self.proxies_list)
            return self.current_proxy
        return None
    
    def _is_relevant(self, text):
        """Проверка релевантности"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Исключения
        exclude = ['газпром', 'т плюс', 'т-плюс', 'вакансия']
        if any(e in text_lower for e in exclude):
            return False
        
        # Ключевые слова
        if not self.keywords:
            return True
        
        return any(k.lower() in text_lower for k in self.keywords)
    
    def search_google(self, query, use_proxy=True):
        """Поиск через Google"""
        articles = []
        
        try:
            # Поиск в Google по Дзену
            search_query = f'site:dzen.ru {query}'
            google_url = f'https://www.google.com/search?q={requests.utils.quote(search_query)}&num=20'
            
            logger.info(f"[DZEN] Поиск в Google: {search_query}")
            
            # Пробуем с прокси
            response = None
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    if use_proxy and Config.USE_FREE_PROXIES == 'True':
                        proxy = self._get_next_proxy()
                        if proxy:
                            logger.info(f"[DZEN] Попытка {attempt + 1}/{max_attempts} с прокси: {proxy[:30]}...")
                            response = requests.get(
                                google_url,
                                headers=self.headers,
                                proxies={'http': proxy, 'https': proxy},
                                timeout=15
                            )
                        else:
                            logger.info(f"[DZEN] Попытка {attempt + 1}/{max_attempts} без прокси")
                            response = requests.get(google_url, headers=self.headers, timeout=15)
                    else:
                        logger.info(f"[DZEN] Попытка {attempt + 1}/{max_attempts} без прокси")
                        response = requests.get(google_url, headers=self.headers, timeout=15)
                    
                    if response and response.status_code == 200:
                        logger.info(f"[DZEN] ✓ Успешное подключение")
                        break
                    else:
                        logger.warning(f"[DZEN] Статус {response.status_code if response else 'None'}")
                        time.sleep(1)
                        
                except Exception as e:
                    logger.debug(f"[DZEN] Ошибка попытки {attempt + 1}: {e}")
                    if attempt < max_attempts - 1:
                        time.sleep(1)
                    continue
            
            if not response or response.status_code != 200:
                logger.warning(f"[DZEN] Google вернул статус {response.status_code if response else 'None'}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем результаты поиска Google
            results = soup.find_all('div', class_='g')
            
            logger.info(f"[DZEN] Найдено результатов: {len(results)}")
            
            for result in results:
                try:
                    # Ссылка
                    link_elem = result.find('a')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    
                    url = link_elem['href']
                    
                    # Фильтруем только статьи Дзен
                    if 'dzen.ru/a/' not in url and 'dzen.ru/media/' not in url:
                        continue
                    
                    # Заголовок
                    title_elem = result.find('h3')
                    title = title_elem.text if title_elem else ''
                    
                    # Описание
                    desc_elem = result.find('div', class_=['VwiC3b', 'yXK7lf'])
                    description = desc_elem.text if desc_elem else ''
                    
                    full_text = f"{title}\n\n{description}"
                    
                    # Проверка релевантности
                    if not self._is_relevant(full_text):
                        continue
                    
                    # ID статьи
                    if '/a/' in url:
                        article_id = url.split('/a/')[-1].split('?')[0].split('#')[0]
                    else:
                        article_id = abs(hash(url))
                    
                    pub_datetime = datetime.now()
                    date_str = pub_datetime.strftime('%Y%m%d')
                    
                    articles.append({
                        'source': 'zen',
                        'source_id': f"dzen_{article_id}_{date_str}",
                        'author': 'Яндекс.Дзен',
                        'author_id': 'dzen',
                        'text': full_text[:500],
                        'url': url,
                        'published_date': pub_datetime,
                        'date': pub_datetime
                    })
                    
                    logger.info(f"[DZEN] ✓ {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[DZEN] Ошибка парсинга результата: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"[DZEN] Ошибка поиска: {e}")
        
        return articles
    
    def collect(self):
        """Сбор статей"""
        all_articles = []
        
        logger.info(f"[DZEN] Начало сбора через Google поиск")
        logger.info(f"[DZEN] Ключевые слова: {', '.join(self.keywords[:3])}")
        
        # Ищем по первым 2 ключевым словам
        for keyword in self.keywords[:2]:
            logger.info(f"\n[DZEN] Поиск по: {keyword}")
            articles = self.search_google(keyword)
            all_articles.extend(articles)
            time.sleep(2)  # Задержка между запросами
        
        logger.info(f"\n[DZEN] Всего найдено релевантных статей: {len(all_articles)}")
        
        return all_articles


if __name__ == '__main__':
    print("="*70)
    print("СБОР НОВОСТЕЙ ИЗ ЯНДЕКС.ДЗЕН (ЧЕРЕЗ ПОИСК)")
    print("="*70)
    
    collector = DzenSearchCollector()
    
    print(f"\nКлючевые слова для поиска: {', '.join(collector.keywords)}")
    print("\n" + "-"*70 + "\n")
    
    articles = collector.collect()
    
    print("\n" + "="*70)
    print(f"Найдено релевантных статей: {len(articles)}")
    print("="*70)
    
    if articles:
        print("\nПримеры статей:\n")
        for i, art in enumerate(articles[:5], 1):
            print(f"{i}. {art['text'][:150]}...")
            print(f"   URL: {art['url']}")
            print()
    else:
        print("\n❌ Статьи не найдены.")
        print("\nВозможные причины:")
        print("  - Google ограничил доступ (капча, блокировка)")
        print("  - Нет статей с ключевыми словами в Дзен")
        print("\nПопробуйте:")
        print("  - Запустить через некоторое время")
        print("  - Использовать VPN или прокси")
