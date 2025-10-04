from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    source_id = db.Column(db.String(255), unique=True, nullable=False)
    author = db.Column(db.String(255))
    author_id = db.Column(db.String(255))
    text = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500))
    published_date = db.Column(db.DateTime)
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    sentiment_score = db.Column(db.Float)
    sentiment_label = db.Column(db.String(20))
    keywords = db.Column(db.Text)
    
    is_moderated = db.Column(db.Boolean, default=False)
    moderation_status = db.Column(db.String(50))
    moderation_reason = db.Column(db.Text)
    requires_manual_review = db.Column(db.Boolean, default=False)
    
    processed = db.Column(db.Boolean, default=False)
    processed_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Review {self.id} from {self.source}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'source_id': self.source_id,
            'author': self.author,
            'author_id': self.author_id,
            'text': self.text,
            'url': self.url,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'collected_date': self.collected_date.isoformat() if self.collected_date else None,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'keywords': self.keywords.split(',') if self.keywords else [],
            'is_moderated': self.is_moderated,
            'moderation_status': self.moderation_status,
            'moderation_reason': self.moderation_reason,
            'requires_manual_review': self.requires_manual_review,
            'processed': self.processed
        }

class MonitoringLog(db.Model):
    __tablename__ = 'monitoring_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    reviews_collected = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<MonitoringLog {self.id} - {self.source}>'
