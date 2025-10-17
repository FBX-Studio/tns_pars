# 📊 Анализ парсинга комментариев по платформам

## 🔍 Текущее состояние

### ✅ База данных
**Модель поддерживает комментарии:**
```python
class Review(db.Model):
    parent_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True)
    is_comment = db.Column(db.Boolean, default=False)
    comments = db.relationship('Review', backref=db.backref('parent', remote_side=[id]))
```

**Проблема:** Коллекторы используют `parent_source_id` (строка), а БД ожидает `parent_id` (integer).

---

## 📋 Статус по платформам

### 1. ✅ Telegram (telegram_user_collector.py)
**Статус:** РАБОТАЕТ ЧАСТИЧНО

**Что работает:**
- Получение ответов на сообщения (replies)
- Пометка `is_comment = True`
- Сохранение `parent_source_id` и `parent_url`

**Проблемы:**
```python
# Текущий код (неправильно)
reply['parent_source_id'] = msg_data['source_id']  # Строка, не ID!
reply['is_comment'] = True
```

**Что нужно исправить:**
- Сначала сохранить родительский пост в БД
- Получить его `id`
- Присвоить `parent_id = post.id`

**Ограничения API:**
- ✅ Полный доступ к комментариям через Telethon
- ✅ Нет лимитов на публичных каналах
- ⚠️ Приватные каналы требуют подписки

---

### 2. ⚠️ VK (vk_collector.py)
**Статус:** МЕТОД ЕСТЬ, НО НЕ ИСПОЛЬЗУЕТСЯ

**Что работает:**
```python
def get_wall_comments(self, owner_id, post_id, count=100):
    # Получает комментарии из VK API
```

**Проблемы:**
1. Метод существует, но нигде не вызывается
2. Не привязывается к родительскому посту
3. Отсутствует флаг `is_comment`

**Что нужно исправить:**
```python
# В методе collect() добавить:
for post in posts:
    # Сохраняем пост
    saved_post = save_to_db(post)
    
    # Получаем комментарии
    if collect_comments:
        comments = self.get_wall_comments(owner_id, post_id)
        for comment in comments:
            comment['parent_id'] = saved_post.id
            comment['is_comment'] = True
            save_to_db(comment)
```

**Ограничения API:**
- ✅ VK API предоставляет доступ к комментариям
- ✅ Метод `wall.getComments` работает
- ⚠️ Лимит: 100 комментариев за запрос
- ⚠️ Требуется access token
- ❌ Закрытые группы недоступны без членства

**Как получить больше комментариев:**
```python
def get_all_comments(self, owner_id, post_id):
    all_comments = []
    offset = 0
    count = 100
    
    while True:
        response = self.vk.wall.getComments(
            owner_id=owner_id,
            post_id=post_id,
            count=count,
            offset=offset
        )
        
        comments = response['items']
        if not comments:
            break
        
        all_comments.extend(comments)
        offset += count
        
        if len(comments) < count:
            break
        
        time.sleep(0.5)  # Избегаем лимитов API
    
    return all_comments
```

---

### 3. ❌ OK.ru (ok_collector.py, ok_selenium_collector.py)
**Статус:** КОММЕНТАРИИ НЕ ПАРСЯТСЯ

**Проблема:**
- В `ok_collector.py` - нет методов для комментариев
- В `ok_selenium_collector.py` - только посты, комментарии не собираются

**Почему сложно:**
1. **Нет официального API** для OK.ru
2. **Selenium** - единственный способ
3. **Динамическая подгрузка** комментариев через JS
4. **Защита от ботов** - капчи, блокировки

**Как добавить:**

```python
def get_post_comments(self, post_url):
    """Парсинг комментариев к посту в OK.ru"""
    if not self.driver:
        return []
    
    comments = []
    
    try:
        self.driver.get(post_url)
        time.sleep(3)
        
        # Кликаем "Показать комментарии"
        try:
            show_comments_btn = self.driver.find_element(By.CLASS_NAME, 'comments-expand')
            show_comments_btn.click()
            time.sleep(2)
        except:
            pass
        
        # Скроллим для подгрузки всех комментариев
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 5
        
        while scroll_attempts < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            scroll_attempts += 1
        
        # Парсим комментарии
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        comment_elements = soup.find_all('div', class_='comments_lst')
        
        for elem in comment_elements:
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
                    'source_id': f"ok_comment_{hash(text)}_{hash(author)}",
                    'author': author,
                    'text': text,
                    'url': post_url,
                    'published_date': datetime.now(),
                    'is_comment': True
                }
                
                comments.append(comment)
                
            except Exception as e:
                logger.debug(f"[OK] Ошибка парсинга комментария: {e}")
                continue
        
        logger.info(f"[OK] Собрано комментариев: {len(comments)}")
        
    except Exception as e:
        logger.error(f"[OK] Ошибка получения комментариев: {e}")
    
    return comments
```

