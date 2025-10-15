# 🔧 Руководство по внедрению системы комментариев

## ✅ Что уже сделано

### 1. **Модель базы данных** ✓
```python
# models.py
class Review(db.Model):
    parent_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True)
    is_comment = db.Column(db.Boolean, default=False)
    comments = db.relationship('Review', backref=db.backref('parent', remote_side=[id]))
```

### 2. **CommentHelper** ✓
Создан `utils/comment_helper.py` с методами:
- `save_post_with_comments()` - сохранение поста с комментариями
- `get_post_comments()` - получение комментариев
- `get_comment_stats()` - статистика комментариев
- `get_posts_without_comments()` - посты без комментариев

### 3. **Документация** ✓
- `COMMENTS_ANALYSIS.md` - полный анализ по платформам
- `test_comments.py` - тесты системы комментариев

---

## 🚀 Как использовать

### Пример 1: Telegram коллектор (ИСПРАВЛЕН)

```python
# collectors/telegram_user_collector.py

from utils.comment_helper import CommentHelper

async def get_channel_messages(self, channel_username, limit=200, collect_comments=False):
    """Получение сообщений из канала"""
    messages = []
    
    async for message in self.client.iter_messages(channel, limit=limit):
        # ... валидация ...
        
        msg_data = {
            'source_id': f"telegram_{channel.id}_{message.id}",
            'author': channel.title or channel_username,
            'text': text,
            'url': f"https://t.me/{channel_username.replace('@', '')}/{message.id}",
            'published_date': message.date,
            'source': 'telegram',
            # НЕ нужно is_comment - установится в CommentHelper
        }
        
        messages.append(msg_data)
        
        # Сбор ответов (комментариев)
        if collect_comments:
            replies = await self.get_message_replies(channel, message)
            
            # НЕ устанавливаем parent_id здесь!
            # Он будет установлен в CommentHelper после сохранения поста
            for reply in replies:
                reply['_parent_temp_id'] = msg_data['source_id']  # Временная метка
                messages.append(reply)
    
    return messages

def collect(self, collect_comments=False):
    """Сбор с правильным сохранением"""
    from utils.comment_helper import CommentHelper
    from analyzers.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    messages = asyncio.run(self.search_in_channels(collect_comments))
    
    # Группируем посты и комментарии
    posts_dict = {}  # {temp_id: post_data}
    comments_dict = {}  # {parent_temp_id: [comments]}
    
    for msg in messages:
        if '_parent_temp_id' in msg:
            # Это комментарий
            parent_temp_id = msg.pop('_parent_temp_id')
            if parent_temp_id not in comments_dict:
                comments_dict[parent_temp_id] = []
            comments_dict[parent_temp_id].append(msg)
        else:
            # Это пост
            posts_dict[msg['source_id']] = msg
    
    # Сохраняем посты с комментариями
    saved_count = 0
    for temp_id, post_data in posts_dict.items():
        comments = comments_dict.get(temp_id, [])
        
        saved_post, saved_comments = CommentHelper.save_post_with_comments(
            post_data, comments, analyzer
        )
        
        if saved_post:
            saved_count += 1
    
    logger.info(f"Сохранено постов: {saved_count}")
    return messages  # Возвращаем для совместимости
```

### Пример 2: VK коллектор (ДОБАВИТЬ КОММЕНТАРИИ)

```python
# collectors/vk_collector.py

from utils.comment_helper import CommentHelper

def collect(self, collect_comments=False):
    """Сбор постов и комментариев из VK"""
    from analyzers.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    all_posts = []
    
    # Поиск по ключевым словам
    for keyword in self.keywords:
        posts = self.search_posts(keyword, count=50)
        
        for post in posts:
            comments = []
            
            # Получаем комментарии если нужно
            if collect_comments:
                # Парсим owner_id и post_id из source_id
                # Формат: vk_post_<owner_id>_<post_id>
                parts = post['source_id'].split('_')
                if len(parts) >= 4:
                    owner_id = parts[2]
                    post_id = parts[3]
                    
                    # Получаем комментарии
                    comments = self.get_wall_comments(owner_id, post_id)
                    logger.info(f"Получено {len(comments)} комментариев для поста {post_id}")
            
            # Сохраняем пост с комментариями
            saved_post, saved_comments = CommentHelper.save_post_with_comments(
                post, comments, analyzer
            )
            
            if saved_post:
                all_posts.append(post)
        
        time.sleep(1)
    
    return all_posts
```

### Пример 3: OK.ru коллектор (ДОБАВИТЬ ПАРСИНГ КОММЕНТАРИЕВ)

