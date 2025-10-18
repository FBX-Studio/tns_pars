"""
Асинхронный монитор с WebSocket поддержкой для реального времени
"""
import asyncio
import logging
from datetime import datetime
from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector

# Настройка логгера
logger = logging.getLogger(__name__)
try:
    from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
except ImportError:
    from collectors.telegram_collector import TelegramCollector
from collectors.news_collector import NewsCollector

# Новые коллекторы - используем Selenium для Дзена (обход капчи)
try:
    from collectors.zen_selenium_collector import ZenSeleniumCollector as ZenCollector
    logger.info("[MONITOR] Используется ZenSeleniumCollector (обход капчи)")
except ImportError:
    try:
        from collectors.zen_collector import ZenCollector
        logger.warning("[MONITOR] ZenSeleniumCollector не найден, используется обычный коллектор")
    except ImportError:
        ZenCollector = None
        logger.warning("[MONITOR] Коллектор Дзена недоступен")
    
try:
    from collectors.ok_selenium_collector import OKSeleniumCollector as OKCollector
    logger.info("[MONITOR] ✓ Используется OK Selenium коллектор (ПРИОРИТЕТ)")
except ImportError as e:
    logger.warning(f"[MONITOR] Selenium коллектор недоступен: {e}")
    try:
        from collectors.ok_collector_working import OKCollectorWorking as OKCollector
        logger.info("[MONITOR] Используется улучшенный OK коллектор (мультиметод)")
    except ImportError:
        try:
            from collectors.ok_collector import OKCollector
            logger.info("[MONITOR] Используется базовый OK коллектор")
        except ImportError:
            OKCollector = None
            logger.warning("[MONITOR] OK коллектор недоступен")
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from analyzers.dostoevsky_analyzer import DostoevskyAnalyzer
from config import Config
from app_enhanced import app

logger = logging.getLogger(__name__)

