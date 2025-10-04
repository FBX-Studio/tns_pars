import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        try:
            # Попытка использовать dostoevsky
            from dostoevsky.tokenization import RegexTokenizer
            from dostoevsky.models import FastTextSocialNetworkModel
            
            self.tokenizer = RegexTokenizer()
            self.model = FastTextSocialNetworkModel(tokenizer=self.tokenizer)
            self.use_dostoevsky = True
            logger.info("Sentiment analyzer initialized with Dostoevsky")
        except ImportError:
            logger.warning("Dostoevsky not available, using simple rule-based analyzer")
            self.use_dostoevsky = False
            self._init_simple_analyzer()
        except Exception as e:
            logger.error(f"Error initializing Dostoevsky: {e}, falling back to simple analyzer")
            self.use_dostoevsky = False
            self._init_simple_analyzer()
    
    def _init_simple_analyzer(self):
        """Инициализация простого анализатора на основе словарей"""
        self.positive_words = {
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'превосходно',
            'качественно', 'быстро', 'удобно', 'вежливо', 'профессионально',
            'спасибо', 'благодарю', 'рекомендую', 'довольны', 'понравилось',
            'ответственно', 'оперативно', 'надежно', 'эффективно'
        }
        
        self.negative_words = {
            'плохо', 'ужасно', 'отвратительно', 'недовольны', 'жалоба',
            'медленно', 'невежливо', 'некачественно', 'проблема', 'ошибка',
            'не работает', 'не могу', 'разочарован', 'хуже', 'грубо',
            'обман', 'мошенники', 'развод', 'не рекомендую', 'ужас'
        }
    
    def analyze(self, text):
        """Analyze sentiment of text"""
        if self.use_dostoevsky:
            return self._analyze_with_dostoevsky(text)
        else:
            return self._analyze_simple(text)
    
    def _analyze_with_dostoevsky(self, text):
        """Анализ с помощью Dostoevsky"""
        try:
            results = self.model.predict([text], k=1)
            if results and len(results) > 0:
                result = results[0]
                
                sentiment_label = 'neutral'
                sentiment_score = 0.0
                
                if 'positive' in result:
                    sentiment_label = 'positive'
                    sentiment_score = result['positive']
                elif 'negative' in result:
                    sentiment_label = 'negative'
                    sentiment_score = -result['negative']
                elif 'neutral' in result:
                    sentiment_label = 'neutral'
                    sentiment_score = 0.0
                
                return {
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'confidence': max(result.values()) if result else 0.0,
                    'raw_result': result
                }
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Dostoevsky: {e}")
        
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0
        }
    
    def _analyze_simple(self, text):
        """Простой анализ на основе словарей"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        total_words = len(text_lower.split())
        if total_words == 0:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0
            }
        
        score = (positive_count - negative_count) / max(total_words, 1)
        
        if score > 0.05:
            sentiment_label = 'positive'
        elif score < -0.05:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        confidence = min(abs(score) * 10, 1.0)
        
        return {
            'sentiment_score': score,
            'sentiment_label': sentiment_label,
            'confidence': confidence
        }
    
    def extract_keywords(self, text, top_n=5):
        """Extract key words and phrases from text"""
        text = text.lower()
        
        text = re.sub(r'[^\w\s\u0400-\u04FF]', ' ', text)
        
        stop_words = {
            'в', 'и', 'на', 'с', 'по', 'к', 'от', 'за', 'из', 'до', 'у', 'о', 'об',
            'что', 'это', 'как', 'так', 'а', 'но', 'же', 'бы', 'был', 'была', 'было',
            'были', 'есть', 'был', 'была', 'для', 'при', 'не', 'мы', 'вы', 'они', 'он',
            'она', 'оно', 'я', 'ты', 'меня', 'тебя', 'его', 'её', 'их', 'нас', 'вас',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been', 'being'
        }
        
        words = text.split()
        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        word_counts = Counter(filtered_words)
        keywords = [word for word, count in word_counts.most_common(top_n)]
        
        return keywords
    
    def analyze_batch(self, texts):
        """Analyze multiple texts"""
        results = []
        for text in texts:
            sentiment = self.analyze(text)
            keywords = self.extract_keywords(text)
            results.append({
                'sentiment': sentiment,
                'keywords': keywords
            })
        return results
