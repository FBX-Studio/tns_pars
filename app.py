from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from models import db, Review, MonitoringLog
from config import Config
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    total_reviews = Review.query.count()
    
    pending_reviews = Review.query.filter_by(requires_manual_review=True, processed=False).count()
    
    positive_reviews = Review.query.filter(Review.sentiment_label == 'positive').count()
    negative_reviews = Review.query.filter(Review.sentiment_label == 'negative').count()
    neutral_reviews = Review.query.filter(Review.sentiment_label == 'neutral').count()
    
    recent_reviews = Review.query.order_by(Review.collected_date.desc()).limit(10).all()
    
    stats = {
        'total': total_reviews,
        'pending': pending_reviews,
        'positive': positive_reviews,
        'negative': negative_reviews,
        'neutral': neutral_reviews
    }
    
    return render_template('dashboard.html', stats=stats, reviews=recent_reviews)

@app.route('/reviews')
def reviews_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    source = request.args.get('source', '')
    sentiment = request.args.get('sentiment', '')
    status = request.args.get('status', '')
    
    query = Review.query
    
    if source:
        query = query.filter_by(source=source)
    if sentiment:
        query = query.filter_by(sentiment_label=sentiment)
    if status == 'pending':
        query = query.filter_by(requires_manual_review=True)
    elif status == 'approved':
        query = query.filter_by(moderation_status='approved')
    elif status == 'rejected':
        query = query.filter_by(moderation_status='rejected')
    
    pagination = query.order_by(Review.collected_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('reviews.html', pagination=pagination, 
                         source=source, sentiment=sentiment, status=status)

@app.route('/review/<int:review_id>')
def review_detail(review_id):
    review = Review.query.get_or_404(review_id)
    return render_template('review_detail.html', review=review)

@app.route('/api/review/<int:review_id>/moderate', methods=['POST'])
def moderate_review(review_id):
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    
    action = data.get('action')
    
    if action == 'approve':
        review.moderation_status = 'approved'
        review.requires_manual_review = False
        review.processed = True
        review.processed_date = datetime.utcnow()
    elif action == 'reject':
        review.moderation_status = 'rejected'
        review.requires_manual_review = False
        review.processed = True
        review.processed_date = datetime.utcnow()
        review.moderation_reason = data.get('reason', 'Rejected by moderator')
    
    db.session.commit()
    
    return jsonify({'success': True, 'review': review.to_dict()})

@app.route('/api/stats')
def api_stats():
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    total = Review.query.count()
    today_count = Review.query.filter(
        db.func.date(Review.collected_date) == today
    ).count()
    week_count = Review.query.filter(
        db.func.date(Review.collected_date) >= week_ago
    ).count()
    
    by_source = db.session.query(
        Review.source, db.func.count(Review.id)
    ).group_by(Review.source).all()
    
    by_sentiment = db.session.query(
        Review.sentiment_label, db.func.count(Review.id)
    ).group_by(Review.sentiment_label).all()
    
    return jsonify({
        'total': total,
        'today': today_count,
        'week': week_count,
        'by_source': dict(by_source),
        'by_sentiment': dict(by_sentiment)
    })

@app.route('/api/monitoring/logs')
def monitoring_logs():
    logs = MonitoringLog.query.order_by(MonitoringLog.started_at.desc()).limit(20).all()
    return jsonify([{
        'id': log.id,
        'source': log.source,
        'started_at': log.started_at.isoformat() if log.started_at else None,
        'completed_at': log.completed_at.isoformat() if log.completed_at else None,
        'status': log.status,
        'reviews_collected': log.reviews_collected,
        'error_message': log.error_message
    } for log in logs])

@app.route('/monitoring')
def monitoring():
    logs = MonitoringLog.query.order_by(MonitoringLog.started_at.desc()).limit(50).all()
    return render_template('monitoring.html', logs=logs, config=Config)

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Запуск мониторинга вручную"""
    try:
        from monitor import ReviewMonitor
        import threading
        
        monitor = ReviewMonitor()
        
        thread = threading.Thread(target=monitor.run_collection)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Мониторинг запущен. Сбор данных выполняется в фоновом режиме.'
        })
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({
            'success': False, 
            'message': f'Ошибка при запуске мониторинга: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
