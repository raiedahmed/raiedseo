#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة فاحص الروابط - مسؤولة عن التحقق من صحة الروابط الداخلية والخارجية

تقوم هذه الوحدة بفحص الروابط في صفحات الويب للتأكد من صحتها وتحديد
الروابط المكسورة والتوجيهات.
"""

import logging
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class LinkChecker:
    """
    فئة لفحص الروابط في صفحات الويب
    """
    
    def __init__(self, max_workers=5, timeout=10, check_external=True, verbose=False):
        """
        تهيئة فاحص الروابط
        
        Args:
            max_workers (int): العدد الأقصى للعمليات المتزامنة
            timeout (int): مهلة انتهاء الطلب بالثواني
            check_external (bool): فحص الروابط الخارجية أيضًا
            verbose (bool): طباعة معلومات إضافية أثناء الفحص
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.check_external = check_external
        self.verbose = verbose
        self.logger = logging.getLogger('rseo.link_checker')
        
        # جلسة للطلبات HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RSEO Link Checker/1.0',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        })
        
        # تخزين مؤقت لنتائج الروابط التي تم فحصها
        self.checked_links = {}
    
    def check_links(self, page_data):
        """
        فحص الروابط في صفحة
        
        Args:
            page_data (dict): بيانات الصفحة المحتوية على HTML والعنوان URL
            
        Returns:
            dict: نتائج فحص الروابط
        """
        url = page_data.get('url', '')
        html_content = page_data.get('html', '')
        
        if not html_content:
            self.logger.error(f"لا يوجد محتوى HTML للتحليل: {url}")
            return {
                'status': 'error',
                'message': 'لا يوجد محتوى HTML للتحليل',
                'issues': []
            }
        
        # تحليل HTML باستخدام BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # استخراج معلومات الموقع الحالي
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # جمع جميع الروابط
        all_links = self._extract_all_links(soup, url)
        
        # تصنيف الروابط
        internal_links = []
        external_links = []
        
        for link in all_links:
            parsed_link = urlparse(link)
            
            # تحديد ما إذا كان الرابط داخليًا أو خارجيًا
            if not parsed_link.netloc or parsed_link.netloc == parsed_url.netloc:
                internal_links.append(link)
            else:
                external_links.append(link)
        
        # فحص الروابط
        internal_links_status = self._check_links_status(internal_links, base_url)
        
        external_links_status = {}
        if self.check_external:
            external_links_status = self._check_links_status(external_links, base_url)
        
        # تجميع النتائج
        result = {
            'total_links': len(all_links),
            'internal_links': {
                'count': len(internal_links),
                'status': internal_links_status
            },
            'external_links': {
                'count': len(external_links),
                'status': external_links_status if self.check_external else {}
            },
            'score': 0,
            'issues': []
        }
        
        # حساب نسبة الروابط الصحيحة
        total_broken = sum(1 for status in internal_links_status.values() if status.get('status_code', 0) >= 400)
        if self.check_external:
            total_broken += sum(1 for status in external_links_status.values() if status.get('status_code', 0) >= 400)
        
        total_checked = len(internal_links_status) + (len(external_links_status) if self.check_external else 0)
        
        # حساب النتيجة استنادًا إلى نسبة الروابط الصحيحة
        if total_checked > 0:
            success_ratio = 1 - (total_broken / total_checked)
            result['score'] = int(success_ratio * 100)
        else:
            result['score'] = 100  # لا توجد روابط للفحص
        
        # تحديد المشاكل
        if total_broken > 0:
            result['issues'].append({
                'type': 'error',
                'message': f'تم العثور على {total_broken} رابط مكسور',
                'impact': 'high' if total_broken > 5 else 'medium',
                'recommendation': 'إصلاح الروابط المكسورة أو إزالتها لتحسين تجربة المستخدم وتقييم محركات البحث'
            })
        
        # التحقق من وجود روابط داخلية كافية
        if len(internal_links) < 3:
            result['issues'].append({
                'type': 'warning',
                'message': f'عدد الروابط الداخلية قليل جدًا ({len(internal_links)})',
                'impact': 'medium',
                'recommendation': 'زيادة عدد الروابط الداخلية لتحسين هيكل الموقع وتوزيع قيمة الروابط'
            })
        
        return result
    
    def _extract_all_links(self, soup, base_url):
        """
        استخراج جميع الروابط من صفحة HTML
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            base_url (str): عنوان URL الأساسي للصفحة
            
        Returns:
            set: مجموعة الروابط الفريدة
        """
        links = set()
        
        # البحث عن جميع وسوم الروابط
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            
            # تجاهل الروابط الفارغة والبريد الإلكتروني وروابط JavaScript
            if not href or href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
            
            # تحويل الروابط النسبية إلى مطلقة
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # إزالة الهاش (الإشارة داخل الصفحة)
            if '#' in href:
                href = href.split('#')[0]
            
            # إزالة المعاملات من الرابط
            if '?' in href:
                href = href.split('?')[0]
            
            # إضافة الرابط إذا كان غير فارغ
            if href:
                links.add(href)
        
        return links
    
    def _check_links_status(self, links, base_url):
        """
        التحقق من حالة قائمة من الروابط
        
        Args:
            links (list): قائمة الروابط للتحقق
            base_url (str): عنوان URL الأساسي للصفحة
            
        Returns:
            dict: حالة كل رابط
        """
        results = {}
        
        # استخدام ThreadPoolExecutor للتحقق من الروابط بشكل متوازٍ
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # إنشاء مهام للتحقق من كل رابط
            future_to_url = {executor.submit(self._check_link_status, link): link for link in links}
            
            # جمع النتائج
            for future in tqdm(as_completed(future_to_url), total=len(links), disable=not self.verbose, desc="فحص الروابط"):
                link = future_to_url[future]
                
                try:
                    status = future.result()
                    results[link] = status
                except Exception as e:
                    self.logger.error(f"خطأ في فحص الرابط {link}: {str(e)}")
                    results[link] = {'status': 'error', 'status_code': 0, 'error': str(e)}
        
        return results
    
    def _check_link_status(self, url):
        """
        التحقق من حالة رابط واحد
        
        Args:
            url (str): عنوان URL للتحقق
            
        Returns:
            dict: حالة الرابط
        """
        # استخدام النتيجة المخزنة مؤقتًا إذا كانت متاحة
        if url in self.checked_links:
            return self.checked_links[url]
        
        try:
            # إرسال طلب HEAD للتحقق من حالة الرابط
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            # إذا كان طلب HEAD غير مدعوم، استخدم GET
            if response.status_code >= 400:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True, stream=True)
                # قراءة جزء صغير من المحتوى فقط
                for chunk in response.iter_content(chunk_size=1024):
                    break
            
            # تحديد ما إذا كان هناك توجيه
            redirected = response.history and len(response.history) > 0
            
            result = {
                'status': 'success' if response.status_code < 400 else 'error',
                'status_code': response.status_code,
                'redirected': redirected
            }
            
            # إضافة معلومات التوجيه إذا كان موجودًا
            if redirected:
                result['original_url'] = url
                result['redirected_url'] = response.url
                result['redirect_count'] = len(response.history)
            
            # تخزين النتيجة مؤقتًا
            self.checked_links[url] = result
            
            return result
            
        except requests.exceptions.Timeout:
            result = {'status': 'error', 'status_code': 0, 'error': 'timeout'}
            self.checked_links[url] = result
            return result
            
        except requests.exceptions.ConnectionError:
            result = {'status': 'error', 'status_code': 0, 'error': 'connection_error'}
            self.checked_links[url] = result
            return result
            
        except requests.exceptions.RequestException as e:
            result = {'status': 'error', 'status_code': 0, 'error': str(e)}
            self.checked_links[url] = result
            return result
