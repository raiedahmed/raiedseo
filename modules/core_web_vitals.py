#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - محلل Core Web Vitals

تحليل مؤشرات Core Web Vitals للصفحات وتقديم توصيات للتحسين
يقيس LCP (Largest Contentful Paint)، FID (First Input Delay)،
وCLS (Cumulative Layout Shift)
"""

import requests
import json
import time
import logging
from urllib.parse import urlparse
import subprocess
import os
import re
import tempfile

class CoreWebVitalsAnalyzer:
    """محلل مؤشرات Core Web Vitals للصفحات"""
    
    def __init__(self, config=None):
        """
        تهيئة محلل مؤشرات Core Web Vitals
        
        Args:
            config (dict, optional): إعدادات التحليل. الافتراضي None.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.pagespeed_api_key = os.environ.get('PAGESPEED_API_KEY', '')
        self.use_api = self.pagespeed_api_key != ''
        
        # العتبات لمؤشرات Core Web Vitals
        self.thresholds = {
            'lcp': {
                'good': 2500,       # أقل من 2.5 ثانية
                'needs_improvement': 4000  # أقل من 4 ثواني
            },
            'fid': {
                'good': 100,        # أقل من 100 مللي ثانية
                'needs_improvement': 300   # أقل من 300 مللي ثانية
            },
            'cls': {
                'good': 0.1,        # أقل من 0.1
                'needs_improvement': 0.25  # أقل من 0.25
            },
            'ttfb': {
                'good': 800,        # أقل من 800 مللي ثانية
                'needs_improvement': 1800  # أقل من 1.8 ثانية
            },
            'fcp': {
                'good': 1800,       # أقل من 1.8 ثانية
                'needs_improvement': 3000  # أقل من 3 ثواني
            }
        }
    
    def analyze(self, url, use_lighthouse=True):
        """
        تحليل مؤشرات Core Web Vitals للصفحة
        
        Args:
            url (str): رابط الصفحة للتحليل
            use_lighthouse (bool): استخدام Lighthouse للتحليل إذا لم يكن API متاحًا
            
        Returns:
            dict: نتائج تحليل مؤشرات Core Web Vitals
        """
        results = {
            'url': url,
            'timestamp': int(time.time()),
            'metrics': {
                'lcp': None,  # Largest Contentful Paint
                'fid': None,  # First Input Delay (تقديري من خلال TBT)
                'cls': None,  # Cumulative Layout Shift
                'fcp': None,  # First Contentful Paint
                'ttfb': None, # Time to First Byte
                'tbt': None,  # Total Blocking Time
                'tti': None   # Time to Interactive
            },
            'scores': {
                'lcp': None,
                'fid': None,
                'cls': None,
                'overall': None
            },
            'status': {},
            'issues': [],
            'suggestions': []
        }
        
        try:
            if self.use_api:
                # استخدام PageSpeed Insights API
                results = self._analyze_with_pagespeed_api(url, results)
            elif use_lighthouse:
                # استخدام Lighthouse محليًا
                results = self._analyze_with_lighthouse(url, results)
            else:
                results['issues'].append("لا يمكن تحليل Core Web Vitals: مفتاح API غير متوفر وLighthouse غير مفعل")
                return results
            
            # تحليل النتائج وإضافة الاقتراحات
            results = self._analyze_results(results)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل Core Web Vitals للصفحة {url}: {str(e)}")
            results['issues'].append(f"خطأ في التحليل: {str(e)}")
        
        return results
    
    def _analyze_with_pagespeed_api(self, url, results):
        """
        تحليل باستخدام PageSpeed Insights API
        
        Args:
            url (str): رابط الصفحة
            results (dict): قاموس النتائج الأولية
            
        Returns:
            dict: النتائج المحدثة
        """
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile&key={self.pagespeed_api_key}"
        
        try:
            response = requests.get(api_url, timeout=60)
            if response.status_code != 200:
                results['issues'].append(f"فشل طلب PageSpeed API: الحالة {response.status_code}")
                return results
            
            data = response.json()
            
            # استخراج البيانات من النتائج
            metrics = data.get('loadingExperience', {}).get('metrics', {})
            lab_data = data.get('lighthouseResult', {}).get('audits', {})
            
            # بيانات المؤشرات الحقيقية (field data)
            if 'LARGEST_CONTENTFUL_PAINT_MS' in metrics:
                lcp_data = metrics['LARGEST_CONTENTFUL_PAINT_MS'].get('distributions', [])
                if lcp_data and len(lcp_data) >= 3:
                    # استخدام القيمة الوسطى (تقريبية)
                    results['metrics']['lcp'] = (lcp_data[0].get('max', 0) + lcp_data[1].get('min', 0)) / 2
            
            if 'FIRST_INPUT_DELAY_MS' in metrics:
                fid_data = metrics['FIRST_INPUT_DELAY_MS'].get('distributions', [])
                if fid_data and len(fid_data) >= 3:
                    # استخدام القيمة الوسطى (تقريبية)
                    results['metrics']['fid'] = (fid_data[0].get('max', 0) + fid_data[1].get('min', 0)) / 2
            
            if 'CUMULATIVE_LAYOUT_SHIFT_SCORE' in metrics:
                cls_data = metrics['CUMULATIVE_LAYOUT_SHIFT_SCORE'].get('distributions', [])
                if cls_data and len(cls_data) >= 3:
                    # استخدام القيمة الوسطى (تقريبية)
                    results['metrics']['cls'] = (cls_data[0].get('max', 0) + cls_data[1].get('min', 0)) / 2
            
            # بيانات المختبر (lab data)
            if 'largest-contentful-paint' in lab_data:
                if results['metrics']['lcp'] is None:  # إذا لم تكن البيانات الحقيقية متوفرة
                    results['metrics']['lcp'] = lab_data['largest-contentful-paint'].get('numericValue')
            
            if 'total-blocking-time' in lab_data:
                results['metrics']['tbt'] = lab_data['total-blocking-time'].get('numericValue')
                # تقدير FID من TBT إذا لم تكن البيانات الحقيقية متوفرة
                if results['metrics']['fid'] is None and results['metrics']['tbt'] is not None:
                    results['metrics']['fid'] = results['metrics']['tbt'] * 0.3  # تقريب مبسط
            
            if 'cumulative-layout-shift' in lab_data:
                if results['metrics']['cls'] is None:  # إذا لم تكن البيانات الحقيقية متوفرة
                    results['metrics']['cls'] = lab_data['cumulative-layout-shift'].get('numericValue')
            
            if 'first-contentful-paint' in lab_data:
                results['metrics']['fcp'] = lab_data['first-contentful-paint'].get('numericValue')
            
            if 'server-response-time' in lab_data:
                results['metrics']['ttfb'] = lab_data['server-response-time'].get('numericValue')
            
            if 'interactive' in lab_data:
                results['metrics']['tti'] = lab_data['interactive'].get('numericValue')
            
            # جمع المشكلات والاقتراحات من تقرير Lighthouse
            if 'lighthouseResult' in data and 'audits' in data['lighthouseResult']:
                audits = data['lighthouseResult']['audits']
                
                performance_issues = [
                    'render-blocking-resources',
                    'unminified-css',
                    'unminified-javascript',
                    'unused-css-rules',
                    'unused-javascript',
                    'offscreen-images',
                    'uses-responsive-images',
                    'uses-webp-images',
                    'uses-optimized-images',
                    'uses-text-compression',
                    'uses-rel-preconnect',
                    'server-response-time',
                    'efficient-animated-content',
                    'duplicated-javascript',
                    'legacy-javascript',
                    'dom-size',
                    'unsized-images'
                ]
                
                for issue in performance_issues:
                    if issue in audits and audits[issue].get('score', 1) < 0.9:
                        description = audits[issue].get('title', '')
                        details = audits[issue].get('description', '').split('.')[0]  # الجملة الأولى فقط
                        results['issues'].append(f"{description}: {details}")
            
        except Exception as e:
            results['issues'].append(f"خطأ في تحليل PageSpeed API: {str(e)}")
        
        return results
    
    def _analyze_with_lighthouse(self, url, results):
        """
        تحليل باستخدام Lighthouse محليًا
        
        Args:
            url (str): رابط الصفحة
            results (dict): قاموس النتائج الأولية
            
        Returns:
            dict: النتائج المحدثة
        """
        try:
            # التحقق من وجود Lighthouse
            try:
                subprocess.run(['lighthouse', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                results['issues'].append("Lighthouse غير مثبت. الرجاء تثبيت Lighthouse بالأمر: npm install -g lighthouse")
                return results
            
            # إنشاء مجلد مؤقت للنتائج
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, 'lighthouse-report.json')
                
                # تشغيل Lighthouse
                cmd = [
                    'lighthouse', url,
                    '--output=json',
                    '--output-path=' + output_path,
                    '--only-categories=performance',
                    '--chrome-flags="--headless --no-sandbox --disable-gpu"'
                ]
                
                subprocess.run(' '.join(cmd), shell=True, check=True)
                
                # قراءة النتائج
                if os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    audits = data.get('audits', {})
                    
                    # استخراج القيم الرقمية
                    if 'largest-contentful-paint' in audits:
                        results['metrics']['lcp'] = audits['largest-contentful-paint'].get('numericValue')
                    
                    if 'total-blocking-time' in audits:
                        results['metrics']['tbt'] = audits['total-blocking-time'].get('numericValue')
                        # تقدير FID من TBT
                        if results['metrics']['tbt'] is not None:
                            results['metrics']['fid'] = results['metrics']['tbt'] * 0.3  # تقريب مبسط
                    
                    if 'cumulative-layout-shift' in audits:
                        results['metrics']['cls'] = audits['cumulative-layout-shift'].get('numericValue')
                    
                    if 'first-contentful-paint' in audits:
                        results['metrics']['fcp'] = audits['first-contentful-paint'].get('numericValue')
                    
                    if 'server-response-time' in audits:
                        results['metrics']['ttfb'] = audits['server-response-time'].get('numericValue')
                    
                    if 'interactive' in audits:
                        results['metrics']['tti'] = audits['interactive'].get('numericValue')
                    
                    # جمع المشكلات والاقتراحات
                    performance_issues = [
                        'render-blocking-resources',
                        'unminified-css',
                        'unminified-javascript',
                        'unused-css-rules',
                        'unused-javascript',
                        'offscreen-images',
                        'uses-responsive-images',
                        'uses-webp-images',
                        'uses-optimized-images',
                        'uses-text-compression',
                        'uses-rel-preconnect',
                        'server-response-time',
                        'efficient-animated-content',
                        'duplicated-javascript',
                        'legacy-javascript',
                        'dom-size',
                        'unsized-images'
                    ]
                    
                    for issue in performance_issues:
                        if issue in audits and audits[issue].get('score', 1) < 0.9:
                            description = audits[issue].get('title', '')
                            details = audits[issue].get('description', '').split('.')[0]  # الجملة الأولى فقط
                            results['issues'].append(f"{description}: {details}")
                else:
                    results['issues'].append("فشل إنشاء تقرير Lighthouse")
        
        except Exception as e:
            results['issues'].append(f"خطأ في تحليل Lighthouse: {str(e)}")
        
        return results
    
    def _analyze_results(self, results):
        """
        تحليل النتائج وإضافة التوصيات بناءً على القياسات
        
        Args:
            results (dict): نتائج التحليل
            
        Returns:
            dict: النتائج مع التوصيات
        """
        metrics = results['metrics']
        
        # تحديد حالة كل مؤشر
        for metric in ['lcp', 'fid', 'cls', 'fcp', 'ttfb']:
            if metrics[metric] is not None:
                value = metrics[metric]
                
                if metric == 'lcp' or metric == 'fid' or metric == 'fcp' or metric == 'ttfb':
                    value_ms = value  # القيم بالمللي ثانية
                    if value_ms <= self.thresholds[metric]['good']:
                        status = "جيد"
                    elif value_ms <= self.thresholds[metric]['needs_improvement']:
                        status = "يحتاج إلى تحسين"
                    else:
                        status = "ضعيف"
                elif metric == 'cls':
                    if value <= self.thresholds[metric]['good']:
                        status = "جيد"
                    elif value <= self.thresholds[metric]['needs_improvement']:
                        status = "يحتاج إلى تحسين"
                    else:
                        status = "ضعيف"
                
                results['status'][metric] = status
                
                # إضافة توصيات محددة لكل مؤشر
                if status in ["يحتاج إلى تحسين", "ضعيف"]:
                    if metric == 'lcp':
                        results['suggestions'].append(
                            "تحسين LCP: تحسين تحميل العناصر الرئيسية، تقليل حجم الصور، استخدام CDN، تحسين وقت استجابة الخادم."
                        )
                    elif metric == 'fid':
                        results['suggestions'].append(
                            "تحسين FID: تقليل وقت تنفيذ JavaScript، تجزئة المهام الطويلة، تأجيل تحميل JavaScript غير الضروري."
                        )
                    elif metric == 'cls':
                        results['suggestions'].append(
                            "تحسين CLS: تعيين أبعاد ثابتة للصور والإعلانات، لا تضف محتوى فوق المحتوى الحالي، استخدم تحولات متسلسلة."
                        )
                    elif metric == 'fcp':
                        results['suggestions'].append(
                            "تحسين FCP: تقليل الموارد المانعة للعرض، ضغط ملفات CSS و JavaScript، تحسين الخطوط."
                        )
                    elif metric == 'ttfb':
                        results['suggestions'].append(
                            "تحسين TTFB: تحسين أداء الخادم، استخدام التخزين المؤقت، CDN، تحسين قواعد البيانات."
                        )
        
        # حساب الدرجات
        for metric in ['lcp', 'fid', 'cls']:
            if metrics[metric] is not None:
                value = metrics[metric]
                
                if metric == 'lcp':
                    # أقل من 2.5 ثانية: 1، أكثر من 4 ثوانٍ: 0
                    if value <= self.thresholds[metric]['good']:
                        score = 1.0
                    elif value >= self.thresholds[metric]['needs_improvement']:
                        score = 0.0
                    else:
                        # درجة خطية بين 0 و 1
                        score = 1.0 - ((value - self.thresholds[metric]['good']) /
                                      (self.thresholds[metric]['needs_improvement'] - self.thresholds[metric]['good']))
                
                elif metric == 'fid':
                    # أقل من 100 مللي ثانية: 1، أكثر من 300 مللي ثانية: 0
                    if value <= self.thresholds[metric]['good']:
                        score = 1.0
                    elif value >= self.thresholds[metric]['needs_improvement']:
                        score = 0.0
                    else:
                        # درجة خطية بين 0 و 1
                        score = 1.0 - ((value - self.thresholds[metric]['good']) /
                                      (self.thresholds[metric]['needs_improvement'] - self.thresholds[metric]['good']))
                
                elif metric == 'cls':
                    # أقل من 0.1: 1، أكثر من 0.25: 0
                    if value <= self.thresholds[metric]['good']:
                        score = 1.0
                    elif value >= self.thresholds[metric]['needs_improvement']:
                        score = 0.0
                    else:
                        # درجة خطية بين 0 و 1
                        score = 1.0 - ((value - self.thresholds[metric]['good']) /
                                      (self.thresholds[metric]['needs_improvement'] - self.thresholds[metric]['good']))
                
                results['scores'][metric] = round(score, 2)
        
        # حساب الدرجة الإجمالية (تقريب للنموذج الحقيقي من Google)
        if all(results['scores'][m] is not None for m in ['lcp', 'fid', 'cls']):
            # أوزان مقاربة لتلك المستخدمة في Core Web Vitals
            weights = {'lcp': 0.25, 'fid': 0.3, 'cls': 0.45}
            overall_score = sum(results['scores'][m] * weights[m] for m in weights)
            results['scores']['overall'] = round(overall_score, 2)
        
        return results
