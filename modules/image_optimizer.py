#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة محسن الصور - مسؤولة عن تحليل وتحسين الصور في صفحات الويب

تقوم هذه الوحدة بتحليل الصور، واكتشاف المشاكل، وتحسين الصور
من خلال الضغط وإعادة التحجيم وتحويل الصيغ.
"""

import os
import re
import logging
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image, UnidentifiedImageError

class ImageOptimizer:
    """
    فئة لتحليل وتحسين الصور في صفحات الويب
    """
    
    def __init__(self, max_size_kb=200, min_dimensions=(100, 100), preferred_formats=None):
        """
        تهيئة محسن الصور
        
        Args:
            max_size_kb (int): الحجم الأقصى المفضل للصور بالكيلوبايت
            min_dimensions (tuple): الحد الأدنى لأبعاد الصور (العرض، الارتفاع)
            preferred_formats (list): صيغ الصور المفضلة
        """
        self.max_size_kb = max_size_kb
        self.min_dimensions = min_dimensions
        self.preferred_formats = preferred_formats or ['webp', 'jpeg', 'png']
        self.logger = logging.getLogger('rseo.image_optimizer')
        
        # جلسة للطلبات HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RSEO Image Optimizer/1.0',
        })
    
    def analyze_images(self, page_data):
        """
        تحليل الصور في صفحة ويب
        
        Args:
            page_data (dict): بيانات الصفحة المحتوية على HTML والعنوان URL
            
        Returns:
            dict: نتائج تحليل الصور والمشاكل والتوصيات
        """
        url = page_data.get('url', '')
        html_content = page_data.get('html', '')
        
        if not html_content:
            self.logger.error(f"لا يوجد محتوى HTML للتحليل: {url}")
            return {
                'status': 'error',
                'message': 'لا يوجد محتوى HTML للتحليل',
                'score': 0,
                'issues': []
            }
        
        # تحليل HTML باستخدام BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # استخراج عناصر الصور
        img_tags = soup.find_all('img')
        
        # إحصائيات الصور
        total_images = len(img_tags)
        images_without_alt = 0
        images_without_dimensions = 0
        large_images = 0
        small_images = 0
        wrong_format_images = 0
        total_size_kb = 0
        
        # تفاصيل الصور
        image_details = []
        issues = []
        
        # معالجة كل صورة
        for img in img_tags:
            # تجاهل الصور الصغيرة جدًا (مثل الأيقونات)
            if self._is_icon(img):
                continue
            
            src = img.get('src', '')
            if not src:
                continue
            
            # تحويل المسارات النسبية إلى مطلقة
            if not src.startswith(('http://', 'https://')):
                src = urljoin(url, src)
            
            # تحليل الصورة
            image_info = self._analyze_single_image(src, img)
            image_details.append(image_info)
            
            # جمع الإحصائيات
            if not img.get('alt'):
                images_without_alt += 1
            
            if not img.get('width') or not img.get('height'):
                images_without_dimensions += 1
            
            if image_info.get('size_kb', 0) > self.max_size_kb:
                large_images += 1
            
            if image_info.get('width', 0) < self.min_dimensions[0] or image_info.get('height', 0) < self.min_dimensions[1]:
                small_images += 1
            
            if image_info.get('format') not in self.preferred_formats:
                wrong_format_images += 1
            
            total_size_kb += image_info.get('size_kb', 0)
        
        # إنشاء قائمة المشاكل
        if images_without_alt > 0:
            issues.append({
                'type': 'error',
                'message': f'{images_without_alt} صورة بدون نص بديل (alt text)',
                'impact': 'high',
                'recommendation': 'أضف نصًا بديلًا وصفيًا لجميع الصور المهمة لتحسين إمكانية الوصول والسيو'
            })
        
        if images_without_dimensions > 0:
            issues.append({
                'type': 'warning',
                'message': f'{images_without_dimensions} صورة بدون تحديد أبعاد (width/height)',
                'impact': 'medium',
                'recommendation': 'حدد أبعاد الصور باستخدام سمات width و height لتحسين سرعة تحميل الصفحة'
            })
        
        if large_images > 0:
            issues.append({
                'type': 'warning',
                'message': f'{large_images} صورة كبيرة الحجم (أكبر من {self.max_size_kb} كيلوبايت)',
                'impact': 'high',
                'recommendation': 'قم بضغط الصور الكبيرة لتحسين سرعة تحميل الصفحة'
            })
        
        if wrong_format_images > 0:
            issues.append({
                'type': 'info',
                'message': f'{wrong_format_images} صورة بصيغة غير مثالية',
                'impact': 'low',
                'recommendation': f'استخدم صيغ الصور الحديثة مثل {", ".join(self.preferred_formats)} لتحسين الأداء'
            })
        
        # حساب نتيجة تحسين الصور
        score = self._calculate_image_score(total_images, images_without_alt, images_without_dimensions, large_images, wrong_format_images)
        
        return {
            'total_images': total_images,
            'images_without_alt': images_without_alt,
            'images_without_dimensions': images_without_dimensions,
            'large_images': large_images,
            'wrong_format_images': wrong_format_images,
            'total_size_kb': round(total_size_kb, 1),
            'average_size_kb': round(total_size_kb / total_images, 1) if total_images > 0 else 0,
            'image_details': image_details,
            'score': score,
            'issues': issues
        }
    
    def _analyze_single_image(self, src, img_tag):
        """
        تحليل صورة واحدة
        
        Args:
            src (str): مصدر الصورة (URL)
            img_tag (Tag): عنصر الصورة في HTML
            
        Returns:
            dict: معلومات الصورة
        """
        image_info = {
            'src': src,
            'alt': img_tag.get('alt', ''),
            'has_alt': bool(img_tag.get('alt')),
            'width': None,
            'height': None,
            'size_kb': None,
            'format': None,
            'filename': os.path.basename(urlparse(src).path),
            'is_data_uri': src.startswith('data:')
        }
        
        # استخراج الأبعاد من الوسوم إذا كانت متوفرة
        if img_tag.get('width'):
            try:
                image_info['width'] = int(img_tag['width'])
            except ValueError:
                pass
        
        if img_tag.get('height'):
            try:
                image_info['height'] = int(img_tag['height'])
            except ValueError:
                pass
        
        # محاولة تحليل الصورة
        try:
            if image_info['is_data_uri']:
                # تحليل صورة Data URI
                data_uri_info = self._analyze_data_uri(src)
                image_info.update(data_uri_info)
            else:
                # تحليل صورة عادية
                image_info['format'] = self._get_format_from_url(src)
                
                # محاولة تحميل الصورة
                try:
                    response = self.session.get(src, timeout=10, stream=True)
                    response.raise_for_status()
                    
                    # حساب حجم الصورة
                    content_length = response.headers.get('content-length')
                    if content_length:
                        image_info['size_kb'] = int(content_length) / 1024
                    else:
                        # إذا كان الحجم غير متوفر في الترويسة، قراءة المحتوى كاملاً
                        content = response.content
                        image_info['size_kb'] = len(content) / 1024
                    
                    # تحليل أبعاد وتنسيق الصورة
                    try:
                        img = Image.open(BytesIO(response.content))
                        if not image_info['width']:
                            image_info['width'] = img.width
                        if not image_info['height']:
                            image_info['height'] = img.height
                        image_info['format'] = img.format.lower() if img.format else image_info['format']
                    except Exception as e:
                        self.logger.debug(f"فشل تحليل الصورة {src}: {str(e)}")
                
                except Exception as e:
                    self.logger.debug(f"فشل تحميل الصورة {src}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الصورة {src}: {str(e)}")
        
        return image_info
    
    def _is_icon(self, img_tag):
        """
        التحقق مما إذا كانت الصورة عبارة عن أيقونة صغيرة
        
        Args:
            img_tag (Tag): عنصر الصورة في HTML
            
        Returns:
            bool: True إذا كانت الصورة أيقونة
        """
        # التحقق من الأبعاد
        width = img_tag.get('width')
        height = img_tag.get('height')
        
        if width and height:
            try:
                width = int(width)
                height = int(height)
                if width < 32 and height < 32:
                    return True
            except ValueError:
                pass
        
        # التحقق من اسم الملف
        src = img_tag.get('src', '')
        if 'icon' in src.lower() or 'logo' in src.lower():
            return True
        
        # التحقق من الفئات
        classes = img_tag.get('class', [])
        if isinstance(classes, list):
            classes_str = ' '.join(classes).lower()
        else:
            classes_str = str(classes).lower()
        
        if 'icon' in classes_str or 'logo' in classes_str:
            return True
        
        return False
    
    def _get_format_from_url(self, url):
        """
        استخراج تنسيق الصورة من عنوان URL
        
        Args:
            url (str): عنوان URL للصورة
            
        Returns:
            str: تنسيق الصورة أو None
        """
        # استخراج امتداد الملف من URL
        path = urlparse(url).path
        ext_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?.*)?$', path)
        
        if ext_match:
            ext = ext_match.group(1).lower()
            # تنسيق الامتداد
            if ext == 'jpg':
                return 'jpeg'
            return ext
        
        return None
    
    def _analyze_data_uri(self, data_uri):
        """
        تحليل صورة Data URI
        
        Args:
            data_uri (str): Data URI للصورة
            
        Returns:
            dict: معلومات الصورة
        """
        result = {
            'width': None,
            'height': None,
            'size_kb': None,
            'format': None
        }
        
        try:
            # استخراج بيانات ونوع الصورة
            header, encoded = data_uri.split(',', 1)
            
            # استخراج نوع MIME
            mime_match = re.search(r'data:([^;]+);', header)
            if mime_match:
                mime_type = mime_match.group(1).lower()
                if 'jpeg' in mime_type or 'jpg' in mime_type:
                    result['format'] = 'jpeg'
                elif 'png' in mime_type:
                    result['format'] = 'png'
                elif 'gif' in mime_type:
                    result['format'] = 'gif'
                elif 'webp' in mime_type:
                    result['format'] = 'webp'
                elif 'svg' in mime_type:
                    result['format'] = 'svg'
            
            # حساب حجم البيانات
            if 'base64' in header:
                import base64
                decoded = base64.b64decode(encoded)
                result['size_kb'] = len(decoded) / 1024
                
                # تحليل أبعاد الصورة
                try:
                    img = Image.open(BytesIO(decoded))
                    result['width'] = img.width
                    result['height'] = img.height
                except UnidentifiedImageError:
                    pass
        
        except Exception as e:
            self.logger.debug(f"فشل تحليل Data URI: {str(e)}")
        
        return result
    
    def _calculate_image_score(self, total, without_alt, without_dimensions, large, wrong_format):
        """
        حساب نتيجة تحسين الصور
        
        Args:
            total (int): إجمالي عدد الصور
            without_alt (int): عدد الصور بدون نص بديل
            without_dimensions (int): عدد الصور بدون أبعاد
            large (int): عدد الصور الكبيرة
            wrong_format (int): عدد الصور بصيغ غير مثالية
            
        Returns:
            int: النتيجة من 0 إلى 100
        """
        if total == 0:
            return 100  # لا توجد صور للتقييم
        
        # حساب النسب المئوية للمشاكل
        alt_penalty = (without_alt / total) * 40  # ترجيح عالٍ لنصوص alt
        dimension_penalty = (without_dimensions / total) * 20
        size_penalty = (large / total) * 30
        format_penalty = (wrong_format / total) * 10
        
        # حساب النتيجة النهائية
        score = 100 - (alt_penalty + dimension_penalty + size_penalty + format_penalty)
        
        return max(0, min(100, round(score)))
    
    def optimize_image(self, image_path, output_path=None, quality=85, max_width=None, format=None):
        """
        تحسين صورة عن طريق الضغط وإعادة التحجيم
        
        Args:
            image_path (str): مسار الصورة الأصلية
            output_path (str, optional): مسار الصورة المحسنة
            quality (int): جودة الصورة (1-100)
            max_width (int, optional): الحد الأقصى للعرض
            format (str, optional): تنسيق الصورة المحسنة (webp, jpeg, png)
            
        Returns:
            dict: معلومات الصورة المحسنة
        """
        try:
            # افتراضيات لمسار الإخراج وتنسيق الصورة
            if not output_path:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_optimized.{format or 'webp'}"
            
            # فتح الصورة
            img = Image.open(image_path)
            
            # إعادة تحجيم الصورة إذا لزم الأمر
            if max_width and img.width > max_width:
                # حساب النسبة للحفاظ على التناسب
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
            
            # تحديد تنسيق الإخراج
            output_format = format or os.path.splitext(output_path)[1][1:] or 'webp'
            if output_format.lower() == 'jpg':
                output_format = 'jpeg'
            
            # حفظ الصورة المحسنة
            if output_format.lower() == 'webp':
                img.save(output_path, 'WEBP', quality=quality, method=6)
            elif output_format.lower() == 'jpeg':
                img = img.convert('RGB')  # تحويل إلى RGB للصور JPEG
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif output_format.lower() == 'png':
                img.save(output_path, 'PNG', optimize=True)
            else:
                img.save(output_path, quality=quality)
            
            # حساب نسبة الضغط
            original_size = os.path.getsize(image_path)
            optimized_size = os.path.getsize(output_path)
            reduction_percent = ((original_size - optimized_size) / original_size) * 100
            
            return {
                'original_path': image_path,
                'optimized_path': output_path,
                'original_size_kb': original_size / 1024,
                'optimized_size_kb': optimized_size / 1024,
                'reduction_percent': round(reduction_percent, 1),
                'width': img.width,
                'height': img.height,
                'format': output_format
            }
        
        except Exception as e:
            self.logger.error(f"فشل تحسين الصورة {image_path}: {str(e)}")
            return {
                'error': str(e),
                'original_path': image_path,
                'success': False
            }
    
    def optimize_images_in_directory(self, directory, output_directory=None, quality=85, max_width=1920, format='webp'):
        """
        تحسين جميع الصور في مجلد معين
        
        Args:
            directory (str): مسار المجلد المحتوي على الصور
            output_directory (str, optional): مسار مجلد الإخراج
            quality (int): جودة الصور (1-100)
            max_width (int): الحد الأقصى لعرض الصور
            format (str): تنسيق الصور المحسنة
            
        Returns:
            dict: ملخص لعملية التحسين
        """
        if not os.path.isdir(directory):
            return {'error': 'المجلد غير موجود', 'success': False}
        
        # إنشاء مجلد الإخراج إذا لم يكن موجودًا
        if output_directory and not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # البحث عن الصور في المجلد
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        images = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    images.append(os.path.join(root, file))
        
        # تحسين كل صورة
        results = []
        total_original_size = 0
        total_optimized_size = 0
        
        for image_path in images:
            # تحديد مسار الإخراج
            if output_directory:
                rel_path = os.path.relpath(image_path, directory)
                output_subdir = os.path.dirname(rel_path)
                
                if output_subdir:
                    full_output_subdir = os.path.join(output_directory, output_subdir)
                    if not os.path.exists(full_output_subdir):
                        os.makedirs(full_output_subdir)
                
                filename = os.path.basename(image_path)
                name, _ = os.path.splitext(filename)
                output_path = os.path.join(output_directory, output_subdir, f"{name}.{format}")
            else:
                output_path = None
            
            # تحسين الصورة
            result = self.optimize_image(image_path, output_path, quality, max_width, format)
            results.append(result)
            
            # حساب الإحصائيات
            if 'error' not in result:
                total_original_size += result['original_size_kb']
                total_optimized_size += result['optimized_size_kb']
        
        # حساب الملخص
        summary = {
            'total_images': len(images),
            'optimized_images': len([r for r in results if 'error' not in r]),
            'failed_images': len([r for r in results if 'error' in r]),
            'total_original_size_kb': round(total_original_size, 1),
            'total_optimized_size_kb': round(total_optimized_size, 1),
            'total_reduction_kb': round(total_original_size - total_optimized_size, 1),
            'average_reduction_percent': round(((total_original_size - total_optimized_size) / total_original_size) * 100, 1) if total_original_size > 0 else 0,
            'details': results
        }
        
        return summary
