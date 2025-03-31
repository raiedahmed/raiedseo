#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - محلل E-E-A-T

تحليل عوامل الخبرة والسلطة والجدارة بالثقة والتجربة (E-E-A-T) للمواقع
وفقًا لإرشادات Google الحديثة
"""

import re
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urljoin
import time
import logging

class EEATAnalyzer:
    """
    محلل عوامل الخبرة والسلطة والجدارة بالثقة والتجربة (E-E-A-T)
    
    يقوم بتحليل عناصر E-E-A-T على الموقع وتقديم توصيات للتحسين
    (Experience, Expertise, Authoritativeness, Trustworthiness)
    """
    
    def __init__(self, config=None):
        """
        تهيئة محلل E-E-A-T
        
        Args:
            config (dict, optional): إعدادات التحليل. الافتراضي None.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def analyze(self, url, html_content=None):
        """
        تحليل مؤشرات E-E-A-T على الصفحة
        
        Args:
            url (str): رابط الصفحة للتحليل
            html_content (str, optional): محتوى HTML للصفحة إذا كان متاحًا. الافتراضي None.
            
        Returns:
            dict: نتائج تحليل E-E-A-T
        """
        results = {
            'url': url,
            'timestamp': int(time.time()),
            'experience': {
                'score': 0,
                'findings': [],
                'suggestions': []
            },
            'expertise': {
                'score': 0,
                'findings': [],
                'suggestions': []
            },
            'authoritativeness': {
                'score': 0,
                'findings': [],
                'suggestions': []
            },
            'trustworthiness': {
                'score': 0,
                'findings': [],
                'suggestions': []
            },
            'overall_score': 0
        }
        
        try:
            # الحصول على محتوى الصفحة إذا لم يتم توفيره
            if not html_content:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    self.logger.error(f"فشل في الحصول على محتوى الصفحة {url}, الحالة: {response.status_code}")
                    return results
                html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # تحليل عامل التجربة (Experience)
            experience_score, experience_findings, experience_suggestions = self._analyze_experience(soup, url)
            results['experience']['score'] = experience_score
            results['experience']['findings'] = experience_findings
            results['experience']['suggestions'] = experience_suggestions
            
            # تحليل عامل الخبرة (Expertise)
            expertise_score, expertise_findings, expertise_suggestions = self._analyze_expertise(soup, url)
            results['expertise']['score'] = expertise_score
            results['expertise']['findings'] = expertise_findings
            results['expertise']['suggestions'] = expertise_suggestions
            
            # تحليل عامل السلطة (Authoritativeness)
            authority_score, authority_findings, authority_suggestions = self._analyze_authoritativeness(soup, url)
            results['authoritativeness']['score'] = authority_score
            results['authoritativeness']['findings'] = authority_findings
            results['authoritativeness']['suggestions'] = authority_suggestions
            
            # تحليل عامل الجدارة بالثقة (Trustworthiness)
            trust_score, trust_findings, trust_suggestions = self._analyze_trustworthiness(soup, url)
            results['trustworthiness']['score'] = trust_score
            results['trustworthiness']['findings'] = trust_findings
            results['trustworthiness']['suggestions'] = trust_suggestions
            
            # حساب النتيجة الإجمالية (مع الأوزان)
            results['overall_score'] = (
                experience_score * 0.2 +  # وزن التجربة
                expertise_score * 0.3 +   # وزن الخبرة
                authority_score * 0.25 +  # وزن السلطة
                trust_score * 0.25        # وزن الجدارة بالثقة
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل E-E-A-T للصفحة {url}: {str(e)}")
        
        return results
    
    def _analyze_experience(self, soup, url):
        """
        تحليل عامل التجربة (Experience)
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            url (str): رابط الصفحة
            
        Returns:
            tuple: (النتيجة، النتائج، التوصيات)
        """
        score = 0
        findings = []
        suggestions = []
        
        # البحث عن مؤشرات تجربة المستخدم
        user_reviews = soup.find_all(class_=re.compile(r'(review|comment|testimonial)', re.I))
        if user_reviews:
            score += min(len(user_reviews) * 5, 30)
            findings.append(f"تم العثور على {len(user_reviews)} مراجعة/شهادة للمستخدمين")
        else:
            suggestions.append("إضافة مراجعات أو شهادات المستخدمين لتعزيز عامل التجربة")
        
        # وجود قسم "من نحن" أو سيرة ذاتية
        about_links = soup.find_all('a', href=re.compile(r'(about|about-us|team|story)', re.I))
        if about_links:
            score += 15
            findings.append("يحتوي الموقع على صفحة 'من نحن' أو قصة الشركة")
        else:
            suggestions.append("إضافة صفحة 'من نحن' تشرح خلفية وتجربة الشركة أو المؤلف")
        
        # وجود صور حقيقية للأشخاص (وليست صور مخزنة)
        person_images = soup.find_all('img', alt=re.compile(r'(team|staff|employee|founder|ceo|author)', re.I))
        if person_images:
            score += 15
            findings.append(f"تم العثور على {len(person_images)} صورة لفريق العمل أو المؤلفين")
        else:
            suggestions.append("إضافة صور حقيقية للفريق أو المؤلفين لتعزيز المصداقية")
        
        # تاريخ آخر تحديث للمحتوى
        update_dates = soup.find_all(string=re.compile(r'(updated|last modified|revised on)', re.I))
        if update_dates:
            score += 10
            findings.append("يحتوي المحتوى على تواريخ التحديث")
        else:
            suggestions.append("إضافة تواريخ التحديث للمحتوى لإظهار أنه محتوى محدّث")
        
        # البحث عن قصص حقيقية أو دراسات حالة
        case_studies = soup.find_all(string=re.compile(r'(case study|success story|experience with)', re.I))
        if case_studies:
            score += 15
            findings.append("يحتوي المحتوى على دراسات حالة أو قصص نجاح")
        else:
            suggestions.append("إضافة دراسات حالة أو قصص نجاح لإظهار الخبرة العملية")
        
        # تقييد النتيجة إلى 100 كحد أقصى
        score = min(score, 100)
        
        return score, findings, suggestions
    
    def _analyze_expertise(self, soup, url):
        """
        تحليل عامل الخبرة (Expertise)
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            url (str): رابط الصفحة
            
        Returns:
            tuple: (النتيجة، النتائج، التوصيات)
        """
        score = 0
        findings = []
        suggestions = []
        
        # البحث عن المؤهلات والشهادات
        qualifications = soup.find_all(string=re.compile(r'(certified|degree|PhD|qualification|diploma|expert|specialist)', re.I))
        if qualifications:
            score += 20
            findings.append("تم العثور على إشارات للمؤهلات أو الشهادات")
        else:
            suggestions.append("إضافة المؤهلات والشهادات ذات الصلة بالمحتوى")
        
        # البحث عن معلومات عن المؤلف
        author_bio = soup.find_all(class_=re.compile(r'(author|bio|profile)', re.I))
        if author_bio:
            score += 20
            findings.append("تم العثور على معلومات عن المؤلف أو السيرة الذاتية")
        else:
            suggestions.append("إضافة معلومات عن المؤلف والخبرة ذات الصلة")
        
        # وجود قسم المراجع أو المصادر
        references = soup.find_all(string=re.compile(r'(reference|source|cited|bibliography)', re.I))
        if references or soup.find_all('cite'):
            score += 20
            findings.append("يحتوي المحتوى على مراجع أو مصادر")
        else:
            suggestions.append("إضافة مراجع أو مصادر للمعلومات المقدمة")
        
        # وجود مصطلحات تقنية متخصصة
        content_text = soup.get_text()
        if re.search(r'(technical term|specialized|methodology|framework|algorithm)', content_text, re.I):
            score += 15
            findings.append("يستخدم المحتوى مصطلحات تقنية متخصصة")
        
        # وجود أقسام استنتاجات أو تحليل
        analysis_sections = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'(analysis|conclusion|findings|results|discussion)', re.I))
        if analysis_sections:
            score += 15
            findings.append("يحتوي المحتوى على أقسام تحليلية أو استنتاجات")
        else:
            suggestions.append("إضافة أقسام تحليلية تظهر الخبرة في الموضوع")
        
        # روابط لمنشورات أكاديمية أو بحثية
        academic_links = soup.find_all('a', href=re.compile(r'(scholar\.google|research|journal|paper|study)', re.I))
        if academic_links:
            score += 10
            findings.append("يحتوي المحتوى على روابط لمصادر أكاديمية أو بحثية")
        else:
            suggestions.append("إضافة روابط لدراسات أكاديمية أو أبحاث ذات صلة")
        
        # تقييد النتيجة إلى 100 كحد أقصى
        score = min(score, 100)
        
        return score, findings, suggestions
    
    def _analyze_authoritativeness(self, soup, url):
        """
        تحليل عامل السلطة (Authoritativeness)
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            url (str): رابط الصفحة
            
        Returns:
            tuple: (النتيجة، النتائج، التوصيات)
        """
        score = 0
        findings = []
        suggestions = []
        
        # تحقق من وجود شعارات أو ارتباطات بمنظمات مرموقة
        affiliation_imgs = soup.find_all('img', alt=re.compile(r'(partner|client|featured in|as seen on)', re.I))
        if affiliation_imgs:
            score += 20
            findings.append(f"تم العثور على {len(affiliation_imgs)} شعار أو ارتباط بمنظمات أخرى")
        else:
            suggestions.append("إضافة شعارات الشركاء أو العملاء المرموقين")
        
        # وجود روابط للمنصات الاجتماعية
        social_links = soup.find_all('a', href=re.compile(r'(twitter\.com|linkedin\.com|facebook\.com|instagram\.com)', re.I))
        if social_links:
            score += 15
            findings.append(f"تم العثور على {len(social_links)} رابط لمنصات التواصل الاجتماعي")
        else:
            suggestions.append("إضافة روابط لحسابات وسائل التواصل الاجتماعي النشطة")
        
        # وجود شهادات أو جوائز
        awards = soup.find_all(string=re.compile(r'(award|recognition|trophy|honor|prize)', re.I))
        if awards:
            score += 20
            findings.append("تم العثور على إشارات للجوائز أو التكريمات")
        else:
            suggestions.append("إضافة الجوائز أو التكريمات التي حصل عليها الموقع أو الشركة")
        
        # وجود اقتباسات من مصادر مرموقة
        quotes = soup.find_all(['blockquote', 'q'])
        if quotes:
            score += 15
            findings.append(f"تم العثور على {len(quotes)} اقتباس في المحتوى")
        
        # وجود شهادة SSL
        if url.startswith('https://'):
            score += 10
            findings.append("الموقع يستخدم شهادة SSL (HTTPS)")
        else:
            suggestions.append("تثبيت شهادة SSL وتفعيل HTTPS للموقع")
        
        # وجود عناوين المكتب الفعلية
        address = soup.find_all(string=re.compile(r'(address|location|headquarter|office)', re.I))
        if address:
            score += 10
            findings.append("تم العثور على عنوان فعلي للشركة أو المكتب")
        else:
            suggestions.append("إضافة عنوان فعلي للشركة أو المؤسسة لزيادة المصداقية")
        
        # وجود صفحة صحفية أو أخبار
        press_links = soup.find_all('a', href=re.compile(r'(press|news|media|coverage)', re.I))
        if press_links:
            score += 10
            findings.append("يحتوي الموقع على قسم للأخبار أو التغطية الإعلامية")
        else:
            suggestions.append("إضافة قسم للأخبار أو التغطية الإعلامية")
        
        # تقييد النتيجة إلى 100 كحد أقصى
        score = min(score, 100)
        
        return score, findings, suggestions
    
    def _analyze_trustworthiness(self, soup, url):
        """
        تحليل عامل الجدارة بالثقة (Trustworthiness)
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            url (str): رابط الصفحة
            
        Returns:
            tuple: (النتيجة، النتائج، التوصيات)
        """
        score = 0
        findings = []
        suggestions = []
        
        # وجود سياسة الخصوصية وشروط الاستخدام
        privacy_links = soup.find_all('a', href=re.compile(r'(privacy|terms|disclaimer)', re.I))
        if privacy_links:
            score += 20
            findings.append("يحتوي الموقع على سياسة الخصوصية وشروط الاستخدام")
        else:
            suggestions.append("إضافة سياسة الخصوصية وشروط الاستخدام")
        
        # وجود معلومات الاتصال
        contact_links = soup.find_all('a', href=re.compile(r'(contact|email|phone|support)', re.I))
        if contact_links:
            score += 15
            findings.append("يحتوي الموقع على معلومات الاتصال")
        else:
            suggestions.append("إضافة معلومات الاتصال الواضحة")
        
        # وجود شهادات الأمان أو الامتثال
        security_badges = soup.find_all('img', alt=re.compile(r'(security|secure|ssl|trust|certified|compliant)', re.I))
        if security_badges:
            score += 15
            findings.append("يعرض الموقع شهادات أمان أو امتثال")
        else:
            suggestions.append("إضافة شهادات الأمان أو الامتثال ذات الصلة")
        
        # وجود تعليقات أو مراجعات العملاء
        reviews = soup.find_all(class_=re.compile(r'(review|rating|testimonial|feedback)', re.I))
        if reviews:
            score += 15
            findings.append(f"تم العثور على {len(reviews)} مراجعة أو تقييم")
        else:
            suggestions.append("إضافة مراجعات وتقييمات العملاء")
        
        # وجود FAQs (أسئلة متكررة)
        faqs = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'(faq|frequently asked|question)', re.I))
        if faqs:
            score += 10
            findings.append("يحتوي الموقع على قسم للأسئلة المتكررة")
        else:
            suggestions.append("إضافة قسم للأسئلة المتكررة لزيادة الشفافية")
        
        # وجود روابط لمواقع خارجية موثوقة
        external_links = soup.find_all('a', attrs={'rel': 'noopener'})
        if external_links:
            score += 10
            findings.append("يحتوي المحتوى على روابط لمصادر خارجية")
        
        # وجود تاريخ نشر أو تحديث واضح
        dates = soup.find_all(['time', 'span'], class_=re.compile(r'(date|time|published|updated)', re.I))
        if dates:
            score += 10
            findings.append("يحتوي المحتوى على تواريخ نشر أو تحديث واضحة")
        else:
            suggestions.append("إضافة تواريخ نشر وتحديث واضحة للمحتوى")
        
        # البحث عن سياسة الاسترجاع أو الضمان (للمتاجر الإلكترونية)
        guarantee = soup.find_all(string=re.compile(r'(guarantee|warranty|refund|return policy)', re.I))
        if guarantee:
            score += 5
            findings.append("يوفر الموقع سياسة ضمان أو استرجاع")
        
        # تقييد النتيجة إلى 100 كحد أقصى
        score = min(score, 100)
        
        return score, findings, suggestions
