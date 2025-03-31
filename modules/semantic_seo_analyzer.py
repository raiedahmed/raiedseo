#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تحليل السيو الدلالي (Semantic SEO) - تحليل الترابط الدلالي للكلمات المفتاحية

تقوم هذه الوحدة بربط الكلمات المفتاحية بالمفاهيم الدلالية القريبة منها باستخدام
تقنيات التضمين (Embeddings) ومعالجة اللغة الطبيعية.
"""

import logging
import numpy as np
from collections import defaultdict
import re
import os
import json

# استيراد المكتبات المتقدمة لمعالجة اللغة
try:
    import spacy
    import tensorflow as tf
    import tensorflow_hub as hub
    from transformers import pipeline, AutoTokenizer, AutoModel, BertTokenizer, BertModel
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import CountVectorizer
    ADVANCED_NLP_AVAILABLE = True
except ImportError:
    ADVANCED_NLP_AVAILABLE = False

class SemanticSEOAnalyzer:
    """
    محلل السيو الدلالي
    """
    
    def __init__(self, use_advanced_models=True, language='ar', embeddings_model='USE'):
        """
        تهيئة محلل السيو الدلالي
        
        Args:
            use_advanced_models (bool): استخدام نماذج NLP متقدمة إذا كانت متوفرة
            language (str): لغة المحتوى الافتراضية ('ar' للعربية، 'en' للإنجليزية)
            embeddings_model (str): نموذج التضمين المستخدم ('USE', 'BERT', 'fastText')
        """
        self.language = language
        self.use_advanced_models = use_advanced_models and ADVANCED_NLP_AVAILABLE
        self.embeddings_model_name = embeddings_model
        self.logger = logging.getLogger('rseo.semantic_seo_analyzer')
        
        # تحميل النماذج المتقدمة إذا كان مطلوبًا
        self.nlp = None
        self.embeddings_model = None
        self.tokenizer = None
        
        if self.use_advanced_models:
            try:
                # تحميل نموذج spaCy المناسب للغة
                if self.language == 'ar':
                    self.nlp = spacy.load('ar_core_news_sm')
                elif self.language == 'en':
                    self.nlp = spacy.load('en_core_web_sm')
                else:
                    self.nlp = spacy.load('xx_ent_wiki_sm')  # نموذج متعدد اللغات
                
                # تحميل نموذج التضمين
                self._load_embeddings_model()
                
            except Exception as e:
                self.logger.warning(f"لم يتم تحميل النماذج المتقدمة: {str(e)}")
                self.use_advanced_models = False
        
        # قاموس مسبق التعريف للمفاهيم المرتبطة ببعض الكلمات المفتاحية
        self._load_predefined_semantic_concepts()
    
    def _load_embeddings_model(self):
        """
        تحميل نموذج التضمين (Embeddings)
        """
        try:
            if self.embeddings_model_name == 'USE':
                # Universal Sentence Encoder
                module_url = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
                self.embeddings_model = hub.load(module_url)
                self.logger.info("تم تحميل نموذج Universal Sentence Encoder")
                
            elif self.embeddings_model_name == 'BERT':
                # BERT Model
                if self.language == 'ar':
                    model_name = "asafaya/bert-base-arabic"
                else:
                    model_name = "bert-base-uncased"
                
                self.tokenizer = BertTokenizer.from_pretrained(model_name)
                self.embeddings_model = BertModel.from_pretrained(model_name)
                self.logger.info(f"تم تحميل نموذج BERT: {model_name}")
                
            else:
                # لم يتم العثور على النموذج المطلوب، استخدام النموذج الافتراضي
                self.logger.warning(f"نموذج التضمين {self.embeddings_model_name} غير معروف. استخدام النموذج الافتراضي")
                module_url = "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3"
                self.embeddings_model = hub.load(module_url)
                
        except Exception as e:
            self.logger.error(f"فشل في تحميل نموذج التضمين: {str(e)}")
            self.use_advanced_models = False
    
    def _load_predefined_semantic_concepts(self):
        """
        تحميل قائمة مسبقة التعريف للمفاهيم المرتبطة ببعض الكلمات المفتاحية
        """
        # هذه قائمة مبسطة، في الحالة الحقيقية يمكن تحميلها من ملف خارجي أو قاعدة بيانات
        self.predefined_concepts = {
            'سيو': [
                'تحسين محركات البحث', 'ترتيب', 'كلمات مفتاحية', 'بناء روابط', 'محتوى',
                'تحليل المنافسين', 'أرشفة', 'ميتا تاج', 'جوجل', 'محرك بحث'
            ],
            'تسويق': [
                'إعلان', 'ترويج', 'مبيعات', 'إعلانات', 'تسويق رقمي', 'علامة تجارية',
                'وسائل التواصل الاجتماعي', 'حملة', 'تسويق المحتوى', 'عملاء'
            ],
            'تصميم مواقع': [
                'html', 'css', 'جافا سكريبت', 'ui', 'ux', 'تجربة المستخدم', 'واجهة المستخدم',
                'تصميم', 'تطوير الويب', 'استضافة', 'ووردبريس', 'متجاوب'
            ]
        }
    
    def get_embedding(self, text):
        """
        الحصول على متجه التضمين (embedding vector) للنص المدخل
        
        Args:
            text (str): النص المراد تحويله إلى متجه
            
        Returns:
            numpy.ndarray: متجه التضمين
        """
        if not self.use_advanced_models or not self.embeddings_model:
            return None
        
        try:
            if self.embeddings_model_name == 'USE':
                # Universal Sentence Encoder
                embeddings = self.embeddings_model([text])
                return embeddings.numpy()[0]
                
            elif self.embeddings_model_name == 'BERT':
                # BERT Model
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
                outputs = self.embeddings_model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy()[0]
                return embedding
            
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على متجه التضمين: {str(e)}")
            return None
    
    def calculate_similarity(self, text1, text2):
        """
        حساب مدى التشابه الدلالي بين نصين
        
        Args:
            text1 (str): النص الأول
            text2 (str): النص الثاني
            
        Returns:
            float: درجة التشابه (0-1)
        """
        if not self.use_advanced_models:
            # استخدام طريقة بسيطة للتشابه في حالة عدم توفر النماذج المتقدمة
            return self._simple_similarity(text1, text2)
        
        try:
            # الحصول على متجهات التضمين
            embedding1 = self.get_embedding(text1)
            embedding2 = self.get_embedding(text2)
            
            if embedding1 is None or embedding2 is None:
                return self._simple_similarity(text1, text2)
            
            # حساب التشابه بطريقة جيب التمام (Cosine Similarity)
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"خطأ في حساب التشابه: {str(e)}")
            return self._simple_similarity(text1, text2)
    
    def _simple_similarity(self, text1, text2):
        """
        حساب التشابه بطريقة بسيطة باستخدام تكرار الكلمات المشتركة
        
        Args:
            text1 (str): النص الأول
            text2 (str): النص الثاني
            
        Returns:
            float: درجة التشابه (0-1)
        """
        # تحويل النصوص إلى كلمات
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        # حساب التشابه باستخدام معامل جاكارد (Jaccard coefficient)
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def find_related_concepts(self, keyword, threshold=0.6, max_concepts=10):
        """
        البحث عن المفاهيم المرتبطة بالكلمة المفتاحية
        
        Args:
            keyword (str): الكلمة المفتاحية
            threshold (float): الحد الأدنى لدرجة التشابه (0-1)
            max_concepts (int): الحد الأقصى لعدد المفاهيم المرتبطة
            
        Returns:
            list: قائمة المفاهيم المرتبطة مع درجة التشابه
        """
        # البحث في القاموس المسبق التعريف أولاً
        related_concepts = []
        
        # تنظيف الكلمة المفتاحية
        cleaned_keyword = keyword.strip().lower()
        
        # البحث في القاموس المسبق التعريف
        for concept_key, concept_list in self.predefined_concepts.items():
            if concept_key in cleaned_keyword or any(term in cleaned_keyword for term in concept_list):
                # إضافة المفاهيم المرتبطة من القاموس
                for related_concept in concept_list:
                    # حساب درجة التشابه
                    similarity = self.calculate_similarity(cleaned_keyword, related_concept)
                    if similarity >= threshold:
                        related_concepts.append({
                            'concept': related_concept,
                            'similarity': similarity,
                            'source': 'predefined'
                        })
        
        # إذا كان النموذج المتقدم متوفراً، استخدامه للعثور على مفاهيم إضافية
        if self.use_advanced_models and self.nlp:
            try:
                # استخدام معالجة اللغة الطبيعية للعثور على كلمات مرتبطة
                doc = self.nlp(cleaned_keyword)
                
                # استخدام المرادفات والكلمات ذات الصلة من spaCy
                for token in doc:
                    # استخدام التشابه الدلالي
                    if token.has_vector:
                        # البحث عن كلمات قريبة من قائمة كبيرة من الكلمات
                        # هذا مبسط، في الواقع سنحتاج إلى قاعدة بيانات أكبر
                        for similar_word in ['تحسين', 'تطوير', 'تحليل', 'استراتيجية', 'تقنية', 
                                           'مراجعة', 'تصنيف', 'ترتيب', 'فهرسة', 'محتوى', 'بيانات']:
                            similarity = self.calculate_similarity(token.text, similar_word)
                            if similarity >= threshold:
                                related_concepts.append({
                                    'concept': similar_word,
                                    'similarity': similarity,
                                    'source': 'nlp_model'
                                })
            except Exception as e:
                self.logger.error(f"خطأ في استخدام نموذج معالجة اللغة: {str(e)}")
        
        # إزالة المفاهيم المتكررة والاحتفاظ بأعلى درجة تشابه
        unique_concepts = {}
        for concept in related_concepts:
            concept_key = concept['concept']
            if concept_key not in unique_concepts or concept['similarity'] > unique_concepts[concept_key]['similarity']:
                unique_concepts[concept_key] = concept
        
        # ترتيب المفاهيم حسب درجة التشابه والاحتفاظ بالحد الأقصى المطلوب
        sorted_concepts = sorted(unique_concepts.values(), key=lambda x: x['similarity'], reverse=True)
        
        return sorted_concepts[:max_concepts]
    
    def analyze_content_semantic_coverage(self, content, main_keyword, related_keywords=None):
        """
        تحليل تغطية المحتوى للمفاهيم الدلالية المرتبطة بالكلمة المفتاحية
        
        Args:
            content (str): محتوى النص
            main_keyword (str): الكلمة المفتاحية الرئيسية
            related_keywords (list, optional): قائمة الكلمات المفتاحية ذات الصلة
            
        Returns:
            dict: تقرير تحليل التغطية الدلالية
        """
        # العثور على المفاهيم المرتبطة بالكلمة المفتاحية الرئيسية
        main_related_concepts = self.find_related_concepts(main_keyword)
        
        # تحضير قائمة كاملة من المفاهيم المرتبطة
        all_concepts = [{'concept': main_keyword, 'primary': True}]
        for concept in main_related_concepts:
            all_concepts.append({
                'concept': concept['concept'],
                'similarity': concept['similarity'],
                'primary': False
            })
        
        # إضافة الكلمات المفتاحية ذات الصلة إذا وجدت
        if related_keywords:
            for keyword in related_keywords:
                # تجنب التكرار
                if keyword.lower() != main_keyword.lower() and not any(c['concept'].lower() == keyword.lower() for c in all_concepts):
                    related_concepts = self.find_related_concepts(keyword, threshold=0.4, max_concepts=5)
                    all_concepts.append({'concept': keyword, 'primary': True})
                    for concept in related_concepts:
                        if not any(c['concept'].lower() == concept['concept'].lower() for c in all_concepts):
                            all_concepts.append({
                                'concept': concept['concept'],
                                'similarity': concept['similarity'],
                                'primary': False
                            })
        
        # تحليل تواجد كل مفهوم في المحتوى
        content_lower = content.lower()
        for i, concept_data in enumerate(all_concepts):
            concept = concept_data['concept'].lower()
            
            # البحث عن تكرار المفهوم في المحتوى
            count = content_lower.count(concept)
            
            # تقييم حالة تواجد المفهوم
            if count > 0:
                status = 'موجود'
            else:
                # البحث عن كلمات مماثلة
                concept_parts = concept.split()
                partial_match = False
                for part in concept_parts:
                    if len(part) > 3 and part in content_lower:  # تجنب الكلمات القصيرة جدًا
                        partial_match = True
                        break
                
                status = 'موجود جزئيًا' if partial_match else 'مفقود'
            
            # إضافة معلومات الحالة
            all_concepts[i]['coverage'] = {
                'status': status,
                'count': count,
                'recommended_count': 1 if concept_data.get('primary', False) else 0  # توصية أولية بسيطة
            }
        
        # حساب نسبة التغطية الإجمالية
        covered_concepts = sum(1 for c in all_concepts if c['coverage']['status'] == 'موجود')
        partially_covered = sum(1 for c in all_concepts if c['coverage']['status'] == 'موجود جزئيًا')
        total_concepts = len(all_concepts)
        
        coverage_score = (covered_concepts + (partially_covered * 0.5)) / total_concepts * 100 if total_concepts > 0 else 0
        
        # تحضير التوصيات
        recommendations = []
        
        for concept_data in all_concepts:
            if concept_data['coverage']['status'] == 'مفقود':
                if concept_data.get('primary', False):
                    recommendations.append({
                        'priority': 'عالية',
                        'concept': concept_data['concept'],
                        'message': f'أضف الكلمة المفتاحية الرئيسية "{concept_data["concept"]}" إلى المحتوى'
                    })
                else:
                    recommendations.append({
                        'priority': 'متوسطة',
                        'concept': concept_data['concept'],
                        'message': f'ضمّن المفهوم ذو الصلة "{concept_data["concept"]}" لتحسين التغطية الدلالية'
                    })
        
        # تحضير التقرير النهائي
        report = {
            'main_keyword': main_keyword,
            'related_keywords': related_keywords or [],
            'coverage': {
                'covered': covered_concepts,
                'partially_covered': partially_covered,
                'missing': total_concepts - covered_concepts - partially_covered,
                'total': total_concepts,
                'score': coverage_score
            },
            'concepts': all_concepts,
            'recommendations': recommendations
        }
        
        return report
    
    def generate_semantic_seo_plan(self, main_topic, subtopics=None, content_type='article'):
        """
        توليد خطة سيو دلالية لموضوع معين
        
        Args:
            main_topic (str): الموضوع الرئيسي
            subtopics (list, optional): قائمة المواضيع الفرعية
            content_type (str): نوع المحتوى (مقال، صفحة منتج، إلخ)
            
        Returns:
            dict: خطة السيو الدلالية
        """
        # البحث عن المفاهيم المرتبطة بالموضوع الرئيسي
        main_related_concepts = self.find_related_concepts(main_topic, threshold=0.5)
        
        # تنظيم المفاهيم في مجموعات
        clusters = self._cluster_concepts(main_related_concepts)
        
        # تحضير المواضيع الفرعية إذا لم تكن موجودة
        if not subtopics:
            subtopics = []
            for cluster_name, concepts in clusters.items():
                if concepts:
                    subtopics.append(cluster_name)
        
        # إنشاء مخطط للمحتوى بناءً على نوع المحتوى
        content_outline = self._generate_content_outline(main_topic, subtopics, content_type)
        
        # تحضير توصيات الكلمات المفتاحية
        keyword_recommendations = []
        
        # الكلمة المفتاحية الرئيسية
        keyword_recommendations.append({
            'keyword': main_topic,
            'type': 'primary',
            'location': ['title', 'h1', 'introduction', 'conclusion'],
            'recommended_count': 3
        })
        
        # المفاهيم المرتبطة
        for concept in main_related_concepts[:5]:  # أعلى 5 مفاهيم
            keyword_recommendations.append({
                'keyword': concept['concept'],
                'type': 'related',
                'similarity': concept['similarity'],
                'location': ['body', 'subheadings'],
                'recommended_count': 1
            })
        
        # المواضيع الفرعية
        for subtopic in subtopics:
            keyword_recommendations.append({
                'keyword': subtopic,
                'type': 'secondary',
                'location': ['subheadings', 'body'],
                'recommended_count': 2
            })
        
        # تجميع الخطة النهائية
        plan = {
            'main_topic': main_topic,
            'subtopics': subtopics,
            'related_concepts': main_related_concepts,
            'clusters': clusters,
            'content_outline': content_outline,
            'keyword_recommendations': keyword_recommendations
        }
        
        return plan
    
    def _cluster_concepts(self, concepts):
        """
        تقسيم المفاهيم إلى مجموعات متشابهة
        
        Args:
            concepts (list): قائمة المفاهيم
            
        Returns:
            dict: المفاهيم مقسمة إلى مجموعات
        """
        # طريقة مبسطة للتجميع
        # في التطبيق الحقيقي، يمكن استخدام خوارزميات التجميع مثل K-means
        
        clusters = {
            'معلومات عامة': [],
            'مواصفات تقنية': [],
            'فوائد وميزات': [],
            'مفاهيم متقدمة': []
        }
        
        technical_terms = ['برمجة', 'تقنية', 'كود', 'خوارزمية', 'تحليل', 'بيانات', 'أدوات']
        benefit_terms = ['فائدة', 'ميزة', 'تحسين', 'زيادة', 'تطوير', 'نمو', 'أفضل']
        advanced_terms = ['متقدم', 'احترافي', 'خبير', 'متخصص', 'استراتيجية']
        
        for concept in concepts:
            concept_text = concept['concept'].lower()
            
            if any(term in concept_text for term in technical_terms):
                clusters['مواصفات تقنية'].append(concept)
            elif any(term in concept_text for term in benefit_terms):
                clusters['فوائد وميزات'].append(concept)
            elif any(term in concept_text for term in advanced_terms):
                clusters['مفاهيم متقدمة'].append(concept)
            else:
                clusters['معلومات عامة'].append(concept)
        
        return clusters
    
    def _generate_content_outline(self, main_topic, subtopics, content_type):
        """
        توليد مخطط للمحتوى بناءً على الموضوع ونوع المحتوى
        
        Args:
            main_topic (str): الموضوع الرئيسي
            subtopics (list): المواضيع الفرعية
            content_type (str): نوع المحتوى
            
        Returns:
            dict: مخطط المحتوى
        """
        outline = {
            'title': f'{main_topic} - دليل شامل',
            'sections': []
        }
        
        # المقدمة
        outline['sections'].append({
            'type': 'introduction',
            'title': 'مقدمة',
            'content_suggestion': f'تقديم الموضوع الرئيسي "{main_topic}" وأهميته وعرض عام لما سيتم تناوله في المحتوى.'
        })
        
        # أقسام فرعية بناءً على المواضيع الفرعية
        for subtopic in subtopics:
            outline['sections'].append({
                'type': 'section',
                'title': subtopic,
                'content_suggestion': f'شرح تفصيلي حول {subtopic} وعلاقته بـ {main_topic}.'
            })
        
        # تعديل العنوان والأقسام حسب نوع المحتوى
        if content_type == 'product':
            outline['title'] = f'{main_topic} - مراجعة شاملة والمميزات'
            outline['sections'].insert(1, {
                'type': 'section',
                'title': 'مميزات المنتج',
                'content_suggestion': f'تفاصيل حول مميزات {main_topic} والفوائد التي يقدمها.'
            })
            outline['sections'].insert(2, {
                'type': 'section',
                'title': 'مواصفات تقنية',
                'content_suggestion': f'المواصفات التقنية لـ {main_topic} بشكل تفصيلي.'
            })
            
        elif content_type == 'guide':
            outline['title'] = f'دليل خطوة بخطوة لـ {main_topic}'
            outline['sections'].insert(1, {
                'type': 'section',
                'title': 'فهم أساسيات',
                'content_suggestion': f'شرح للمفاهيم الأساسية في {main_topic} قبل الانتقال للخطوات التفصيلية.'
            })
        
        # إضافة خاتمة
        outline['sections'].append({
            'type': 'conclusion',
            'title': 'الخلاصة',
            'content_suggestion': f'تلخيص النقاط الرئيسية حول {main_topic} مع التأكيد على أهميته.'
        })
        
        # إضافة أسئلة شائعة
        outline['sections'].append({
            'type': 'faq',
            'title': 'أسئلة شائعة',
            'content_suggestion': f'إجابة على الأسئلة الشائعة المتعلقة بـ {main_topic}.'
        })
        
        return outline
