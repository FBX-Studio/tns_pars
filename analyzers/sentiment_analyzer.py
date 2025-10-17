import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer_type = None
        self.model = None
        self.tokenizer = None
        
        # Попытка 1: RuSentiment (Transformers + BERT)
        try:
            from transformers import pipeline
            logger.info("Attempting to load RuSentiment (Transformers)...")
            self.model = pipeline(
                "sentiment-analysis",
                model="blanchefort/rubert-base-cased-sentiment",
                truncation=True,
                max_length=512
            )
            self.analyzer_type = 'rusentiment'
            logger.info("✓ Sentiment analyzer initialized with RuSentiment (Transformers)")
            return
        except ImportError:
            logger.warning("Transformers not available, trying Dostoevsky...")
        except Exception as e:
            logger.warning(f"Could not load RuSentiment: {e}, trying Dostoevsky...")
        
        # Попытка 2: Dostoevsky
        try:
            from dostoevsky.tokenization import RegexTokenizer
            from dostoevsky.models import FastTextSocialNetworkModel
            
            self.tokenizer = RegexTokenizer()
            self.model = FastTextSocialNetworkModel(tokenizer=self.tokenizer)
            self.analyzer_type = 'dostoevsky'
            logger.info("✓ Sentiment analyzer initialized with Dostoevsky")
            return
        except ImportError:
            logger.warning("Dostoevsky not available, using rule-based analyzer")
        except Exception as e:
            logger.warning(f"Error initializing Dostoevsky: {e}, using rule-based analyzer")
        
        # Попытка 3: Rule-based (fallback)
        self.analyzer_type = 'rule_based'
        self._init_simple_analyzer()
        logger.info("✓ Sentiment analyzer initialized with Rule-Based method")
    
    def _init_simple_analyzer(self):
        """Инициализация простого анализатора на основе словарей"""
        # Позитивные слова и фразы
        self.positive_words = {
            # Общие позитивные
            'хорошо', 'отлично', 'прекрасно', 'замечательно', 'превосходно',
            'качественно', 'быстро', 'удобно', 'вежливо', 'профессионально',
            'спасибо', 'благодарю', 'благодарен', 'благодарна', 'признателен',
            'рекомендую', 'советую', 'довольны', 'доволен', 'довольна',
            'понравилось', 'понравился', 'понравилась', 'нравится',
            'ответственно', 'оперативно', 'надежно', 'эффективно',
            
            # Превосходные степени
            'молодцы', 'супер', 'классно', 'круто', 'здорово', 'чудесно',
            'великолепно', 'шикарно', 'восхитительно', 'изумительно',
            'потрясающе', 'фантастически', 'блестяще', 'идеально',
            
            # Позитивные действия
            'помогли', 'помогают', 'решили', 'исправили', 'устранили',
            'разобрались', 'поддержали', 'содействовали', 'выручили',
            'компетентно', 'грамотно', 'профессионально', 'квалифицированно',
            'своевременно', 'вовремя', 'срочно', 'незамедлительно',
            
            # Качество
            'качество', 'качественный', 'добротно', 'надежность',
            'стабильно', 'бесперебойно', 'исправно', 'четко',
            
            # Эмоции
            'радует', 'устраивает', 'восторг', 'восхищен', 'восхищена',
            'рад', 'рада', 'счастлив', 'счастлива', 'доволен', 'довольна',
            'удовлетворен', 'удовлетворена', 'приятно', 'комфортно',
            
            # Превосходство
            'лучшие', 'лучший', 'лучшая', 'лучше', 'первоклассный',
            'высококлассный', 'высокий уровень', 'на высоте',
            
            # Успех
            'успех', 'успешно', 'достижение', 'прогресс', 'улучшение',
            'результат', 'эффект', 'польза', 'выгода', 'преимущество',
            
            # Одобрение
            'одобряю', 'поддерживаю', 'согласен', 'правильно', 'верно',
            'справедливо', 'честно', 'корректно', 'адекватно',
            
            # Комплименты
            'умницы', 'молодец', 'респект', 'браво', 'аплодисменты',
            'достойный', 'достойная', 'похвально', 'заслуженно',
            
            # Фразы
            'всё хорошо', 'всё отлично', 'всё понравилось', 'всё устраивает',
            'отлично работает', 'хорошо работает', 'без проблем', 'без нареканий',
            'на высшем уровне', 'выше всяких похвал', 'не нарадуюсь',
            'большое спасибо', 'огромное спасибо', 'сердечное спасибо',
            
            # ========== СПЕЦИФИКА ДЛЯ ТНС ЭНЕРГО ==========
            
            # Подключение и обслуживание
            'быстро подключили', 'оперативно подключили', 'удобное подключение',
            'легко подключиться', 'простое оформление', 'быстрое оформление',
            'помогли подключить', 'помогли с документами', 'всё оформили',
            'без очередей', 'без бюрократии', 'без волокиты',
            
            # Показания и счета
            'удобная передача показаний', 'легко передать показания',
            'понятный счет', 'прозрачные начисления', 'корректный расчет',
            'правильный счет', 'без ошибок в счетах', 'точные показания',
            'удобный личный кабинет', 'работает личный кабинет',
            
            # Тарифы и оплата
            'выгодный тариф', 'справедливые цены', 'приемлемые цены',
            'удобная оплата', 'много способов оплаты', 'легко оплатить',
            'без комиссии', 'выгодные условия', 'гибкие тарифы',
            
            # Поддержка и консультации
            'отзывчивые сотрудники', 'вежливые операторы', 'компетентные специалисты',
            'помогли разобраться', 'подробно объяснили', 'всё объяснили',
            'быстро ответили', 'оперативный ответ', 'решили вопрос',
            'пошли навстречу', 'учли ситуацию', 'вошли в положение',
            
            # Надежность
            'стабильное электроснабжение', 'без перебоев', 'надежное снабжение',
            'всегда есть свет', 'не было отключений', 'стабильная подача',
            
            # Техподдержка
            'быстро устранили', 'оперативно починили', 'быстрый ремонт',
            'качественное обслуживание', 'профессиональный монтаж'
        }
        
        # Негативные слова и фразы
        self.negative_words = {
            # Общие негативные
            'плохо', 'ужасно', 'отвратительно', 'недовольны', 'недоволен', 'недовольна',
            'жалоба', 'претензия', 'рекламация', 'недовольство',
            'медленно', 'невежливо', 'некачественно', 'непрофессионально',
            
            # Проблемы
            'проблема', 'проблемы', 'ошибка', 'ошибки', 'сбой', 'авария',
            'неполадка', 'неисправность', 'дефект', 'брак', 'поломка',
            'не работает', 'не функционирует', 'сломалось', 'вышло из строя',
            
            # Разочарование
            'разочарован', 'разочарована', 'разочарование', 'огорчен', 'огорчена',
            'расстроен', 'расстроена', 'обижен', 'обижена', 'опечален',
            
            # Качество
            'хуже', 'худший', 'худшая', 'отвратительный', 'кошмарный',
            'никудышный', 'никакой', 'бездарный', 'паршивый',
            
            # Поведение
            'грубо', 'грубость', 'хамство', 'хамят', 'наглость', 'нагло',
            'невежливо', 'неуважительно', 'пренебрежительно', 'высокомерно',
            'арогантно', 'нахально', 'беспардонно',
            
            # Обман
            'обман', 'обманули', 'обманывают', 'мошенники', 'мошенничество',
            'развод', 'разводят', 'афера', 'жульничество', 'воры',
            'украли', 'кража', 'обирают', 'вымогательство',
            
            # Реакция
            'не рекомендую', 'не советую', 'ужас', 'кошмар', 'катастрофа',
            'безобразие', 'беспредел', 'бардак', 'хаос', 'произвол',
            'возмутительно', 'недопустимо', 'неприемлемо', 'скандал',
            
            # Время
            'задержка', 'задержки', 'опоздание', 'долго', 'очень долго',
            'медленно', 'тормозит', 'затягивают', 'волокита',
            'ждал', 'ждали', 'ожидание', 'простой', 'застой',
            
            # Отсутствие действий
            'не отвечают', 'не реагируют', 'игнорируют', 'не слушают',
            'не помогли', 'не решили', 'не исправили', 'не устранили',
            'не пришло', 'не пришёл', 'не появился', 'не явился',
            'отказали', 'отказались', 'отказ', 'отклонили',
            
            # Повреждения
            'испортили', 'сломали', 'повредили', 'разбили', 'уничтожили',
            'потеряли', 'утеряли', 'пропали', 'исчезли',
            
            # Эмоции
            'неприятно', 'противно', 'отвратительно', 'гадко', 'мерзко',
            'гнев', 'ярость', 'злость', 'ненависть', 'отвращение',
            'возмущен', 'возмущена', 'возмущение', 'негодование',
            'шок', 'шокирован', 'шокирована', 'ужаснулся', 'ужаснулась',
            
            # Юридическое
            'судиться', 'суд', 'иск', 'подам в суд', 'жалоба',
            'роспотребнадзор', 'прокуратура', 'полиция', 'жалуюсь', 'пожалуюсь',
            'заявление', 'обращение', 'инстанция',
            
            # Критика
            'критика', 'критикую', 'осуждаю', 'порицаю', 'обвиняю',
            'виноваты', 'виновен', 'виновна', 'ответственность', 'халатность',
            
            # Фразы
            'больше никогда', 'никому не советую', 'обходите стороной',
            'не связывайтесь', 'бегите отсюда', 'ни в коем случае',
            'полное разочарование', 'сплошное разочарование', 'одни проблемы',
            'сервис на нуле', 'никакого сервиса', 'нет сервиса',
            
            # ========== СПЕЦИФИКА ДЛЯ ТНС ЭНЕРГО ==========
            
            # Показания и счета (проблемы)
            'неправильный счет', 'ошибка в счете', 'неверные начисления',
            'завышенный счет', 'огромный счет', 'космический счет',
            'счет не сходится', 'неправильный расчет', 'ошибки в расчетах',
            'двойное начисление', 'лишние начисления', 'необоснованные начисления',
            'не принимают показания', 'не проходят показания', 'сбой при передаче',
            'не работает личный кабинет', 'глючит сайт', 'сайт не работает',
            
            # Отключения и перебои
            'постоянные отключения', 'частые отключения', 'отключили свет',
            'отключили электричество', 'нет света', 'без света', 'перебои со светом',
            'нестабильная подача', 'скачки напряжения', 'плохое напряжение',
            'отключили без предупреждения', 'внезапное отключение',
            'долго без света', 'часами без электричества',
            
            # Подключение (проблемы)
            'долго подключают', 'невозможно подключиться', 'отказали в подключении',
            'сложное подключение', 'много бумаг', 'куча документов',
            'бюрократия', 'волокита с подключением', 'тянут с подключением',
            'дорого подключение', 'завышенная цена подключения',
            
            # Тарифы и оплата (проблемы)
            'дорогой тариф', 'высокие тарифы', 'завышенные тарифы',
            'грабительские тарифы', 'дорогое электричество', 'растут цены',
            'постоянно дорожает', 'невыгодные условия', 'скрытые платежи',
            'непонятные комиссии', 'дополнительные сборы', 'навязывают услуги',
            
            # Служба поддержки (проблемы)
            'не дозвониться', 'не берут трубку', 'долго ждать на линии',
            'вечно занято', 'бросают трубку', 'не перезванивают',
            'грубые операторы', 'хамят по телефону', 'некомпетентные сотрудники',
            'не могут объяснить', 'путаются в показаниях', 'отправляют в офис',
            'гоняют по кабинетам', 'никто не знает', 'отфутболивают',
            
            # Техподдержка (проблемы)
            'долго устраняют', 'не приезжают', 'не реагируют на заявки',
            'игнорируют заявки', 'неделями ждать', 'месяцами не чинят',
            'некачественный ремонт', 'кое-как починили', 'опять сломалось',
            
            # Долги и отключения
            'отключили за долг', 'списали без спроса', 'принудительное списание',
            'угрожают отключением', 'шантажируют отключением',
            'незаконное отключение', 'отключили по ошибке',
            
            # Персонал
            'хамское отношение', 'наплевательское отношение', 'безразличие',
            'не хотят помогать', 'отмахиваются', 'посылают',
            
            # Общие претензии
            'монополисты', 'монополия', 'беспредел монополиста',
            'пользуются монополией', 'диктуют условия', 'навязывают',
            'нет альтернативы', 'некуда деваться', 'вынуждены терпеть'
        }
        
        # Усилители (увеличивают вес слова)
        self.intensifiers = {
            'очень', 'крайне', 'чрезвычайно', 'невероятно', 'абсолютно',
            'совершенно', 'полностью', 'максимально', 'предельно',
            'исключительно', 'чрезмерно', 'сверх', 'супер', 'ультра',
            'ужасно', 'страшно', 'жутко', 'дико', 'безумно', 'нереально',
            'весьма', 'более чем', 'слишком', 'излишне'
        }
        
        # Отрицания (инвертируют тональность)
        self.negations = {
            'не', 'ни', 'нет', 'без', 'никогда', 'никак', 'ничуть',
            'нисколько', 'отнюдь', 'вовсе не', 'далеко не'
        }
    
    def analyze(self, text):
        """Analyze sentiment of text"""
        if self.analyzer_type == 'rusentiment':
            return self._analyze_with_rusentiment(text)
        elif self.analyzer_type == 'dostoevsky':
            return self._analyze_with_dostoevsky(text)
        else:
            return self._analyze_simple(text)
    
    def _analyze_with_rusentiment(self, text):
        """Анализ с помощью RuSentiment (Transformers)"""
        if not text or not text.strip():
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'analyzer': 'rusentiment'
            }
        
        try:
            # Ограничиваем текст до 512 токенов
            text_truncated = text[:512]
            
            result = self.model(text_truncated)[0]
            
            # RuSentiment возвращает: LABEL_0 (negative), LABEL_1 (neutral), LABEL_2 (positive)
            label_mapping = {
                'LABEL_0': ('negative', -1.0),
                'LABEL_1': ('neutral', 0.0),
                'LABEL_2': ('positive', 1.0),
                'negative': ('negative', -1.0),
                'neutral': ('neutral', 0.0),
                'positive': ('positive', 1.0),
            }
            
            raw_label = result['label']
            score_value = result['score']  # уверенность от 0 до 1
            
            sentiment_label, base_score = label_mapping.get(raw_label, ('neutral', 0.0))
            
            # Итоговый score: направление * уверенность
            sentiment_score = base_score * score_value
            
            return {
                'sentiment_score': float(sentiment_score),
                'sentiment_label': sentiment_label,
                'confidence': float(score_value),
                'analyzer': 'rusentiment',
                'raw_result': result
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment with RuSentiment: {e}")
            # Fallback к rule-based
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
                    'analyzer': 'dostoevsky',
                    'raw_result': result
                }
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Dostoevsky: {e}")
        
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0,
            'analyzer': 'dostoevsky'
        }
    
    def _analyze_simple(self, text):
        """Улучшенный анализ на основе словарей с учетом усилителей"""
        if not text:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'analyzer': 'rule_based'
            }
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Подсчет с учетом усилителей
        positive_score = 0.0
        negative_score = 0.0
        
        for i, word in enumerate(words):
            # Проверяем усилитель перед словом
            multiplier = 1.0
            if i > 0 and words[i-1] in self.intensifiers:
                multiplier = 1.5
            
            # Проверяем полные фразы
            for phrase in self.positive_words:
                if phrase in text_lower:
                    positive_score += multiplier * len(phrase.split())
            
            for phrase in self.negative_words:
                if phrase in text_lower:
                    negative_score += multiplier * len(phrase.split())
        
        # Также проверяем отдельные слова
        for word in self.positive_words:
            if ' ' not in word and word in text_lower:
                positive_score += 1.0
        
        for word in self.negative_words:
            if ' ' not in word and word in text_lower:
                negative_score += 1.0
        
        # Нормализация
        total_words = max(len(words), 1)
        
        # Вычисляем итоговый score
        if positive_score > 0 or negative_score > 0:
            # Используем разницу, нормализованную на длину текста
            score = (positive_score - negative_score) / (total_words / 10.0)
            score = max(-1.0, min(1.0, score))  # Ограничиваем от -1 до 1
        else:
            score = 0.0
        
        # Определяем метку (более мягкие пороги)
        if score > 0.01:
            sentiment_label = 'positive'
        elif score < -0.01:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Уверенность зависит от силы сигнала
        confidence = min(abs(score), 1.0)
        
        return {
            'sentiment_score': float(score),
            'sentiment_label': sentiment_label,
            'confidence': float(confidence),
            'analyzer': 'rule_based',
            'debug': {
                'positive_score': positive_score,
                'negative_score': negative_score,
                'total_words': total_words
            }
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
    
    def get_analyzer_info(self):
        """Получить информацию о текущем анализаторе"""
        info = {
            'type': self.analyzer_type,
            'available': True
        }
        
        if self.analyzer_type == 'rusentiment':
            info.update({
                'name': 'RuSentiment (Transformers + BERT)',
                'model': 'blanchefort/rubert-base-cased-sentiment',
                'language': 'Russian',
                'description': 'Современная нейросетевая модель на основе BERT для анализа тональности русскоязычных текстов',
                'accuracy': 'Высокая (~85-90%)',
                'speed': 'Средняя (требует GPU для оптимальной скорости)'
            })
        elif self.analyzer_type == 'dostoevsky':
            info.update({
                'name': 'Dostoevsky',
                'model': 'FastText Social Network Model',
                'language': 'Russian',
                'description': 'Быстрая модель для анализа тональности текстов из социальных сетей',
                'accuracy': 'Хорошая (~80-85%)',
                'speed': 'Быстрая'
            })
        else:  # rule_based
            info.update({
                'name': 'Rule-Based Analyzer',
                'model': 'Dictionary-based with custom keywords',
                'language': 'Russian',
                'description': 'Анализатор на основе словарей с специализированными словами для энергетической отрасли',
                'accuracy': 'Средняя (~70-75%), но высокая для специфичных задач ТНС Энерго',
                'speed': 'Очень быстрая'
            })
        
        return info
