#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - محلل المنافسين
تحليل مواقع المنافسين ومقارنتها مع موقعك
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import time
from concurrent.futures import ThreadPoolExecutor

from utils.logger import get_logger
from modules.crawler import WebCrawler

class CompetitorAnalyzer:
    """محلل المنافسين - يقوم بتحليل المواقع المنافسة ومقارنتها مع موقعك"""

    def __init__(self, config=None):
        """تهيئة محلل المنافسين مع الإعدادات المقدمة

        Args:
            config (dict, optional): إعدادات التحليل. الافتراضي None.
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.max_threads = self.config.get('max_threads', 5)
    
    def analyze(self, domain, max_pages=10):
        """تحليل موقع منافس

        Args:
            domain (str): المجال المراد تحليله
            max_pages (int, optional): الحد الأقصى لعدد الصفحات للتحليل. الافتراضي 10.

        Returns:
            dict: نتائج تحليل المنافس
        """
        self.logger.info(f"بدء تحليل المنافس: {domain}")
        
        # تحقق من صحة المجال
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        # استخراج المجال الأساسي
        parsed_domain = urlparse(domain)
        base_domain = parsed_domain.netloc
        
        results = {
            'domain': base_domain,
            'url': domain,
            'analysis_timestamp': int(time.time()),
            'meta': self._analyze_meta(domain),
            'pages': [],
            'keywords': {},
            'backlinks': self._analyze_backlinks(base_domain),
            'social': self._analyze_social_presence(base_domain),
            'technology': self._detect_technology(domain),
            'performance': self._analyze_performance(domain)
        }
        
        # زحف عدد محدود من الصفحات
        try:
            crawler = WebCrawler(
                start_url=domain,
                max_pages=max_pages,
                max_depth=2,
                respect_robots_txt=True
            )
            pages = crawler.crawl()
            
            # تحليل كل صفحة
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                page_results = list(executor.map(
                    lambda item: self._analyze_page(item[0], item[1]), 
                    list(pages.items())[:max_pages]
                ))
            
            results['pages'] = page_results
            
            # استخراج وتجميع الكلمات المفتاحية
            all_keywords = {}
            for page_result in page_results:
                for keyword, frequency in page_result.get('keywords', {}).items():
                    if keyword in all_keywords:
                        all_keywords[keyword] += frequency
                    else:
                        all_keywords[keyword] = frequency
            
            # ترتيب الكلمات المفتاحية حسب التكرار
            sorted_keywords = dict(sorted(
                all_keywords.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20])  # الاحتفاظ بأعلى 20 كلمة مفتاحية
            
            results['keywords'] = sorted_keywords
            
            # حساب متوسط نتيجة SEO من جميع الصفحات
            seo_scores = [page.get('seo_score', 0) for page in page_results if 'seo_score' in page]
            if seo_scores:
                results['average_seo_score'] = sum(seo_scores) / len(seo_scores)
            else:
                results['average_seo_score'] = 0
        
        except Exception as e:
            self.logger.error(f"خطأ أثناء تحليل المنافس {domain}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_meta(self, url):
        """تحليل البيانات الوصفية للموقع

        Args:
            url (str): عنوان URL للموقع

        Returns:
            dict: نتائج تحليل البيانات الوصفية
        """
        meta_data = {
            'title': '',
            'description': '',
            'canonical': '',
            'robots': '',
            'favicon': '',
            'language': '',
            'viewport': '',
            'charset': '',
            'og_tags': {},
            'twitter_tags': {}
        }
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # استخراج عنوان الصفحة
                title_tag = soup.find('title')
                if title_tag:
                    meta_data['title'] = title_tag.text.strip()
                
                # استخراج الوصف
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    meta_data['description'] = meta_desc.get('content', '')
                
                # استخراج الصفحة المرجعية
                canonical = soup.find('link', attrs={'rel': 'canonical'})
                if canonical:
                    meta_data['canonical'] = canonical.get('href', '')
                
                # استخراج تعليمات الروبوتات
                robots = soup.find('meta', attrs={'name': 'robots'})
                if robots:
                    meta_data['robots'] = robots.get('content', '')
                
                # استخراج أيقونة المفضلة
                favicon = soup.find('link', attrs={'rel': 'icon'}) or soup.find('link', attrs={'rel': 'shortcut icon'})
                if favicon:
                    meta_data['favicon'] = favicon.get('href', '')
                
                # استخراج اللغة
                html_tag = soup.find('html')
                if html_tag and html_tag.has_attr('lang'):
                    meta_data['language'] = html_tag.get('lang', '')
                
                # استخراج إعداد العرض
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                if viewport:
                    meta_data['viewport'] = viewport.get('content', '')
                
                # استخراج ترميز النص
                charset = soup.find('meta', attrs={'charset': True})
                if charset:
                    meta_data['charset'] = charset.get('charset', '')
                
                # استخراج علامات Open Graph
                og_tags = {}
                for tag in soup.find_all('meta', attrs={'property': re.compile('^og:')}):
                    property_name = tag.get('property', '').replace('og:', '')
                    og_tags[property_name] = tag.get('content', '')
                meta_data['og_tags'] = og_tags
                
                # استخراج علامات Twitter
                twitter_tags = {}
                for tag in soup.find_all('meta', attrs={'name': re.compile('^twitter:')}):
                    property_name = tag.get('name', '').replace('twitter:', '')
                    twitter_tags[property_name] = tag.get('content', '')
                meta_data['twitter_tags'] = twitter_tags
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل البيانات الوصفية للموقع {url}: {str(e)}")
        
        return meta_data
    
    def _analyze_page(self, url, page_data):
        """تحليل صفحة من موقع المنافس

        Args:
            url (str): عنوان URL للصفحة
            page_data (dict): بيانات الصفحة

        Returns:
            dict: نتائج تحليل الصفحة
        """
        page_result = {
            'url': url,
            'title': page_data.get('title', ''),
            'h1': page_data.get('h1', []),
            'keywords': {},
            'content_length': len(page_data.get('text', '')),
            'images_count': len(page_data.get('images', [])),
            'links_count': len(page_data.get('links', [])),
            'seo_score': 0,
            'issues': []
        }
        
        try:
            # تحليل الكلمات المفتاحية في النص
            text = page_data.get('text', '')
            if text:
                # تنظيف النص وتقسيمه إلى كلمات
                words = re.findall(r'\b\w+\b', text.lower())
                
                # استبعاد الكلمات الشائعة
                stop_words = self._get_stop_words()
                filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]
                
                # حساب تكرار الكلمات
                word_frequency = {}
                for word in filtered_words:
                    if word in word_frequency:
                        word_frequency[word] += 1
                    else:
                        word_frequency[word] = 1
                
                # ترتيب الكلمات حسب التكرار
                sorted_words = dict(sorted(
                    word_frequency.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10])  # الاحتفاظ بأعلى 10 كلمات
                
                page_result['keywords'] = sorted_words
            
            # تقييم نتيجة SEO
            seo_score = 100  # نتيجة أولية مثالية
            
            # تحقق من وجود عنوان
            if not page_data.get('title'):
                page_result['issues'].append('العنوان مفقود')
                seo_score -= 10
            elif len(page_data.get('title', '')) < 10:
                page_result['issues'].append('العنوان قصير جداً')
                seo_score -= 5
            elif len(page_data.get('title', '')) > 70:
                page_result['issues'].append('العنوان طويل جداً')
                seo_score -= 5
            
            # تحقق من وجود H1
            if not page_data.get('h1'):
                page_result['issues'].append('عنوان H1 مفقود')
                seo_score -= 10
            elif len(page_data.get('h1', [])) > 1:
                page_result['issues'].append('أكثر من عنوان H1 واحد')
                seo_score -= 5
            
            # تحقق من طول المحتوى
            if page_result['content_length'] < 300:
                page_result['issues'].append('المحتوى قصير جداً')
                seo_score -= 15
            
            # تحقق من وجود الصور
            if page_result['images_count'] == 0:
                page_result['issues'].append('لا توجد صور')
                seo_score -= 5
            
            # تحقق من الصور بدون نص بديل
            images_without_alt = 0
            for img in page_data.get('images', []):
                if not img.get('alt'):
                    images_without_alt += 1
            
            if images_without_alt > 0:
                page_result['issues'].append(f'{images_without_alt} صورة بدون نص بديل')
                seo_score -= min(10, images_without_alt * 2)
            
            # تجنب النتيجة السلبية
            page_result['seo_score'] = max(0, seo_score)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الصفحة {url}: {str(e)}")
            page_result['error'] = str(e)
        
        return page_result
    
    def _analyze_backlinks(self, domain):
        """تحليل الروابط الخلفية للمجال

        Args:
            domain (str): اسم المجال

        Returns:
            dict: معلومات الروابط الخلفية
        """
        backlinks_info = {
            'count': 0,
            'domains': 0,
            'top_referring_domains': []
        }
        
        try:
            # يمكن استخدام API لتحليل الروابط الخلفية مثل Moz أو Ahrefs أو Majestic
            # هذا تنفيذ بسيط للتوضيح
            
            # محاكاة بيانات الروابط الخلفية
            sample_data = {
                'count': 1250,
                'domains': 89,
                'top_referring_domains': [
                    {'domain': 'example1.com', 'backlinks': 45},
                    {'domain': 'example2.org', 'backlinks': 32},
                    {'domain': 'example3.net', 'backlinks': 27}
                ]
            }
            
            backlinks_info.update(sample_data)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الروابط الخلفية للمجال {domain}: {str(e)}")
        
        return backlinks_info
    
    def _analyze_social_presence(self, domain):
        """تحليل الحضور الاجتماعي للمجال

        Args:
            domain (str): اسم المجال

        Returns:
            dict: معلومات الحضور الاجتماعي
        """
        social_info = {
            'facebook': {'url': '', 'found': False},
            'twitter': {'url': '', 'found': False},
            'instagram': {'url': '', 'found': False},
            'linkedin': {'url': '', 'found': False},
            'youtube': {'url': '', 'found': False}
        }
        
        try:
            # محاكاة بيانات الحضور الاجتماعي
            # يمكن استخدام API أو تقنيات الزحف لاكتشاف الروابط الاجتماعية
            
            # للتبسيط، نفترض روابط افتراضية
            facebook_url = f"https://facebook.com/{domain.split('.')[0]}"
            twitter_url = f"https://twitter.com/{domain.split('.')[0]}"
            instagram_url = f"https://instagram.com/{domain.split('.')[0]}"
            linkedin_url = f"https://linkedin.com/company/{domain.split('.')[0]}"
            youtube_url = f"https://youtube.com/c/{domain.split('.')[0]}"
            
            # تحديث المعلومات بافتراض العثور على بعض الروابط
            social_info['facebook'] = {'url': facebook_url, 'found': True}
            social_info['twitter'] = {'url': twitter_url, 'found': True}
            social_info['instagram'] = {'url': instagram_url, 'found': False}
            social_info['linkedin'] = {'url': linkedin_url, 'found': True}
            social_info['youtube'] = {'url': youtube_url, 'found': False}
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الحضور الاجتماعي للمجال {domain}: {str(e)}")
        
        return social_info
    
    def _detect_technology(self, url):
        """اكتشاف التقنيات المستخدمة في الموقع

        Args:
            url (str): عنوان URL للموقع

        Returns:
            dict: التقنيات المكتشفة
        """
        tech_info = {
            'cms': 'unknown',
            'server': 'unknown',
            'analytics': [],
            'javascript_libraries': [],
            'frameworks': [],
            'advertising': []
        }
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                # التحقق من خوادم الويب
                server_header = response.headers.get('Server', '')
                if server_header:
                    tech_info['server'] = server_header
                
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # اكتشاف نظام إدارة المحتوى (CMS)
                # WordPress
                if "wp-content" in html_content:
                    tech_info['cms'] = "WordPress"
                # Joomla
                elif "joomla" in html_content.lower():
                    tech_info['cms'] = "Joomla"
                # Drupal
                elif "drupal" in html_content.lower():
                    tech_info['cms'] = "Drupal"
                # Magento
                elif "magento" in html_content.lower():
                    tech_info['cms'] = "Magento"
                # Shopify
                elif "shopify" in html_content.lower():
                    tech_info['cms'] = "Shopify"
                
                # اكتشاف أدوات التحليل
                # Google Analytics
                if "google-analytics.com" in html_content or "googletagmanager.com" in html_content:
                    tech_info['analytics'].append("Google Analytics")
                # Facebook Pixel
                if "connect.facebook.net" in html_content:
                    tech_info['analytics'].append("Facebook Pixel")
                # Hotjar
                if "hotjar.com" in html_content:
                    tech_info['analytics'].append("Hotjar")
                
                # اكتشاف مكتبات JavaScript
                # jQuery
                if "jquery" in html_content.lower():
                    tech_info['javascript_libraries'].append("jQuery")
                # React
                if "react" in html_content.lower() or "_reactRootContainer" in html_content:
                    tech_info['javascript_libraries'].append("React")
                # Angular
                if "ng-" in html_content or "angular" in html_content.lower():
                    tech_info['javascript_libraries'].append("Angular")
                # Vue.js
                if "vue" in html_content.lower() or "v-" in html_content:
                    tech_info['javascript_libraries'].append("Vue.js")
                
                # اكتشاف أطر العمل
                # Bootstrap
                if "bootstrap" in html_content.lower():
                    tech_info['frameworks'].append("Bootstrap")
                # Tailwind CSS
                if "tailwind" in html_content.lower():
                    tech_info['frameworks'].append("Tailwind CSS")
                # Foundation
                if "foundation" in html_content.lower():
                    tech_info['frameworks'].append("Foundation")
                
                # اكتشاف شبكات الإعلانات
                # Google Adsense
                if "adsbygoogle" in html_content or "googlesyndication.com" in html_content:
                    tech_info['advertising'].append("Google AdSense")
                # Facebook Ads
                if "fbq('init'" in html_content:
                    tech_info['advertising'].append("Facebook Ads")
                
        except Exception as e:
            self.logger.error(f"خطأ في اكتشاف التقنيات للموقع {url}: {str(e)}")
        
        return tech_info
    
    def _analyze_performance(self, url):
        """تحليل أداء الموقع

        Args:
            url (str): عنوان URL للموقع

        Returns:
            dict: مقاييس الأداء
        """
        performance_metrics = {
            'load_time_ms': 0,
            'page_size_kb': 0,
            'requests_count': 0,
            'response_time_ms': 0
        }
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=10)
            end_time = time.time()
            
            # قياس وقت الاستجابة
            response_time_ms = int((end_time - start_time) * 1000)
            performance_metrics['response_time_ms'] = response_time_ms
            
            if response.status_code == 200:
                # حجم الصفحة
                page_size_bytes = len(response.content)
                page_size_kb = round(page_size_bytes / 1024, 2)
                performance_metrics['page_size_kb'] = page_size_kb
                
                # وقت التحميل الإجمالي (محاكاة)
                # هذا تقدير تقريبي جداً، قد يتطلب أدوات أكثر تقدماً للقياس الدقيق
                performance_metrics['load_time_ms'] = response_time_ms * 2
                
                # عدد الطلبات (تقدير بسيط)
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = len(soup.find_all('script', src=True))
                stylesheets = len(soup.find_all('link', rel='stylesheet'))
                images = len(soup.find_all('img'))
                
                performance_metrics['requests_count'] = scripts + stylesheets + images + 1  # +1 للصفحة الرئيسية
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل أداء الموقع {url}: {str(e)}")
        
        return performance_metrics
    
    def _get_stop_words(self):
        """الحصول على قائمة الكلمات الشائعة (الإنجليزية والعربية) التي يجب استبعادها من تحليل الكلمات المفتاحية

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
