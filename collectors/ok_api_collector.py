"""
Коллектор для OK.ru через официальный API
Документация: https://apiok.ru
"""
import requests
import hashlib
from datetime import datetime
from config import Config
import logging
import time

logger = logging.getLogger(__name__)

class OKAPICollector:
    """Коллектор постов из OK через официальный API"""
    
    def __init__(self):
        self.app_id = Config.get('OK_APP_ID', '')
        self.public_key = Config.get('OK_PUBLIC_KEY', '')
        self.secret_key = Config.get('OK_SECRET_KEY', '')
        self.access_token = Config.get('OK_ACCESS_TOKEN', '')
        self.keywords = Config.COMPANY_KEYWORDS
        
        self.api_url = 'https://api.ok.ru/fb.do'
        
        # ID групп для мониторинга (из Config или дефолтные)
        group_ids_str = Config.get('OK_GROUP_IDS', '')
        self.group_ids = [g.strip() for g in group_ids_str.split(',') if g.strip()]
        
        # Популярные новостные группы Нижнего Новгорода
        # Чтобы добавить группу:
        # 1. Найдите группу на ok.ru (например "НН.ру" или "Нижний Новгород новости")
        # 2. Откройте её страницу
        # 3. Скопируйте ID из URL: ok.ru/group/123456789
        # 4. Добавьте ID в OK_GROUP_IDS в .env файле
        self.default_nn_groups = [
            # Добавьте ID когда найдете группы
            # Пример: '53935793176806'  # НН.ру или другая новостная группа
        ]
        
        # Используем группы из конфига или дефолтные
        if not self.group_ids:
            self.group_ids = self.default_nn_groups
        
    def _generate_sig(self, params):
        """
        Генерация подписи для запроса OK API
        
        Алгоритм:
        1. Отсортировать параметры по алфавиту
        2. Склеить в строку: param1=value1param2=value2...
        3. Добавить secret_key в конец
        4. Вычислить MD5
        """
        # Сортируем параметры по ключу
        sorted_params = sorted(params.items())
        
        # Склеиваем в строку
        param_str = ''.join([f'{k}={v}' for k, v in sorted_params])
        
        # Добавляем секретный ключ
        sig_base = param_str + self.secret_key
        
        # MD5 хеш
        return hashlib.md5(sig_base.encode('utf-8')).hexdigest()
    
    def _is_relevant(self, text):
        """Проверка релевантности текста"""
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
    
    def _make_api_request(self, method, params=None):
        """Выполнение запроса к OK API"""
        if not self.access_token:
            logger.warning("[OK API] Access token не настроен")
            return None
        
        if params is None:
            params = {}
        
        # Обязательные параметры
        params['application_key'] = self.public_key
        params['method'] = method
        params['format'] = 'json'
        params['access_token'] = self.access_token
        
        # Генерируем подпись
        sig = self._generate_sig(params)
        params['sig'] = sig
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"[OK API] Ошибка {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[OK API] Ошибка запроса: {e}")
            return None
    
    def get_user_feed(self, count=50):
        """
        Получение ленты пользователя
        Метод: stream.get
        """
        logger.info("[OK API] Получение ленты пользователя")
        
        params = {
            'count': count,
            'patterns': 'POST'  # Только посты
        }
        
        result = self._make_api_request('stream.get', params)
        
        if result and 'entities' in result:
            return result['entities']
        
        return []
    
    def search_in_groups(self, group_ids):
        """
        Поиск в группах
        Метод: group.getInfo + stream для групп
        """
        posts = []
        
        for group_id in group_ids:
            logger.info(f"[OK API] Поиск в группе: {group_id}")
            
            params = {
                'uids': group_id,
                'fields': 'name,description'
            }
            
            result = self._make_api_request('group.getInfo', params)
            
            if result:
                # Получаем посты группы
                stream_params = {
                    'gid': group_id,
                    'count': 20,
                    'patterns': 'POST'
                }
                
                stream = self._make_api_request('stream.get', stream_params)
                
                if stream and 'entities' in stream:
                    posts.extend(stream['entities'])
            
            time.sleep(1)  # Задержка между запросами
        
        return posts
    
    def _parse_post(self, entity):
        """Парсинг поста из ответа API"""
        try:
            # Извлекаем текст
            text = entity.get('text', '')
            
            # Если нет текста, пропускаем
            if not text:
                return None
            
            # Проверка релевантности
            if not self._is_relevant(text):
                return None
            
            # Извлекаем метаданные
            entity_id = entity.get('id', '')
            author_name = entity.get('author_name', 'OK.ru')
            created_ms = entity.get('created_ms', 0)
            
            # Дата публикации
            if created_ms:
                pub_date = datetime.fromtimestamp(created_ms / 1000)
            else:
                pub_date = datetime.now()
            
            # URL поста
            url = f"https://ok.ru/feed/{entity_id}" if entity_id else ''
            
            return {
                'source': 'ok',
                'source_id': f"ok_{entity_id}_{pub_date.strftime('%Y%m%d')}",
                'author': author_name,
                'author_id': f"ok_{entity.get('author_id', '')}",
                'text': text[:500],
                'url': url,
                'published_date': pub_date,
                'date': pub_date
            }
            
        except Exception as e:
            logger.debug(f"[OK API] Ошибка парсинга поста: {e}")
            return None
    
    def collect(self):
        """Сбор постов из OK"""
        all_posts = []
        
        try:
            logger.info("[OK API] Запуск сбора из Одноклассников")
            
            # Проверка токена
            if not self.access_token:
                logger.error("[OK API] ❌ Access token не настроен!")
                logger.info("[OK API] См. инструкцию: OK_API_COMPLETE_GUIDE.md")
                return []
            
            if not self.secret_key:
                logger.error("[OK API] ❌ Secret key не настроен!")
                return []
            
            logger.info("[OK API] ✓ API ключи настроены")
            
            # ОГРАНИЧЕНИЕ OK API: Нет публичного поиска!
            # Доступно только:
            # 1. Личная лента (stream.get) - посты друзей
            # 2. Конкретные группы по ID
            
            # Получаем ленту пользователя
            logger.info("[OK API] Получение ленты пользователя...")
            entities = self.get_user_feed(count=100)
            
            logger.info(f"[OK API] Получено записей из ленты: {len(entities)}")
            
            # Парсим посты
            for entity in entities:
                post = self._parse_post(entity)
                if post:
                    all_posts.append(post)
                    logger.info(f"[OK API] ✓ {post['text'][:50]}...")
            
            # Получаем посты из групп (если указаны)
            if self.group_ids:
                logger.info(f"[OK API] Проверка {len(self.group_ids)} групп...")
                group_posts = self.search_in_groups(self.group_ids)
                
                for post_data in group_posts:
                    post = self._parse_post(post_data)
                    if post:
                        all_posts.append(post)
                        logger.info(f"[OK API] ✓ [Группа] {post['text'][:50]}...")
                
                logger.info(f"[OK API] Найдено в группах: {len(group_posts)}")
            else:
                logger.info("[OK API] ℹ️ Группы для мониторинга не указаны")
                logger.info("[OK API] Добавьте OK_GROUP_IDS в .env для поиска в группах")
            
            # Информация о результатах
            if len(entities) == 0 and not self.group_ids:
                logger.warning("[OK API] ⚠️ Лента пользователя пуста и группы не указаны")
                logger.info("[OK API] Рекомендации:")
                logger.info("[OK API] 1. Подпишитесь на новостные группы НН в OK")
                logger.info("[OK API] 2. Или добавьте ID групп в OK_GROUP_IDS (.env)")
            elif len(entities) == 0:
                logger.warning("[OK API] ⚠️ Лента пользователя пуста")
                logger.info("[OK API] Это нормально если у вас нет друзей или подписок")
            
            if len(all_posts) == 0 and len(entities) > 0:
                logger.info("[OK API] ℹ️ В ленте нет постов с ключевыми словами")
                logger.info(f"[OK API] Ключевые слова: {', '.join(self.keywords)}")
            
            logger.info(f"[OK API] Всего релевантных постов: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"[OK API] Ошибка сбора: {e}")
            import traceback
            traceback.print_exc()
        
        return all_posts
