#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة زاحف الويب - المسؤولة عن زحف وجمع صفحات الموقع للتحليل

تقوم هذه الوحدة بزحف موقع ويب بدءًا من URL معين واستخراج المحتوى
مع احترام ملف robots.txt وقواعد الزحف.
"""

import re
import time
import logging
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from fake_useragent import UserAgent
import validators

class WebCrawler:
    """
    فئة لزحف المواقع واستخراج بيانات الصفحات للتحليل
    """
    
    def __init__(self, start_url, max_pages=100, max_depth=3, delay=1, 
                 respect_robots_txt=True, user_agent=None, verbose=False):
        """
        تهيئة الزاحف
        
        Args:
            start_url (str): نقطة البداية للزحف
            max_pages (int): العدد الأقصى للصفحات المراد زحفها
            max_depth (int): عمق الزحف الأقصى
            delay (float): التأخير بين الطلبات (ثوانٍ)
            respect_robots_txt (bool): احترام توجيهات ملف robots.txt
            user_agent (str): نص User-Agent المخصص
            verbose (bool): طباعة معلومات مفصلة أثناء الزحف
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.respect_robots_txt = respect_robots_txt
        self.verbose = verbose
        
        # التحقق من صحة الرابط
        if not validators.url(start_url):
            raise ValueError(f"الرابط غير صالح: {start_url}")
            
        # استخراج المعلومات الأساسية
        parsed_url = urlparse(start_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.domain = parsed_url.netloc
        
        # إنشاء session مع User-Agent
        self.session = requests.Session()
        if user_agent:
            self.user_agent = user_agent
        else:
            try:
                self.user_agent = UserAgent().random
            except:
                self.user_agent = "RSEO Bot/1.0"
        
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        })
        
        # إعداد المسجل
        self.logger = logging.getLogger('rseo.crawler')
        
        # تهيئة متغيرات التتبع
        self.visited_urls = set()
        self.urls_to_visit = [(start_url, 0)]  # (url, depth)
        self.disallowed_paths = []
        
        # قراءة ملف robots.txt إذا كان مطلوبًا
        if self.respect_robots_txt:
            self._parse_robots_txt()
    
    def _parse_robots_txt(self):
        """قراءة وتحليل ملف robots.txt للحصول على القواعد"""
        robots_url = f"{self.base_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                lines = response.text.split('\n')
                user_agent_match = False
                
                for line in lines:
                    line = line.strip().lower()
                    
                    # البحث عن القواعد المطبقة على الروبوت الحالي أو جميع الروبوتات
                    if line.startswith('user-agent:'):
                        ua = line.split(':', 1)[1].strip()
                        user_agent_match = (ua == '*' or 'bot' in ua.lower())
                    
                    # إذا كانت القاعدة تنطبق، قم بحفظ المسارات المحظورة
                    if user_agent_match and line.startswith('disallow:') and len(line) > 10:
                        path = line.split(':', 1)[1].strip()
                        if path:
                            self.disallowed_paths.append(path)
                
                if self.verbose:
                    self.logger.info(f"تم تحليل ملف robots.txt: تم العثور على {len(self.disallowed_paths)} مسار محظور")
        except Exception as e:
            self.logger.warning(f"فشل قراءة ملف robots.txt: {str(e)}")
    
    def _is_allowed(self, url):
        """التحقق مما إذا كان URL مسموحًا به"""
        if not self.respect_robots_txt or not self.disallowed_paths:
            return True
        
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        for disallowed in self.disallowed_paths:
            if disallowed == '/' and path == '/':
                return False
            if path.startswith(disallowed):
                return False
        
        return True
    
    def _is_valid_url(self, url):
        """التحقق من صلاحية الرابط للزحف"""
        # تجاهل الروابط الخارجية
        if not url.startswith(self.base_url):
            return False
        
        # تجاهل المرفقات المحددة
        excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.jpeg', '.png',
                               '.gif', '.svg', '.mp3', '.mp4', '.avi', '.mov', '.webm', '.css', '.js']
        
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        if any(path.endswith(ext) for ext in excluded_extensions):
            return False
        
        # التحقق من مسارات robots.txt
        if not self._is_allowed(url):
            return False
        
        # التحقق من الهاش (تجاهل الأجزاء داخل الصفحة)
        if '#' in url:
            url = url.split('#')[0]
        
        # تجاهل المسارات الخاصة
        if '/wp-admin/' in url or '/wp-includes/' in url:
            return False
        
        return True
    
    def _normalize_url(self, url):
        """تنظيف وتوحيد شكل الروابط"""
        # إزالة المعاملات من الرابط
        if '?' in url:
            url = url.split('?')[0]
        
        # إزالة الهاش
        if '#' in url:
            url = url.split('#')[0]
        
        # التأكد من عدم وجود شرطة مائلة في النهاية
        if url.endswith('/') and url != self.base_url + '/':
            url = url[:-1]
        
        return url
    
    def _extract_links(self, soup, page_url):
        """استخراج الروابط من صفحة HTML"""
        links = set()
        
        # البحث عن جميع الروابط في الصفحة
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            
            # تجاهل الروابط الفارغة والبريد الإلكتروني وروابط JavaScript
            if not href or href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
            
            # تحويل الروابط النسبية إلى مطلقة
            if not href.startswith(('http://', 'https://')):
                href = urljoin(page_url, href)
            
            # تنظيف الرابط
            href = self._normalize_url(href)
            
            # إضافة الرابط إذا كان صالحًا
            if self._is_valid_url(href):
                links.add(href)
        
        return links
    
    def _get_page(self, url):
        """الحصول على محتوى صفحة ويب"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # التأكد من أن المحتوى هو HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                self.logger.warning(f"تم تجاهل {url}: ليس HTML ({content_type})")
                return None
            
            # محاولة تحديد ترميز الصفحة
            if response.encoding == 'ISO-8859-1':
                # محاولة اكتشاف الترميز من المحتوى
                if 'charset=utf-8' in response.text.lower():
                    response.encoding = 'utf-8'
                elif 'charset=windows-1256' in response.text.lower():
                    response.encoding = 'windows-1256'
                elif any(arabic_char in response.text for arabic_char in 'ةكمنتالبيسش'):
                    response.encoding = 'utf-8'
            
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"خطأ في الحصول على {url}: {str(e)}")
            return None
    
    def crawl(self):
        """
        بدء عملية زحف الموقع
        
        Returns:
            dict: البيانات المجمعة للصفحات المزحوفة
        """
        pages_data = {}
        
        # عرض شريط التقدم إذا كان الوضع المفصل مفعلًا
        progress_bar = tqdm(total=self.max_pages, desc="زحف الصفحات", disable=not self.verbose)
        
        while self.urls_to_visit and len(self.visited_urls) < self.max_pages:
            # استخراج الرابط التالي وعمقه
            url, depth = self.urls_to_visit.pop(0)
            
            # تجاهل الرابط إذا تمت زيارته بالفعل أو تجاوز العمق المسموح
            if url in self.visited_urls or depth > self.max_depth:
                continue
            
            # تعيين الرابط كتمت زيارته
            self.visited_urls.add(url)
            
            # الحصول على محتوى الصفحة
            html_content = self._get_page(url)
            if not html_content:
                continue
            
            # تحليل HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # تخزين بيانات الصفحة
            pages_data[url] = {
                'url': url,
                'html': html_content,
                'title': soup.title.text.strip() if soup.title else '',
                'depth': depth,
                'timestamp': time.time()
            }
            
            # تحديث شريط التقدم
            progress_bar.update(1)
            
            # إيقاف الزحف إذا وصلنا للحد الأقصى من الصفحات
            if len(pages_data) >= self.max_pages:
                break
            
            # استخراج روابط الصفحة وإضافتها للزيارة
            if depth < self.max_depth:
                links = self._extract_links(soup, url)
                for link in links:
                    if link not in self.visited_urls:
                        self.urls_to_visit.append((link, depth + 1))
            
            # إضافة تأخير بين الطلبات
            if self.delay > 0:
                time.sleep(self.delay)
        
        # إغلاق شريط التقدم
        progress_bar.close()
        
        self.logger.info(f"اكتمل الزحف: تمت زيارة {len(self.visited_urls)} صفحة، تم تحليل {len(pages_data)} صفحة")
        
        return pages_data
