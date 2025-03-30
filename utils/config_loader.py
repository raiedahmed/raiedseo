#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة تحميل الإعدادات - تستخدم لقراءة وإدارة إعدادات التطبيق
"""

import os
import yaml
from .logger import get_logger

logger = get_logger(__name__)

class ConfigLoader:
    """
    فئة تحميل وإدارة إعدادات التطبيق
    """
    
    def __init__(self, config_file=None):
        """
        تهيئة محمل الإعدادات
        
        Args:
            config_file (str, optional): مسار ملف الإعدادات
        """
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config.yaml')
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """
        تحميل الإعدادات من الملف
        
        Returns:
            dict: الإعدادات المحملة
        """
        try:
            # التحقق من وجود الملف
            if not os.path.exists(self.config_file):
                logger.warning(f"ملف الإعدادات غير موجود: {self.config_file}")
                return {}
            
            # قراءة الملف
            with open(self.config_file, 'r', encoding='utf-8') as f:
                logger.info(f"جاري تحميل الإعدادات من: {self.config_file}")
                self.config = yaml.safe_load(f)
            
            return self.config
        except yaml.YAMLError as e:
            logger.error(f"خطأ في تنسيق YAML: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات: {str(e)}")
            return {}
    
    def save_config(self, config=None):
        """
        حفظ الإعدادات في الملف
        
        Args:
            config (dict, optional): الإعدادات المراد حفظها
            
        Returns:
            bool: نجاح العملية
        """
        try:
            # استخدام الإعدادات المحددة أو الحالية
            config_to_save = config or self.config
            
            # إنشاء مجلد الإعدادات إذا لم يكن موجودًا
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # كتابة الإعدادات في الملف
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"تم حفظ الإعدادات بنجاح في: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """
        الحصول على قيمة من الإعدادات باستخدام المفتاح
        
        Args:
            key (str): المفتاح
            default: القيمة الافتراضية إذا لم يوجد المفتاح
            
        Returns:
            القيمة المستردة
        """
        # دعم مفاتيح متعددة المستويات (على سبيل المثال، 'crawler.max_pages')
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            try:
                value = value[k]
            except (KeyError, TypeError):
                return default
        
        return value
    
    def set(self, key, value):
        """
        تعيين قيمة في الإعدادات
        
        Args:
            key (str): المفتاح
            value: القيمة المراد تعيينها
            
        Returns:
            bool: نجاح العملية
        """
        # دعم مفاتيح متعددة المستويات
        keys = key.split('.')
        config = self.config
        
        # بناء مسار المفتاح
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # تعيين القيمة
        config[keys[-1]] = value
        
        return True
    
    def update(self, new_config):
        """
        تحديث الإعدادات بقيم جديدة
        
        Args:
            new_config (dict): الإعدادات الجديدة
            
        Returns:
            bool: نجاح العملية
        """
        def update_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    update_dict(d[k], v)
                else:
                    d[k] = v
        
        try:
            update_dict(self.config, new_config)
            return True
        except Exception as e:
            logger.error(f"خطأ في تحديث الإعدادات: {str(e)}")
            return False
    
    def reload(self):
        """
        إعادة تحميل الإعدادات من الملف
        
        Returns:
            dict: الإعدادات المحملة
        """
        return self.load_config()
    
    def get_all(self):
        """
        الحصول على جميع الإعدادات
        
        Returns:
            dict: جميع الإعدادات
        """
        return self.config
    
    def __str__(self):
        """
        تمثيل نصي للإعدادات
        
        Returns:
            str: تمثيل نصي للإعدادات
        """
        return yaml.dump(self.config, default_flow_style=False, allow_unicode=True)


# إنشاء كائن الإعدادات العام
config = ConfigLoader()


def get_config():
    """
    الحصول على كائن الإعدادات العام
    
    Returns:
        ConfigLoader: كائن الإعدادات
    """
    return config
