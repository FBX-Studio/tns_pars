from config import Config
import re
import logging

logger = logging.getLogger(__name__)

class Moderator:
    def __init__(self):
        self.block_words = Config.BLOCK_WORDS
        self.negative_threshold = Config.NEGATIVE_THRESHOLD
        
        self.profanity_patterns = [
            r'\b(хуй|пизд|ебл|еба|еби|бля|сук|дура|дурак|идиот|мудак|гавно|говно|жоп)\w*\b',
            r'\b(fuck|shit|bitch|ass|damn|hell|crap|bastard)\w*\b'
        ]
        
        self.spam_patterns = [
            r'(https?://\S+){3,}',
            r'(\b\w+\b\s*){50,}',
            r'([А-ЯA-Z]{10,})',
            r'(!!!+|\.\.\.+){3,}'
        ]
    
    def check_profanity(self, text):
        """Check for profanity in text"""
        text_lower = text.lower()
        
        for word in self.block_words:
            if word.strip() and word.lower() in text_lower:
                return True, f"Blocked word detected: {word}"
        
        for pattern in self.profanity_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, "Profanity detected"
        
        return False, None
    
    def check_spam(self, text):
        """Check if text looks like spam"""
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                return True, "Spam pattern detected"
        
        if len(text) > 3000:
            return True, "Text too long"
        
        unique_chars = len(set(text.replace(' ', '')))
        if len(text) > 100 and unique_chars < 10:
            return True, "Low character diversity (possible spam)"
        
        return False, None
    
    def check_sentiment(self, sentiment_score):
        """Check if sentiment is too negative"""
        if sentiment_score < self.negative_threshold:
            return True, f"Highly negative sentiment: {sentiment_score:.2f}"
        return False, None
    
    def moderate(self, text, sentiment_score=None):
        """
        Moderate a review
        Returns: (status, reason, requires_manual_review)
        Status: 'approved', 'rejected', 'pending'
        """
        
        is_profane, profanity_reason = self.check_profanity(text)
        if is_profane:
            return 'rejected', profanity_reason, False
        
        is_spam, spam_reason = self.check_spam(text)
        if is_spam:
            return 'rejected', spam_reason, False
        
        if sentiment_score is not None:
            is_negative, sentiment_reason = self.check_sentiment(sentiment_score)
            if is_negative:
                return 'pending', sentiment_reason, True
        
        suspicious_phrases = [
            'займ', 'кредит', 'заработок', 'скидка', 'акция', 'промокод',
            'переходи по ссылке', 'жми на ссылку', 'регистрируйся',
            'loan', 'credit', 'discount', 'promo', 'click here'
        ]
        
        text_lower = text.lower()
        for phrase in suspicious_phrases:
            if phrase in text_lower and 'http' in text_lower:
                return 'pending', 'Suspicious promotional content', True
        
        return 'approved', None, False
    
    def moderate_batch(self, reviews):
        """Moderate multiple reviews"""
        results = []
        for review in reviews:
            text = review.get('text', '')
            sentiment_score = review.get('sentiment_score')
            
            status, reason, requires_manual = self.moderate(text, sentiment_score)
            
            results.append({
                'review_id': review.get('id'),
                'status': status,
                'reason': reason,
                'requires_manual_review': requires_manual
            })
        
        return results