```python
# collectors/ok_selenium_collector.py

from utils.comment_helper import CommentHelper

def get_post_comments(self, post_url):
    """Парсинг комментариев к посту OK.ru через Selenium"""
    if not self.driver:
        return []
    
    comments = []
    
    try:
        logger.info(f"[OK-COMMENTS] Парсинг комментариев: {post_url}")
        self.driver.get(post_url)
        time.sleep(3)
        
        # Клик "Показать комментарии"
        try:
            show_btn = self.driver.find_element(By.CLASS_NAME, 'comments-expand')
            show_btn.click()
            time.sleep(2)
        except:
            pass
        
        # Скролл для подгрузки комментариев
        for _ in range(3):  # Ограничиваем 3 скроллами
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Парсим комментарии (структура может меняться!)
        comment_elements = soup.find_all('div', class_='comments_lst')
        
        for elem in comment_elements[:30]:  # Ограничиваем 30 комментариями
            try:
                text_elem = elem.find('div', class_='comments_txt')
                author_elem = elem.find('a', class_='comments_ath')
                
                if not text_elem:
                    continue
                
                text = text_elem.get_text(strip=True)
                
                if not self._is_relevant(text):
                    continue
                
                author = author_elem.get_text(strip=True) if author_elem else 'OK User'
                
                comment = {
                    'source': 'ok',
                    'source_id': f"ok_comment_{hash(post_url)}_{hash(text)}",
                    'author': author,
                    'text': text,
                    'url': post_url,
                    'published_date': datetime.now()
                }
                
                comments.append(comment)
                
            except Exception as e:
                logger.debug(f"[OK-COMMENTS] Ошибка парсинга комментария: {e}")
                continue
        
        logger.info(f"[OK-COMMENTS] Собрано: {len(comments)} комментариев")
        
    except Exception as e:
        logger.error(f"[OK-COMMENTS] Ошибка: {e}")
    
    return comments

def collect(self, collect_comments=False):
    """Сбор с комментариями"""
    from utils.comment_helper import CommentHelper
    from analyzers.sentiment_analyzer import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    all_posts = []
    
    if not self._init_driver(headless=True):
        logger.error("[OK-SELENIUM] Не удалось запустить WebDriver")
        return all_posts
    
    try:
        for keyword in self.keywords[:3]:
            logger.info(f"[OK-SELENIUM] Поиск по: {keyword}")
            
            posts = self.search_ok(keyword, max_results=10)
            
            for post in posts:
                comments = []
                
                # Получаем комментарии если нужно
                if collect_comments:
                    try:
                        comments = self.get_post_comments(post['url'])
                        time.sleep(random.uniform(2, 4))  # Задержка между постами
                    except Exception as e:
                        logger.error(f"[OK-SELENIUM] Ошибка получения комментариев: {e}")
                
                # Сохраняем с комментариями
                saved_post, saved_comments = CommentHelper.save_post_with_comments(
                    post, comments, analyzer
                )
                
                if saved_post:
                    all_posts.append(post)
            
            time.sleep(random.uniform(3, 5))
        
    finally:
        self._close_driver()
    
    return all_posts
```

---

## 📊 API для фронтенда

Добавьте в `app_enhanced.py`:

```python
from utils.comment_helper import CommentHelper

@app.route('/api/post/<int:post_id>/comments')
def get_post_comments_api(post_id):
    """Получить комментарии к посту"""
    try:
        comments = CommentHelper.get_post_comments(post_id, limit=100)
        stats = CommentHelper.get_comment_stats(post_id)
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'comments': [c.to_dict() for c in comments],
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/with-comments')
def get_posts_with_comments_api():
    """Получить посты с комментариями"""
    source = request.args.get('source')
    limit = int(request.args.get('limit', 50))
    
    try:
        posts_data = CommentHelper.get_posts_with_comments(source, limit)
        
        result = []
        for item in posts_data:
            result.append({
                'post': item['post'].to_dict(),
                'comments': [c.to_dict() for c in item['comments']],
                'stats': item['stats']
            })
        
        return jsonify({
            'success': True,
            'posts': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/without-comments')
def get_posts_without_comments_api():
    """Посты без комментариев (для дополнительного парсинга)"""
    source = request.args.get('source')
    limit = int(request.args.get('limit', 100))
    
    try:
        posts = CommentHelper.get_posts_without_comments(source, limit)
        
        return jsonify({
            'success': True,
            'count': len(posts),
            'posts': [p.to_dict() for p in posts]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/comments')
def get_comments_stats_api():
    """Общая статистика комментариев"""
    try:
        total_comments = CommentHelper.get_all_comments_count()
        total_posts = Review.query.filter_by(is_comment=False).count()
        
        # Статистика по источникам
        sources_stats = db.session.query(
            Review.source,
            db.func.count(Review.id).label('count')
        ).filter_by(is_comment=True).group_by(Review.source).all()
        
        return jsonify({
            'success': True,
            'total_comments': total_comments,
            'total_posts': total_posts,
            'avg_comments_per_post': round(total_comments / total_posts, 2) if total_posts > 0 else 0,
            'by_source': {source: count for source, count in sources_stats}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## 🧪 Тестирование

### Быстрый тест (без RuSentiment):

```python
# test_comments_quick.py
from utils.comment_helper import CommentHelper
from datetime import datetime

# Создаем тестовые данные
post = {
    'source': 'test',
    'source_id': 'test_post_1',
    'author': 'Test User',
    'text': 'Test post',
    'url': 'https://test.com/1',
    'published_date': datetime.now()
}

