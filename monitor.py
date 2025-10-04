import schedule
import time
import logging
from datetime import datetime
from models import db, Review, MonitoringLog
from collectors.vk_collector import VKCollector
try:
    from collectors.telegram_user_collector import TelegramUserCollector as TelegramCollector
except ImportError:
    from collectors.telegram_collector import TelegramCollector
try:
    from collectors.news_collector import NewsCollector
except ImportError:
    from collectors.web_collector import WebCollector as NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.moderator import Moderator
from config import Config
from app import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReviewMonitor:
    def __init__(self):
        self.vk_collector = VKCollector()
        self.telegram_collector = TelegramCollector()
        self.news_collector = NewsCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.moderator = Moderator()
    
    def collect_from_source(self, source_name, collector):
        """Collect reviews from a single source"""
        log = MonitoringLog(source=source_name, status='running')
        
        with app.app_context():
            db.session.add(log)
            db.session.commit()
            log_id = log.id
        
        try:
            logger.info(f"Starting collection from {source_name}")
            reviews = collector.collect()
            
            reviews_added = 0
            
            with app.app_context():
                for review_data in reviews:
                    existing = Review.query.filter_by(
                        source_id=review_data['source_id']
                    ).first()
                    
                    if existing:
                        logger.debug(f"Review {review_data['source_id']} already exists")
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
                
                db.session.commit()
                
                log = MonitoringLog.query.get(log_id)
                log.completed_at = datetime.utcnow()
                log.status = 'success'
                log.reviews_collected = reviews_added
                db.session.commit()
            
            logger.info(f"Completed collection from {source_name}: {reviews_added} new reviews")
            
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")
            
            with app.app_context():
                log = MonitoringLog.query.get(log_id)
                log.completed_at = datetime.utcnow()
                log.status = 'error'
                log.error_message = str(e)
                db.session.commit()
    
    def run_collection(self):
        """Run collection from all sources"""
        logger.info("Starting monitoring cycle")
        
        self.collect_from_source('vk', self.vk_collector)
        time.sleep(2)
        
        self.collect_from_source('telegram', self.telegram_collector)
        time.sleep(2)
        
        self.collect_from_source('news', self.news_collector)
        
        logger.info("Monitoring cycle completed")
    
    def start_scheduler(self):
        """Start the monitoring scheduler"""
        logger.info(f"Starting scheduler with interval: {Config.MONITORING_INTERVAL_MINUTES} minutes")
        
        schedule.every(Config.MONITORING_INTERVAL_MINUTES).minutes.do(self.run_collection)
        
        self.run_collection()
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    monitor = ReviewMonitor()
    
    try:
        monitor.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
