"""
Помощник для работы с комментариями
Обеспечивает правильную связь между постами и комментариями
"""
from models import Review, db
import logging

logger = logging.getLogger(__name__)

class CommentHelper:
    """Помощник для работы с комментариями"""
    
    @staticmethod
    def save_post_with_comments(post_data, comments_data=None, analyzer=None):
        """
        Сохраняет пост и его комментарии с правильными связями
        
        Args:
            post_data: Данные поста (dict)
            comments_data: Список комментариев (list of dict), опционально
            analyzer: Анализатор тональности (опционально)
        
        Returns:
            (saved_post, saved_comments) - кортеж сохраненных объектов
        """
        if comments_data is None:
            comments_data = []
        
        try:
            # 1. Сохраняем основной пост
            post_data['is_comment'] = False
            
            # Анализ тональности поста
            if analyzer and 'sentiment_score' not in post_data:
                try:
                    sentiment = analyzer.analyze(post_data.get('text', ''))
                    post_data['sentiment_score'] = sentiment.get('sentiment_score', 0.0)
                    post_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                except Exception as e:
                    logger.error(f"Error analyzing post sentiment: {e}")
            
            # Проверяем дубликаты
            existing_post = Review.query.filter_by(
                source_id=post_data['source_id']
            ).first()
            
            if existing_post:
                logger.debug(f"Post already exists: {post_data['source_id']}")
                saved_post = existing_post
            else:
                # Убираем поля, которых нет в модели
                clean_post_data = CommentHelper._clean_post_data(post_data)
                
                saved_post = Review(**clean_post_data)
                db.session.add(saved_post)
                db.session.flush()  # Получаем ID не коммитя
                logger.info(f"✓ Saved post: {saved_post.id} ({saved_post.source})")
            
            # 2. Сохраняем комментарии
            saved_comments = []
            
            for comment_data in comments_data:
                try:
                    comment_data['is_comment'] = True
                    comment_data['parent_id'] = saved_post.id
                    
                    # Убираем старые поля если есть
                    comment_data.pop('parent_source_id', None)
                    comment_data.pop('parent_url', None)
                    
                    # Анализ тональности комментария
                    if analyzer and 'sentiment_score' not in comment_data:
                        try:
                            sentiment = analyzer.analyze(comment_data.get('text', ''))
                            comment_data['sentiment_score'] = sentiment.get('sentiment_score', 0.0)
                            comment_data['sentiment_label'] = sentiment.get('sentiment_label', 'neutral')
                        except Exception as e:
                            logger.error(f"Error analyzing comment sentiment: {e}")
                    
                    # Проверяем дубликаты
                    existing_comment = Review.query.filter_by(
                        source_id=comment_data['source_id']
                    ).first()
                    
                    if existing_comment:
                        logger.debug(f"Comment already exists: {comment_data['source_id']}")
                        continue
                    
                    # Убираем поля, которых нет в модели
                    clean_comment_data = CommentHelper._clean_post_data(comment_data)
                    
                    saved_comment = Review(**clean_comment_data)
                    db.session.add(saved_comment)
                    saved_comments.append(saved_comment)
                    
                except Exception as e:
                    logger.error(f"Error saving comment: {e}")
                    continue
            
            db.session.commit()
            
            if saved_comments:
                logger.info(f"✓ Saved {len(saved_comments)} comments for post {saved_post.id}")
            
            return saved_post, saved_comments
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving post with comments: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    @staticmethod
    def _clean_post_data(data):
        """Убирает поля, которых нет в модели Review"""
        valid_fields = {
            'source', 'source_id', 'author', 'author_id', 'text', 'url',
            'published_date', 'collected_date', 'parent_id', 'is_comment',
            'sentiment_score', 'sentiment_label', 'keywords',
            'is_moderated', 'moderation_status', 'moderation_reason',
            'requires_manual_review', 'processed', 'processed_date'
        }
        
        return {k: v for k, v in data.items() if k in valid_fields}
    
    @staticmethod
    def save_posts_batch(posts_data, analyzer=None):
        """
        Пакетное сохранение постов (без комментариев)
        
        Args:
            posts_data: Список постов
            analyzer: Анализатор тональности (опционально)
        
        Returns:
            Список сохраненных постов
        """
        saved_posts = []
        
        for post_data in posts_data:
            try:
                saved_post, _ = CommentHelper.save_post_with_comments(
                    post_data, [], analyzer
                )
                if saved_post:
                    saved_posts.append(saved_post)
            except Exception as e:
                logger.error(f"Error saving post in batch: {e}")
                continue
        
        return saved_posts
    
    @staticmethod
    def get_post_comments(post_id, limit=100):
        """
        Получить комментарии к посту
        
        Args:
            post_id: ID поста
            limit: Максимальное количество комментариев
        
        Returns:
            Список комментариев (Review objects)
        """
        try:
            return Review.query.filter_by(
                parent_id=post_id,
                is_comment=True
            ).order_by(Review.published_date.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting comments for post {post_id}: {e}")
            return []
    
    @staticmethod
    def get_comment_stats(post_id):
        """
        Статистика комментариев к посту
        
        Args:
            post_id: ID поста
        
        Returns:
            Словарь со статистикой
        """
        try:
            comments = Review.query.filter_by(
                parent_id=post_id,
                is_comment=True
            ).all()
            
            if not comments:
                return {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'avg_sentiment': 0.0
                }
            
            sentiment_counts = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            total_sentiment = 0.0
            
            for comment in comments:
                label = comment.sentiment_label or 'neutral'
                sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
                total_sentiment += comment.sentiment_score or 0.0
            
            avg_sentiment = total_sentiment / len(comments) if comments else 0.0
            
            stats = {
                'total': len(comments),
                'positive': sentiment_counts['positive'],
                'negative': sentiment_counts['negative'],
                'neutral': sentiment_counts['neutral'],
                'avg_sentiment': round(avg_sentiment, 3)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting comment stats for post {post_id}: {e}")
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'avg_sentiment': 0.0
            }
    
    @staticmethod
    def get_posts_with_comments(source=None, limit=50):
        """
        Получить посты вместе с их комментариями
        
        Args:
            source: Фильтр по источнику (опционально)
            limit: Максимальное количество постов
        
        Returns:
            Список словарей {post: Review, comments: [Review], stats: dict}
        """
        try:
            query = Review.query.filter_by(is_comment=False)
            
            if source:
                query = query.filter_by(source=source)
            
            posts = query.order_by(Review.published_date.desc()).limit(limit).all()
            
            result = []
            for post in posts:
                comments = CommentHelper.get_post_comments(post.id)
                stats = CommentHelper.get_comment_stats(post.id)
                
                result.append({
                    'post': post,
                    'comments': comments,
                    'stats': stats
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting posts with comments: {e}")
            return []
    
    @staticmethod
    def get_all_comments_count():
        """Получить общее количество комментариев"""
        try:
            return Review.query.filter_by(is_comment=True).count()
        except Exception as e:
            logger.error(f"Error counting comments: {e}")
            return 0
    
    @staticmethod
    def get_posts_without_comments(source=None, limit=100):
        """
        Получить посты без комментариев (для дополнительного парсинга)
        
        Args:
            source: Фильтр по источнику
            limit: Максимальное количество
        
        Returns:
            Список постов без комментариев
        """
        try:
            query = Review.query.filter_by(is_comment=False)
            
            if source:
                query = query.filter_by(source=source)
            
            # Подзапрос для постов с комментариями
            posts_with_comments = db.session.query(Review.parent_id).filter(
                Review.is_comment == True
            ).distinct().subquery()
            
            # Посты БЕЗ комментариев
            query = query.filter(~Review.id.in_(posts_with_comments))
            
            return query.order_by(Review.published_date.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting posts without comments: {e}")
            return []