comments = [
    {
        'source': 'test',
        'source_id': 'test_comment_1',
        'author': 'Commenter 1',
        'text': 'Great post!',
        'url': 'https://test.com/1#c1',
        'published_date': datetime.now()
    }
]

# Сохраняем
saved_post, saved_comments = CommentHelper.save_post_with_comments(post, comments)

print(f"Post ID: {saved_post.id}")
print(f"Comments saved: {len(saved_comments)}")

# Получаем обратно
retrieved = CommentHelper.get_post_comments(saved_post.id)
print(f"Comments retrieved: {len(retrieved)}")

# Статистика
stats = CommentHelper.get_comment_stats(saved_post.id)
print(f"Stats: {stats}")
```

Запуск:
```bash
python test_comments_quick.py
```

---

## 📋 Чек-лист внедрения

### Обязательно (1-2 часа):
- [x] ✅ Создан `utils/comment_helper.py`
- [ ] ⏳ Обновить Telegram коллектор
- [ ] ⏳ Обновить VK коллектор  
- [ ] ⏳ Добавить API endpoints
- [ ] ⏳ Протестировать на реальных данных

### Опционально (2-3 часа):
- [ ] ⏳ Добавить парсинг комментариев OK.ru
- [ ] ⏳ Обновить Дзен коллектор
- [ ] ⏳ Создать фронтенд для отображения комментариев
- [ ] ⏳ Добавить фильтры и поиск по комментариям

### Дополнительно (1-2 дня):
- [ ] ⏳ Асинхронный парсинг комментариев (Celery)
- [ ] ⏳ Кеширование (Redis)
- [ ] ⏳ Экспорт комментариев в Excel/CSV
- [ ] ⏳ Аналитика: тренды в комментариях
- [ ] ⏳ Уведомления о важных комментариях

---

## ⚠️ Важные замечания

### 1. Производительность
**Проблема:** Парсинг комментариев через Selenium медленный (3-5 сек на пост).

**Решение:**
- Парсить комментарии только для важных постов
- Использовать асинхронные задачи (Celery)
- Ограничить количество комментариев (первые 20-50)

```python
# Пример с Celery
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def parse_comments_async(post_id, post_url):
    """Асинхронный парсинг комментариев"""
    collector = OKSeleniumCollector()
    comments = collector.get_post_comments(post_url)
    
    # Сохраняем
    post = Review.query.get(post_id)
    for comment_data in comments:
        comment_data['parent_id'] = post_id
        comment_data['is_comment'] = True
        comment = Review(**comment_data)
        db.session.add(comment)
    
    db.session.commit()
```

### 2. Блокировки
**Проблема:** OK.ru и Дзен блокируют за частые запросы.

**Решение:**
- Использовать прокси-сервера
- Добавить случайные задержки (2-5 сек)
- Ротация User-Agent
- Ограничить количество запросов в день

```python
import random
time.sleep(random.uniform(2, 5))  # Случайная задержка
```

### 3. Хранение
**Проблема:** Комментарии занимают много места.

**Решение:**
- Архивировать старые комментарии (>30 дней)
- Удалять неинформативные комментарии (короткие, без ключевых слов)
- Использовать индексы для ускорения поиска

```sql
CREATE INDEX idx_reviews_parent_id ON reviews(parent_id);
CREATE INDEX idx_reviews_is_comment ON reviews(is_comment);
CREATE INDEX idx_reviews_published_date ON reviews(published_date);
```

---

## 🎯 Готовые команды

### Запуск сбора с комментариями:

```bash
# Telegram
python -c "from collectors.telegram_user_collector import TelegramUserCollector; c = TelegramUserCollector(); c.collect(collect_comments=True)"

# VK
python -c "from collectors.vk_collector import VKCollector; c = VKCollector(); c.collect(collect_comments=True)"

# OK.ru (после внедрения)
python -c "from collectors.ok_selenium_collector import OKSeleniumCollector; c = OKSeleniumCollector(); c.collect(collect_comments=True)"
```

### Проверка комментариев в БД:

```bash
# SQLite CLI
sqlite3 database.db "SELECT COUNT(*) FROM reviews WHERE is_comment=1"
sqlite3 database.db "SELECT parent_id, COUNT(*) FROM reviews WHERE is_comment=1 GROUP BY parent_id"
```

### Python:

```python
from models import Review, db
from utils.comment_helper import CommentHelper

# Статистика
total = CommentHelper.get_all_comments_count()
print(f"Всего комментариев: {total}")

# Посты с комментариями
posts = CommentHelper.get_posts_with_comments(limit=10)
for item in posts:
    print(f"Пост {item['post'].id}: {item['stats']['total']} комментариев")
```

---

## 📚 Дополнительные ресурсы

- `COMMENTS_ANALYSIS.md` - полный анализ парсинга по платформам
- `utils/comment_helper.py` - готовый helper
- `test_comments.py` - полные тесты системы
- `models.py` - модель БД с поддержкой комментариев

**Вопросы?** Проверьте документацию или создайте issue.
