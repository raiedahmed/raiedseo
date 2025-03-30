#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة التسجيل - مسؤولة عن إعداد وتكوين نظام تسجيل الأحداث
"""

import os
import logging
import logging.handlers
from datetime import datetime
import sys

def setup_logger(name, log_level=None, log_file=None):
    """
    إعداد مسجل الأحداث
    
    Args:
        name (str): اسم المسجل
        log_level (str, optional): مستوى التسجيل (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): مسار ملف السجل
        
    Returns:
        logging.Logger: كائن المسجل
    """
    # تحديد مستوى التسجيل
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # إنشاء مسجل
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # إزالة المعالجات السابقة إذا وجدت
    if logger.handlers:
        logger.handlers.clear()
    
    # إنشاء منسق السجل - تعديل لتجنب مشكلة الترميز
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # إضافة معالج لعرض السجلات في وحدة التحكم
    console_handler = logging.StreamHandler(sys.stdout)  # استخدام stdout بدلاً من stderr
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # إضافة معالج لكتابة السجلات في ملف إذا تم تحديد مسار
    if log_file is None and os.getenv('LOG_FILE'):
        log_file = os.getenv('LOG_FILE')
    
    if log_file:
        # إنشاء مجلد السجلات إذا لم يكن موجودًا
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # إضافة معالج الملف
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 ميغابايت كحد أقصى
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """
    الحصول على مسجل موجود أو إنشاء مسجل جديد
    
    Args:
        name (str): اسم المسجل
        
    Returns:
        logging.Logger: كائن المسجل
    """
    logger = logging.getLogger(name)
    
    # إذا لم يكن المسجل قد تم إعداده بعد
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

def log_function_call(func):
    """
    مزخرف لتسجيل استدعاءات الدوال
    
    Args:
        func: الدالة المراد تسجيل استدعاءاتها
        
    Returns:
        function: دالة مغلفة
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        try:
            logger.debug(f"استدعاء {func.__name__} بالمعاملات: args={args}, kwargs={kwargs}")
        except UnicodeEncodeError:
            logger.debug(f"استدعاء {func.__name__} (تم تجاهل تفاصيل المعاملات بسبب مشكلة الترميز)")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"اكتمال {func.__name__} بنجاح")
            return result
        except Exception as e:
            try:
                logger.error(f"خطأ في تنفيذ {func.__name__}: {str(e)}")
            except UnicodeEncodeError:
                logger.error(f"خطأ في تنفيذ {func.__name__}: (تم تجاهل تفاصيل الخطأ بسبب مشكلة الترميز)")
            raise
    
    return wrapper

class LoggerManager:
    """
    مدير للمسجلات لتسهيل التعامل مع مسجلات متعددة
    """
    
    def __init__(self):
        """تهيئة مدير المسجلات"""
        self.loggers = {}
    
    def get_logger(self, name, log_level=None, log_file=None):
        """
        الحصول على مسجل موجود أو إنشاء مسجل جديد
        
        Args:
            name (str): اسم المسجل
            log_level (str, optional): مستوى التسجيل
            log_file (str, optional): مسار ملف السجل
            
        Returns:
            logging.Logger: كائن المسجل
        """
        if name not in self.loggers:
            self.loggers[name] = setup_logger(name, log_level, log_file)
        
        return self.loggers[name]
    
    def set_global_level(self, level):
        """
        تعيين مستوى التسجيل لجميع المسجلات
        
        Args:
            level (str): مستوى التسجيل
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        for logger in self.loggers.values():
            logger.setLevel(numeric_level)
    
    def disable_console_output(self):
        """تعطيل عرض السجلات في وحدة التحكم لجميع المسجلات"""
        for logger in self.loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    logger.removeHandler(handler)
    
    def create_log_file(self, log_dir='logs'):
        """
        إنشاء ملف سجل جديد باستخدام التاريخ والوقت الحاليين
        
        Args:
            log_dir (str): مجلد السجلات
            
        Returns:
            str: مسار ملف السجل
        """
        # إنشاء مجلد السجلات إذا لم يكن موجودًا
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # إنشاء اسم الملف باستخدام التاريخ والوقت
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'rseo_{timestamp}.log')
        
        return log_file
