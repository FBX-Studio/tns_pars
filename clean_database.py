import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app
from models import db, Review
from utils.language_detector import LanguageDetector

language_detector = LanguageDetector()

def is_relevant_to_company(text):
    text_lower = text.lower()
    
    main_patterns = [
        'тнс энерго',
        'тнсэнерго',
        'тнс-энерго'
    ]
    
    has_main = any(pattern in text_lower for pattern in main_patterns)
    
    if has_main:
        return True
    
    secondary_patterns = ['энергосбыт', 'энергоснабжение']
    nizhny_patterns = ['нижний новгород', 'нижегородск', 'н.новгород', 'н новгород']
    
    has_secondary = any(pattern in text_lower for pattern in secondary_patterns)
    has_nizhny = any(pattern in text_lower for pattern in nizhny_patterns)
    
    return has_secondary and has_nizhny

def is_nizhny_region(text):
    text_lower = text.lower()
    geo_keywords = ['нижний новгород', 'нижегородск', 'нн', 'н.новгород', 'н новгород', 'нижегор']
    return any(keyword.lower() in text_lower for keyword in geo_keywords)

def is_russian(text):
    return language_detector.is_russian(text)

def clean_database():
    with app.app_context():
        reviews = Review.query.all()
        total = len(reviews)
        deleted = 0
        
        print(f"Total reviews: {total}")
        print("Checking relevance...")
        
        for review in reviews:
            text = review.text or ''
            
            if not is_relevant_to_company(text):
                print(f"Deleting irrelevant: {review.id} - {review.author} - {text[:50]}...")
                db.session.delete(review)
                deleted += 1
                continue
            
            if not is_nizhny_region(text):
                print(f"Deleting wrong region: {review.id} - {review.author} - {text[:50]}...")
                db.session.delete(review)
                deleted += 1
                continue
            
            if not is_russian(text):
                print(f"Deleting non-russian: {review.id} - {review.author} - {text[:50]}...")
                db.session.delete(review)
                deleted += 1
        
        db.session.commit()
        
        print(f"\nCleaning completed:")
        print(f"Total reviews: {total}")
        print(f"Deleted: {deleted}")
        print(f"Remaining: {total - deleted}")

if __name__ == '__main__':
    clean_database()
