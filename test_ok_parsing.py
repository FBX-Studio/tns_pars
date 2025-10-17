"""
Тестовый скрипт для отладки парсинга OK.ru
"""
import requests
from bs4 import BeautifulSoup
import time

# Заголовки браузера
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

print("=" * 80)
print("ТЕСТ ПАРСИНГА OK.RU")
print("=" * 80)

# Тест 1: Прямой поиск на OK
print("\n[ТЕСТ 1] Прямой поиск на OK.ru")
print("-" * 80)
search_url = 'https://ok.ru/search?st.query=ТНС энерго НН&st.mode=GlobalSearch'
print(f"URL: {search_url}")

try:
    response = requests.get(search_url, headers=headers, timeout=15, allow_redirects=True)
    print(f"Статус: {response.status_code}")
    print(f"Финальный URL: {response.url}")
    print(f"Размер ответа: {len(response.content)} байт")
    
    # Проверка на редиректы
    if len(response.history) > 0:
        print(f"Редиректы: {len(response.history)}")
        for r in response.history:
            print(f"  -> {r.status_code}: {r.url}")
    
    # Проверка на капчу
    html = response.text
    if len(html) == 0:
        print("!!! OK.ru ВЕРНУЛ ПУСТОЙ ОТВЕТ - ПОЛНАЯ БЛОКИРОВКА !!!")
    elif 'captcha' in html.lower():
        print("!!! ОБНАРУЖЕНА КАПЧА !!!")
    elif 'robot' in html.lower() or 'проверка' in html.lower():
        print("!!! ОБНАРУЖЕНА ПРОВЕРКА НА РОБОТА !!!")
    else:
        print("OK: Капчи не обнаружено")
    
    # Сохраняем HTML для анализа
    with open('ok_search_response.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ HTML сохранен в ok_search_response.html")
    
    # Ищем ссылки
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/topic/' in href or 'st.topicId' in href:
            if href.startswith('/'):
                href = f"https://ok.ru{href}"
            if href not in links:
                links.append(href)
    
    print(f"Найдено ссылок на топики: {len(links)}")
    if links:
        print("Примеры ссылок:")
        for link in links[:5]:
            print(f"  - {link}")
    
except Exception as e:
    print(f"ОШИБКА: {e}")

# Тест 2: Группа Нижнего Новгорода
print("\n[ТЕСТ 2] Парсинг группы Нижнего Новгорода")
print("-" * 80)
group_url = 'https://ok.ru/nizhnynovgorod'
print(f"URL: {group_url}")

try:
    time.sleep(2)
    response = requests.get(group_url, headers=headers, timeout=15, allow_redirects=True)
    print(f"Статус: {response.status_code}")
    print(f"Финальный URL: {response.url}")
    print(f"Размер ответа: {len(response.content)} байт")
    
    html = response.text
    
    # Проверки
    if 'captcha' in html.lower():
        print("!!! ОБНАРУЖЕНА КАПЧА !!!")
    elif 'login' in response.url or 'st.layer.cmd=PopLayerLogin' in html:
        print("!!! ТРЕБУЕТСЯ АВТОРИЗАЦИЯ !!!")
    else:
        print("OK: Доступ получен")
    
    # Сохраняем
    with open('ok_group_response.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("OK: HTML сохранен в ok_group_response.html")
    
    # Ищем топики
    soup = BeautifulSoup(html, 'html.parser')
    topics = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/topic/' in href:
            if href.startswith('/'):
                href = f"https://ok.ru{href}"
            if href not in topics:
                topics.append(href)
    
    print(f"Найдено топиков: {len(topics)}")
    if topics:
        print("Примеры топиков:")
        for topic in topics[:5]:
            print(f"  - {topic}")

except Exception as e:
    print(f"ОШИБКА: {e}")

# Тест 3: Мобильная версия
print("\n[ТЕСТ 3] Мобильная версия m.ok.ru")
print("-" * 80)
mobile_url = 'https://m.ok.ru/search?st.query=ТНС энерго'
print(f"URL: {mobile_url}")

# Мобильные заголовки
mobile_headers = headers.copy()
mobile_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'

try:
    time.sleep(2)
    response = requests.get(mobile_url, headers=mobile_headers, timeout=15, allow_redirects=True)
    print(f"Статус: {response.status_code}")
    print(f"Финальный URL: {response.url}")
    print(f"Размер ответа: {len(response.content)} байт")
    
    html = response.text
    
    if 'captcha' in html.lower():
        print("!!! ОБНАРУЖЕНА КАПЧА !!!")
    else:
        print("OK: Капчи нет")
    
    # Сохраняем
    with open('ok_mobile_response.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("OK: HTML сохранен в ok_mobile_response.html")
    
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'topic' in href.lower():
            links.append(href)
    
    print(f"Найдено ссылок с 'topic': {len(links)}")
    
except Exception as e:
    print(f"ОШИБКА: {e}")

print("\n" + "=" * 80)
print("ИТОГИ:")
print("=" * 80)
print("1. Проверьте файлы ok_search_response.html, ok_group_response.html, ok_mobile_response.html")
print("2. Откройте их в браузере и посмотрите что именно возвращает OK.ru")
print("3. Если видите капчу - нужен прокси/VPN")
print("4. Если требуется авторизация - нужен API или selenium с авторизацией")
print("=" * 80)
