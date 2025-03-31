#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تحليل نية البحث (Search Intent Detection) - مسؤولة عن تحديد الهدف من الكلمات المفتاحية

تقوم هذه الوحدة بتحليل نية المستخدم من خلال الكلمات المفتاحية واستخدام تقنيات معالجة اللغة الطبيعية NLP
لتحديد ما إذا كانت النية معلوماتية، أو تجارية، أو شرائية، أو ملاحية.
"""

import re
import logging
import numpy as np
from collections import Counter
from urllib.parse import urlparse

# استيراد المكتبات المتقدمة لمعالجة اللغة
try:
    import spacy
    import tensorflow as tf
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from sklearn.feature_extraction.text import TfidfVectorizer
    ADVANCED_NLP_AVAILABLE = True
except ImportError:
    ADVANCED_NLP_AVAILABLE = False

class SearchIntentDetector:
    """
    محلل نية البحث للكلمات المفتاحية
    """
    
    # تصنيفات نية البحث
    INTENT_TYPES = {
        'informational': 'معلوماتية',
        'navigational': 'ملاحية',
        'commercial': 'تجارية',
        'transactional': 'شرائية'
    }
    
    # كلمات مفتاحية ترتبط بكل نوع من النوايا
    INTENT_KEYWORDS = {
        'informational': [
            'ما هو', 'كيف', 'لماذا', 'متى', 'أين', 'من', 'شرح', 'تعريف', 'معنى', 'دليل',
            'طريقة', 'خطوات', 'معلومات عن', 'ما معنى', 'ما هي', 'أمثلة', 'الفرق بين',
            'أفضل طريقة', 'نصائح', 'أسباب', 'مقارنة', 'تاريخ', 'what is', 'how to', 'why',
            'when', 'where', 'who', 'guide', 'tutorial', 'explanation', 'define',
            'meaning', 'examples', 'difference between', 'best way', 'tips', 'reasons'
        ],
        'navigational': [
            'موقع', 'تسجيل الدخول', 'تسجيل دخول', 'صفحة', 'الرسمي', 'تحميل', 'تنزيل',
            'تطبيق', 'عنوان', 'التواصل مع', 'حساب', 'بوابة', 'login', 'sign in', 'website',
            'download', 'app', 'official', 'address', 'contact', 'account', 'portal'
        ],
        'commercial': [
            'أفضل', 'مقارنة', 'مراجعة', 'تقييم', 'ضد', 'مقابل', 'أو', 'افضل', 'قارن',
            'توصيات', 'سعر', 'عروض', 'vs', 'versus', 'or', 'comparison', 'compare',
            'review', 'top', 'best', 'price', 'prices', 'rating', 'ratings', 'deals'
        ],
        'transactional': [
            'شراء', 'بيع', 'اشتري', 'سعر', 'خصم', 'عرض', 'كوبون', 'تخفيض', 'توصيل',
            'حجز', 'اشتراك', 'تذكرة', 'كم سعر', 'buy', 'sell', 'purchase', 'order',
            'discount', 'deal', 'coupon', 'sale', 'shipping', 'booking', 'subscription',
            'ticket', 'price', 'delivery', 'shop', 'cheap', 'cost'
        ]
    }
    
    def __init__(self, use_advanced_models=True, language='ar'):
        """
        تهيئة محلل نية البحث
        
        Args:
            use_advanced_models (bool): استخدام نماذج NLP متقدمة إذا كانت متوفرة
            language (str): لغة المحتوى الافتراضية ('ar' للعربية، 'en' للإنجليزية)
        """
        self.language = language
        self.use_advanced_models = use_advanced_models and ADVANCED_NLP_AVAILABLE
        self.logger = logging.getLogger('rseo.search_intent_detector')
        
        # تحميل النماذج المتقدمة إذا كان مطلوبًا
        self.nlp = None
        self.intent_classifier = None
        
        if self.use_advanced_models:
            try:
                # تحميل نموذج spaCy المناسب للغة
                if self.language == 'ar':
                    self.nlp = spacy.load('ar_core_news_sm')
                elif self.language == 'en':
                    self.nlp = spacy.load('en_core_web_sm')
                else:
                    self.nlp = spacy.load('xx_ent_wiki_sm')  # نموذج متعدد اللغات
                
                # إعداد مصنف النية باستخدام Hugging Face
                # هذا نموذج افتراضي، الأفضل استخدام نموذج مدرب خصيصًا على تصنيف نية البحث
                try:
                    model_name = "distilbert-base-uncased"
                    # يمكن استبداله بنموذج مخصص للعربية أو للتصنيف المحدد
                    self.intent_classifier = pipeline("text-classification", model=model_name)
                    self.logger.info("تم تحميل نموذج تصنيف النية بنجاح")
                except Exception as e:
                    self.logger.warning(f"لم يتم تحميل نموذج تصنيف النية: {str(e)}")
                    
            except Exception as e:
                self.logger.warning(f"لم يتم تحميل نموذج spaCy: {str(e)}")
                self.use_advanced_models = False
    
    def detect_intent(self, keyword, context=None):
        """
        تحليل نية البحث للكلمة المفتاحية
        
        Args:
            keyword (str): الكلمة المفتاحية المراد تحليلها
            context (str, optional): سياق إضافي للكلمة المفتاحية (مثل محتوى الصفحة)
            
        Returns:
            dict: نتائج تحليل النية تتضمن النوع والثقة
        """
        keyword = keyword.strip().lower()
        
        # تحليل نية البحث باستخدام القواعد البسيطة
        rule_based_intent = self._rule_based_intent_detection(keyword)
        
        # تحليل النية باستخدام النموذج المتقدم إذا كان متاحًا
        ml_based_intent = None
        if self.use_advanced_models and self.intent_classifier:
            ml_based_intent = self._ml_based_intent_detection(keyword, context)
        
        # دمج النتائج من الطريقتين
        if ml_based_intent:
            # أخذ المتوسط المرجح بين النتيجتين (وزن أعلى للنموذج المتقدم)
            final_intent = self._combine_intent_results(rule_based_intent, ml_based_intent, 
                                                       rule_weight=0.3, ml_weight=0.7)
        else:
            final_intent = rule_based_intent
        
        # استخراج المعلومات الإضافية من الكلمة المفتاحية
        additional_info = self._extract_additional_info(keyword)
        
        # إضافة توصيات للمحتوى بناءً على نية البحث
        recommendations = self._generate_content_recommendations(final_intent, keyword)
        
        # تجميع النتائج النهائية
        result = {
            'keyword': keyword,
            'primary_intent': final_intent['primary_intent'],
            'primary_intent_name': self.INTENT_TYPES.get(final_intent['primary_intent'], 'غير معروف'),
            'confidence': final_intent['confidence'],
            'all_intents': final_intent['all_intents'],
            'additional_info': additional_info,
            'recommendations': recommendations
        }
        
        return result
    
    def _rule_based_intent_detection(self, keyword):
        """
        تحليل نية البحث باستخدام القواعد البسيطة
        
        Args:
            keyword (str): الكلمة المفتاحية
            
        Returns:
            dict: نتائج التحليل
        """
        scores = {intent: 0.0 for intent in self.INTENT_TYPES.keys()}
        
        # قواعد بسيطة: البحث عن كلمات مفتاحية ترتبط بكل نوع من أنواع النية
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for intent_keyword in keywords:
                if intent_keyword in keyword:
                    scores[intent] += 1.0
        
        # قواعد إضافية
        # الاستعلامات القصيرة مثل أسماء العلامات التجارية غالبًا ما تكون ملاحية
        if len(keyword.split()) <= 2 and not any(keyword.startswith(q) for q in ['كيف', 'ما', 'لماذا', 'متى', 'أين', 'من', 'how', 'what', 'why', 'when', 'where', 'who']):
            scores['navigational'] += 0.5
        
        # الاستعلامات التي تحتوي على "شراء" أو "buy" غالبًا ما تكون شرائية
        if any(term in keyword for term in ['شراء', 'اشتري', 'بيع', 'سعر', 'buy', 'purchase', 'price']):
            scores['transactional'] += 1.0
        
        # الاستعلامات التي تبدأ بأسئلة غالبًا ما تكون معلوماتية
        if any(keyword.startswith(q) for q in ['كيف', 'ما', 'لماذا', 'متى', 'أين', 'من', 'how', 'what', 'why', 'when', 'where', 'who']):
            scores['informational'] += 1.5
        
        # تطبيع النتائج
        total_score = sum(scores.values())
        if total_score > 0:
            normalized_scores = {intent: score / total_score for intent, score in scores.items()}
        else:
            # إذا لم يتم العثور على أي مطابقة، فالافتراض هو النية المعلوماتية
            normalized_scores = {intent: 0.1 for intent in scores.keys()}
            normalized_scores['informational'] = 0.7
        
        # ترتيب النوايا حسب النتيجة
        sorted_intents = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'primary_intent': sorted_intents[0][0],
            'confidence': sorted_intents[0][1],
            'all_intents': {intent: score for intent, score in sorted_intents}
        }
    
    def _ml_based_intent_detection(self, keyword, context=None):
        """
        تحليل نية البحث باستخدام النماذج المتقدمة
        
        Args:
            keyword (str): الكلمة المفتاحية
            context (str, optional): سياق إضافي للكلمة المفتاحية
            
        Returns:
            dict: نتائج التحليل
        """
        # هذه دالة وهمية تحتاج للتنفيذ باستخدام نموذج مدرب خصيصًا
        # في الواقع، ستحتاج إلى نموذج تم تدريبه على بيانات نية البحث
        
        try:
            # استخدام النموذج المدرب مسبقًا لتصنيف النية
            # ملاحظة: هذا مثال فقط، يجب استبداله بنموذج حقيقي
            # نظرًا لتصميم النموذج، قد نحتاج لتعديل الفئات المخرجة لتناسب تصنيفاتنا للنية
            
            # دمج الكلمة المفتاحية والسياق إذا كان متوفرًا
            input_text = keyword
            if context:
                input_text = f"{keyword} - {context[:100]}"  # استخدام جزء من السياق
            
            # محاكاة نتائج تصنيف النموذج
            # في التطبيق الحقيقي، هنا سنستدعي النموذج
            # prediction = self.intent_classifier(input_text)
            
            # محاكاة النتائج (يجب استبدالها بنتائج حقيقية من النموذج)
            if "كيف" in keyword or "how" in keyword:
                simulated_scores = {
                    'informational': 0.85,
                    'commercial': 0.08,
                    'navigational': 0.05,
                    'transactional': 0.02
                }
            elif "شراء" in keyword or "buy" in keyword:
                simulated_scores = {
                    'transactional': 0.78,
                    'commercial': 0.18,
                    'informational': 0.03,
                    'navigational': 0.01
                }
            elif "أفضل" in keyword or "best" in keyword:
                simulated_scores = {
                    'commercial': 0.72,
                    'informational': 0.20,
                    'transactional': 0.06,
                    'navigational': 0.02
                }
            elif "موقع" in keyword or "login" in keyword or "تسجيل دخول" in keyword:
                simulated_scores = {
                    'navigational': 0.88,
                    'informational': 0.07,
                    'commercial': 0.03,
                    'transactional': 0.02
                }
            else:
                # افتراضيًا، اعتبرها معلوماتية مع بعض الاحتمالات للأنواع الأخرى
                simulated_scores = {
                    'informational': 0.60,
                    'commercial': 0.20,
                    'navigational': 0.10,
                    'transactional': 0.10
                }
            
            # ترتيب النوايا حسب النتيجة
            sorted_intents = sorted(simulated_scores.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'primary_intent': sorted_intents[0][0],
                'confidence': sorted_intents[0][1],
                'all_intents': {intent: score for intent, score in sorted_intents}
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل النية باستخدام النموذج المتقدم: {str(e)}")
            return None
    
    def _combine_intent_results(self, rule_based, ml_based, rule_weight=0.3, ml_weight=0.7):
        """
        دمج نتائج التحليل من الطرق المختلفة
        
        Args:
            rule_based (dict): نتائج التحليل القائم على القواعد
            ml_based (dict): نتائج التحليل القائم على التعلم الآلي
            rule_weight (float): وزن نتائج القواعد
            ml_weight (float): وزن نتائج التعلم الآلي
            
        Returns:
            dict: النتائج المدمجة
        """
        if not ml_based:
            return rule_based
        
        # دمج جميع النوايا من كلا المصدرين
        all_intents = {}
        for intent in self.INTENT_TYPES.keys():
            rule_score = rule_based['all_intents'].get(intent, 0)
            ml_score = ml_based['all_intents'].get(intent, 0)
            
            # المتوسط المرجح
            combined_score = (rule_score * rule_weight) + (ml_score * ml_weight)
            all_intents[intent] = combined_score
        
        # ترتيب النوايا حسب النتيجة المدمجة
        sorted_intents = sorted(all_intents.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'primary_intent': sorted_intents[0][0],
            'confidence': sorted_intents[0][1],
            'all_intents': {intent: score for intent, score in sorted_intents}
        }
    
    def _extract_additional_info(self, keyword):
        """
        استخراج معلومات إضافية من الكلمة المفتاحية
        
        Args:
            keyword (str): الكلمة المفتاحية
            
        Returns:
            dict: معلومات إضافية
        """
        additional_info = {}
        
        # تحديد اللغة
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in keyword)
        additional_info['language'] = 'ar' if is_arabic else 'en'
        
        # تحديد طول الذيل (short-tail vs long-tail)
        word_count = len(keyword.split())
        if word_count <= 2:
            additional_info['tail_type'] = 'short-tail'
        elif word_count <= 5:
            additional_info['tail_type'] = 'medium-tail'
        else:
            additional_info['tail_type'] = 'long-tail'
        
        # تحديد وجود أسماء العلامات التجارية أو المنتجات
        # هذا مبسط جدًا وسيتطلب قاعدة بيانات للعلامات التجارية المعروفة
        brands = ['samsung', 'apple', 'sony', 'lg', 'nike', 'adidas', 'سامسونج', 'أبل', 'سوني', 'نايك']
        found_brands = [brand for brand in brands if brand in keyword.lower()]
        if found_brands:
            additional_info['brands'] = found_brands
        
        # تحديد وجود مواقع جغرافية
        # هذا مبسط جدًا أيضًا
        locations = ['مصر', 'السعودية', 'الإمارات', 'الرياض', 'القاهرة', 'دبي', 'egypt', 'saudi', 'uae', 'dubai']
        found_locations = [loc for loc in locations if loc in keyword.lower()]
        if found_locations:
            additional_info['locations'] = found_locations
        
        return additional_info
    
    def _generate_content_recommendations(self, intent_result, keyword):
        """
        توليد توصيات للمحتوى بناءً على نية البحث
        
        Args:
            intent_result (dict): نتائج تحليل النية
            keyword (str): الكلمة المفتاحية
            
        Returns:
            dict: توصيات للمحتوى
        """
        primary_intent = intent_result['primary_intent']
        recommendations = {
            'content_type': [],
            'structure': [],
            'elements': []
        }
        
        # توصيات حسب نوع النية
        if primary_intent == 'informational':
            recommendations['content_type'] = [
                'مقال معلوماتي شامل',
                'دليل تفصيلي',
                'سلسلة من الخطوات',
                'محتوى تعليمي',
                'أسئلة وأجوبة',
                'تفسير علمي'
            ]
            recommendations['structure'] = [
                'قسم المحتوى إلى عناوين فرعية واضحة',
                'ابدأ بتعريف المفهوم أو الموضوع',
                'استخدم قوائم نقطية وأرقام لتسهيل القراءة',
                'أضف جدول محتويات للمقالات الطويلة',
                'أعط أمثلة توضيحية'
            ]
            recommendations['elements'] = [
                'رسوم بيانية توضيحية',
                'صور شارحة',
                'فيديو تعليمي',
                'اقتباسات من مصادر موثوقة',
                'إحصائيات ودراسات'
            ]
            
        elif primary_intent == 'navigational':
            recommendations['content_type'] = [
                'صفحة تعريفية',
                'صفحة "من نحن"',
                'دليل استخدام الموقع',
                'صفحة التواصل',
                'صفحة تسجيل الدخول'
            ]
            recommendations['structure'] = [
                'هيكل بسيط وواضح',
                'روابط سريعة للصفحات الرئيسية',
                'معلومات التواصل واضحة وبارزة',
                'تصميم سهل التنقل'
            ]
            recommendations['elements'] = [
                'شعار العلامة التجارية',
                'أزرار دعوة للعمل واضحة',
                'خريطة الموقع',
                'نموذج بحث',
                'معلومات الاتصال'
            ]
            
        elif primary_intent == 'commercial':
            recommendations['content_type'] = [
                'مقالات مقارنة',
                'مراجعات المنتجات',
                'قوائم "أفضل المنتجات"',
                'دليل الشراء',
                'اختبارات ومقارنات'
            ]
            recommendations['structure'] = [
                'مقارنة مباشرة بين المنتجات',
                'إبراز مزايا وعيوب كل خيار',
                'جداول مقارنة',
                'تصنيف واضح للمنتجات',
                'خلاصة وتوصيات نهائية'
            ]
            recommendations['elements'] = [
                'صور للمنتجات',
                'تقييمات بالنجوم',
                'توصيات الخبراء',
                'أزرار "اعرف المزيد" أو "اشتر الآن"',
                'مؤشرات الأسعار'
            ]
            
        elif primary_intent == 'transactional':
            recommendations['content_type'] = [
                'صفحات المنتجات',
                'عروض خاصة',
                'صفحات التسوق',
                'صفحات السلة والدفع',
                'عمليات شراء سهلة'
            ]
            recommendations['structure'] = [
                'معلومات المنتج واضحة ومختصرة',
                'أسعار وخيارات الشراء بارزة',
                'خطوات شراء بسيطة',
                'عرض المزايا والفوائد الرئيسية',
                'توفير معلومات الشحن والضمان'
            ]
            recommendations['elements'] = [
                'صور وفيديوهات عالية الجودة للمنتج',
                'أزرار "اشتر الآن" و"أضف إلى السلة" بارزة',
                'شهادات العملاء',
                'ضمانات الشراء الآمن',
                'خيارات الدفع المتاحة',
                'معلومات التوصيل والإرجاع'
            ]
        
        return recommendations
    
    def analyze_keyword_list(self, keywords):
        """
        تحليل قائمة من الكلمات المفتاحية وتصنيف نواياها
        
        Args:
            keywords (list): قائمة الكلمات المفتاحية
            
        Returns:
            dict: نتائج التحليل مصنفة حسب النية
        """
        results = {
            'informational': [],
            'navigational': [],
            'commercial': [],
            'transactional': []
        }
        
        for keyword in keywords:
            intent_analysis = self.detect_intent(keyword)
            primary_intent = intent_analysis['primary_intent']
            results[primary_intent].append({
                'keyword': keyword,
                'confidence': intent_analysis['confidence'],
                'additional_info': intent_analysis['additional_info']
            })
        
        # حساب إحصائيات إضافية
        statistics = {
            'total_keywords': len(keywords),
            'distribution': {
                intent: {'count': len(items), 'percentage': (len(items) / len(keywords)) * 100 if keywords else 0}
                for intent, items in results.items()
            }
        }
        
        return {
            'results': results,
            'statistics': statistics
        }
