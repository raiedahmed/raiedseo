#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة الدوال المساعدة - توفر وظائف عامة مستخدمة في أنحاء التطبيق
"""

import os
import re
import logging
import validators
from urllib.parse import urlparse
from datetime import datetime, timedelta

logger = logging.getLogger('rseo.helpers')

def validate_url(url):
    """
    التحقق من صحة عنوان URL
    
    Args:
        url (str): عنوان URL المراد التحقق منه
        
    Returns:
        bool: True إذا كان العنوان صحيحًا، False خلاف ذلك
    """
    # التأكد من وجود بروتوكول (http أو https)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # التحقق من صحة الرابط
    return validators.url(url)

def create_directory(directory_path):
    """
    إنشاء مجلد إذا لم يكن موجودًا
    
    Args:
        directory_path (str): مسار المجلد المراد إنشاؤه
        
    Returns:
        bool: True إذا تم الإنشاء بنجاح أو كان المجلد موجودًا بالفعل
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logger.info(f"تم إنشاء المجلد: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"فشل إنشاء المجلد {directory_path}: {str(e)}")
        return False

def get_domain_from_url(url):
    """
    استخراج اسم النطاق من عنوان URL
    
    Args:
        url (str): عنوان URL
        
    Returns:
        str: اسم النطاق
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # إزالة www. إذا كانت موجودة
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

def format_time(seconds):
    """
    تنسيق الوقت بالثواني إلى صيغة مقروءة
    
    Args:
        seconds (float): الوقت بالثواني
        
    Returns:
        str: الوقت بصيغة مقروءة
    """
    if seconds < 60:
        return f"{seconds:.1f} ثانية"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} دقيقة"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ساعة"

def sanitize_filename(filename):
    """
    تنظيف اسم الملف من الأحرف غير المسموح بها
    
    Args:
        filename (str): اسم الملف المراد تنظيفه
        
    Returns:
        str: اسم الملف بعد التنظيف
    """
    # استبدال الأحرف غير المسموح بها بشرطة
    sanitized = re.sub(r'[\\/*?:"<>|]', '-', filename)
    # إزالة النقاط المتكررة
    sanitized = re.sub(r'\.+', '.', sanitized)
    # إزالة المسافات المتكررة
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    return sanitized.strip()

def get_file_extension(url):
    """
    استخراج امتداد الملف من عنوان URL
    
    Args:
        url (str): عنوان URL
        
    Returns:
        str: امتداد الملف أو سلسلة فارغة إذا لم يكن هناك امتداد
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # البحث عن امتداد الملف
    match = re.search(r'\.([a-zA-Z0-9]+)$', path)
    if match:
        return match.group(1).lower()
    
    return ""

def is_image_url(url):
    """
    التحقق مما إذا كان عنوان URL يشير إلى صورة
    
    Args:
        url (str): عنوان URL
        
    Returns:
        bool: True إذا كان العنوان يشير إلى صورة، False خلاف ذلك
    """
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
    extension = get_file_extension(url)
    
    return extension in image_extensions

def format_bytes(size):
    """
    تنسيق حجم الملف بالبايت إلى صيغة مقروءة
    
    Args:
        size (int): حجم الملف بالبايت
        
    Returns:
        str: الحجم بصيغة مقروءة
    """
    power = 2**10  # 1024
    n = 0
    power_labels = {0: 'بايت', 1: 'كيلوبايت', 2: 'ميغابايت', 3: 'غيغابايت', 4: 'تيرابايت'}
    
    while size > power:
        size /= power
        n += 1
    
    return f"{size:.1f} {power_labels.get(n, '')}"
