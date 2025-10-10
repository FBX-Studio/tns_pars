"""
Менеджер бесплатных прокси для обхода блокировок
"""
import requests
import random
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class ProxyManager:
    """Управление бесплатными прокси для парсинга"""
    
    def __init__(self):
        self.proxies = []
        self.current_index = 0
        
        # Источники бесплатных прокси
        self.proxy_sources = [
            'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        ]
        
    def fetch_proxies(self) -> List[str]:
        """Получить список бесплатных прокси"""
        all_proxies = []
        
        logger.info("[PROXY] Загрузка бесплатных прокси...")
        
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    proxies = [p.strip() for p in proxies if p.strip() and ':' in p]
                    all_proxies.extend(proxies)
                    logger.info(f"[PROXY] Загружено {len(proxies)} из {source[:50]}...")
            except Exception as e:
                logger.debug(f"[PROXY] Ошибка загрузки из {source}: {e}")
                
        # Убираем дубликаты
        all_proxies = list(set(all_proxies))
        
        logger.info(f"[PROXY] Всего уникальных прокси: {len(all_proxies)}")
        
        return all_proxies
    
    def test_proxy(self, proxy: str, timeout: int = 5) -> bool:
        """Проверить работоспособность прокси"""
        proxy_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def get_working_proxies(self, count: int = 10, test: bool = True) -> List[str]:
        """Получить список работающих прокси"""
        if not self.proxies:
            self.proxies = self.fetch_proxies()
        
        if not test:
            # Вернуть случайные без проверки
            return random.sample(self.proxies, min(count, len(self.proxies)))
        
        # Проверить и вернуть рабочие
        working = []
        logger.info(f"[PROXY] Проверка прокси (нужно {count} рабочих)...")
        
        tested = 0
        for proxy in random.sample(self.proxies, min(len(self.proxies), count * 3)):
            tested += 1
            if tested % 10 == 0:
                logger.info(f"[PROXY] Проверено {tested}, найдено рабочих: {len(working)}")
                
            if self.test_proxy(proxy):
                working.append(proxy)
                logger.info(f"[PROXY] ✓ Рабочий: {proxy}")
                
                if len(working) >= count:
                    break
        
        logger.info(f"[PROXY] Найдено {len(working)} рабочих прокси из {tested} проверенных")
        
        return working
    
    def get_next_proxy(self) -> Optional[dict]:
        """Получить следующий прокси для использования (ротация)"""
        if not self.proxies:
            self.proxies = self.get_working_proxies(count=5, test=False)
        
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def get_random_proxy(self) -> Optional[dict]:
        """Получить случайный прокси"""
        if not self.proxies:
            self.proxies = self.get_working_proxies(count=5, test=False)
        
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def remove_proxy(self, proxy: dict) -> None:
        """Удалить нерабочий прокси из списка"""
        if not proxy:
            return
        
        # Извлекаем адрес прокси из словаря
        proxy_addr = None
        if isinstance(proxy, dict):
            if 'http' in proxy:
                proxy_addr = proxy['http'].replace('http://', '').replace('https://', '')
            elif 'https' in proxy:
                proxy_addr = proxy['https'].replace('http://', '').replace('https://', '')
        
        if proxy_addr and proxy_addr in self.proxies:
            self.proxies.remove(proxy_addr)
            logger.debug(f"[PROXY] Removed non-working proxy: {proxy_addr}")


# Глобальный менеджер прокси
_proxy_manager = None

def get_proxy_manager() -> ProxyManager:
    """Получить глобальный экземпляр менеджера прокси"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
