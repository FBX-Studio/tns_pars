"""
Анализатор тональности на основе Dostoevsky
Быстрая и точная модель для русского языка
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DostoevskyAnalyzer:
    """
    Анализатор тональности с использованием библиотеки Dostoevsky
    Оптимизирован для русскоязычных текстов из социальных сетей
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._init_model()
    
    def _init_model(self):
        """Инициализация модели Dostoevsky"""
        try:
            from dostoevsky.tokenization import RegexTokenizer
            from dostoevsky.models import FastTextSocialNetworkModel
            
            logger.info("[DOSTOEVSKY] Инициализация модели...")
            self.tokenizer = RegexTokenizer()
            self.model = FastTextSocialNetworkModel(tokenizer=self.tokenizer)
            logger.info("[DOSTOEVSKY] ✓ Модель инициализирована успешно")
            
        except ImportError as e:
            logger.error(f"[DOSTOEVSKY] Библиотека не установлена: {e}")
            logger.error("[DOSTOEVSKY] Установите: pip install dostoevsky")
            logger.error("[DOSTOEVSKY] Затем загрузите модели: python -m dostoevsky download fasttext-social-network-model")
            raise
        except Exception as e:
            logger.error(f"[DOSTOEVSKY] Ошибка инициализации: {e}")
            logger.error("[DOSTOEVSKY] Возможно, модели не загружены. Выполните: python -m dostoevsky download fasttext-social-network-model")
            raise
    
    def analyze(self, text: str) -> Dict:
        """
        Анализ тональности текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            {
                'sentiment_score': float (-1.0 до 1.0),
                'sentiment_label': str ('positive', 'negative', 'neutral'),
                'confidence': float (0.0 до 1.0),
                'details': {
                    'positive': float,
                    'negative': float,
                    'neutral': float,
                    'speech': float,
                    'skip': float
                }
            }
        """
        if not text or not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'details': {}
            }
        
        try:
            # Получаем предсказание от модели
            results = self.model.predict([text], k=2)
            
            if not results or len(results) == 0:
                logger.warning(f"[DOSTOEVSKY] Нет результатов для текста: {text[:50]}...")
                return self._get_neutral_result()
            
            result = results[0]
            
            # Извлекаем вероятности эмоций
            positive = result.get('positive', 0.0)
            negative = result.get('negative', 0.0)
            neutral = result.get('neutral', 0.0)
            speech = result.get('speech', 0.0)  # речь (дополнительная метрика)
            skip = result.get('skip', 0.0)  # пропуск (нерелевантный текст)
            
            # Вычисляем общий score от -1 до 1
            sentiment_score = positive - negative
            
            # Определяем метку тональности
            max_sentiment = max(positive, negative, neutral)
            
            if max_sentiment == positive and positive > 0.3:
                sentiment_label = 'positive'
                confidence = positive
            elif max_sentiment == negative and negative > 0.3:
                sentiment_label = 'negative'
                confidence = negative
            else:
                sentiment_label = 'neutral'
                confidence = neutral
            
            # Если skip высокий, снижаем уверенность
            if skip > 0.5:
                confidence = confidence * (1 - skip)
            
            return {
                'sentiment_score': float(sentiment_score),
                'sentiment_label': sentiment_label,
                'confidence': float(confidence),
                'details': {
                    'positive': float(positive),
                    'negative': float(negative),
                    'neutral': float(neutral),
                    'speech': float(speech),
                    'skip': float(skip)
                }
            }
            
        except Exception as e:
            logger.error(f"[DOSTOEVSKY] Ошибка анализа: {e}")
            return self._get_neutral_result()
    
    def _get_neutral_result(self) -> Dict:
        """Возвращает нейтральный результат при ошибках"""
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0,
            'details': {}
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Анализ нескольких текстов с оптимизацией
        
        Args:
            texts: Список текстов для анализа
            
        Returns:
            Список словарей с результатами анализа
        """
        if not texts:
            return []
        
        try:
            # Dostoevsky может обрабатывать батчи эффективно
            results = self.model.predict(texts, k=2)
            
            analyzed = []
            for i, result in enumerate(results):
                if not result:
                    analyzed.append(self._get_neutral_result())
                    continue
                
                positive = result.get('positive', 0.0)
                negative = result.get('negative', 0.0)
                neutral = result.get('neutral', 0.0)
                speech = result.get('speech', 0.0)
                skip = result.get('skip', 0.0)
                
                sentiment_score = positive - negative
                
                max_sentiment = max(positive, negative, neutral)
                
                if max_sentiment == positive and positive > 0.3:
                    sentiment_label = 'positive'
                    confidence = positive
                elif max_sentiment == negative and negative > 0.3:
                    sentiment_label = 'negative'
                    confidence = negative
                else:
                    sentiment_label = 'neutral'
                    confidence = neutral
                
                if skip > 0.5:
                    confidence = confidence * (1 - skip)
                
                analyzed.append({
                    'sentiment_score': float(sentiment_score),
                    'sentiment_label': sentiment_label,
                    'confidence': float(confidence),
                    'details': {
                        'positive': float(positive),
                        'negative': float(negative),
                        'neutral': float(neutral),
                        'speech': float(speech),
                        'skip': float(skip)
                    }
                })
            
            return analyzed
            
        except Exception as e:
            logger.error(f"[DOSTOEVSKY] Ошибка батч-анализа: {e}")
            return [self._get_neutral_result() for _ in texts]
    
    def is_available(self) -> bool:
        """Проверка доступности модели"""
        return self.model is not None
    
    def get_info(self) -> Dict:
        """Информация о модели"""
        return {
            'name': 'Dostoevsky',
            'version': '0.6+',
            'language': 'Russian',
            'type': 'FastText Social Network Model',
            'available': self.is_available(),
            'description': 'Быстрая и точная модель для анализа тональности русскоязычных текстов из соцсетей'
        }
