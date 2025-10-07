"""
Сбор постов из Одноклассников через Яндекс поиск
Альтернативный метод для обхода блокировок
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

class OKYandexCollector:
    """Коллектор постов из OK через Яндекс поиск"""
    
    def __init__(self):
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
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
    
    def search_yandex(self, query):
        """Поиск через Яндекс"""
        posts = []
        
        try:
            # Поиск в Яндексе
            search_query = f'site:ok.ru {query} Нижний Новгород'
            yandex_url = f'https://yandex.ru/search/?text={requests.utils.quote(search_query)}&lr=47'
            
            logger.info(f"[OK] Поиск в Яндекс: {search_query}")
            
            response = self.session.get(yandex_url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"[OK] Яндекс вернул статус {response.status_code}")
                return []
            
            if 'showcaptcha' in response.url:
                logger.warning("[OK] Яндекс показал капчу")
                return []
            
            logger.info(f"[OK] ✓ Успешное подключение")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем ссылки на OK из результатов Яндекса
            ok_links = set()
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Прямые ссылки на ok.ru
                if href.startswith('https://ok.ru/') or href.startswith('http://ok.ru/'):
                    clean_url = href.split('?')[0]
                    if any(x in clean_url for x in ['/topic/', '/group/', '/profile/']):
                        if clean_url not in ok_links:
                            ok_links.add(clean_url)
                            logger.debug(f"[OK] Найдена ссылка: {clean_url}")
                
                # Редиректы через yandex
                elif 'ok.ru/' in href and any(x in href for x in ['/topic/', '/group/']):
                    try:
                        if 'url=' in href:
                            clean_url = href.split('url=')[1].split('&')[0]
                        else:
                            clean_url = href
                        
                        from urllib.parse import unquote
                        clean_url = unquote(clean_url)
                        
                        if 'ok.ru/' in clean_url:
                            clean_url = clean_url.split('?')[0]
                            if clean_url.startswith('http') and clean_url not in ok_links:
                                ok_links.add(clean_url)
                                logger.debug(f"[OK] Найдена ссылка (редирект): {clean_url}")
                    except Exception as e:
                        logger.debug(f"[OK] Ошибка парсинга ссылки: {e}")
            
            logger.info(f"[OK] Всего найдено ссылок: {len(ok_links)}")
            
            # Для каждой ссылки извлекаем метаданные из Яндекса
            for link in list(ok_links)[:10]:  # Ограничение 10 постов
                try:
                    # Извлекаем заголовок из результатов Яндекса
                    title = ''
                    description = ''
                    
                    # Ищем результат поиска содержащий эту ссылку
                    for li in soup.find_all('li', class_=lambda x: x and ('serp-item' in x or 'organic' in x)):
                        li_html = str(li)
                        if link in li_html or link.replace('https://', '') in li_html:
                            # Заголовок
                            h2 = li.find('h2')
                            if h2:
                                title = h2.get_text(strip=True)
                            
                            # Описание
                            text_div = li.find('div', class_=lambda x: x and ('text' in x or 'snippet' in x))
                            if text_div:
                                description = text_div.get_text(strip=True)
                            
                            if title:
                                break
                    
                    if not title:
                        continue
                    
                    full_text = f"{title}\n\n{description}"
                    
                    # Проверка релевантности
                    if not self._is_relevant(full_text):
                        continue
                    
                    post_id = abs(hash(link))
                    pub_datetime = datetime.now()
                    date_str = pub_datetime.strftime('%Y%m%d')
                    
                    posts.append({
                        'source': 'ok',
                        'source_id': f"ok_{post_id}_{date_str}",
                        'author': 'Одноклассники',
                        'author_id': 'ok',
                        'text': full_text[:500],
                        'url': link,
                        'published_date': pub_datetime,
                        'date': pub_datetime
                    })
                    
                    logger.info(f"[OK] ✓ {title[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[OK] Ошибка обработки ссылки {link}: {e}")
                    continue
            
            logger.info(f"[OK] Релевантных постов: {len(posts)}")
            
        except Exception as e:
            logger.error(f"[OK] Ошибка поиска: {e}")
            import traceback
            traceback.print_exc()
        
        return posts
    
    def collect(self):
        """Сбор постов"""
        all_posts = []
        
        logger.info(f"[OK] Начало сбора через Яндекс поиск")
        logger.info(f"[OK] Ключевые слова: {', '.join(self.keywords[:3])}")
        
        # Ищем по первым 2 ключевым словам
        for keyword in self.keywords[:2]:
            logger.info(f"\n[OK] Поиск по: {keyword}")
            posts = self.search_yandex(keyword)
            all_posts.extend(posts)
            delay = random.uniform(3, 5)
            time.sleep(delay)
        
        logger.info(f"\n[OK] Всего найдено релевантных постов: {len(all_posts)}")
        
        return all_posts


if __name__ == '__main__':
    print("="*70)
    print("СБОР ПОСТОВ ИЗ ОДНОКЛАССНИКОВ (ЧЕРЕЗ ЯНДЕКС)")
    print("="*70)
    
    collector = OKYandexCollector()
    
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
        print("  - Яндекс показывает капчу (требуется обход)")
        print("\nРекомендации:")
        print("  - Попробуйте позже")
        print("  - Используйте VPN или прокси")
