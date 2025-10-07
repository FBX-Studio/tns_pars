"""
Сбор новостей из Яндекс.Дзен через DuckDuckGo
DuckDuckGo более лояльно относится к автоматическим запросам
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
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DzenDuckDuckGoCollector:
    """Коллектор статей из Дзен через DuckDuckGo"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    
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
    
    def search_duckduckgo(self, query):
        """Поиск через DuckDuckGo HTML версию"""
        articles = []
        
        try:
            # Поиск в DuckDuckGo
            search_query = f'site:dzen.ru {query}'
            # Используем HTML версию DuckDuckGo
            ddg_url = f'https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}'
            
            logger.info(f"[DZEN] Поиск в DuckDuckGo: {search_query}")
            
            response = requests.get(ddg_url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"[DZEN] DuckDuckGo вернул статус {response.status_code}")
                return []
            
            logger.info(f"[DZEN] ✓ Успешное подключение")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # DuckDuckGo HTML использует класс 'result'
            results = soup.find_all('div', class_='result')
            
            logger.info(f"[DZEN] Найдено результатов: {len(results)}")
            
            for result in results:
                try:
                    # Ссылка
                    link_elem = result.find('a', class_='result__a')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    
                    url = link_elem['href']
                    
                    # Фильтруем только статьи Дзен
                    if 'dzen.ru' not in url:
                        continue
                    
                    # Извлекаем реальный URL (DuckDuckGo может оборачивать в редирект)
                    if 'uddg=' in url:
                        # Декодируем URL из редиректа
                        from urllib.parse import unquote, parse_qs, urlparse
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        if 'uddg' in params:
                            url = unquote(params['uddg'][0])
                    
                    # Проверяем что это статья
                    if '/a/' not in url and '/media/' not in url:
                        continue
                    
                    # Заголовок
                    title = link_elem.text.strip()
                    
                    # Описание
                    desc_elem = result.find('a', class_='result__snippet')
                    description = desc_elem.text.strip() if desc_elem else ''
                    
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
            import traceback
            traceback.print_exc()
        
        return articles
    
    def collect(self):
        """Сбор статей"""
        all_articles = []
        
        logger.info(f"[DZEN] Начало сбора через DuckDuckGo")
        logger.info(f"[DZEN] Ключевые слова: {', '.join(self.keywords[:3])}")
        
        # Ищем по первым 3 ключевым словам
        for keyword in self.keywords[:3]:
            logger.info(f"\n[DZEN] Поиск по: {keyword}")
            articles = self.search_duckduckgo(keyword)
            all_articles.extend(articles)
            # Задержка между запросами
            delay = random.uniform(2, 4)
            time.sleep(delay)
        
        logger.info(f"\n[DZEN] Всего найдено релевантных статей: {len(all_articles)}")
        
        return all_articles


if __name__ == '__main__':
    print("="*70)
    print("СБОР НОВОСТЕЙ ИЗ ЯНДЕКС.ДЗЕН (ЧЕРЕЗ DUCKDUCKGO)")
    print("="*70)
    
    collector = DzenDuckDuckGoCollector()
    
    print(f"\nКлючевые слова для поиска: {', '.join(collector.keywords)}")
    print("\n" + "-"*70 + "\n")
    
    articles = collector.collect()
    
    print("\n" + "="*70)
    print(f"Найдено релевантных статей: {len(articles)}")
    print("="*70)
    
    if articles:
        print("\nНайденные статьи:\n")
        for i, art in enumerate(articles, 1):
            print(f"{i}. {art['text'][:150]}...")
            print(f"   URL: {art['url']}")
            print()
    else:
        print("\n❌ Статьи не найдены.")
        print("\nВозможные причины:")
        print("  - Нет статей с ключевыми словами в Дзен")
        print("  - DuckDuckGo изменил структуру страницы")
