"""
Асинхронный монитор с WebSocket поддержкой для реального времени
"""
import asyncio
import logging
from datetime import datetime
from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector
try:
    from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
except ImportError:
    from collectors.telegram_collector import TelegramCollector
try:
    from collectors.news_collector_light import NewsCollectorLight as NewsCollector
except ImportError:
    try:
        from collectors.news_collector import NewsCollector
    except ImportError:
        from collectors.web_collector import WebCollector as NewsCollector

# Новые коллекторы
try:
    from collect_dzen_duckduckgo import DzenDuckDuckGoCollector as ZenCollector
except ImportError:
    try:
        from collectors.zen_collector_manual import ZenCollectorManual as ZenCollector
    except ImportError:
        try:
            from collectors.zen_collector_selenium import ZenCollectorSelenium as ZenCollector
        except ImportError:
            try:
                from collectors.zen_collector import ZenCollector
            except ImportError:
                ZenCollector = None
    
try:
    from collectors.ok_collector import OKCollector
except ImportError:
    OKCollector = None
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from config import Config
from app_enhanced import app

logger = logging.getLogger(__name__)

class AsyncReviewMonitorWebSocket:
    def __init__(self, socketio, period='day'):
        self.socketio = socketio
        self.period = period
        self.since_date = self._calculate_since_date(period)
        self.vk_collector = VKCollector()
        self.telegram_collector = TelegramCollector()
        self.news_collector = NewsCollector()
        self.zen_collector = ZenCollector() if ZenCollector else None
        self.ok_collector = OKCollector() if OKCollector else None
        self.sentiment_analyzer = SentimentAnalyzer()
        self.moderator = Moderator()
        self.is_running = False
    
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
    
    async def collect_from_source_async(self, source_name, collector):
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
            reviews = await loop.run_in_executor(None, collector.collect)
            
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
                            continue
                        
                        logger.info(f"[{source_name}] Новая запись: {review_data.get('text', '')[:60]}...")
                        
                        sentiment = self.sentiment_analyzer.analyze(review_data['text'])
                        keywords = self.sentiment_analyzer.extract_keywords(review_data['text'])
                        
                        moderation_status, moderation_reason, requires_manual = self.moderator.moderate(
                            review_data['text'],
                            sentiment['sentiment_score']
                        )
                        
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
                            processed=not requires_manual
                        )
                        
                        db.session.add(review)
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
        
        # Определяем активные источники
        sources = ['vk', 'telegram', 'news']
        if self.zen_collector:
            sources.append('zen')
        if self.ok_collector:
            sources.append('ok')
        
        self.socketio.emit('monitoring_started', {
            'start_time': start_time.isoformat(),
            'sources': sources
        })
        
        self.is_running = True
        
        tasks = [
            self.collect_from_source_async('vk', self.vk_collector),
            self.collect_from_source_async('telegram', self.telegram_collector),
            self.collect_from_source_async('news', self.news_collector),
        ]
        
        # Добавляем новые коллекторы если доступны
        if self.zen_collector:
            tasks.append(self.collect_from_source_async('zen', self.zen_collector))
        if self.ok_collector:
            tasks.append(self.collect_from_source_async('ok', self.ok_collector))
        
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
