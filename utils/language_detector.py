import re

class LanguageDetector:
    def __init__(self):
        self.cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
        self.latin_pattern = re.compile(r'[a-zA-Z]')
    
    def is_russian(self, text):
        if not text or len(text.strip()) < 3:
            return True
        
        cyrillic_count = len(self.cyrillic_pattern.findall(text))
        latin_count = len(self.latin_pattern.findall(text))
        
        total_letters = cyrillic_count + latin_count
        
        if total_letters == 0:
            return True
        
        cyrillic_ratio = cyrillic_count / total_letters
        
        return cyrillic_ratio > 0.5
    
    def detect_language(self, text):
        if self.is_russian(text):
            return 'ru'
        return 'other'
