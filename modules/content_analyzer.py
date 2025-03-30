#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تحليل المحتوى - مسؤولة عن تحليل النص والكلمات المفتاحية في صفحات الويب

تقوم هذه الوحدة بتحليل المحتوى النصي للصفحة، وتقييم الكلمات المفتاحية وكثافتها،
وقابلية القراءة، وجودة المحتوى.
"""

import re
import logging
from collections import Counter
from bs4 import BeautifulSoup
import spacy
from urllib.parse import urlparse

class ContentAnalyzer:
    """
    محلل المحتوى والكلمات المفتاحية للصفحات
    """
    
    def __init__(self, language='ar', min_words=300, use_spacy=True):
        """
        تهيئة محلل المحتوى
        
        Args:
            language (str): لغة المحتوى الافتراضية ('ar' للعربية، 'en' للإنجليزية)
            min_words (int): الحد الأدنى لعدد الكلمات المستحسن
            use_spacy (bool): استخدام spaCy للتحليل اللغوي (إذا كان متاحًا)
        """
        self.language = language
        self.min_words = min_words
        self.use_spacy = use_spacy
        self.logger = logging.getLogger('rseo.content_analyzer')
        
        # قائمة الكلمات الشائعة التي يجب استبعادها من تحليل الكلمات المفتاحية
        self.arabic_stopwords = set([
            'من', 'الى', 'إلى', 'عن', 'على', 'في', 'حول', 'حتى', 'اذا', 'إذا', 'لكن',
            'و', 'ف', 'ثم', 'أو', 'أم', 'لا', 'ما', 'هذا', 'هذه', 'ذلك', 'تلك', 'هناك',
            'كان', 'كانت', 'يكون', 'تكون', 'اي', 'أي', 'كل', 'بعض', 'غير', 'بين', 
            'منذ', 'عند', 'عندما', 'قد', 'لقد', 'قبل', 'بعد', 'خلال', 'تحت', 'فوق',
            'هو', 'هي', 'انت', 'أنت', 'انا', 'أنا', 'نحن', 'انتم', 'أنتم', 'هم', 'هن'
        ])
        
        self.english_stopwords = set([
            'the', 'and', 'a', 'in', 'to', 'of', 'is', 'that', 'for', 'on', 'it', 'with',
            'as', 'was', 'be', 'by', 'at', 'this', 'are', 'or', 'an', 'but', 'not', 'they',
            'he', 'she', 'we', 'you', 'i', 'from', 'have', 'has', 'had', 'do', 'does', 'did',
            'can', 'could', 'will', 'would', 'should', 'if', 'then', 'there', 'when', 'what',
            'where', 'which', 'who', 'whom', 'whose', 'why', 'how'
        ])
        
        # محاولة تحميل نموذج spaCy إذا كان مطلوبًا
        self.nlp = None
        if self.use_spacy:
            try:
                if self.language == 'ar':
                    self.nlp = spacy.load('ar_core_news_sm')
                elif self.language == 'en':
                    self.nlp = spacy.load('en_core_web_sm')
                else:
                    self.nlp = spacy.load('xx_ent_wiki_sm')  # نموذج متعدد اللغات
            except Exception as e:
                self.logger.warning(f"لم يتم تحميل نموذج spaCy: {str(e)}")
                self.logger.warning("تأكد من تثبيت النموذج اللغوي المناسب باستخدام الأمر: python -m spacy download ar_core_news_sm")
                self.use_spacy = False
    
    def analyze(self, page_data):
        """
        تحليل محتوى صفحة ويب
        
        Args:
            page_data (dict): بيانات الصفحة المحتوية على HTML والعنوان URL
            
        Returns:
            dict: نتائج تحليل المحتوى
        """
        url = page_data.get('url', '')
        html_content = page_data.get('html', '')
        
        if not html_content:
            self.logger.error(f"لا يوجد محتوى HTML للتحليل: {url}")
            return {
                'status': 'error',
                'message': 'لا يوجد محتوى HTML للتحليل',
                'score': 0,
                'issues': []
            }
        
        # تحليل HTML باستخدام BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # استخراج النص الرئيسي للصفحة (تجاهل العناصر غير الضرورية)
        main_text = self._extract_main_content(soup)
        
        # حساب عدد الكلمات
        words = self._tokenize_text(main_text)
        word_count = len(words)
        
        # تحليل الكلمات المفتاحية
        keywords = self._extract_keywords(words, soup, url)
        
        # تحليل قابلية القراءة
        readability = self._analyze_readability(main_text)
        
        # تجميع النتائج
        result = {
            'word_count': word_count,
            'keywords': keywords[:10],  # أهم 10 كلمات مفتاحية
            'keyword_density': self._calculate_keyword_density(keywords, word_count),
            'readability': readability,
            'score': 0,
            'issues': []
        }
        
        # التحقق من الحد الأدنى لعدد الكلمات
        if word_count < self.min_words:
            result['issues'].append({
                'type': 'warning',
                'message': f'محتوى الصفحة قصير ({word_count} كلمة)',
                'impact': 'high',
                'recommendation': f'زيادة طول المحتوى ليتجاوز {self.min_words} كلمة لتحسين جودة الصفحة في محركات البحث'
            })
        
        # التحقق من كثافة الكلمات المفتاحية
        for keyword, data in result['keyword_density'].items():
            if data['density'] > 5:  # تجاوز كثافة 5%
                result['issues'].append({
                    'type': 'warning',
                    'message': f'كثافة الكلمة المفتاحية "{keyword}" مرتفعة جدًا ({data["density"]:.1f}%)',
                    'impact': 'medium',
                    'recommendation': 'تقليل كثافة الكلمة المفتاحية لتجنب الحشو والتأثير السلبي على السيو'
                })
        
        # التحقق من قابلية القراءة
        if readability.get('score', 0) < 50:
            result['issues'].append({
                'type': 'info',
                'message': 'المحتوى صعب القراءة نسبيًا',
                'impact': 'medium',
                'recommendation': 'تبسيط اللغة المستخدمة وتقسيم الجمل الطويلة لتحسين قابلية القراءة'
            })
        
        # حساب النتيجة الإجمالية
        result['score'] = self._calculate_content_score(result)
        
        return result
    
    def _extract_main_content(self, soup):
        """
        استخراج المحتوى النصي الرئيسي من الصفحة
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup لتحليل HTML
            
        Returns:
            str: النص الرئيسي للصفحة
        """
        # إزالة العناصر غير المرغوب بها
        for element in soup(['script', 'style', 'head', 'title', 'meta', 'link', 
                            'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()
        
        # محاولة العثور على المحتوى الرئيسي
        main_element = soup.find('main') or soup.find('article') or soup.find('div', {'class': ['content', 'main-content', 'entry-content', 'post-content']})
        
        if main_element:
            text = main_element.get_text(separator=' ')
        else:
            # استخدام جسم الصفحة بالكامل إذا لم يتم العثور على المحتوى الرئيسي
            text = soup.body.get_text(separator=' ') if soup.body else soup.get_text(separator=' ')
        
        # تنظيف النص
        text = re.sub(r'\s+', ' ', text)  # استبدال مساحات متعددة بمسافة واحدة
        text = re.sub(r'\n+', '\n', text)  # استبدال أسطر متعددة بسطر واحد
        
        return text.strip()
    
    def _tokenize_text(self, text):
        """
        تقسيم النص إلى كلمات
        
        Args:
            text (str): النص المراد تقسيمه
            
        Returns:
            list: قائمة الكلمات
        """
        if self.use_spacy and self.nlp:
            # استخدام spaCy للتحليل اللغوي
            doc = self.nlp(text)
            return [token.text for token in doc if not token.is_punct and not token.is_space]
        else:
            # استخدام طريقة بسيطة للتقسيم
            # إزالة علامات الترقيم والأرقام والرموز الخاصة
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\d+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            
            # تقسيم النص إلى كلمات
            return [word for word in text.split() if len(word) > 1]
    
    def _extract_keywords(self, words, soup, url):
        """
        استخراج الكلمات المفتاحية من المحتوى
        
        Args:
            words (list): قائمة الكلمات في النص
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            url (str): عنوان URL للصفحة
            
        Returns:
            list: قائمة الكلمات المفتاحية مرتبة حسب الأهمية
        """
        # تحديد اللغة المحتملة للمحتوى
        lang = self._detect_language(words)
        
        # اختيار قائمة الكلمات الشائعة المناسبة
        stopwords = self.arabic_stopwords if lang == 'ar' else self.english_stopwords
        
        # إنشاء قاموس تكرار الكلمات (مع استبعاد الكلمات الشائعة)
        word_counts = Counter([word.lower() for word in words if word.lower() not in stopwords])
        
        # استخراج الكلمات المفتاحية من العناصر المهمة في الصفحة
        title_keywords = self._extract_keywords_from_element(soup.title.text if soup.title else "", stopwords)
        
        meta_keywords = []
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'content' in meta_desc.attrs:
            meta_keywords = self._extract_keywords_from_element(meta_desc['content'], stopwords)
        
        h1_keywords = []
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            h1_keywords.extend(self._extract_keywords_from_element(h1.text, stopwords))
        
        # استخراج كلمات مفتاحية من المسار URL
        url_path = urlparse(url).path
        url_keywords = self._extract_keywords_from_element(url_path.replace('-', ' ').replace('/', ' '), stopwords)
        
        # ترجيح الكلمات المفتاحية
        for keyword in title_keywords:
            word_counts[keyword] += 5  # ترجيح أكبر للكلمات الموجودة في العنوان
        
        for keyword in meta_keywords:
            word_counts[keyword] += 3  # ترجيح للكلمات الموجودة في الوصف
        
        for keyword in h1_keywords:
            word_counts[keyword] += 4  # ترجيح للكلمات الموجودة في H1
        
        for keyword in url_keywords:
            word_counts[keyword] += 2  # ترجيح للكلمات الموجودة في URL
        
        # البحث عن عبارات من كلمتين مهمة (Bigrams)
        bigrams = self._extract_bigrams(words, stopwords)
        
        # دمج الكلمات المفردة والعبارات
        all_keywords = [(word, count) for word, count in word_counts.most_common(20)]
        all_keywords.extend([(phrase, count) for phrase, count in bigrams.most_common(10)])
        
        # ترتيب القائمة النهائية حسب عدد التكرار
        return sorted(all_keywords, key=lambda x: x[1], reverse=True)
    
    def _extract_keywords_from_element(self, text, stopwords):
        """
        استخراج الكلمات المفتاحية من نص معين
        
        Args:
            text (str): النص المراد تحليله
            stopwords (set): مجموعة الكلمات الشائعة للاستبعاد
            
        Returns:
            list: قائمة الكلمات المفتاحية
        """
        # تنظيف النص
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # تقسيم النص إلى كلمات
        words = [word.lower() for word in text.split() if len(word) > 1]
        
        # إزالة الكلمات الشائعة
        return [word for word in words if word not in stopwords]
    
    def _extract_bigrams(self, words, stopwords):
        """
        استخراج عبارات من كلمتين متتاليتين (Bigrams)
        
        Args:
            words (list): قائمة الكلمات
            stopwords (set): مجموعة الكلمات الشائعة للاستبعاد
            
        Returns:
            Counter: عداد للعبارات مع تكرارها
        """
        bigrams = Counter()
        
        # تحويل القائمة إلى كلمات صغيرة
        words = [word.lower() for word in words]
        
        # إنشاء عبارات من كلمتين متتاليتين
        for i in range(len(words) - 1):
            word1 = words[i]
            word2 = words[i + 1]
            
            # استبعاد العبارات التي تبدأ أو تنتهي بكلمة شائعة
            if word1 not in stopwords and word2 not in stopwords:
                if len(word1) > 2 and len(word2) > 2:  # استبعاد الكلمات القصيرة جدًا
                    bigram = f"{word1} {word2}"
                    bigrams[bigram] += 1
        
        return bigrams
    
    def _calculate_keyword_density(self, keywords, total_words):
        """
        حساب كثافة الكلمات المفتاحية
        
        Args:
            keywords (list): قائمة الكلمات المفتاحية وتكرارها
            total_words (int): إجمالي عدد الكلمات في النص
            
        Returns:
            dict: قاموس يحتوي على كثافة كل كلمة مفتاحية
        """
        densities = {}
        
        if total_words == 0:
            return densities
        
        for keyword, count in keywords:
            density = (count / total_words) * 100
            densities[keyword] = {
                'count': count,
                'density': density
            }
        
        return densities
    
    def _analyze_readability(self, text):
        """
        تحليل قابلية القراءة للنص
        
        Args:
            text (str): النص المراد تحليله
            
        Returns:
            dict: نتائج تحليل قابلية القراءة
        """
        # تقسيم النص إلى جمل
        sentences = re.split(r'[.!?؟]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # تقسيم النص إلى كلمات
        words = self._tokenize_text(text)
        
        # حساب متوسط طول الجملة
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # حساب متوسط طول الكلمة
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # حساب نسبة الكلمات الطويلة (أكثر من 6 أحرف)
        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = (long_words / len(words)) * 100 if words else 0
        
        # حساب عدد الفقرات
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # حساب درجة قابلية القراءة البسيطة (مقياس مخصص)
        # درجة أقل = أسهل في القراءة
        if avg_sentence_length > 0:
            readability_score = (0.4 * avg_sentence_length) + (0.2 * avg_word_length)
            
            # تحويل الدرجة إلى مقياس من 0 إلى 100 (100 = أسهل في القراءة)
            normalized_score = max(0, min(100, 100 - (readability_score * 5)))
        else:
            normalized_score = 0
        
        return {
            'avg_sentence_length': avg_sentence_length,
            'avg_word_length': avg_word_length,
            'long_word_ratio': long_word_ratio,
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'score': normalized_score,
            'level': self._get_readability_level(normalized_score)
        }
    
    def _get_readability_level(self, score):
        """
        تحديد مستوى قابلية القراءة بناءً على الدرجة
        
        Args:
            score (float): درجة قابلية القراءة
            
        Returns:
            str: مستوى قابلية القراءة
        """
        if score >= 80:
            return 'سهل جدًا'
        elif score >= 65:
            return 'سهل'
        elif score >= 50:
            return 'متوسط'
        elif score >= 30:
            return 'صعب'
        else:
            return 'صعب جدًا'
    
    def _detect_language(self, words):
        """
        اكتشاف لغة النص بطريقة بسيطة
        
        Args:
            words (list): قائمة الكلمات في النص
            
        Returns:
            str: رمز اللغة المكتشفة (ar أو en)
        """
        # عينة من الكلمات للاختبار
        sample = words[:100] if len(words) > 100 else words
        
        # تحقق من وجود أحرف عربية
        arabic_chars = 0
        english_chars = 0
        
        for word in sample:
            # نطاق الأحرف العربية في Unicode
            for char in word:
                if '\u0600' <= char <= '\u06FF':
                    arabic_chars += 1
                elif char.isascii() and char.isalpha():
                    english_chars += 1
        
        # تحديد اللغة بناءً على نسبة الأحرف
        return 'ar' if arabic_chars > english_chars else 'en'
    
    def _calculate_content_score(self, results):
        """
        حساب النتيجة الإجمالية للمحتوى
        
        Args:
            results (dict): نتائج تحليل المحتوى
            
        Returns:
            int: نتيجة جودة المحتوى (0-100)
        """
        score = 100  # البداية بنتيجة كاملة
        
        # خصم النقاط بناءً على المشاكل
        for issue in results['issues']:
            if issue['impact'] == 'high':
                score -= 15
            elif issue['impact'] == 'medium':
                score -= 10
            elif issue['impact'] == 'low':
                score -= 5
        
        # إضافة نقاط بناءً على عدد الكلمات
        word_count = results['word_count']
        if word_count < self.min_words:
            score -= 10
        elif word_count >= self.min_words * 2:
            score += 10
        elif word_count >= self.min_words:
            score += 5
        
        # إضافة نقاط بناءً على قابلية القراءة
        readability_score = results['readability']['score']
        if readability_score >= 70:
            score += 10
        elif readability_score >= 50:
            score += 5
        elif readability_score < 30:
            score -= 10
        
        # ضمان أن النتيجة بين 0 و 100
        return max(0, min(100, score))
