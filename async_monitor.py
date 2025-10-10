"""
Асинхронная система мониторинга отзывов
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
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from config import Config
from app import app
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AsyncReviewMonitor:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.vk_collector = VKCollector()
        self.telegram_collector = TelegramCollector()
        self.news_collector = NewsCollector(sentiment_analyzer=self.sentiment_analyzer)
        self.moderator = Moderator()
        self.is_running = False
    
    async def collect_from_source_async(self, source_name, collect_callable):
        """Асинхронный сбор отзывов из одного источника"""
        log = None
        log_id = None
        
        try:
            logger.info(f"")
            logger.info(f"{'='*60}")
            logger.info(f"[{source_name.upper()}] ЭТАП 1/4: Инициализация сбора")
            logger.info(f"{'='*60}")
            
            with app.app_context():
                log = MonitoringLog(source=source_name, status='running')
                db.session.add(log)
                db.session.commit()
                log_id = log.id
            
            logger.info(f"[{source_name.upper()}] ✓ Лог создан (ID: {log_id})")
            logger.info(f"")
            logger.info(f"[{source_name.upper()}] ЭТАП 2/4: Сбор данных из источника...")
            
            loop = asyncio.get_event_loop()
            reviews = await loop.run_in_executor(None, collect_callable)
            
            logger.info(f"[{source_name.upper()}] ✓ Получено записей: {len(reviews)}")
            logger.info(f"")
            logger.info(f"[{source_name.upper()}] ЭТАП 3/4: Анализ и модерация...")
            
            reviews_added = 0
            
            with app.app_context():
                processed_count = 0
                for review_data in reviews:
                    processed_count += 1
                    try:
                        if processed_count % 5 == 0:
                            logger.info(f"[{source_name.upper()}]   → Обработано: {processed_count}/{len(reviews)}")
                        
                        existing = Review.query.filter_by(
                            source_id=review_data['source_id']
                        ).first()
                        
                        if existing:
                            logger.debug(f"[{source_name.upper()}] Отзыв {review_data['source_id']} уже существует")
                            continue
                        
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
                        logger.error(f"[{source_name.upper()}] Ошибка обработки отзыва: {e}")
                        continue
                
                logger.info(f"")
                logger.info(f"[{source_name.upper()}] ЭТАП 4/4: Сохранение в базу данных...")
                
                db.session.commit()
                
                if log_id:
                    log = MonitoringLog.query.get(log_id)
                    if log:
                        log.completed_at = datetime.utcnow()
                        log.status = 'success'
                        log.reviews_collected = reviews_added
                        db.session.commit()
            
            logger.info(f"")
            logger.info(f"[{source_name.upper()}] {'='*60}")
            logger.info(f"[{source_name.upper()}] ✓ ЗАВЕРШЕНО")
            logger.info(f"[{source_name.upper()}]   Обработано: {len(reviews)}")
            logger.info(f"[{source_name.upper()}]   Добавлено новых: {reviews_added}")
            logger.info(f"[{source_name.upper()}]   Дубликатов пропущено: {len(reviews) - reviews_added}")
            logger.info(f"[{source_name.upper()}] {'='*60}")
            
            return {'source': source_name, 'success': True, 'count': reviews_added}
            
        except Exception as e:
            logger.error(f"")
            logger.error(f"[{source_name.upper()}] {'='*60}")
            logger.error(f"[{source_name.upper()}] ✗ ОШИБКА")
            logger.error(f"[{source_name.upper()}]   {str(e)}")
            logger.error(f"[{source_name.upper()}] {'='*60}")
            
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
                logger.error(f"[{source_name.upper()}] Ошибка записи в БД: {db_error}")
            
            return {'source': source_name, 'success': False, 'error': str(e)}
    
    async def run_collection_async(self):
        """Асинхронный запуск сбора из всех источников параллельно"""
        start_time = datetime.utcnow()
        
        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + " " * 20 + "ЗАПУСК ЦИКЛА МОНИТОРИНГА" + " " * 34 + "║")
        logger.info("║" + " " * 25 + "(АСИНХРОННЫЙ РЕЖИМ)" + " " * 35 + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info(f"Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        logger.info("📊 Запуск параллельного сбора из 3 источников:")
        logger.info("   1️⃣  VK (ВКонтакте)")
        logger.info("   2️⃣  Telegram (каналы)")
        logger.info("   3️⃣  News (новостные сайты)")
        logger.info("")
        
        self.is_running = True
        
        def call_with_comments(collector):
            def _call():
                try:
                    return collector.collect(collect_comments=True)
                except TypeError:
                    return collector.collect()
            return _call

        tasks = [
            self.collect_from_source_async('vk', lambda: self.vk_collector.collect()),
            self.collect_from_source_async('telegram', call_with_comments(self.telegram_collector)),
            self.collect_from_source_async('news', lambda: self.news_collector.collect_with_comments()),
        ]
        
        logger.info("⚡ Сбор данных начат одновременно из всех источников...")
        logger.info("")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + " " * 25 + "ИТОГОВЫЕ РЕЗУЛЬТАТЫ" + " " * 35 + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info("")
        
        total_collected = 0
        success_count = 0
        error_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"❌ Необработанная ошибка: {result}")
            elif isinstance(result, dict):
                if result.get('success'):
                    count = result.get('count', 0)
                    total_collected += count
                    success_count += 1
                    source_emoji = {'vk': '1️⃣', 'telegram': '2️⃣', 'news': '3️⃣'}.get(result['source'], '📌')
                    logger.info(f"{source_emoji}  {result['source'].upper():<12} → ✓ Добавлено: {count:>3} новых отзывов")
                else:
                    error_count += 1
                    source_emoji = {'vk': '1️⃣', 'telegram': '2️⃣', 'news': '3️⃣'}.get(result['source'], '📌')
                    logger.error(f"{source_emoji}  {result['source'].upper():<12} → ✗ Ошибка: {result.get('error', 'неизвестная')}")
        
        logger.info("")
        logger.info("─" * 80)
        logger.info(f"📈 СТАТИСТИКА:")
        logger.info(f"   • Успешных источников: {success_count}/3")
        logger.info(f"   • Ошибок: {error_count}")
        logger.info(f"   • Всего собрано: {total_collected} новых отзывов")
        logger.info(f"   • Время выполнения: {duration:.1f} секунд")
        logger.info(f"   • Завершено: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("─" * 80)
        logger.info("")
        
        if total_collected > 0:
            logger.info("✅ Цикл мониторинга завершен успешно!")
        elif error_count == 3:
            logger.warning("⚠️  Все источники вернули ошибки!")
        else:
            logger.info("ℹ️  Цикл мониторинга завершен (новых отзывов не найдено)")
        
        logger.info("")
        
        self.is_running = False
        return total_collected
    
    def run_collection_sync(self):
        """Синхронная обертка для запуска из Flask"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_collection_async())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Ошибка в синхронной обертке: {e}")
            raise
    
    async def start_scheduler_async(self):
        """Асинхронный планировщик задач"""
        interval_seconds = Config.MONITORING_INTERVAL_MINUTES * 60
        
        logger.info(f"Запуск асинхронного планировщика с интервалом: {Config.MONITORING_INTERVAL_MINUTES} минут")
        
        await self.run_collection_async()
        
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                if not self.is_running:
                    await self.run_collection_async()
                else:
                    logger.warning("Предыдущий цикл мониторинга еще выполняется, пропускаем...")
            except asyncio.CancelledError:
                logger.info("Планировщик остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)

def run_monitor_background():
    """Запуск мониторинга в фоновом потоке"""
    with app.app_context():
        db.create_all()
    
    monitor = AsyncReviewMonitor()
    
    try:
        asyncio.run(monitor.start_scheduler_async())
    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен пользователем")

if __name__ == '__main__':
    run_monitor_background()
