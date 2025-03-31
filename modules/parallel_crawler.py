#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة الزحف المتوازي لتحليل مواقع الويب بشكل متزامن

تستخدم هذه الوحدة asyncio وaiohttp لزحف الصفحات بشكل متوازٍ
مما يزيد بشكل كبير من سرعة تحليل المواقع الكبيرة.
"""

import os
import asyncio
import aiohttp
import logging
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import robotexclusionrulesparser as robots

# إعداد المسجل
logger = logging.getLogger(__name__)

class AsyncWebCrawler:
    """فئة للزحف المتوازي لصفحات الويب باستخدام asyncio وaiohttp"""
    
    def __init__(self, start_url, max_pages=100, max_depth=3, delay=0.5,
                 respect_robots_txt=True, max_concurrent=10, timeout=30, verbose=False):
        """
        تهيئة زاحف الويب المتوازي
        
        Args:
            start_url (str): عنوان URL البداية للزحف
            max_pages (int): أقصى عدد للصفحات المراد زحفها
            max_depth (int): أقصى عمق للزحف
            delay (float): التأخير بين الطلبات للنطاق نفسه (بالثواني)
            respect_robots_txt (bool): احترام ملف robots.txt
            max_concurrent (int): أقصى عدد للطلبات المتزامنة
            timeout (int): مهلة الطلب (بالثواني)
            verbose (bool): طباعة معلومات تفصيلية أثناء التنفيذ
        """
        self.start_url = start_url
        self.base_url = urlparse(start_url).scheme + "://" + urlparse(start_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.respect_robots_txt = respect_robots_txt
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.verbose = verbose
        
        self.visited_urls = set()
        self.to_visit = asyncio.Queue()
        self.pages = {}
        self.robots_parser = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiters = {}  # تخزين أدوات تحديد معدل الطلبات لكل نطاق
        
    async def initialize(self):
        """تهيئة الزاحف المتوازي وتجهيز ملف robots.txt إذا لزم الأمر"""
        if self.respect_robots_txt:
            try:
                robots_url = urljoin(self.base_url, '/robots.txt')
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url, timeout=self.timeout) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                            self.robots_parser = robots.RobotExclusionRulesParser()
                            self.robots_parser.parse(robots_content)
                            if self.verbose:
                                logger.info(f"تم تحميل ملف robots.txt من {robots_url}")
            except Exception as e:
                logger.warning(f"فشل تحميل ملف robots.txt: {str(e)}")
        
        # إضافة URL البداية إلى قائمة الانتظار مع عمق 0
        await self.to_visit.put((self.start_url, 0))
    
    async def _can_fetch(self, url):
        """التحقق مما إذا كان يمكن زحف عنوان URL وفقًا لملف robots.txt"""
        if not self.respect_robots_txt or not self.robots_parser:
            return True
        
        try:
            return self.robots_parser.is_allowed("*", url)
        except Exception as e:
            logger.error(f"خطأ أثناء التحقق من robots.txt: {str(e)}")
            return True  # في حالة الشك، نسمح بالزحف
    
    async def get_domain_semaphore(self, domain):
        """الحصول على أداة تحديد المعدل الخاصة بالنطاق"""
        if domain not in self.rate_limiters:
            self.rate_limiters[domain] = asyncio.Semaphore(1)
        return self.rate_limiters[domain]
    
    async def fetch_url(self, url, depth):
        """
        جلب محتوى URL وتحليله
        
        Args:
            url (str): URL المراد جلبه
            depth (int): عمق URL الحالي
            
        Returns:
            dict or None: بيانات الصفحة أو None في حالة الفشل
        """
        domain = urlparse(url).netloc
        domain_semaphore = await self.get_domain_semaphore(domain)
        
        # استخدام أداة تحديد المعدل للنطاق
        async with domain_semaphore:
            # استخدام أداة تحديد العدد الإجمالي للطلبات المتزامنة
            async with self.semaphore:
                if self.verbose:
                    logger.info(f"جاري جلب: {url} (العمق: {depth})")
                
                if not await self._can_fetch(url):
                    if self.verbose:
                        logger.info(f"تم حظر الوصول بواسطة robots.txt: {url}")
                    return None
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=self.timeout, 
                                              headers={'User-Agent': 'RSEO-Analyzer/1.0'}) as response:
                            if response.status != 200:
                                if self.verbose:
                                    logger.warning(f"رمز الحالة {response.status} لـ {url}")
                                return None
                            
                            content_type = response.headers.get('Content-Type', '')
                            if 'text/html' not in content_type.lower():
                                if self.verbose:
                                    logger.info(f"تخطي نوع المحتوى غير المدعوم: {content_type} لـ {url}")
                                return None
                            
                            html_content = await response.text()
                            soup = BeautifulSoup(html_content, 'html.parser')
                            
                            # استخراج البيانات الأساسية
                            page_data = {
                                'url': url,
                                'html': html_content,
                                'title': soup.title.string if soup.title else '',
                                'status_code': response.status,
                                'content_type': content_type,
                                'depth': depth,
                                'links': set(),
                                'images': [],
                                'scripts': [],
                                'styles': [],
                                'metadata': {},
                                'headers': dict(response.headers)
                            }
                            
                            # معالجة العناوين
                            headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
                            for h_level, h_list in headings.items():
                                for heading in soup.find_all(h_level):
                                    h_list.append(heading.get_text(strip=True))
                            page_data['headings'] = headings
                            
                            # معالجة البيانات الوصفية
                            for meta in soup.find_all('meta'):
                                name = meta.get('name', meta.get('property', ''))
                                if name:
                                    page_data['metadata'][name] = meta.get('content', '')
                            
                            # معالجة الروابط
                            if depth < self.max_depth:
                                for link in soup.find_all('a', href=True):
                                    href = link.get('href', '').strip()
                                    if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                                        absolute_url = urljoin(url, href)
                                        if urlparse(absolute_url).netloc == urlparse(self.base_url).netloc:
                                            # تنظيف URL (إزالة المرساة، إلخ)
                                            parsed = urlparse(absolute_url)
                                            cleaned_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                            if parsed.query:
                                                cleaned_url += f"?{parsed.query}"
                                            
                                            page_data['links'].add(cleaned_url)
                                            if (cleaned_url not in self.visited_urls and 
                                                len(self.visited_urls) < self.max_pages):
                                                await self.to_visit.put((cleaned_url, depth + 1))
                            
                            # معالجة الصور
                            for img in soup.find_all('img', src=True):
                                src = img.get('src', '').strip()
                                if src:
                                    img_data = {
                                        'src': urljoin(url, src),
                                        'alt': img.get('alt', ''),
                                        'title': img.get('title', '')
                                    }
                                    page_data['images'].append(img_data)
                            
                            # معالجة النصوص البرمجية
                            for script in soup.find_all('script', src=True):
                                src = script.get('src', '').strip()
                                if src:
                                    page_data['scripts'].append(urljoin(url, src))
                            
                            # معالجة أوراق الأنماط
                            for style in soup.find_all('link', rel='stylesheet'):
                                href = style.get('href', '').strip()
                                if href:
                                    page_data['styles'].append(urljoin(url, href))
                            
                            return page_data
                except Exception as e:
                    logger.error(f"خطأ في جلب {url}: {str(e)}")
                    return None
                
                # تأخير بعد الطلب (احترام تحديد المعدل)
                await asyncio.sleep(self.delay)
    
    async def crawl_async(self):
        """تنفيذ الزحف المتوازي للمواقع"""
        await self.initialize()
        
        start_time = time.time()
        
        # معالجة قائمة انتظار URL حتى اكتمال العدد المطلوب أو نفاد قائمة الانتظار
        while len(self.visited_urls) < self.max_pages:
            try:
                if self.to_visit.empty():
                    break
                
                url, depth = await self.to_visit.get()
                
                # تخطي URL التي تمت زيارتها بالفعل
                if url in self.visited_urls:
                    continue
                
                self.visited_urls.add(url)
                
                page_data = await self.fetch_url(url, depth)
                if page_data:
                    self.pages[url] = page_data
                
                self.to_visit.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"خطأ أثناء الزحف: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        if self.verbose:
            logger.info(f"اكتمل الزحف. تمت زيارة {len(self.visited_urls)} URL، وتحليل {len(self.pages)} صفحة.")
            logger.info(f"استغرق الزحف {duration:.2f} ثانية.")
        
        return self.pages
    
    def crawl(self):
        """
        واجهة متزامنة لبدء الزحف المتوازي
        
        Returns:
            dict: نتائج الزحف (URL -> بيانات الصفحة)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.crawl_async())
        finally:
            loop.close()
