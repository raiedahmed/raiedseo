#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تحليل سرعة الصفحة - مسؤولة عن قياس وتحليل أداء سرعة تحميل الصفحة

تستخدم هذه الوحدة Google PageSpeed Insights API و/أو Lighthouse لتحليل
أداء صفحات الويب وتقديم توصيات لتحسين السرعة.
"""

import os
import json
import logging
import requests
import time
import tempfile
import subprocess
from urllib.parse import quote_plus
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class PageSpeedAnalyzer:
    """
    محلل سرعة تحميل الصفحة باستخدام Google PageSpeed Insights API
    أو Lighthouse محليًا إذا لم يكن مفتاح API متوفرًا
    """
    
    def __init__(self, use_api=True):
        """
        تهيئة محلل سرعة الصفحة
        
        Args:
            use_api (bool): استخدام Google PageSpeed Insights API إذا كان متاحًا
        """
        self.logger = logging.getLogger('rseo.page_speed')
        self.api_key = os.getenv('PAGESPEED_API_KEY')
        self.use_api = use_api and self.api_key
        
        if not self.api_key and use_api:
            self.logger.warning("مفتاح PageSpeed API غير محدد. سيتم استخدام التحليل المحلي إذا كان متاحًا.")
    
    def analyze(self, url, strategy='mobile'):
        """
        تحليل سرعة صفحة ويب
        
        Args:
            url (str): عنوان URL للصفحة المراد تحليلها
            strategy (str): استراتيجية التحليل ('mobile' أو 'desktop')
            
        Returns:
            dict: نتائج تحليل سرعة الصفحة والتوصيات
        """
        if self.use_api:
            return self._analyze_with_api(url, strategy)
        else:
            return self._analyze_with_lighthouse(url, strategy)
    
    def _analyze_with_api(self, url, strategy='mobile'):
        """
        تحليل سرعة الصفحة باستخدام Google PageSpeed Insights API
        
        Args:
            url (str): عنوان URL للصفحة المراد تحليلها
            strategy (str): استراتيجية التحليل ('mobile' أو 'desktop')
            
        Returns:
            dict: نتائج تحليل سرعة الصفحة والتوصيات
        """
        api_url = (
            f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={quote_plus(url)}"
            f"&strategy={strategy}"
            f"&locale=ar"
            f"&key={self.api_key}"
        )
        
        try:
            response = requests.get(api_url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # استخراج النتائج المهمة
            result = self._parse_pagespeed_result(data, strategy)
            return result
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"خطأ في تحليل سرعة الصفحة لـ {url}: {str(e)}")
            return self._get_empty_result(url, strategy)
    
    def _analyze_with_lighthouse(self, url, strategy='mobile'):
        """
        تحليل سرعة الصفحة محليًا باستخدام Lighthouse إذا كان متاحًا
        
        Args:
            url (str): عنوان URL للصفحة المراد تحليلها
            strategy (str): استراتيجية التحليل ('mobile' أو 'desktop')
            
        Returns:
            dict: نتائج تحليل سرعة الصفحة والتوصيات
        """
        # التحقق من وجود Lighthouse (يتطلب Node.js و npm)
        try:
            result = subprocess.run(
                ["lighthouse", "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            if result.returncode != 0:
                self.logger.warning("Lighthouse غير مثبت. يتطلب Node.js و npm.")
                return self._get_empty_result(url, strategy)
        except FileNotFoundError:
            self.logger.warning("Lighthouse غير مثبت. يتطلب Node.js و npm.")
            return self._get_empty_result(url, strategy)
        
        # إنشاء مجلد مؤقت لحفظ التقرير
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "lighthouse-report.json")
        
        try:
            # تنفيذ تحليل Lighthouse
            device_flag = "--preset=desktop" if strategy == "desktop" else "--preset=mobile"
            
            command = [
                "lighthouse", url,
                "--output=json",
                "--output-path", output_path,
                "--chrome-flags=\"--headless\"",
                device_flag
            ]
            
            self.logger.info(f"تشغيل Lighthouse: {' '.join(command)}")
            
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                self.logger.error(f"فشل تنفيذ Lighthouse: {process.stderr}")
                return self._get_empty_result(url, strategy)
            
            # قراءة ملف التقرير
            with open(output_path, 'r', encoding='utf-8') as f:
                lighthouse_data = json.load(f)
            
            # تحليل نتائج Lighthouse
            result = self._parse_lighthouse_result(lighthouse_data, strategy)
            return result
            
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ Lighthouse: {str(e)}")
            return self._get_empty_result(url, strategy)
            
        finally:
            # إزالة الملفات المؤقتة
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rmdir(temp_dir)
            except Exception:
                pass
    
    def _parse_pagespeed_result(self, data, strategy):
        """
        تحليل نتائج Google PageSpeed Insights API
        
        Args:
            data (dict): بيانات استجابة PageSpeed API
            strategy (str): استراتيجية التحليل المستخدمة
            
        Returns:
            dict: نتائج منظمة لسرعة الصفحة
        """
        result = {
            'url': data.get('id', ''),
            'strategy': strategy,
            'score': 0,
            'loading_time': None,
            'scores': {},
            'metrics': {},
            'opportunities': [],
            'diagnostics': [],
            'passed_audits': [],
            'issues': []
        }
        
        try:
            # استخراج درجات التقييم الرئيسية
            if 'lighthouseResult' in data and 'categories' in data['lighthouseResult']:
                categories = data['lighthouseResult']['categories']
                
                # درجة التقييم الكلية للأداء
                if 'performance' in categories:
                    perf_score = categories['performance']['score'] * 100
                    result['score'] = round(perf_score)
                    result['scores']['performance'] = round(perf_score)
                
                # درجات التقييم الأخرى
                if 'accessibility' in categories:
                    result['scores']['accessibility'] = round(categories['accessibility']['score'] * 100)
                
                if 'best-practices' in categories:
                    result['scores']['best_practices'] = round(categories['best-practices']['score'] * 100)
                
                if 'seo' in categories:
                    result['scores']['seo'] = round(categories['seo']['score'] * 100)
            
            # استخراج المقاييس الرئيسية
            if 'lighthouseResult' in data and 'audits' in data['lighthouseResult']:
                audits = data['lighthouseResult']['audits']
                
                # زمن التحميل والتفاعل
                if 'interactive' in audits:
                    result['metrics']['time_to_interactive'] = audits['interactive']['numericValue'] / 1000
                    result['loading_time'] = result['metrics']['time_to_interactive']
                
                if 'speed-index' in audits:
                    result['metrics']['speed_index'] = audits['speed-index']['numericValue'] / 1000
                
                if 'first-contentful-paint' in audits:
                    result['metrics']['first_contentful_paint'] = audits['first-contentful-paint']['numericValue'] / 1000
                
                if 'largest-contentful-paint' in audits:
                    result['metrics']['largest_contentful_paint'] = audits['largest-contentful-paint']['numericValue'] / 1000
                
                if 'total-blocking-time' in audits:
                    result['metrics']['total_blocking_time'] = audits['total-blocking-time']['numericValue']
                
                if 'cumulative-layout-shift' in audits:
                    result['metrics']['cumulative_layout_shift'] = audits['cumulative-layout-shift']['numericValue']
                
                # إجمالي حجم الصفحة
                if 'total-byte-weight' in audits:
                    result['metrics']['total_size'] = audits['total-byte-weight']['numericValue'] / (1024 * 1024)  # تحويل إلى ميغابايت
            
            # فرص التحسين
            if 'lighthouseResult' in data and 'audits' in data['lighthouseResult']:
                for audit_id, audit in data['lighthouseResult']['audits'].items():
                    if audit.get('score') is not None and audit.get('score') < 1:
                        if audit.get('details', {}).get('type') == 'opportunity':
                            opportunity = {
                                'id': audit_id,
                                'title': audit.get('title', ''),
                                'description': audit.get('description', ''),
                                'score': audit.get('score', 0),
                                'impact': self._get_impact_level(audit.get('score', 0))
                            }
                            
                            # إضافة مقدار التوفير المحتمل في الوقت
                            if 'numericValue' in audit:
                                opportunity['saving_ms'] = audit['numericValue']
                            
                            result['opportunities'].append(opportunity)
                            
                            # إضافة المشاكل المهمة
                            if audit.get('score', 0) <= 0.5:
                                result['issues'].append({
                                    'type': 'warning',
                                    'message': audit.get('title', ''),
                                    'impact': self._get_impact_level(audit.get('score', 0)),
                                    'recommendation': audit.get('description', '')
                                })
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل نتائج PageSpeed: {str(e)}")
        
        return result
    
    def _parse_lighthouse_result(self, data, strategy):
        """
        تحليل نتائج Lighthouse المباشرة
        
        Args:
            data (dict): بيانات تقرير Lighthouse
            strategy (str): استراتيجية التحليل المستخدمة
            
        Returns:
            dict: نتائج منظمة لسرعة الصفحة
        """
        # بنية مشابهة لتحليل نتائج PageSpeed API
        result = {
            'url': data.get('finalUrl', data.get('requestedUrl', '')),
            'strategy': strategy,
            'score': 0,
            'loading_time': None,
            'scores': {},
            'metrics': {},
            'opportunities': [],
            'diagnostics': [],
            'passed_audits': [],
            'issues': []
        }
        
        try:
            # استخراج درجات التقييم الرئيسية
            if 'categories' in data:
                categories = data['categories']
                
                # درجة التقييم الكلية للأداء
                if 'performance' in categories:
                    perf_score = categories['performance']['score'] * 100
                    result['score'] = round(perf_score)
                    result['scores']['performance'] = round(perf_score)
                
                # درجات التقييم الأخرى
                if 'accessibility' in categories:
                    result['scores']['accessibility'] = round(categories['accessibility']['score'] * 100)
                
                if 'best-practices' in categories:
                    result['scores']['best_practices'] = round(categories['best-practices']['score'] * 100)
                
                if 'seo' in categories:
                    result['scores']['seo'] = round(categories['seo']['score'] * 100)
            
            # استخراج المقاييس الرئيسية
            if 'audits' in data:
                audits = data['audits']
                
                # زمن التحميل والتفاعل
                if 'interactive' in audits:
                    result['metrics']['time_to_interactive'] = audits['interactive']['numericValue'] / 1000
                    result['loading_time'] = result['metrics']['time_to_interactive']
                
                if 'speed-index' in audits:
                    result['metrics']['speed_index'] = audits['speed-index']['numericValue'] / 1000
                
                if 'first-contentful-paint' in audits:
                    result['metrics']['first_contentful_paint'] = audits['first-contentful-paint']['numericValue'] / 1000
                
                if 'largest-contentful-paint' in audits:
                    result['metrics']['largest_contentful_paint'] = audits['largest-contentful-paint']['numericValue'] / 1000
                
                if 'total-blocking-time' in audits:
                    result['metrics']['total_blocking_time'] = audits['total-blocking-time']['numericValue']
                
                if 'cumulative-layout-shift' in audits:
                    result['metrics']['cumulative_layout_shift'] = audits['cumulative-layout-shift']['numericValue']
                
                # إجمالي حجم الصفحة
                if 'total-byte-weight' in audits:
                    result['metrics']['total_size'] = audits['total-byte-weight']['numericValue'] / (1024 * 1024)  # تحويل إلى ميغابايت
                
                # فرص التحسين
                for audit_id, audit in audits.items():
                    if audit.get('score') is not None and audit.get('score') < 1:
                        if audit.get('details', {}).get('type') == 'opportunity':
                            opportunity = {
                                'id': audit_id,
                                'title': audit.get('title', ''),
                                'description': audit.get('description', ''),
                                'score': audit.get('score', 0),
                                'impact': self._get_impact_level(audit.get('score', 0))
                            }
                            
                            # إضافة مقدار التوفير المحتمل في الوقت
                            if 'numericValue' in audit:
                                opportunity['saving_ms'] = audit['numericValue']
                            
                            result['opportunities'].append(opportunity)
                            
                            # إضافة المشاكل المهمة
                            if audit.get('score', 0) <= 0.5:
                                result['issues'].append({
                                    'type': 'warning',
                                    'message': audit.get('title', ''),
                                    'impact': self._get_impact_level(audit.get('score', 0)),
                                    'recommendation': audit.get('description', '')
                                })
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل نتائج Lighthouse: {str(e)}")
        
        return result
    
    def _get_empty_result(self, url, strategy):
        """
        إنشاء نتيجة فارغة في حالة فشل التحليل
        
        Args:
            url (str): عنوان URL للصفحة
            strategy (str): استراتيجية التحليل
            
        Returns:
            dict: هيكل بيانات فارغ لنتائج سرعة الصفحة
        """
        return {
            'url': url,
            'strategy': strategy,
            'score': None,
            'loading_time': None,
            'error': True,
            'error_message': 'فشل تحليل سرعة الصفحة',
            'scores': {},
            'metrics': {},
            'opportunities': [],
            'issues': [{
                'type': 'error',
                'message': 'لم يتم اكتمال تحليل سرعة الصفحة',
                'impact': 'high',
                'recommendation': 'تحقق من توفر أدوات التحليل أو أضف مفتاح PageSpeed API صالح'
            }]
        }
    
    def _get_impact_level(self, score):
        """
        تحديد مستوى تأثير مشكلة بناءً على النتيجة
        
        Args:
            score (float): درجة التقييم بين 0 و 1
            
        Returns:
            str: مستوى التأثير (high, medium, low)
        """
        if score is None:
            return 'medium'
        
        if score <= 0.3:
            return 'high'
        elif score <= 0.7:
            return 'medium'
        else:
            return 'low'
