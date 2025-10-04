import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, Review, MonitoringLog
from monitor import ReviewMonitor

def clear_all_reviews():
    with app.app_context():
        review_count = Review.query.count()
        log_count = MonitoringLog.query.count()
        
        print(f"Deleting {review_count} reviews...")
        Review.query.delete()
        
        print(f"Deleting {log_count} monitoring logs...")
        MonitoringLog.query.delete()
        
        db.session.commit()
        
        print("Database cleared successfully!")

def collect_new_reviews():
    with app.app_context():
        print("\nStarting new collection with updated filters...")
        monitor = ReviewMonitor()
        monitor.run_collection()
        
        new_count = Review.query.count()
        print(f"\nCollection completed! Found {new_count} new reviews.")

if __name__ == '__main__':
    clear_all_reviews()
    collect_new_reviews()
