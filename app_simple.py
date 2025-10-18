"""
Упрощенная версия без SocketIO для диагностики
"""
from flask import Flask, render_template, jsonify
from models import db, Review
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
    """Простая главная страница"""
    try:
        total = Review.query.count()
        return f"""
        <html>
        <head><title>TNS Monitoring</title></head>
        <body>
        <h1>TNS Monitoring System</h1>
        <p>Total reviews: {total}</p>
        <p>Server is working!</p>
        <a href="/dashboard">Dashboard</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/api/test')
def api_test():
    """Тестовый API endpoint"""
    return jsonify({
        "status": "ok",
        "message": "API is working",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/dashboard')
def dashboard():
    """Dashboard страница"""
    try:
        with app.app_context():
            total_reviews = Review.query.count()
            
            today = datetime.utcnow().date()
            today_count = Review.query.filter(
                db.func.date(Review.collected_date) == today
            ).count()
            
            positive = Review.query.filter(Review.sentiment_label == 'positive').count()
            negative = Review.query.filter(Review.sentiment_label == 'negative').count()
            neutral = Review.query.filter(Review.sentiment_label == 'neutral').count()
            
            stats = {
                'total': total_reviews,
                'today': today_count,
                'positive': positive,
                'negative': negative,
                'neutral': neutral
            }
            
            return f"""
            <html>
            <head><title>Dashboard</title></head>
            <body>
            <h1>Dashboard</h1>
            <ul>
                <li>Total: {stats['total']}</li>
                <li>Today: {stats['today']}</li>
                <li>Positive: {stats['positive']}</li>
                <li>Negative: {stats['negative']}</li>
                <li>Neutral: {stats['neutral']}</li>
            </ul>
            <a href="/">Back</a>
            </body>
            </html>
            """
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    print("Starting simple server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)
