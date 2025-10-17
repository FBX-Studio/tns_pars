"""
Улучшенное Flask приложение с WebSocket поддержкой
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from models import db, Review, MonitoringLog
from config import Config
from datetime import datetime, timedelta
import logging
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Глобальное состояние мониторинга
monitoring_state = {
    'is_running': False,
    'stop_requested': False,
    'progress': {},
    'results': {},
    'start_time': None
}

with app.app_context():
    db.create_all()

# ==================== ГЛАВНАЯ СТРАНИЦА ====================
@app.route('/')
def index():
    """Современный Dashboard"""
    with app.app_context():
        total_reviews = Review.query.count()
        
        today = datetime.utcnow().date()
        today_count = Review.query.filter(
            db.func.date(Review.collected_date) == today
        ).count()
        
        # Вчера для расчета изменения
        yesterday = today - timedelta(days=1)
        yesterday_count = Review.query.filter(
            db.func.date(Review.collected_date) == yesterday
        ).count()
        
        # Изменение за 24 часа
        today_change = today_count - yesterday_count
        
        week_ago = today - timedelta(days=7)
        week_count = Review.query.filter(
            db.func.date(Review.collected_date) >= week_ago
        ).count()
        
        positive = Review.query.filter(Review.sentiment_label == 'positive').count()
        negative = Review.query.filter(Review.sentiment_label == 'negative').count()
        neutral = Review.query.filter(Review.sentiment_label == 'neutral').count()
        
        # Расчет процентов
        positive_percent = round((positive / total_reviews * 100) if total_reviews > 0 else 0, 1)
        negative_percent = round((negative / total_reviews * 100) if total_reviews > 0 else 0, 1)
        neutral_percent = round((neutral / total_reviews * 100) if total_reviews > 0 else 0, 1)
        
        by_source = db.session.query(
            Review.source, 
            db.func.count(Review.id)
        ).group_by(Review.source).all()
        
        recent_reviews = Review.query.order_by(
            Review.collected_date.desc()
        ).limit(10).all()
        
        last_monitoring = MonitoringLog.query.order_by(
            MonitoringLog.started_at.desc()
        ).first()
        
        stats = {
            'total': total_reviews,
            'today': today_count,
            'today_change': today_change,
            'week': week_count,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_percent': positive_percent,
            'negative_percent': negative_percent,
            'neutral_percent': neutral_percent,
            'by_source': dict(by_source),
            'last_monitoring': last_monitoring,
            'is_running': monitoring_state['is_running']
        }
        
        return render_template('dashboard_enhanced.html', 
                             stats=stats, 
                             reviews=recent_reviews,
                             config=Config)

# ==================== СТРАНИЦА ОТЗЫВОВ ====================
@app.route('/reviews')
def reviews_list():
    """Страница со списком отзывов и фильтрами"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    source = request.args.get('source', '')
    sentiment = request.args.get('sentiment', '')
    time_filter = request.args.get('time', 'all')
    search = request.args.get('search', '')
    kind = request.args.get('kind', 'all')
    
    query = Review.query
    
    # Фильтр по источнику
    if source:
        query = query.filter_by(source=source)
    
    # Фильтр по тональности
    if sentiment:
        query = query.filter_by(sentiment_label=sentiment)

    # Фильтр по типу записи
    if kind == 'comments':
        query = query.filter(Review.is_comment.is_(True))
    elif kind == 'posts':
        query = query.filter((Review.is_comment.is_(False)) | (Review.is_comment.is_(None)))
    
    # Фильтр по времени
    now = datetime.utcnow()
    if time_filter == 'hour':
        query = query.filter(Review.collected_date >= now - timedelta(hours=1))
    elif time_filter == 'day':
        query = query.filter(Review.collected_date >= now - timedelta(days=1))
    elif time_filter == 'week':
        query = query.filter(Review.collected_date >= now - timedelta(weeks=1))
    elif time_filter == 'month':
        query = query.filter(Review.collected_date >= now - timedelta(days=30))
    elif time_filter == 'year':
        query = query.filter(Review.collected_date >= now - timedelta(days=365))
    
    # Поиск по тексту
    if search:
        query = query.filter(Review.text.contains(search))
    
    pagination = query.order_by(Review.collected_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('reviews_enhanced.html', 
                         pagination=pagination,
                         source=source,
                         sentiment=sentiment,
                         time_filter=time_filter,
                         search=search,
                         kind=kind)

# ==================== МОНИТОРИНГ ====================
@app.route('/monitoring')
def monitoring():
    """Страница мониторинга с историей"""
    logs = MonitoringLog.query.order_by(
        MonitoringLog.started_at.desc()
    ).limit(50).all()
    
    return render_template('monitoring_enhanced.html', 
                         logs=logs, 
                         config=Config,
                         is_running=monitoring_state['is_running'])

# ==================== НАСТРОЙКИ ====================
@app.route('/settings')
def settings():
    """Страница настроек"""
    return render_template('settings.html', config=Config)

# ==================== ПОМОЩЬ ====================
@app.route('/help')
def help_page():
    """Страница с инструкцией"""
    return render_template('help.html')

# ==================== API ====================
@app.route('/api/stats')
def api_stats():
    """API статистики"""
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

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Запуск асинхронного мониторинга с прогрессом"""
    if monitoring_state['is_running']:
        return jsonify({
            'success': False,
            'message': 'Мониторинг уже запущен'
        }), 400
    
    try:
        # Получаем период из запроса
        data = request.get_json() or {}
        period = data.get('period', 'day')  # По умолчанию - день
        
        from async_monitor_websocket import AsyncReviewMonitorWebSocket
        
        monitoring_state['is_running'] = True
        monitoring_state['progress'] = {}
        monitoring_state['results'] = {}
        monitoring_state['start_time'] = datetime.utcnow()
        monitoring_state['period'] = period  # Сохраняем выбранный период
        
        monitor = AsyncReviewMonitorWebSocket(socketio, period=period)
        
        thread = threading.Thread(target=monitor.run_collection_sync)
        thread.daemon = True
        thread.start()
        
        period_text = {
            'hour': 'за последний час',
            'day': 'за последний день', 
            'week': 'за последнюю неделю',
            'month': 'за последний месяц',
            'all': 'за всё время'
        }.get(period, 'за выбранный период')
        
        return jsonify({
            'success': True,
            'message': f'Мониторинг запущен {period_text}. Следите за прогрессом в реальном времени.'
        })
    except Exception as e:
        monitoring_state['is_running'] = False
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

@app.route('/api/monitoring/status')
def monitoring_status():
    """Статус текущего мониторинга"""
    return jsonify({
        'is_running': monitoring_state['is_running'],
        'progress': monitoring_state['progress'],
        'results': monitoring_state['results'],
        'start_time': monitoring_state['start_time'].isoformat() if monitoring_state['start_time'] else None
    })

@app.route('/api/database/clear', methods=['POST'])
def clear_database():
    """Очистка базы данных"""
    try:
        data = request.get_json()
        clear_type = data.get('type', 'all')
        
        if clear_type == 'reviews':
            count = Review.query.count()
            Review.query.delete()
            message = f'Удалено отзывов: {count}'
        elif clear_type == 'logs':
            count = MonitoringLog.query.count()
            MonitoringLog.query.delete()
            message = f'Удалено логов: {count}'
        elif clear_type == 'all':
            reviews_count = Review.query.count()
            logs_count = MonitoringLog.query.count()
            Review.query.delete()
            MonitoringLog.query.delete()
            message = f'Удалено отзывов: {reviews_count}, логов: {logs_count}'
        else:
            return jsonify({'success': False, 'message': 'Неверный тип очистки'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing database: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Остановка мониторинга"""
    if not monitoring_state['is_running']:
        return jsonify({
            'success': False,
            'message': 'Мониторинг не запущен'
        }), 400
    
    # Помечаем что нужно остановить
    monitoring_state['is_running'] = False
    monitoring_state['stop_requested'] = True
    
    return jsonify({
        'success': True,
        'message': 'Запрос на остановку отправлен'
    })

@app.route('/api/reviews/filtered', methods=['GET'])
def get_filtered_reviews():
    """Получение отзывов с фильтрацией"""
    time_filter = request.args.get('time', 'all')
    source = request.args.get('source', '')
    sentiment = request.args.get('sentiment', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = Review.query
    
    # Фильтр по времени
    now = datetime.utcnow()
    if time_filter == 'hour':
        query = query.filter(Review.collected_date >= now - timedelta(hours=1))
    elif time_filter == 'day':
        query = query.filter(Review.collected_date >= now - timedelta(days=1))
    elif time_filter == 'week':
        query = query.filter(Review.collected_date >= now - timedelta(weeks=1))
    elif time_filter == 'month':
        query = query.filter(Review.collected_date >= now - timedelta(days=30))
    elif time_filter == 'year':
        query = query.filter(Review.collected_date >= now - timedelta(days=365))
    
    # Дополнительные фильтры
    if source:
        query = query.filter_by(source=source)
    if sentiment:
        query = query.filter_by(sentiment_label=sentiment)
    
    total = query.count()
    reviews = query.order_by(Review.collected_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': reviews.pages,
        'reviews': [r.to_dict() for r in reviews.items]
    })

@app.route('/api/settings/save', methods=['POST'])
def save_settings():
    """Сохранение настроек в .env файл"""
    try:
        import os
        from pathlib import Path
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Нет данных для сохранения'}), 400
        
        # Путь к .env файлу
        env_path = Path(__file__).parent / '.env'
        
        # Читаем существующий .env
        env_vars = {}
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Обновляем значения
        for key, value in data.items():
            if value:  # Только если значение не пустое
                env_vars[key] = value
        
        # Записываем обратно
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('# Настройки приложения\n')
            f.write('# Автоматически сгенерировано через веб-интерфейс\n\n')
            
            # Группируем по категориям
            categories = {
                'Flask': ['FLASK_HOST', 'FLASK_PORT', 'FLASK_DEBUG', 'FLASK_SECRET_KEY'],
                'Database': ['DATABASE_URL'],
                'VK': ['VK_ACCESS_TOKEN', 'VK_GROUP_IDS'],
                'Telegram': ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_CHANNELS'],
                'Keywords': ['COMPANY_KEYWORDS', 'GEO_KEYWORDS'],
                'Proxy': ['USE_TOR', 'TOR_PROXY', 'HTTP_PROXY', 'HTTPS_PROXY', 'SOCKS_PROXY'],
                'Other': []
            }
            
            written_keys = set()
            
            for category, keys in categories.items():
                if category == 'Other':
                    continue
                
                category_vars = {k: v for k, v in env_vars.items() if k in keys}
                if category_vars:
                    f.write(f'# {category}\n')
                    for key, value in category_vars.items():
                        f.write(f'{key}={value}\n')
                        written_keys.add(key)
                    f.write('\n')
            
            # Записываем остальные переменные
            other_vars = {k: v for k, v in env_vars.items() if k not in written_keys}
            if other_vars:
                f.write('# Other\n')
                for key, value in other_vars.items():
                    f.write(f'{key}={value}\n')
        
        logger.info('Settings saved successfully')
        
        return jsonify({
            'success': True,
            'message': 'Настройки успешно сохранены'
        })
    
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

# ==================== WebSocket СОБЫТИЯ ====================
@socketio.on('connect')
def handle_connect(auth=None):
    """Клиент подключился"""
    logger.info('Client connected')
    # Сериализуем datetime в ISO формат для JSON
    state_copy = monitoring_state.copy()
    if state_copy.get('start_time'):
        state_copy['start_time'] = state_copy['start_time'].isoformat()
    emit('status', state_copy)

@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключился"""
    logger.info('Client disconnected')

@socketio.on('request_status')
def handle_status_request():
    """Запрос статуса"""
    state_copy = monitoring_state.copy()
    if state_copy.get('start_time'):
        state_copy['start_time'] = state_copy['start_time'].isoformat()
    emit('status', state_copy)

# ==================== API ДЛЯ КОММЕНТАРИЕВ ====================

@app.route('/api/post/<int:post_id>/comments')
def get_post_comments_api(post_id):
    """Получить комментарии к посту"""
    try:
        from utils.comment_helper import CommentHelper
        
        limit = int(request.args.get('limit', 100))
        comments = CommentHelper.get_post_comments(post_id, limit=limit)
        stats = CommentHelper.get_comment_stats(post_id)
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'count': len(comments),
            'comments': [c.to_dict() for c in comments],
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting comments for post {post_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/with-comments')
def get_posts_with_comments_api():
    """Получить посты с комментариями"""
    try:
        from utils.comment_helper import CommentHelper
        
        source = request.args.get('source')
        limit = int(request.args.get('limit', 50))
        
        posts_data = CommentHelper.get_posts_with_comments(source, limit)
        
        result = []
        for item in posts_data:
            result.append({
                'post': item['post'].to_dict(),
                'comments': [c.to_dict() for c in item['comments']],
                'stats': item['stats']
            })
        
        return jsonify({
            'success': True,
            'count': len(result),
            'posts': result
        })
    except Exception as e:
        logger.error(f"Error getting posts with comments: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/without-comments')
def get_posts_without_comments_api():
    """Посты без комментариев (для дополнительного парсинга)"""
    try:
        from utils.comment_helper import CommentHelper
        
        source = request.args.get('source')
        limit = int(request.args.get('limit', 100))
        
        posts = CommentHelper.get_posts_without_comments(source, limit)
        
        return jsonify({
            'success': True,
            'count': len(posts),
            'posts': [p.to_dict() for p in posts]
        })
    except Exception as e:
        logger.error(f"Error getting posts without comments: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/comments')
def get_comments_stats_api():
    """Общая статистика комментариев"""
    try:
        from utils.comment_helper import CommentHelper
        
        total_comments = CommentHelper.get_all_comments_count()
        total_posts = Review.query.filter_by(is_comment=False).count()
        
        # Статистика по источникам
        sources_stats = db.session.query(
            Review.source,
            db.func.count(Review.id).label('count')
        ).filter_by(is_comment=True).group_by(Review.source).all()
        
        # Статистика по тональности комментариев
        sentiment_stats = db.session.query(
            Review.sentiment_label,
            db.func.count(Review.id).label('count')
        ).filter_by(is_comment=True).group_by(Review.sentiment_label).all()
        
        return jsonify({
            'success': True,
            'total_comments': total_comments,
            'total_posts': total_posts,
            'avg_comments_per_post': round(total_comments / total_posts, 2) if total_posts > 0 else 0,
            'by_source': {source: count for source, count in sources_stats},
            'by_sentiment': {label or 'neutral': count for label, count in sentiment_stats}
        })
    except Exception as e:
        logger.error(f"Error getting comments stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Временно отключаем debug для быстрого запуска
    # Используем порт 5001 чтобы избежать конфликтов
    socketio.run(app, 
                host='0.0.0.0', 
                port=5001, 
                debug=False,
                allow_unsafe_werkzeug=True)