**Ограничения:**
- ❌ Нет официального API
- ⚠️ Selenium медленный (3-5 сек на пост)
- ⚠️ Риск блокировки IP
- ⚠️ Капчи при большом количестве запросов
- ⚠️ Требуется авторизация для некоторых постов

**Рекомендации:**
1. Использовать прокси-сервера
2. Случайные задержки между запросами
3. Ротация User-Agent
4. Ограничить количество комментариев (первые 20-30)
5. Парсить комментарии только для важных постов

---

### 4. ✅ Яндекс.Дзен (zen_collector.py, zen_selenium_collector.py)
**Статус:** РАБОТАЕТ ЧАСТИЧНО

**Что работает:**
```python
def parse_dzen_comments(self, article_url):
    # Парсит комментарии через Selenium
```

**Проблемы:**
1. Используется `parent_url` вместо `parent_id`
2. Комментарии не всегда привязаны к статьям

**Что нужно исправить:**
```python
# После сохранения статьи
saved_article = save_to_db(article)

# Получаем комментарии
if collect_comments:
    comments = self.parse_dzen_comments(article['url'])
    for comment in comments:
        comment['parent_id'] = saved_article.id
        comment['is_comment'] = True
        save_to_db(comment)
```

**Ограничения API:**
- ❌ Нет официального API
- ✅ Selenium работает хорошо
- ⚠️ Яндекс может показывать капчи
- ⚠️ Комментарии подгружаются динамически (требуется скролл)

---

### 5. ⚠️ Новостные сайты (news_collector.py)
**Статус:** РАБОТАЕТ ЧАСТИЧНО

**Что работает:**
```python
def parse_article_comments(self, article_url):
    # Парсит комментарии с новостных сайтов
```

**Проблемы:**
- Каждый сайт имеет свою структуру
- Комментарии могут быть в iframe
- Часто используются сторонние системы (Disqus, VK Comments)

**Ограничения:**
- ✅ HTML парсинг работает
- ⚠️ Разная структура на каждом сайте
- ❌ Disqus требует API ключ
- ❌ VK Comments требует VK API

---

## 🔧 План исправлений

### Шаг 1: Создать helper для сохранения с комментариями

```python
# utils/comment_helper.py

from models import Review, db
import logging

logger = logging.getLogger(__name__)

class CommentHelper:
    """Помощник для работы с комментариями"""
    
    @staticmethod
    def save_post_with_comments(post_data, comments_data, analyzer=None):
        """
        Сохраняет пост и его комментарии с правильными связями
        
        Args:
            post_data: Данные поста
            comments_data: Список комментариев
            analyzer: Анализатор тональности (опционально)
        
        Returns:
            (saved_post, saved_comments) - кортеж сохраненных объектов
        """
        try:
            # 1. Сохраняем основной пост
            post_data['is_comment'] = False
            
            # Анализ тональности поста
            if analyzer and 'sentiment_score' not in post_data:
                sentiment = analyzer.analyze(post_data['text'])
                post_data['sentiment_score'] = sentiment['sentiment_score']
                post_data['sentiment_label'] = sentiment['sentiment_label']
            
            # Проверяем дубликаты
            existing_post = Review.query.filter_by(
                source_id=post_data['source_id']
            ).first()
            
            if existing_post:
                logger.debug(f"Post already exists: {post_data['source_id']}")
                saved_post = existing_post
            else:
                saved_post = Review(**post_data)
                db.session.add(saved_post)
                db.session.flush()  # Получаем ID не коммитя
                logger.info(f"Saved post: {saved_post.id}")
            
            # 2. Сохраняем комментарии
            saved_comments = []
            
            for comment_data in comments_data:
                comment_data['is_comment'] = True
                comment_data['parent_id'] = saved_post.id
                
                # Анализ тональности комментария
                if analyzer and 'sentiment_score' not in comment_data:
                    sentiment = analyzer.analyze(comment_data['text'])
                    comment_data['sentiment_score'] = sentiment['sentiment_score']
                    comment_data['sentiment_label'] = sentiment['sentiment_label']
                
                # Проверяем дубликаты
                existing_comment = Review.query.filter_by(
                    source_id=comment_data['source_id']
                ).first()
                
                if existing_comment:
                    logger.debug(f"Comment already exists: {comment_data['source_id']}")
                    continue
                
                saved_comment = Review(**comment_data)
                db.session.add(saved_comment)
                saved_comments.append(saved_comment)
            
            db.session.commit()
            logger.info(f"Saved {len(saved_comments)} comments for post {saved_post.id}")
            
            return saved_post, saved_comments
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving post with comments: {e}")
            return None, []
    
    @staticmethod
    def get_post_comments(post_id, limit=100):
        """Получить комментарии к посту"""
        return Review.query.filter_by(
            parent_id=post_id,
            is_comment=True
        ).order_by(Review.published_date.desc()).limit(limit).all()
    
    @staticmethod
    def get_comment_stats(post_id):
        """Статистика комментариев к посту"""
        comments = Review.query.filter_by(
            parent_id=post_id,
            is_comment=True
        ).all()
        
        if not comments:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
        
        stats = {
            'total': len(comments),
            'positive': sum(1 for c in comments if c.sentiment_label == 'positive'),
            'negative': sum(1 for c in comments if c.sentiment_label == 'negative'),
            'neutral': sum(1 for c in comments if c.sentiment_label == 'neutral')
        }
        
        return stats
```

