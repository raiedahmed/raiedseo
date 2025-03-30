#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - محلل الكلمات المفتاحية
تحليل وتقييم الكلمات المفتاحية للمواقع
"""

import re
import requests
from bs4 import BeautifulSoup
import json
import time
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from utils.logger import get_logger

class KeywordAnalyzer:
    """محلل الكلمات المفتاحية - تحليل وتقييم الكلمات المفتاحية للمواقع"""

    def __init__(self):
        """تهيئة محلل الكلمات المفتاحية"""
        self.logger = get_logger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.stop_words = self._get_stop_words()
    
    def analyze(self, page_data):
        """تحليل الكلمات المفتاحية في صفحة

        Args:
            page_data (dict): بيانات الصفحة

        Returns:
            dict: نتائج تحليل الكلمات المفتاحية
        """
        results = {
            'keywords': {},
            'keyword_density': {},
            'title_keywords': [],
            'meta_keywords': [],
            'heading_keywords': [],
            'prominent_keywords': []
        }
        
        try:
            # استخراج النص الكامل
            text = page_data.get('text', '')
            title = page_data.get('title', '')
            description = page_data.get('meta', {}).get('description', '')
            
            # استخراج الكلمات المفتاحية من العنوان
            title_keywords = self._extract_keywords(title)
            results['title_keywords'] = title_keywords
            
            # استخراج الكلمات المفتاحية من الوصف
            description_keywords = self._extract_keywords(description)
            
            # استخراج الكلمات المفتاحية من العناوين
            heading_keywords = []
            for heading_level in ['h1', 'h2', 'h3']:
                if heading_level in page_data:
                    for heading in page_data[heading_level]:
                        heading_keywords.extend(self._extract_keywords(heading))
            
            results['heading_keywords'] = list(set(heading_keywords))
            
            # تحليل نص الصفحة
            if text:
                # تنظيف النص وتقسيمه إلى كلمات
                keywords = self._extract_keywords(text)
                
                # حساب تكرار الكلمات
                keyword_counts = Counter(keywords)
                
                # إجمالي عدد الكلمات (بعد التصفية)
                total_words = len(keywords)
                
                # حساب كثافة الكلمات المفتاحية
                keyword_density = {}
                for keyword, count in keyword_counts.items():
                    density = (count / total_words) * 100 if total_words > 0 else 0
                    keyword_density[keyword] = round(density, 2)
                
                # ترتيب الكلمات حسب التكرار
                sorted_keywords = dict(sorted(
                    keyword_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20])  # الاحتفاظ بأعلى 20 كلمة
                
                results['keywords'] = sorted_keywords
                results['keyword_density'] = dict(sorted(
                    keyword_density.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:20])
                
                # تحديد الكلمات المفتاحية البارزة (التي تظهر في العنوان والوصف والعناوين والمحتوى)
                prominent_keywords = []
                
                for keyword in keyword_counts:
                    prominence_score = 0
                    
                    # زيادة النتيجة إذا ظهرت الكلمة في العنوان
                    if keyword in title_keywords:
                        prominence_score += 3
                    
                    # زيادة النتيجة إذا ظهرت الكلمة في الوصف
                    if keyword in description_keywords:
                        prominence_score += 2
                    
                    # زيادة النتيجة إذا ظهرت الكلمة في العناوين
                    if keyword in heading_keywords:
                        prominence_score += 2
                    
                    # زيادة النتيجة بناءً على كثافة الكلمة في النص
                    density = keyword_density.get(keyword, 0)
                    if density > 3:
                        prominence_score += 3
                    elif density > 1:
                        prominence_score += 2
                    elif density > 0.5:
                        prominence_score += 1
                    
                    if prominence_score >= 3:  # اعتبار الكلمة بارزة إذا كانت النتيجة >= 3
                        prominent_keywords.append({
                            'keyword': keyword,
                            'score': prominence_score,
                            'count': keyword_counts[keyword],
                            'density': keyword_density.get(keyword, 0)
                        })
                
                # ترتيب الكلمات البارزة حسب النتيجة
                prominent_keywords.sort(key=lambda x: x['score'], reverse=True)
                results['prominent_keywords'] = prominent_keywords[:10]  # أعلى 10 كلمات بارزة
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الكلمات المفتاحية: {str(e)}")
        
        return results
    
    def analyze_keywords(self, keywords, url=None):
        """تحليل قائمة كلمات مفتاحية وتقييمها

        Args:
            keywords (list): قائمة الكلمات المفتاحية للتحليل
            url (str, optional): رابط الموقع للتحقق من وجود الكلمات المفتاحية فيه. الافتراضي None.

        Returns:
            dict: نتائج تحليل الكلمات المفتاحية
        """
        results = {
            'keywords': [],
            'summary': {
                'total': len(keywords),
                'analyzed': 0,
                'high_competition': 0,
                'medium_competition': 0,
                'low_competition': 0
            }
        }
        
        try:
            # تحليل كل كلمة مفتاحية
            with ThreadPoolExecutor(max_workers=5) as executor:
                keyword_results = list(executor.map(self._analyze_single_keyword, keywords))
            
            results['keywords'] = keyword_results
            
            # تحديث الملخص
            results['summary']['analyzed'] = len(keyword_results)
            
            for keyword_data in keyword_results:
                competition = keyword_data.get('competition', '')
                if competition == 'high':
                    results['summary']['high_competition'] += 1
                elif competition == 'medium':
                    results['summary']['medium_competition'] += 1
                elif competition == 'low':
                    results['summary']['low_competition'] += 1
            
            # إذا كان هناك رابط، تحقق من وجود الكلمات المفتاحية في الموقع
            if url:
                self.logger.info(f"التحقق من وجود الكلمات المفتاحية في {url}")
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # استخراج النص
                        text = soup.get_text()
                        # استخراج العنوان
                        title = soup.title.text if soup.title else ''
                        # استخراج العناوين
                        headings = ' '.join([h.text for h in soup.find_all(['h1', 'h2', 'h3'])])
                        # استخراج الميتا ديسكريبشن
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        description = meta_desc['content'] if meta_desc else ''
                        
                        # فحص كل كلمة مفتاحية
                        for i, keyword_data in enumerate(results['keywords']):
                            keyword = keyword_data['keyword']
                            
                            # التحقق من وجود الكلمة المفتاحية في العنوان
                            in_title = keyword.lower() in title.lower()
                            
                            # التحقق من وجود الكلمة المفتاحية في العناوين
                            in_headings = keyword.lower() in headings.lower()
                            
                            # التحقق من وجود الكلمة المفتاحية في الوصف
                            in_description = keyword.lower() in description.lower()
                            
                            # حساب عدد مرات ظهور الكلمة المفتاحية في النص
                            occurrences = text.lower().count(keyword.lower())
                            
                            # تحديث بيانات الكلمة المفتاحية
                            results['keywords'][i]['site_analysis'] = {
                                'in_title': in_title,
                                'in_headings': in_headings,
                                'in_description': in_description,
                                'occurrences': occurrences,
                                'found': occurrences > 0
                            }
                            
                            # تقييم مدى تحسين الكلمة المفتاحية
                            optimization_score = 0
                            if in_title:
                                optimization_score += 3
                            if in_headings:
                                optimization_score += 2
                            if in_description:
                                optimization_score += 2
                            
                            if occurrences > 5:
                                optimization_score += 3
                            elif occurrences > 2:
                                optimization_score += 2
                            elif occurrences > 0:
                                optimization_score += 1
                            
                            optimization_level = 'high' if optimization_score >= 6 else 'medium' if optimization_score >= 3 else 'low'
                            results['keywords'][i]['site_analysis']['optimization_level'] = optimization_level
                
                except Exception as e:
                    self.logger.error(f"خطأ في تحليل الموقع {url}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الكلمات المفتاحية: {str(e)}")
        
        return results
    
    def _analyze_single_keyword(self, keyword):
        """تحليل كلمة مفتاحية واحدة

        Args:
            keyword (str): الكلمة المفتاحية للتحليل

        Returns:
            dict: نتائج تحليل الكلمة المفتاحية
        """
        result = {
            'keyword': keyword,
            'length': len(keyword),
            'word_count': len(keyword.split()),
            'has_numbers': bool(re.search(r'\d', keyword)),
            'has_special_chars': bool(re.search(r'[^\w\s]', keyword)),
            'competition': 'medium',  # الافتراضي
            'search_volume': None,
            'difficulty': None,
            'trend': None,
            'suggestions': []
        }
        
        try:
            # محاكاة بيانات البحث (في التطبيق الفعلي، يمكن استخدام API مثل Google Keyword Planner)
            result.update(self._simulate_keyword_data(keyword))
            
            # اقتراح كلمات مفتاحية ذات صلة
            result['suggestions'] = self._get_related_keywords(keyword)
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الكلمة المفتاحية '{keyword}': {str(e)}")
        
        return result
    
    def _extract_keywords(self, text):
        """استخراج الكلمات المفتاحية من النص

        Args:
            text (str): النص المراد تحليله

        Returns:
            list: قائمة الكلمات المفتاحية
        """
        if not text:
            return []
        
        # تحويل النص إلى أحرف صغيرة وإزالة الأرقام والرموز الخاصة
        text = text.lower()
        
        # تقسيم النص إلى كلمات
        words = re.findall(r'\b\w+\b', text)
        
        # استبعاد الكلمات القصيرة والكلمات الشائعة
        filtered_words = [word for word in words if len(word) > 3 and word not in self.stop_words]
        
        return filtered_words
    
    def _get_stop_words(self):
        """الحصول على قائمة الكلمات الشائعة التي يجب استبعادها

        Returns:
            set: مجموعة الكلمات الشائعة
        """
        # كلمات شائعة باللغة الإنجليزية
        english_stop_words = {
            'the', 'and', 'to', 'of', 'a', 'in', 'for', 'is', 'on', 'that',
            'by', 'this', 'with', 'i', 'you', 'it', 'not', 'or', 'be', 'are',
            'from', 'at', 'as', 'your', 'have', 'more', 'has', 'an', 'was', 'we'
        }
        
        # كلمات شائعة باللغة العربية
        arabic_stop_words = {
            'في', 'من', 'إلى', 'على', 'أن', 'عن', 'مع', 'هذا', 'هذه', 'ذلك',
            'التي', 'الذي', 'وهو', 'وهي', 'أو', 'ثم', 'حتى', 'إذا', 'كما', 'كان',
            'لكن', 'و', 'ف', 'ب', 'ل', 'لل', 'ال', 'الى'
        }
        
        return english_stop_words.union(arabic_stop_words)
    
    def _simulate_keyword_data(self, keyword):
        """محاكاة بيانات الكلمة المفتاحية (حجم البحث، المنافسة، إلخ)

        Args:
            keyword (str): الكلمة المفتاحية

        Returns:
            dict: بيانات الكلمة المفتاحية
        """
        # هذه دالة محاكاة لأغراض العرض
        # في التطبيق الفعلي، يمكن استخدام API مثل Google Keyword Planner أو SEMrush
        
        # تحديد درجة المنافسة بناءً على طول الكلمة المفتاحية
        word_count = len(keyword.split())
        has_long_tail = word_count >= 3
        
        if word_count == 1:
            competition = 'high'
            search_volume = 1000 + (hash(keyword) % 9000)  # قيمة عشوائية بين 1000 و 10000
            difficulty = 70 + (hash(keyword[::-1]) % 30)  # قيمة عشوائية بين 70 و 100
        elif word_count == 2:
            competition = 'medium'
            search_volume = 100 + (hash(keyword) % 900)  # قيمة عشوائية بين 100 و 1000
            difficulty = 40 + (hash(keyword[::-1]) % 30)  # قيمة عشوائية بين 40 و 70
        else:
            competition = 'low'
            search_volume = 10 + (hash(keyword) % 90)  # قيمة عشوائية بين 10 و 100
            difficulty = 10 + (hash(keyword[::-1]) % 30)  # قيمة عشوائية بين 10 و 40
        
        # محاكاة اتجاه البحث
        trend_options = ['rising', 'stable', 'declining']
        trend = trend_options[hash(keyword) % 3]
        
        return {
            'competition': competition,
            'search_volume': search_volume,
            'difficulty': difficulty,
            'trend': trend,
            'is_long_tail': has_long_tail
        }
    
    def _get_related_keywords(self, keyword):
        """الحصول على اقتراحات للكلمات المفتاحية ذات الصلة

        Args:
            keyword (str): الكلمة المفتاحية الأساسية

        Returns:
            list: قائمة الاقتراحات
        """
        # هذه دالة محاكاة لأغراض العرض
        # في التطبيق الفعلي، يمكن استخدام API مثل Google Suggest أو Ubersuggest
        
        words = keyword.split()
        
        if len(words) == 1:
            # كلمة مفتاحية من كلمة واحدة
            suggestions = [
                f"best {keyword}",
                f"{keyword} online",
                f"{keyword} benefits",
                f"{keyword} vs",
                f"how to {keyword}",
                f"what is {keyword}"
            ]
        else:
            # كلمة مفتاحية من عدة كلمات
            suggestions = [
                f"best {keyword}",
                f"{keyword} examples",
                f"{keyword} tutorial",
                f"how to use {keyword}",
                f"{keyword} alternatives",
                f"{keyword} meaning"
            ]
        
        return suggestions
