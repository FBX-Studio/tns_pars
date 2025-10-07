"""
Отладка Google поиска для Дзен
"""
import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Пробуем разные варианты поиска
queries = [
    'dzen.ru ТНС энерго НН',
    'site:dzen.ru ТНС энерго',
    'dzen.ru энергетика Нижний Новгород',
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Поиск: {query}")
    print('='*60)
    
    url = f'https://www.google.com/search?q={requests.utils.quote(query)}&num=20'
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"Status: {r.status_code}")
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Ищем все ссылки
        dzen_count = 0
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'dzen.ru' in href:
                dzen_count += 1
                print(f"\nНайдена ссылка: {href[:150]}...")
                
                # Пробуем извлечь чистый URL
                if '/url?q=' in href:
                    try:
                        clean_url = href.split('/url?q=')[1].split('&')[0]
                        print(f"  Чистый URL: {clean_url}")
                        
                        if '/a/' in clean_url:
                            print(f"  ✓ Это статья!")
                    except:
                        pass
        
        print(f"\nВсего ссылок с dzen.ru: {dzen_count}")
        
        # Сохраним HTML для анализа
        if dzen_count == 0:
            filename = f'google_search_{queries.index(query)}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(r.text)
            print(f"HTML сохранен в {filename}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("Проверяем прямую ссылку на статью из примера:")
print("="*60)

article_url = 'https://dzen.ru/a/aEbEbU32L0xbz5Ga'
print(f"\nURL: {article_url}")

try:
    r = requests.get(article_url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.content)}")
    
    if 'sso.dzen.ru' in r.text:
        print("⚠ Требуется авторизация (редирект на SSO)")
    
    # Попробуем через API Дзена (если есть)
    api_url = f'https://dzen.ru/api/v3/launcher/more?country_code=ru'
    print(f"\nПробуем API: {api_url}")
    r2 = requests.get(api_url, headers=headers, timeout=10)
    print(f"API Status: {r2.status_code}")
    
except Exception as e:
    print(f"Ошибка: {e}")