### Шаг 2: Обновить коллекторы

Для каждого коллектора нужно:
1. Использовать `CommentHelper.save_post_with_comments()`
2. Убрать `parent_source_id` и `parent_url`
3. Правильно получать комментарии

### Шаг 3: Обновить API для фронтенда

```python
# В app_enhanced.py добавить endpoint:

@app.route('/api/post/<int:post_id>/comments')
def get_post_comments(post_id):
    """Получить комментарии к посту"""
    from utils.comment_helper import CommentHelper
    
    comments = CommentHelper.get_post_comments(post_id)
    stats = CommentHelper.get_comment_stats(post_id)
    
    return jsonify({
        'post_id': post_id,
        'comments': [c.to_dict() for c in comments],
        'stats': stats
    })
```

---

## 📊 Сводная таблица доступности комментариев

| Платформа | API | Selenium | Сложность | Статус | Рекомендация |
|-----------|-----|----------|-----------|--------|--------------|
| **Telegram** | ✅ Да | - | Легко | ✅ Работает | Исправить parent_id |
| **VK** | ✅ Да | - | Легко | ⚠️ Не используется | Добавить вызов метода |
| **OK.ru** | ❌ Нет | ⚠️ Да | Сложно | ❌ Не реализовано | Добавить через Selenium |
| **Яндекс.Дзен** | ❌ Нет | ✅ Да | Средне | ⚠️ Частично | Исправить parent_id |
| **Новостные сайты** | ❌ Нет | ⚠️ Да | Сложно | ⚠️ Частично | Индивидуально |

---

## 🚀 Быстрый старт (что сделать сейчас)

### Минимальные исправления (30 минут):
1. ✅ Создать `utils/comment_helper.py`
2. ✅ Исправить Telegram коллектор
3. ✅ Исправить VK коллектор

### Полные исправления (2-3 часа):
1. ✅ Все минимальные исправления
2. ✅ Добавить парсинг комментариев OK.ru
3. ✅ Исправить Дзен коллектор
4. ✅ Обновить API
5. ✅ Создать тесты

---

## 📝 Примеры использования

### Пример 1: Сохранение поста с комментариями

```python
from utils.comment_helper import CommentHelper
from analyzers.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Данные поста
post = {
    'source': 'vk',
    'source_id': 'vk_post_123_456',
    'text': 'Отличная работа ТНС Энерго!',
    # ... другие поля
}

# Комментарии
comments = [
    {
        'source': 'vk',
        'source_id': 'vk_comment_123_456_1',
        'text': 'Полностью согласен!',
        # ... другие поля
    },
    {
        'source': 'vk',
        'source_id': 'vk_comment_123_456_2',
        'text': 'Да, молодцы',
        # ... другие поля
    }
]

# Сохраняем с автоматической привязкой
saved_post, saved_comments = CommentHelper.save_post_with_comments(
    post, comments, analyzer
)

print(f"Сохранен пост ID: {saved_post.id}")
print(f"Сохранено комментариев: {len(saved_comments)}")
```

### Пример 2: Получение комментариев к посту

```python
from utils.comment_helper import CommentHelper

# Получить все комментарии
comments = CommentHelper.get_post_comments(post_id=123)

for comment in comments:
    print(f"{comment.author}: {comment.text}")

# Получить статистику
stats = CommentHelper.get_comment_stats(post_id=123)
print(f"Всего: {stats['total']}")
print(f"Позитивных: {stats['positive']}")
print(f"Негативных: {stats['negative']}")
```

---

## ⚠️ Важные замечания

1. **Производительность:** Парсинг комментариев через Selenium медленный. Рекомендуется:
   - Парсить комментарии асинхронно
   - Ограничить количество комментариев на пост (например, первые 50)
   - Использовать очереди задач (Celery)

2. **Блокировки:** OK.ru и Дзен могут блокировать за частые запросы:
   - Используйте прокси
   - Добавляйте случайные задержки
   - Ротируйте User-Agent

3. **Хранение:** Комментарии могут занимать много места в БД:
   - Архивируйте старые комментарии (>30 дней)
   - Удаляйте неинформативные комментарии
   - Используйте индексы для быстрого поиска
