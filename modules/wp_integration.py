#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تكامل ووردبريس - مسؤولة عن التفاعل مع WordPress API

تقوم هذه الوحدة بالتواصل مع WordPress API للحصول على المحتوى
وتطبيق التغييرات والإصلاحات على المقالات والصفحات.
"""

import os
import re
import json
import base64
import logging
import requests
from urllib.parse import urljoin, urlparse

class WordPressIntegration:
    """
    فئة للتفاعل مع WordPress API
    """
    
    def __init__(self, site_url, username=None, password=None, token=None):
        """
        تهيئة التكامل مع ووردبريس
        
        Args:
            site_url (str): عنوان URL لموقع ووردبريس
            username (str, optional): اسم المستخدم لـ WordPress
            password (str, optional): كلمة المرور أو كلمة مرور التطبيق
            token (str, optional): رمز JWT للمصادقة
        """
        self.logger = logging.getLogger('rseo.wp_integration')
        
        # تنظيف عنوان URL
        self.site_url = site_url.rstrip('/')
        
        # التحقق من وجود WordPress API
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        
        # معلومات اعتماد المصادقة
        self.username = username or os.getenv('WP_USERNAME')
        self.password = password or os.getenv('WP_PASSWORD')
        self.token = token
        
        # إنشاء جلسة مع ترويسات المصادقة
        self.session = requests.Session()
        
        # إضافة المصادقة إذا كانت متوفرة
        if self.username and self.password:
            auth_string = f"{self.username}:{self.password}"
            auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
            self.session.headers.update({'Authorization': auth_header})
        elif self.token:
            self.session.headers.update({'Authorization': f"Bearer {self.token}"})
        
        # إضافة ترويسات إضافية
        self.session.headers.update({
            'User-Agent': 'RSEO WP Integration/1.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # التحقق من إمكانية الوصول إلى WordPress API
        self._check_wp_api_access()
    
    def _check_wp_api_access(self):
        """
        التحقق من إمكانية الوصول إلى WordPress API
        
        Returns:
            bool: True إذا كان الوصول ممكنًا، False خلاف ذلك
        """
        try:
            response = self.session.get(f"{self.api_url}", timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"تم الاتصال بـ WordPress API: {self.site_url}")
                return True
            
            # محاولة الحصول على رمز مصادقة إذا كانت المصادقة مطلوبة
            elif response.status_code == 401 and self.username and self.password:
                token = self._get_auth_token()
                if token:
                    self.token = token
                    self.session.headers.update({'Authorization': f"Bearer {self.token}"})
                    self.logger.info("تم الحصول على رمز المصادقة وتحديث الترويسات")
                    return True
            
            self.logger.warning(f"فشل الاتصال بـ WordPress API: {response.status_code} - {response.text}")
            return False
        
        except Exception as e:
            self.logger.error(f"خطأ في الاتصال بـ WordPress API: {str(e)}")
            return False
    
    def _get_auth_token(self):
        """
        الحصول على رمز JWT للمصادقة
        
        Returns:
            str: رمز المصادقة أو None في حالة الفشل
        """
        try:
            # محاولة استخدام JWT API إذا كانت متاحة
            jwt_url = f"{self.site_url}/wp-json/jwt-auth/v1/token"
            
            response = requests.post(jwt_url, data={
                'username': self.username,
                'password': self.password
            })
            
            if response.status_code == 200:
                return response.json().get('token')
            
            self.logger.warning(f"فشل الحصول على رمز المصادقة: {response.status_code} - {response.text}")
            return None
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على رمز المصادقة: {str(e)}")
            return None
    
    def get_posts(self, page=1, per_page=10, categories=None, search=None):
        """
        الحصول على قائمة المقالات من WordPress
        
        Args:
            page (int): رقم الصفحة
            per_page (int): عدد المقالات في الصفحة
            categories (list, optional): فئات المقالات
            search (str, optional): نص البحث
            
        Returns:
            list: قائمة المقالات
        """
        try:
            # إنشاء معاملات الطلب
            params = {
                'page': page,
                'per_page': per_page,
                'context': 'edit',
                '_embed': 1
            }
            
            if categories:
                params['categories'] = ','.join(map(str, categories))
            
            if search:
                params['search'] = search
            
            # إرسال الطلب
            response = self.session.get(f"{self.api_url}/posts", params=params)
            response.raise_for_status()
            
            # استخراج إجمالي عدد الصفحات
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            total_posts = int(response.headers.get('X-WP-Total', 0))
            
            self.logger.info(f"تم الحصول على {len(response.json())} مقالة (الإجمالي: {total_posts})")
            
            return {
                'posts': response.json(),
                'total_pages': total_pages,
                'total_posts': total_posts
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المقالات: {str(e)}")
            return {'posts': [], 'total_pages': 0, 'total_posts': 0}
    
    def get_post(self, post_id):
        """
        الحصول على مقالة محددة من WordPress
        
        Args:
            post_id (int): معرف المقالة
            
        Returns:
            dict: بيانات المقالة
        """
        try:
            response = self.session.get(f"{self.api_url}/posts/{post_id}?context=edit&_embed=1")
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المقالة {post_id}: {str(e)}")
            return None
    
    def update_post(self, post_id, data):
        """
        تحديث مقالة في WordPress
        
        Args:
            post_id (int): معرف المقالة
            data (dict): البيانات المراد تحديثها
            
        Returns:
            dict: بيانات المقالة المحدثة
        """
        try:
            # إرسال طلب تحديث المقالة
            response = self.session.post(f"{self.api_url}/posts/{post_id}", json=data)
            response.raise_for_status()
            
            self.logger.info(f"تم تحديث المقالة {post_id} بنجاح")
            return response.json()
        
        except Exception as e:
            self.logger.error(f"خطأ في تحديث المقالة {post_id}: {str(e)}")
            return None
    
    def get_pages(self, page=1, per_page=10, search=None):
        """
        الحصول على قائمة الصفحات من WordPress
        
        Args:
            page (int): رقم الصفحة
            per_page (int): عدد الصفحات في الصفحة
            search (str, optional): نص البحث
            
        Returns:
            list: قائمة الصفحات
        """
        try:
            # إنشاء معاملات الطلب
            params = {
                'page': page,
                'per_page': per_page,
                'context': 'edit',
                '_embed': 1
            }
            
            if search:
                params['search'] = search
            
            # إرسال الطلب
            response = self.session.get(f"{self.api_url}/pages", params=params)
            response.raise_for_status()
            
            # استخراج إجمالي عدد الصفحات
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            total_items = int(response.headers.get('X-WP-Total', 0))
            
            self.logger.info(f"تم الحصول على {len(response.json())} صفحة (الإجمالي: {total_items})")
            
            return {
                'pages': response.json(),
                'total_pages': total_pages,
                'total_items': total_items
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الصفحات: {str(e)}")
            return {'pages': [], 'total_pages': 0, 'total_items': 0}
    
    def get_page(self, page_id):
        """
        الحصول على صفحة محددة من WordPress
        
        Args:
            page_id (int): معرف الصفحة
            
        Returns:
            dict: بيانات الصفحة
        """
        try:
            response = self.session.get(f"{self.api_url}/pages/{page_id}?context=edit&_embed=1")
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الصفحة {page_id}: {str(e)}")
            return None
    
    def update_page(self, page_id, data):
        """
        تحديث صفحة في WordPress
        
        Args:
            page_id (int): معرف الصفحة
            data (dict): البيانات المراد تحديثها
            
        Returns:
            dict: بيانات الصفحة المحدثة
        """
        try:
            # إرسال طلب تحديث الصفحة
            response = self.session.post(f"{self.api_url}/pages/{page_id}", json=data)
            response.raise_for_status()
            
            self.logger.info(f"تم تحديث الصفحة {page_id} بنجاح")
            return response.json()
        
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الصفحة {page_id}: {str(e)}")
            return None
    
    def get_media(self, page=1, per_page=20, search=None):
        """
        الحصول على قائمة الوسائط من WordPress
        
        Args:
            page (int): رقم الصفحة
            per_page (int): عدد العناصر في الصفحة
            search (str, optional): نص البحث
            
        Returns:
            list: قائمة الوسائط
        """
        try:
            # إنشاء معاملات الطلب
            params = {
                'page': page,
                'per_page': per_page,
                'media_type': 'image'
            }
            
            if search:
                params['search'] = search
            
            # إرسال الطلب
            response = self.session.get(f"{self.api_url}/media", params=params)
            response.raise_for_status()
            
            # استخراج إجمالي عدد الصفحات
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            total_items = int(response.headers.get('X-WP-Total', 0))
            
            return {
                'media': response.json(),
                'total_pages': total_pages,
                'total_items': total_items
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الوسائط: {str(e)}")
            return {'media': [], 'total_pages': 0, 'total_items': 0}
    
    def update_media(self, media_id, alt_text):
        """
        تحديث النص البديل لوسائط
        
        Args:
            media_id (int): معرف الوسائط
            alt_text (str): النص البديل الجديد
            
        Returns:
            dict: بيانات الوسائط المحدثة
        """
        try:
            # إرسال طلب تحديث الوسائط
            response = self.session.post(f"{self.api_url}/media/{media_id}", json={
                'alt_text': alt_text
            })
            response.raise_for_status()
            
            self.logger.info(f"تم تحديث النص البديل للوسائط {media_id} بنجاح")
            return response.json()
        
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الوسائط {media_id}: {str(e)}")
            return None
    
    def find_post_by_url(self, url):
        """
        البحث عن مقالة أو صفحة بواسطة عنوان URL
        
        Args:
            url (str): عنوان URL للمقالة أو الصفحة
            
        Returns:
            dict: بيانات المقالة أو الصفحة
        """
        try:
            # استخراج المسار النسبي من عنوان URL
            parsed_url = urlparse(url)
            path = parsed_url.path.strip('/')
            
            # البحث في المقالات أولاً
            posts = self.get_posts(per_page=100)
            for post in posts.get('posts', []):
                post_url = urlparse(post.get('link', '')).path.strip('/')
                if post_url == path:
                    return {'type': 'post', 'id': post['id'], 'data': post}
            
            # البحث في الصفحات إذا لم يتم العثور على المقالة
            pages = self.get_pages(per_page=100)
            for page in pages.get('pages', []):
                page_url = urlparse(page.get('link', '')).path.strip('/')
                if page_url == path:
                    return {'type': 'page', 'id': page['id'], 'data': page}
            
            # لم يتم العثور على أي مطابقة
            self.logger.warning(f"لم يتم العثور على مقالة أو صفحة بعنوان URL: {url}")
            return None
        
        except Exception as e:
            self.logger.error(f"خطأ في البحث عن مقالة بعنوان URL {url}: {str(e)}")
            return None
    
    def apply_fixes(self, url, fixes):
        """
        تطبيق الإصلاحات على مقالة أو صفحة
        
        Args:
            url (str): عنوان URL للمقالة أو الصفحة
            fixes (dict): الإصلاحات المراد تطبيقها
            
        Returns:
            dict: نتائج تطبيق الإصلاحات
        """
        try:
            # البحث عن المقالة أو الصفحة
            content_item = self.find_post_by_url(url)
            
            if not content_item:
                self.logger.warning(f"لم يتم العثور على محتوى لتطبيق الإصلاحات: {url}")
                return {
                    'success': False,
                    'message': 'لم يتم العثور على المحتوى'
                }
            
            # بيانات العنصر
            item_type = content_item['type']
            item_id = content_item['id']
            item_data = content_item['data']
            
            # تطبيق التحديثات
            update_data = {}
            applied_fixes = []
            
            # معالجة الإصلاحات التي تم تطبيقها
            for fix in fixes.get('applied_fixes', []):
                fix_type = fix.get('type')
                
                # تحديث العنوان
                if fix_type == 'title':
                    # استخراج العنوان الجديد
                    match = re.search(r'تم توليد عنوان جديد: "(.*?)"', fix.get('fix', ''))
                    if match:
                        new_title = match.group(1)
                        update_data['title'] = new_title
                        applied_fixes.append({
                            'type': 'title',
                            'old_value': item_data.get('title', {}).get('rendered', ''),
                            'new_value': new_title
                        })
                
                # تحديث الوصف التعريفي
                elif fix_type == 'meta_description':
                    # استخراج الوصف الجديد
                    match = re.search(r'تم توليد وصف جديد: "(.*?)"', fix.get('fix', ''))
                    if match:
                        new_description = match.group(1)
                        
                        # الحصول على البيانات الوصفية الحالية
                        meta = item_data.get('meta', {})
                        if not meta:
                            meta = {}
                        
                        meta['_yoast_wpseo_metadesc'] = new_description
                        update_data['meta'] = meta
                        
                        applied_fixes.append({
                            'type': 'meta_description',
                            'old_value': item_data.get('meta', {}).get('_yoast_wpseo_metadesc', ''),
                            'new_value': new_description
                        })
                
                # إضافة النص البديل للصور
                elif fix_type == 'alt_text':
                    # تحليل المحتوى للبحث عن الصور
                    content = item_data.get('content', {}).get('rendered', '')
                    
                    # البحث عن جميع وسوم الصور بدون سمة alt
                    images_without_alt = re.findall(r'<img[^>]*(?:alt=""|alt=\'\')[^>]*>', content)
                    images_without_alt.extend(re.findall(r'<img[^>]*(?!alt=)[^>]*>', content))
                    
                    # تحديث محتوى المقالة بإضافة النص البديل
                    for i, img_tag in enumerate(images_without_alt):
                        # توليد نص بديل بسيط
                        alt_text = f"صورة توضيحية لـ {item_data.get('title', {}).get('rendered', 'المقالة')}"
                        
                        # إضافة سمة alt إذا لم تكن موجودة
                        if 'alt=' not in img_tag:
                            new_img_tag = img_tag.replace('<img', f'<img alt="{alt_text}"')
                        else:
                            new_img_tag = re.sub(r'alt=(""|\'\')', f'alt="{alt_text}"', img_tag)
                        
                        content = content.replace(img_tag, new_img_tag)
                    
                    # تحديث المحتوى
                    if content != item_data.get('content', {}).get('rendered', ''):
                        update_data['content'] = content
                        applied_fixes.append({
                            'type': 'alt_text',
                            'count': len(images_without_alt)
                        })
            
            # تطبيق التحديثات إذا كانت موجودة
            if update_data:
                if item_type == 'post':
                    result = self.update_post(item_id, update_data)
                else:
                    result = self.update_page(item_id, update_data)
                
                if result:
                    return {
                        'success': True,
                        'applied_fixes': applied_fixes,
                        'message': f'تم تطبيق {len(applied_fixes)} إصلاح بنجاح'
                    }
            
            return {
                'success': True,
                'applied_fixes': applied_fixes,
                'message': 'لم يتم تطبيق أي إصلاحات'
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في تطبيق الإصلاحات على {url}: {str(e)}")
            return {
                'success': False,
                'message': f'خطأ في تطبيق الإصلاحات: {str(e)}'
            }
