"""
Сбор постов из Одноклассников через DuckDuckGo
Обход проблем с авторизацией
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

class OKDuckDuckGoCollector:
    """Коллектор постов из OK через DuckDuckGo"""
    
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
        exclude = ['газпром', 'т плюс', 'т-плюс', 'вакансия', 'требуется']
        if any(e in text_lower for e in exclude):
            return False
        
        # Ключевые слова
        if not self.keywords:
            return True
        
        return any(k.lower() in text_lower for k in self.keywords)
    
    def search_duckduckgo(self, query):
        """Поиск через DuckDuckGo HTML версию"""
        posts = []
        
        try:
            # Поиск в DuckDuckGo с фокусом на OK.ru и Нижний Новгород
            search_query = f'site:ok.ru {query} "Нижний Новгород"'
            ddg_url = f'https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}'
            
            logger.info(f"[OK] Поиск в DuckDuckGo: {search_query}")
            
            response = requests.get(ddg_url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"[OK] DuckDuckGo вернул статус {response.status_code}")
                return []
            
            logger.info(f"[OK] ✓ Успешное подключение")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # DuckDuckGo HTML использует класс 'result'
            results = soup.find_all('div', class_='result')
            
            logger.info(f"[OK] Найдено результатов: {len(results)}")
            
            for result in results:
                try:
                    # Ссылка
                    link_elem = result.find('a', class_='result__a')
                    if not link_elem or 'href' not in link_elem.attrs:
                        continue
                    
                    url = link_elem['href']
                    
                    # Фильтруем только посты OK
                    if 'ok.ru' not in url:
                        continue
                    
                    # Извлекаем реальный URL (DuckDuckGo может оборачивать в редирект)
                    if 'uddg=' in url:
                        from urllib.parse import unquote, parse_qs, urlparse
                        parsed = urlparse(url)
                        params = parse_qs(parsed.query)
                        if 'uddg' in params:
                            url = unquote(params['uddg'][0])
                    
                    # Проверяем что это пост/топик/группа
                    if not any(x in url for x in ['/topic/', '/group/', '/profile/']):
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
                    
                    # ID поста
                    post_id = abs(hash(url))
                    
                    pub_datetime = datetime.now()
                    date_str = pub_datetime.strftime('%Y%m%d')
                    
                    posts.append({
                        'source': 'ok',
                        'source_id': f"ok_{post_id}_{date_str}",
                        'author': 'Одноклассники',
                        'author_id': 'ok',
                        'text': full_text[:500],
                        'url': url,
                        'published_date': pub_datetime,
                        'date': pub_datetime
                    })
                    
                    logger.info(f"[OK] ✓ {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[OK] Ошибка парсинга результата: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"[OK] Ошибка поиска: {e}")
            import traceback
            traceback.print_exc()
        
        return posts
    
    def collect(self):
        """Сбор постов"""
        all_posts = []
        
        logger.info(f"[OK] Начало сбора через DuckDuckGo")
        logger.info(f"[OK] Ключевые слова: {', '.join(self.keywords[:3])}")
        
        # Ищем по первым 3 ключевым словам
        for keyword in self.keywords[:3]:
            logger.info(f"\n[OK] Поиск по: {keyword}")
            posts = self.search_duckduckgo(keyword)
            all_posts.extend(posts)
            # Задержка между запросами
            delay = random.uniform(2, 4)
            time.sleep(delay)
        
        logger.info(f"\n[OK] Всего найдено релевантных постов: {len(all_posts)}")
        
        return all_posts


if __name__ == '__main__':
    print("="*70)
    print("СБОР ПОСТОВ ИЗ ОДНОКЛАССНИКОВ (ЧЕРЕЗ DUCKDUCKGO)")
    print("="*70)
    
    collector = OKDuckDuckGoCollector()
    
    print(f"\nКлючевые слова для поиска: {', '.join(collector.keywords)}")
    print("\n" + "-"*70 + "\n")
    
    posts = collector.collect()
    
    print("\n" + "="*70)
    print(f"Найдено релевантных постов: {len(posts)}")
    print("="*70)
    
    if posts:
        print("\nНайденные посты:\n")
        for i, post in enumerate(posts, 1):
            print(f"{i}. {post['text'][:150]}...")
            print(f"   URL: {post['url']}")
            print()
    else:
        print("\n❌ Посты не найдены.")
        print("\nВозможные причины:")
        print("  - Нет постов с ключевыми словами в OK")
        print("  - DuckDuckGo изменил структуру страницы")
        print("  - Временная блокировка запросов")