class AsyncReviewMonitorWebSocket:
    def __init__(self, socketio, period='day'):
        self.socketio = socketio
        self.period = period
        self.since_date = self._calculate_since_date(period)
        
        # Инициализируем анализатор Dostoevsky
        # ВРЕМЕННО ОТКЛЮЧЕНО: Dostoevsky блокирует первый запрос
        logger.info("[MONITOR] Используем стандартный анализатор (Dostoevsky отключен)")
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # try:
        #     logger.info("[MONITOR] Инициализация Dostoevsky анализатора...")
        #     self.sentiment_analyzer = DostoevskyAnalyzer()
        #     logger.info("[MONITOR] ✓ Dostoevsky анализатор загружен")
        # except Exception as e:
        #     logger.warning(f"[MONITOR] Не удалось загрузить Dostoevsky: {e}")
        #     logger.warning("[MONITOR] Используем стандартный анализатор")
        #     self.sentiment_analyzer = SentimentAnalyzer()
        
        # Ленивая инициализация коллекторов (создаются при первом запуске)
        self.vk_collector = None
        self.telegram_collector = None
        self.news_collector = None
        self.zen_collector = None
        self.ok_collector = None
        self.moderator = None
        self.is_running = False
        
    def _init_collectors(self):
        """Инициализация коллекторов при первом запуске"""
        if self.vk_collector is not None:
            return  # Уже инициализированы
        
        logger.info("[MONITOR] Инициализация коллекторов...")
        
        self.vk_collector = VKCollector(sentiment_analyzer=self.sentiment_analyzer)
        logger.info("[MONITOR] ✓ VK коллектор инициализирован")
        
        self.telegram_collector = TelegramCollector(sentiment_analyzer=self.sentiment_analyzer)
        logger.info("[MONITOR] ✓ Telegram коллектор инициализирован")
        
        self.news_collector = NewsCollector(sentiment_analyzer=self.sentiment_analyzer)
        logger.info("[MONITOR] ✓ News коллектор инициализирован")
        
        try:
            self.zen_collector = ZenCollector(sentiment_analyzer=self.sentiment_analyzer) if ZenCollector else None
            if self.zen_collector:
                logger.info("[MONITOR] ✓ Zen коллектор инициализирован")
            else:
                logger.warning("[MONITOR] ✗ Zen коллектор не доступен (класс не найден)")
        except Exception as e:
            logger.error(f"[MONITOR] ✗ Ошибка инициализации Zen коллектора: {e}")
            self.zen_collector = None
        
        try:
            self.ok_collector = OKCollector(sentiment_analyzer=self.sentiment_analyzer) if OKCollector else None
            if self.ok_collector:
                logger.info("[MONITOR] ✓ OK коллектор инициализирован")
            else:
                logger.warning("[MONITOR] ✗ OK коллектор не доступен (класс не найден)")
        except Exception as e:
            logger.error(f"[MONITOR] ✗ Ошибка инициализации OK коллектора: {e}")
            self.ok_collector = None
        
        self.moderator = Moderator()
        logger.info("[MONITOR] ✓ Все коллекторы инициализированы")
    
    def _calculate_since_date(self, period):
        """Вычисляет дату начала парсинга на основе периода"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        if period == 'hour':
            return now - timedelta(hours=1)
        elif period == 'day':
            return now - timedelta(days=1)
        elif period == 'week':
            return now - timedelta(weeks=1)
        elif period == 'month':
            return now - timedelta(days=30)
        else:  # 'all'
            return None  # Без ограничения по дате
    
    def _is_within_period(self, review_data):
        """Проверяет, входит ли отзыв в выбранный период"""
        if not self.since_date:
            return True  # Если период 'all', пропускаем все
        
        # Пытаемся получить дату из различных полей
        review_date = None
        
        # Варианты полей с датой
        date_fields = ['date', 'created_date', 'collected_date', 'published_date', 'timestamp']
        
        for field in date_fields:
            if field in review_data and review_data[field]:
                date_value = review_data[field]
                
                # Если это timestamp (число)
                if isinstance(date_value, (int, float)):
                    from datetime import datetime
                    review_date = datetime.fromtimestamp(date_value)
                    break
                
                # Если это строка даты
                elif isinstance(date_value, str):
                    try:
                        from dateutil import parser
                        review_date = parser.parse(date_value)
                        break
                    except:
                        pass
                
                # Если это уже datetime объект
                elif hasattr(date_value, 'year'):
                    review_date = date_value
                    break
        
        # Если дата не найдена, пропускаем (считаем что подходит)
        if not review_date:
            return True
        
        # Сравниваем с since_date
        # Приводим к UTC если есть timezone
        if hasattr(review_date, 'tzinfo') and review_date.tzinfo:
            review_date = review_date.replace(tzinfo=None)
        
        return review_date >= self.since_date
    
    def emit_progress(self, source, stage, message, data=None):
        """Отправка прогресса через WebSocket"""
        progress_data = {
            'source': source,
            'stage': stage,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if data:
            progress_data.update(data)
        
        self.socketio.emit('monitoring_progress', progress_data)
        logger.info(f"[{source.upper()}] {stage}: {message}")
    
    async def collect_from_source_async(self, source_name, collect_callable):
        """Асинхронный сбор с отправкой прогресса"""
        log = None
        log_id = None
        
        try:
            # Этап 1: Инициализация
            self.emit_progress(source_name, 'init', 'Инициализация сбора', {
                'progress': 0
            })
            
            with app.app_context():
                log = MonitoringLog(source=source_name, status='running')
                db.session.add(log)
                db.session.commit()
                log_id = log.id
            
            # Этап 2: Сбор данных
            self.emit_progress(source_name, 'collecting', 'Сбор данных из источника...', {
                'progress': 25
            })
            
            loop = asyncio.get_event_loop()
            reviews = await loop.run_in_executor(None, collect_callable)
            
            # Фильтрация по периоду, если указан
            if self.since_date:
                initial_count = len(reviews)
                reviews = [r for r in reviews if self._is_within_period(r)]
                self.emit_progress(source_name, 'filtering', 
                                 f'Отфильтровано: {len(reviews)} из {initial_count} (период: {self.period})', {
                    'progress': 45,
                    'filtered': len(reviews),
                    'total': initial_count
                })
            
            self.emit_progress(source_name, 'collected', f'Получено записей: {len(reviews)}', {
                'progress': 50,
                'count': len(reviews)
            })
            
            # Этап 3: Анализ
            self.emit_progress(source_name, 'analyzing', 'Анализ и модерация...', {
                'progress': 60
            })
            
            reviews_added = 0
            
            with app.app_context():
                processed_count = 0
                # Сначала создаем словарь для хранения созданных постов по source_id
                created_posts = {}
                
                for review_data in reviews:
                    processed_count += 1
                    
                    # Обновление прогресса каждые 5 записей
                    if processed_count % 5 == 0:
                        progress_pct = 60 + (30 * processed_count / len(reviews))
                        self.emit_progress(source_name, 'analyzing', 
                                         f'Обработано: {processed_count}/{len(reviews)}', {
                            'progress': int(progress_pct),
                            'processed': processed_count,
                            'total': len(reviews)
                        })
                    
                    try:
                        existing = Review.query.filter_by(
                            source_id=review_data['source_id']
                        ).first()
                        
                        if existing:
                            logger.debug(f"[{source_name}] Пропуск дубликата: {review_data['source_id']}")
                            # Сохраняем существующий пост для связи с комментариями
                            if not review_data.get('is_comment', False):
                                created_posts[review_data['source_id']] = existing
                            continue
                        
                        logger.info(f"[{source_name}] Новая запись: {review_data.get('text', '')[:60]}...")
                        
                        sentiment = self.sentiment_analyzer.analyze(review_data['text'])
                        keywords = self.sentiment_analyzer.extract_keywords(review_data['text'])
                        
                        moderation_status, moderation_reason, requires_manual = self.moderator.moderate(
                            review_data['text'],
                            sentiment['sentiment_score']
                        )
                        
                        # Определяем parent_id если это комментарий
                        parent_id = None
                        is_comment = review_data.get('is_comment', False)
                        
                        if is_comment and 'parent_source_id' in review_data:
                            parent_source_id = review_data['parent_source_id']
                            # Ищем родительский пост в созданных или в БД
                            if parent_source_id in created_posts:
                                parent_id = created_posts[parent_source_id].id
                            else:
                                parent_post = Review.query.filter_by(source_id=parent_source_id).first()
                                if parent_post:
                                    parent_id = parent_post.id
                                    created_posts[parent_source_id] = parent_post
                        
                        review = Review(
                            source=review_data['source'],
                            source_id=review_data['source_id'],
                            author=review_data.get('author'),
                            author_id=review_data.get('author_id'),
                            text=review_data['text'],
                            url=review_data.get('url'),
                            published_date=review_data.get('published_date'),
                            sentiment_score=sentiment['sentiment_score'],
                            sentiment_label=sentiment['sentiment_label'],
                            keywords=','.join(keywords) if keywords else None,
                            moderation_status=moderation_status,
                            moderation_reason=moderation_reason,
                            requires_manual_review=requires_manual,
                            processed=not requires_manual,
                            is_comment=is_comment,
                            parent_id=parent_id
                        )
                        
                        db.session.add(review)
                        db.session.flush()  # Получаем ID для возможной связи с комментариями
                        
                        # Сохраняем созданный пост для связи с комментариями
                        if not is_comment:
                            created_posts[review_data['source_id']] = review
                        
                        reviews_added += 1
                        
                    except Exception as e:
                        logger.error(f"[{source_name}] Ошибка обработки: {e}")
                        continue
                
                # Этап 4: Сохранение
                self.emit_progress(source_name, 'saving', 'Сохранение в базу данных...', {
                    'progress': 90
                })
                
                db.session.commit()
                
                if log_id:
                    log = MonitoringLog.query.get(log_id)
                    if log:
                        log.completed_at = datetime.utcnow()
                        log.status = 'success'
                        log.reviews_collected = reviews_added
                        db.session.commit()
            
            # Завершено
            self.emit_progress(source_name, 'completed', 
                             f'Завершено! Добавлено: {reviews_added}', {
                'progress': 100,
                'added': reviews_added,
                'duplicates': len(reviews) - reviews_added
            })
            
            return {'source': source_name, 'success': True, 'count': reviews_added}
            
        except Exception as e:
            self.emit_progress(source_name, 'error', f'Ошибка: {str(e)}', {
                'progress': 100,
                'error': str(e)
            })
            
            try:
                with app.app_context():
                    if log_id:
                        log = MonitoringLog.query.get(log_id)
                        if log:
                            log.completed_at = datetime.utcnow()
                            log.status = 'error'
                            log.error_message = str(e)
                            db.session.commit()
            except Exception as db_error:
                logger.error(f"[{source_name}] DB error: {db_error}")
            
            return {'source': source_name, 'success': False, 'error': str(e)}
    
    async def run_collection_async(self):
        """Асинхронный сбор из всех источников"""
        start_time = datetime.utcnow()
        
        # Инициализируем коллекторы при первом запуске
        self._init_collectors()
        
        # Определяем активные источники
        sources = ['vk', 'telegram', 'news']
        if self.zen_collector:
            sources.append('zen')
            logger.info("[MONITOR] Zen коллектор активен")
        else:
            logger.warning("[MONITOR] Zen коллектор недоступен")
            
        if self.ok_collector:
            sources.append('ok')
            logger.info("[MONITOR] OK коллектор активен")
        else:
            logger.warning("[MONITOR] OK коллектор недоступен")
        
        logger.info(f"[MONITOR] Всего активных источников: {len(sources)} - {sources}")
        
        self.socketio.emit('monitoring_started', {
            'start_time': start_time.isoformat(),
            'sources': sources
        })
        
        self.is_running = True
        
        def call_with_comments(collector):
            def _call():
                try:
                    return collector.collect(collect_comments=True)
                except TypeError:
                    return collector.collect()
            return _call

        tasks = [
            self.collect_from_source_async('vk', lambda: self.vk_collector.collect(collect_comments=True)),
            self.collect_from_source_async('telegram', call_with_comments(self.telegram_collector)),
            self.collect_from_source_async('news', lambda: self.news_collector.collect_with_comments()),
        ]

        # Добавляем новые коллекторы если доступны
        if self.zen_collector:
            tasks.append(self.collect_from_source_async('zen', call_with_comments(self.zen_collector)))
        if self.ok_collector:
            tasks.append(self.collect_from_source_async('ok', lambda: self.ok_collector.collect(collect_comments=True)))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        total_collected = 0
        success_count = 0
        error_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            elif isinstance(result, dict):
                if result.get('success'):
                    total_collected += result.get('count', 0)
                    success_count += 1
                else:
                    error_count += 1
        
        # Отправка итогов
        self.socketio.emit('monitoring_completed', {
            'end_time': end_time.isoformat(),
            'duration': duration,
            'total_collected': total_collected,
            'success_count': success_count,
            'error_count': error_count,
            'results': [r for r in results if isinstance(r, dict)]
        })
        
        self.is_running = False
        
        # Обновление глобального состояния
        from app_enhanced import monitoring_state
        monitoring_state['is_running'] = False
        monitoring_state['results'] = {
            'total': total_collected,
            'duration': duration,
            'success': success_count,
            'errors': error_count
        }
        
        return total_collected
    
    def run_collection_sync(self):
        """Синхронная обертка"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_collection_async())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка в синхронной обертке: {e}")
            self.socketio.emit('monitoring_error', {
                'error': str(e)
            })
            from app_enhanced import monitoring_state
            monitoring_state['is_running'] = False
            raise
