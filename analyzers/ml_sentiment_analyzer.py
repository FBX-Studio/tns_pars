"""
Анализатор тональности с использованием ML моделей
Поддерживает несколько моделей на выбор
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MLSentimentAnalyzer:
    """
    Анализатор тональности с поддержкой нескольких ML моделей:
    1. RuBERT (лучшая точность)
    2. Dostoevsky (быстрая)
    3. VADER (для английского)
    4. TextBlob (простая)
    5. Словарный (fallback)
    """
    
    def __init__(self, model_type='auto'):
        """
        model_type: 'rubert', 'dostoevsky', 'vader', 'textblob', 'dictionary', 'auto'
        auto - автоматический выбор лучшей доступной модели
        """
        self.model_type = model_type
        self.model = None
        self.tokenizer = None
        
        if model_type == 'auto':
            self._init_best_available()
        else:
            self._init_model(model_type)
    
    def _init_best_available(self):
        """Инициализация лучшей доступной модели"""
        models_priority = ['rubert', 'dostoevsky', 'vader', 'textblob', 'dictionary']
        
        for model_type in models_priority:
            try:
                self._init_model(model_type)
                logger.info(f"[SENTIMENT] Инициализирована модель: {model_type}")
                return
            except Exception as e:
                logger.debug(f"[SENTIMENT] {model_type} недоступна: {e}")
                continue
        
        # Fallback на словарь
        self._init_model('dictionary')
    
    def _init_model(self, model_type):
        """Инициализация конкретной модели"""
        if model_type == 'rubert':
            self._init_rubert()
        elif model_type == 'dostoevsky':
            self._init_dostoevsky()
        elif model_type == 'vader':
            self._init_vader()
        elif model_type == 'textblob':
            self._init_textblob()
        elif model_type == 'dictionary':
            self._init_dictionary()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _init_rubert(self):
        """Инициализация RuBERT (лучшая точность для русского)"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            model_name = "blanchefort/rubert-base-cased-sentiment"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model_type = 'rubert'
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            
            logger.info("[SENTIMENT] ✓ RuBERT инициализирован")
        except ImportError:
            raise ImportError("transformers и torch не установлены. Установите: pip install transformers torch")
        except Exception as e:
            raise Exception(f"Ошибка инициализации RuBERT: {e}")
    
    def _init_dostoevsky(self):
        """Инициализация Dostoevsky (быстрая модель)"""
        try:
            from dostoevsky.tokenization import RegexTokenizer
            from dostoevsky.models import FastTextSocialNetworkModel
            
            self.tokenizer = RegexTokenizer()
            self.model = FastTextSocialNetworkModel(tokenizer=self.tokenizer)
            self.model_type = 'dostoevsky'
            
            logger.info("[SENTIMENT] ✓ Dostoevsky инициализирован")
        except ImportError:
            raise ImportError("dostoevsky не установлен. Установите: pip install dostoevsky")
        except Exception as e:
            raise Exception(f"Ошибка инициализации Dostoevsky: {e}")
    
    def _init_vader(self):
        """Инициализация VADER (хорош для соцсетей)"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            
            self.model = SentimentIntensityAnalyzer()
            self.model_type = 'vader'
            
            logger.info("[SENTIMENT] ✓ VADER инициализирован")
        except ImportError:
            raise ImportError("vaderSentiment не установлен. Установите: pip install vaderSentiment")
        except Exception as e:
            raise Exception(f"Ошибка инициализации VADER: {e}")
    
    def _init_textblob(self):
        """Инициализация TextBlob (простая модель)"""
        try:
            from textblob import TextBlob
            
            self.model = TextBlob
            self.model_type = 'textblob'
            
            logger.info("[SENTIMENT] ✓ TextBlob инициализирован")
        except ImportError:
            raise ImportError("textblob не установлен. Установите: pip install textblob")
        except Exception as e:
            raise Exception(f"Ошибка инициализации TextBlob: {e}")
    
    def _init_dictionary(self):
        """Инициализация словарного анализатора (fallback)"""
        self.model_type = 'dictionary'
        
        self.positive_words = {
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'превосходно',
            'качественно', 'быстро', 'удобно', 'вежливо', 'профессионально',
            'спасибо', 'благодарю', 'рекомендую', 'довольны', 'понравилось',
            'ответственно', 'оперативно', 'надежно', 'эффективно', 'молодцы',
            'супер', 'класс', 'отлично', 'здорово', 'круто'
        }
        
        self.negative_words = {
            'плохо', 'ужасно', 'отвратительно', 'недовольны', 'жалоба',
            'медленно', 'невежливо', 'некачественно', 'проблема', 'ошибка',
            'не работает', 'не могу', 'разочарован', 'хуже', 'грубо',
            'обман', 'мошенники', 'развод', 'не рекомендую', 'ужас',
            'кошмар', 'безобразие', 'возмутительно', 'беспредел'
        }
        
        logger.info("[SENTIMENT] ✓ Словарный анализатор инициализирован")
    
    def analyze(self, text: str) -> Dict:
        """
        Анализ тональности текста
        
        Returns:
            {
                'sentiment_score': float (-1.0 до 1.0),
                'sentiment_label': str ('positive', 'negative', 'neutral'),
                'confidence': float (0.0 до 1.0),
                'model': str (название модели)
            }
        """
        if not text or not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'model': self.model_type
            }
        
        if self.model_type == 'rubert':
            return self._analyze_rubert(text)
        elif self.model_type == 'dostoevsky':
            return self._analyze_dostoevsky(text)
        elif self.model_type == 'vader':
            return self._analyze_vader(text)
        elif self.model_type == 'textblob':
            return self._analyze_textblob(text)
        elif self.model_type == 'dictionary':
            return self._analyze_dictionary(text)
        else:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'model': 'unknown'
            }
    
    def _analyze_rubert(self, text: str) -> Dict:
        """Анализ с помощью RuBERT"""
        import torch
        
        try:
            # Токенизация
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Предсказание
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # RuBERT модель: 0=negative, 1=neutral, 2=positive
            scores = predictions[0].cpu().numpy()
            
            negative_score = float(scores[0])
            neutral_score = float(scores[1])
            positive_score = float(scores[2])
            
            # Вычисляем общий score от -1 до 1
            sentiment_score = positive_score - negative_score
            
            # Определяем label
            if positive_score > negative_score and positive_score > neutral_score:
                sentiment_label = 'positive'
                confidence = positive_score
            elif negative_score > positive_score and negative_score > neutral_score:
                sentiment_label = 'negative'
                confidence = negative_score
            else:
                sentiment_label = 'neutral'
                confidence = neutral_score
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'model': 'rubert',
                'details': {
                    'positive': positive_score,
                    'neutral': neutral_score,
                    'negative': negative_score
                }
            }
            
        except Exception as e:
            logger.error(f"[SENTIMENT] Ошибка RuBERT: {e}")
            return self._analyze_dictionary(text)
    
    def _analyze_dostoevsky(self, text: str) -> Dict:
        """Анализ с помощью Dostoevsky"""
        try:
            results = self.model.predict([text], k=1)
            if results and len(results) > 0:
                result = results[0]
                
                positive = result.get('positive', 0.0)
                negative = result.get('negative', 0.0)
                neutral = result.get('neutral', 0.0)
                
                sentiment_score = positive - negative
                
                if positive > negative and positive > neutral:
                    sentiment_label = 'positive'
                    confidence = positive
                elif negative > positive and negative > neutral:
                    sentiment_label = 'negative'
                    confidence = negative
                else:
                    sentiment_label = 'neutral'
                    confidence = neutral
                
                return {
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'confidence': confidence,
                    'model': 'dostoevsky'
                }
        except Exception as e:
            logger.error(f"[SENTIMENT] Ошибка Dostoevsky: {e}")
        
        return self._analyze_dictionary(text)
    
    def _analyze_vader(self, text: str) -> Dict:
        """Анализ с помощью VADER"""
        try:
            scores = self.model.polarity_scores(text)
            
            sentiment_score = scores['compound']
            confidence = abs(sentiment_score)
            
            if sentiment_score >= 0.05:
                sentiment_label = 'positive'
            elif sentiment_score <= -0.05:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'confidence': confidence,
                'model': 'vader'
            }
        except Exception as e:
            logger.error(f"[SENTIMENT] Ошибка VADER: {e}")
        
        return self._analyze_dictionary(text)
    
    def _analyze_textblob(self, text: str) -> Dict:
        """Анализ с помощью TextBlob"""
        try:
            blob = self.model(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                sentiment_label = 'positive'
            elif polarity < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': polarity,
                'sentiment_label': sentiment_label,
                'confidence': abs(polarity),
                'model': 'textblob'
            }
        except Exception as e:
            logger.error(f"[SENTIMENT] Ошибка TextBlob: {e}")
        
        return self._analyze_dictionary(text)
    
    def _analyze_dictionary(self, text: str) -> Dict:
        """Простой анализ на основе словарей"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        total_words = len(text_lower.split())
        if total_words == 0:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'model': 'dictionary'
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
            'confidence': confidence,
            'model': 'dictionary'
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Анализ нескольких текстов"""
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict:
        """Информация о текущей модели"""
        return {
            'model_type': self.model_type,
            'model_loaded': self.model is not None,
            'description': self._get_model_description()
        }
    
    def _get_model_description(self) -> str:
        """Описание текущей модели"""
        descriptions = {
            'rubert': 'RuBERT - трансформер, лучшая точность для русского языка',
            'dostoevsky': 'Dostoevsky - FastText модель, быстрая и точная',
            'vader': 'VADER - хорошо работает с текстами из соцсетей',
            'textblob': 'TextBlob - простая модель, базовый анализ',
            'dictionary': 'Словарный анализатор - быстрый, но менее точный'
        }
        return descriptions.get(self.model_type, 'Неизвестная модель')
