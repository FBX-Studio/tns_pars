"""
Тест парсинга статьи с Дзен
"""
import requests
from bs4 import BeautifulSoup

url = 'https://dzen.ru/a/aEbEbU32L0xbz5Ga'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

print(f"Parsing: {url}")

try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.content)}")
    
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # Ищем заголовок
    title = soup.find('title')
    if title:
        print(f"Title: {title.text}")
    
    # Ищем h1
    h1 = soup.find('h1')
    if h1:
        print(f"H1: {h1.text}")
    
    # Ищем meta описание
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc:
        print(f"Description: {meta_desc.get('content', '')[:100]}")
    
    # Ищем meta og:title
    og_title = soup.find('meta', {'property': 'og:title'})
    if og_title:
        print(f"OG Title: {og_title.get('content', '')}")
    
    # Сохраним HTML для анализа
    with open('dzen_sample.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("\nHTML saved to dzen_sample.html")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
