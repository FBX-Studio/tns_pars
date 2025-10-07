"""
Тест Яндекс поиска
"""
import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = 'dzen.ru ТНС энерго'
url = f'https://yandex.ru/search/?text={requests.utils.quote(query)}&lr=47'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print(f"Поиск: {query}")
print(f"URL: {url}\n")

r = requests.get(url, headers=headers, timeout=20)
print(f"Status: {r.status_code}")
print(f"Content length: {len(r.content)}")

soup = BeautifulSoup(r.content, 'html.parser')

print(f"\n'dzen.ru' в HTML: {'dzen.ru' in r.text}")
print(f"'dzen.ru/a/' в HTML: {'dzen.ru/a/' in r.text}")

# Ищем все ссылки с dzen.ru
links = [a['href'] for a in soup.find_all('a', href=True) if 'dzen.ru' in a['href']]
print(f"\nНайдено ссылок с dzen.ru: {len(links)}")

for i, link in enumerate(links[:10], 1):
    print(f"{i}. {link[:150]}")

# Сохраним HTML
with open('yandex_search.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
print(f"\nHTML сохранен в yandex_search.html")

# Проверим есть ли прямые ссылки на статьи
print("\nПроверка прямых ссылок на статьи (https://dzen.ru/a/):")
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith('https://dzen.ru/a/') or href.startswith('http://dzen.ru/a/'):
        print(f"  Найдена: {href}")
