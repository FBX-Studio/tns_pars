"""
Тест парсинга новостей с работающими RSS-фидами
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_rss_feeds():
    """Тест доступных RSS фидов"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    # Рабочие RSS фиды и альтернативы
    feeds = [
        # Google News - всегда работает
        'https://news.google.com/rss/search?q=%D0%A2%D0%9D%D0%A1+%D1%8D%D0%BD%D0%B5%D1%80%D0%B3%D0%BE+%D0%9D%D0%B8%D0%B6%D0%BD%D0%B8%D0%B9+%D0%9D%D0%BE%D0%B2%D0%B3%D0%BE%D1%80%D0%BE%D0%B4&hl=ru&gl=RU&ceid=RU:ru',
        # Yandex News
        'https://news.yandex.ru/yandsearch?text=%D0%A2%D0%9D%D0%A1+%D1%8D%D0%BD%D0%B5%D1%80%D0%B3%D0%BE+%D0%9D%D0%B8%D0%B6%D0%BD%D0%B8%D0%B9+%D0%9D%D0%BE%D0%B2%D0%B3%D0%BE%D1%80%D0%BE%D0%B4&rpt=nnews2&grhow=clutop',
        # NewsNN
        'https://newsnn.ru/rss/',
        # В городе Н
        'https://www.vgoroden.ru/rss',
        # Время N
        'https://www.vremyan.ru/rss/news.xml',
    ]
    
    articles = []
    
    for feed_url in feeds:
        try:
            print(f"\n[INFO] Пробуем RSS feed: {feed_url[:50]}...")
            
            # Пробуем без SSL проверки
            response = requests.get(
                feed_url, 
                headers=headers, 
                timeout=10,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                print(f"[ERROR] Статус код {response.status_code}")
                continue
            
            # Парсинг XML
            soup = BeautifulSoup(response.content, 'xml')
            if not soup.find_all('item'):
                # Пробуем как HTML
                soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.find_all('item')[:5]  # Берем первые 5
            
            for item in items:
                title_tag = item.find('title')
                desc_tag = item.find('description')
                link_tag = item.find('link')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    link = link_tag.get_text(strip=True) if link_tag else ''
                    
                    # Проверяем релевантность
                    full_text = f"{title} {description}".lower()
                    
                    keywords = ['тнс', 'энерго', 'энергосбыт', 'электро', 'свет', 'нижний новгород', 'нижегородск']
                    if any(kw in full_text for kw in keywords):
                        articles.append({
                            'title': title[:100],
                            'description': description[:200],
                            'link': link,
                            'source': feed_url[:30]
                        })
                        print(f"[FOUND] Релевантная новость: {title[:50]}...")
            
            if items:
                print(f"[SUCCESS] Найдено {len(items)} новостей из {feed_url[:30]}...")
            else:
                print(f"[WARNING] Нет новостей в фиде")
                
        except Exception as e:
            print(f"[ERROR] Ошибка для {feed_url[:30]}: {str(e)[:50]}")
    
    return articles

def test_web_scraping():
    """Тест прямого парсинга сайтов"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    sites = [
        {
            'url': 'https://newsnn.ru/search?q=ТНС+энерго',
            'name': 'NewsNN'
        },
        {
            'url': 'https://www.vgoroden.ru/search?q=ТНС+энерго',
            'name': 'В городе Н'
        }
    ]
    
    articles = []
    
    for site in sites:
        try:
            print(f"\n[INFO] Парсинг {site['name']}...")
            
            response = requests.get(
                site['url'],
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ищем статьи по распространенным паттернам
                article_selectors = [
                    {'class': 'article'},
                    {'class': 'news-item'},
                    {'class': 'post'},
                    {'class': 'entry'},
                    {'class': 'item'},
                ]
                
                for selector in article_selectors:
                    items = soup.find_all(['div', 'article', 'li'], selector)
                    if items:
                        print(f"[SUCCESS] Найдено {len(items)} элементов с селектором {selector}")
                        break
                
            else:
                print(f"[ERROR] Статус {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] {site['name']}: {str(e)[:50]}")
    
    return articles

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ СБОРА НОВОСТЕЙ")
    print("=" * 60)
    
    # Тест RSS
    print("\n1. Тестируем RSS фиды...")
    rss_articles = test_rss_feeds()
    
    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТЫ RSS: Найдено {len(rss_articles)} релевантных новостей")
    
    if rss_articles:
        print("\nПервые 3 новости:")
        for i, article in enumerate(rss_articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Источник: {article['source']}")
            print(f"   Ссылка: {article['link'][:50]}...")
    
    # Тест веб-скрапинга
    print("\n" + "=" * 60)
    print("2. Тестируем прямой парсинг сайтов...")
    web_articles = test_web_scraping()
    
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f"- RSS: {len(rss_articles)} новостей")
    print(f"- Web: {len(web_articles)} новостей")
    
    if not rss_articles and not web_articles:
        print("\n⚠️ ПРОБЛЕМА: Не удалось собрать новости!")
        print("Возможные причины:")
        print("1. Блокировка сайтов")
        print("2. Изменение структуры сайтов") 
        print("3. Проблемы с сетью")
        print("\nРЕКОМЕНДАЦИИ:")
        print("1. Использовать VPN или прокси")
        print("2. Использовать Selenium для динамических сайтов")
        print("3. Добавить больше источников RSS")
