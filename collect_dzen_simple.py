"""
Простой сборщик новостей из Яндекс.Дзен
Работает с RSS каналов напрямую
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDzenCollector:
    """Простой коллектор для Дзен через RSS"""
    
    def __init__(self):
        self.channels = Config.DZEN_CHANNELS
        self.keywords = Config.COMPANY_KEYWORDS
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
    
    def collect_from_channel(self, channel_url):
        """Сбор из одного канала"""
        articles = []
        
        try:
            # Формируем RSS URL
            if 'dzen.ru/id/' in channel_url:
                channel_id = channel_url.split('id/')[-1].strip()
            elif 'dzen.ru/' in channel_url and '/id/' not in channel_url:
                channel_id = channel_url.split('dzen.ru/')[-1].strip()
            else:
                channel_id = channel_url.strip()
            
            rss_url = f'https://dzen.ru/id/{channel_id}/rss'
            
            logger.info(f"[DZEN] Запрос к каналу: {channel_id}")
            logger.info(f"[DZEN] RSS URL: {rss_url}")
            
            response = requests.get(rss_url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"[DZEN] Ошибка {response.status_code} для канала {channel_id}")
                return []
            
            # Парсим RSS через BeautifulSoup
            soup = BeautifulSoup(response.content, 'xml')
            
            items = soup.find_all('item')
            logger.info(f"[DZEN] Найдено статей: {len(items)}")
            
            for item in items:
                try:
                    title = item.find('title')
                    title_text = title.text if title else ''
                    
                    description = item.find('description')
                    desc_text = description.text if description else ''
                    
                    link = item.find('link')
                    url = link.text if link else ''
                    
                    pub_date = item.find('pubDate')
                    date_text = pub_date.text if pub_date else ''
                    
                    full_text = f"{title_text}\n\n{desc_text}"
                    
                    # Проверка релевантности
                    if not self._is_relevant(full_text):
                        continue
                    
                    # Парсим дату
                    try:
                        pub_datetime = datetime.strptime(date_text, '%a, %d %b %Y %H:%M:%S %z')
                    except:
                        pub_datetime = datetime.now()
                    
                    article_id = url.split('/a/')[-1] if '/a/' in url else abs(hash(url))
                    date_str = pub_datetime.strftime('%Y%m%d')
                    
                    articles.append({
                        'source': 'zen',
                        'source_id': f"dzen_{article_id}_{date_str}",
                        'author': f'Дзен: {channel_id}',
                        'author_id': f'dzen_{channel_id}',
                        'text': full_text[:500],
                        'url': url,
                        'published_date': pub_datetime,
                        'date': pub_datetime
                    })
                    
                    logger.info(f"[DZEN] ✓ {title_text[:60]}...")
                    
                except Exception as e:
                    logger.debug(f"[DZEN] Ошибка парсинга статьи: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"[DZEN] Ошибка канала {channel_url}: {e}")
        
        return articles
    
    def collect(self):
        """Сбор со всех каналов"""
        all_articles = []
        
        logger.info(f"[DZEN] Начало сбора из {len(self.channels)} каналов")
        logger.info(f"[DZEN] Ключевые слова: {', '.join(self.keywords)}")
        
        for channel in self.channels:
            channel = channel.strip()
            if not channel:
                continue
            
            articles = self.collect_from_channel(channel)
            all_articles.extend(articles)
        
        logger.info(f"[DZEN] Всего релевантных статей: {len(all_articles)}")
        
        return all_articles


if __name__ == '__main__':
    print("="*70)
    print("СБОР НОВОСТЕЙ ИЗ ЯНДЕКС.ДЗЕН")
    print("="*70)
    
    collector = SimpleDzenCollector()
    
    if not collector.channels:
        print("\n⚠ ВНИМАНИЕ: Список каналов пуст!")
        print("\nДобавьте каналы в .env файл:")
        print("  DZEN_CHANNELS=id1,id2,id3")
        sys.exit(1)
    
    print(f"\nКаналы ({len(collector.channels)}):")
    for i, ch in enumerate(collector.channels, 1):
        if ch.strip():
            print(f"  {i}. {ch.strip()}")
    
    print("\n" + "-"*70)
    
    articles = collector.collect()
    
    print("\n" + "="*70)
    print(f"Найдено релевантных статей: {len(articles)}")
    print("="*70)
    
    if articles:
        print("\nПримеры статей:\n")
        for i, art in enumerate(articles[:5], 1):
            print(f"{i}. {art['text'][:100]}...")
            print(f"   URL: {art['url']}")
            print()
