import requests
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ProxyManager:
    """Менеджер для получения и проверки бесплатных прокси"""
    
    def __init__(self):
        self.proxies = []
        self.last_update = None
        self.update_interval = timedelta(hours=1)
        self.test_url = 'http://httpbin.org/ip'
        self.timeout = 5
        
    def fetch_free_proxies(self) -> List[Dict]:
        """Получить список бесплатных прокси из различных источников"""
        all_proxies = []
        
        # Source 1: Free Proxy List
        try:
            logger.info("Fetching proxies from Free Proxy List...")
            response = requests.get('https://www.proxy-list.download/api/v1/get?type=http', timeout=10)
            if response.ok:
                proxies = response.text.strip().split('\r\n')
                for proxy in proxies:
                    if proxy and ':' in proxy:
                        all_proxies.append({
                            'ip': proxy.split(':')[0],
                            'port': proxy.split(':')[1],
                            'protocol': 'http',
                            'source': 'proxy-list.download'
                        })
                logger.info(f"Got {len(proxies)} proxies from proxy-list.download")
        except Exception as e:
            logger.warning(f"Failed to fetch from proxy-list.download: {e}")
        
        # Source 2: ProxyScrape
        try:
            logger.info("Fetching proxies from ProxyScrape...")
            response = requests.get('https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all', timeout=10)
            if response.ok:
                proxies = response.text.strip().split('\r\n')
                for proxy in proxies:
                    if proxy and ':' in proxy:
                        all_proxies.append({
                            'ip': proxy.split(':')[0],
                            'port': proxy.split(':')[1],
                            'protocol': 'http',
                            'source': 'proxyscrape.com'
                        })
                logger.info(f"Got {len(proxies)} proxies from proxyscrape.com")
        except Exception as e:
            logger.warning(f"Failed to fetch from proxyscrape.com: {e}")
        
        # Source 3: GeoNode
        try:
            logger.info("Fetching proxies from GeoNode...")
            response = requests.get('https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc', timeout=10)
            if response.ok:
                data = response.json()
                if 'data' in data:
                    for item in data['data']:
                        all_proxies.append({
                            'ip': item['ip'],
                            'port': str(item['port']),
                            'protocol': item['protocols'][0] if item['protocols'] else 'http',
                            'source': 'geonode.com'
                        })
                logger.info(f"Got {len(data.get('data', []))} proxies from geonode.com")
        except Exception as e:
            logger.warning(f"Failed to fetch from geonode.com: {e}")
        
        # Source 4: Pubproxy
        try:
            logger.info("Fetching proxies from Pubproxy...")
            for _ in range(5):  # Get 5 proxies
                response = requests.get('http://pubproxy.com/api/proxy?format=txt&type=http', timeout=10)
                if response.ok:
                    proxy = response.text.strip()
                    if proxy and ':' in proxy:
                        all_proxies.append({
                            'ip': proxy.split(':')[0],
                            'port': proxy.split(':')[1],
                            'protocol': 'http',
                            'source': 'pubproxy.com'
                        })
                time.sleep(1)
            logger.info(f"Got proxies from pubproxy.com")
        except Exception as e:
            logger.warning(f"Failed to fetch from pubproxy.com: {e}")
        
        logger.info(f"Total proxies fetched: {len(all_proxies)}")
        return all_proxies
    
    def test_proxy(self, proxy: Dict) -> bool:
        """Проверить работоспособность прокси"""
        proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        try:
            response = requests.get(
                self.test_url, 
                proxies=proxies, 
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response.ok:
                logger.debug(f"Proxy {proxy_url} is working")
                return True
        except Exception as e:
            logger.debug(f"Proxy {proxy_url} failed: {e}")
        
        return False
    
    def update_proxies(self, max_working=10):
        """Обновить список рабочих прокси"""
        logger.info("Updating proxy list...")
        
        # Получаем свежие прокси
        free_proxies = self.fetch_free_proxies()
        
        if not free_proxies:
            logger.warning("No free proxies fetched")
            return
        
        # Перемешиваем для случайной проверки
        random.shuffle(free_proxies)
        
        # Проверяем прокси до достижения max_working рабочих
        working_proxies = []
        for proxy in free_proxies:
            if len(working_proxies) >= max_working:
                break
            
            logger.info(f"Testing proxy {proxy['ip']}:{proxy['port']}...")
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
                logger.info(f"Found working proxy: {proxy['ip']}:{proxy['port']} ({len(working_proxies)}/{max_working})")
            
            # Небольшая задержка между проверками
            time.sleep(0.5)
        
        self.proxies = working_proxies
        self.last_update = datetime.now()
        
        logger.info(f"Proxy list updated. Working proxies: {len(self.proxies)}")
        
        return len(self.proxies)
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Получить случайный рабочий прокси"""
        # Обновляем список если он пустой или устарел
        if not self.proxies or (self.last_update and datetime.now() - self.last_update > self.update_interval):
            self.update_proxies()
        
        if not self.proxies:
            logger.warning("No working proxies available")
            return None
        
        proxy = random.choice(self.proxies)
        return {
            'http': f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}",
            'https': f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
        }
    
    def get_all_proxies(self) -> List[Dict]:
        """Получить все рабочие прокси"""
        if not self.proxies or (self.last_update and datetime.now() - self.last_update > self.update_interval):
            self.update_proxies()
        
        return [
            {
                'http': f"{p['protocol']}://{p['ip']}:{p['port']}",
                'https': f"{p['protocol']}://{p['ip']}:{p['port']}"
            }
            for p in self.proxies
        ]
    
    def remove_proxy(self, proxy_dict: Dict):
        """Удалить нерабочий прокси из списка"""
        proxy_url = proxy_dict.get('http', '').replace('http://', '').replace('https://', '')
        if not proxy_url:
            return
        
        self.proxies = [p for p in self.proxies if f"{p['ip']}:{p['port']}" != proxy_url]
        logger.info(f"Removed non-working proxy: {proxy_url}")
