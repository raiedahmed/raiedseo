#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - أداة تتبع التصنيف في محركات البحث

تتبع تصنيف المواقع والكلمات المفتاحية في محركات البحث
"""

import time
import random
import json
import re
import logging
import os
import csv
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote_plus
import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor

from utils.config_loader import ConfigLoader
from utils.helpers import validate_url

class RankTracker:
    """
    أداة تتبع تصنيف المواقع في محركات البحث ومراقبة الكلمات المفتاحية
    """
    
    def __init__(self, config=None, db_path="data/rank_tracker.db"):
        """
        تهيئة متتبع التصنيف
        
        Args:
            config (dict, optional): إعدادات التهيئة
            db_path (str, optional): مسار قاعدة البيانات
        """
        self.config = config or ConfigLoader().get_all()
        self.logger = logging.getLogger(__name__)
        
        # التأكد من وجود المجلد
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # الاتصال بقاعدة البيانات
        self.db_path = db_path
        self.setup_database()
        
        # تكوين المتغيرات
        self.proxies = self.config.get('proxies', [])
        self.api_keys = {
            'serpapi': os.environ.get('SERPAPI_KEY', ''),
            'semrush': os.environ.get('SEMRUSH_KEY', ''),
            'ahrefs': os.environ.get('AHREFS_KEY', '')
        }
        
        # محركات البحث المدعومة
        self.search_engines = {
            'google': self._search_google,
            'bing': self._search_bing,
            'yahoo': self._search_yahoo
        }
        
        # إنشاء UserAgent متغير
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
    
    def setup_database(self):
        """إنشاء قاعدة البيانات وتهيئة الجداول إذا لم تكن موجودة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # جدول الكلمات المفتاحية
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                domain TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(keyword, domain)
            )
            ''')
            
            # جدول التصنيفات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER,
                domain TEXT,
                position INTEGER,
                url TEXT,
                search_engine TEXT,
                date_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            )
            ''')
            
            # جدول الروابط الخلفية
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS backlinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                source_url TEXT,
                target_url TEXT,
                anchor_text TEXT,
                follow BOOLEAN,
                date_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_url, target_url)
            )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"خطأ في إعداد قاعدة البيانات: {str(e)}")
    
    def track_keyword(self, keyword, domain, search_engine='google', pages=3, use_api=False):
        """
        تتبع تصنيف كلمة مفتاحية لنطاق معين
        
        Args:
            keyword (str): الكلمة المفتاحية المراد تتبعها
            domain (str): النطاق المراد تتبعه
            search_engine (str, optional): محرك البحث المستخدم. الافتراضي 'google'.
            pages (int, optional): عدد صفحات البحث للفحص. الافتراضي 3.
            use_api (bool, optional): استخدام API بدلاً من الزحف. الافتراضي False.
            
        Returns:
            dict: نتائج التتبع (الموقع، الرابط، إلخ)
        """
        # تنظيف النطاق
        domain = domain.lower()
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        # التحقق من صحة المدخلات
        if not keyword or not domain:
            return {'error': 'يجب تحديد الكلمة المفتاحية والنطاق'}
        
        # التحقق من وجود الكلمة المفتاحية في قاعدة البيانات أو إضافتها
        keyword_id = self._add_keyword(keyword, domain)
        
        results = {
            'keyword': keyword,
            'domain': domain,
            'search_engine': search_engine,
            'date_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'position': None,
            'url': None,
            'page': None,
            'total_results': 0,
            'serp_features': [],
            'other_domains': []
        }
        
        try:
            # استخدم API أو الزحف بناءً على الخيار
            if use_api and self.api_keys['serpapi']:
                serp_data = self._search_with_api(keyword, search_engine)
                position_data = self._extract_position_from_api(serp_data, domain)
            else:
                if search_engine in self.search_engines:
                    serp_data = self.search_engines[search_engine](keyword, pages)
                    position_data = self._extract_position(serp_data, domain)
                else:
                    return {'error': f'محرك البحث {search_engine} غير مدعوم'}
            
            # تحديث النتائج بالبيانات المستخرجة
            results.update(position_data)
            
            # تخزين النتائج في قاعدة البيانات
            self._save_ranking(keyword_id, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"خطأ في تتبع الكلمة المفتاحية: {str(e)}")
            return {'error': str(e)}
    
    def track_keywords_bulk(self, keywords, domain, search_engine='google', pages=3, use_api=False, max_workers=5):
        """
        تتبع مجموعة من الكلمات المفتاحية لنطاق معين
        
        Args:
            keywords (list): قائمة الكلمات المفتاحية المراد تتبعها
            domain (str): النطاق المراد تتبعه
            search_engine (str, optional): محرك البحث المستخدم
            pages (int, optional): عدد صفحات البحث للفحص
            use_api (bool, optional): استخدام API بدلاً من الزحف
            max_workers (int, optional): عدد المعالجات المتزامنة
            
        Returns:
            dict: نتائج التتبع لجميع الكلمات المفتاحية
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_keyword = {
                executor.submit(
                    self.track_keyword, 
                    keyword, 
                    domain, 
                    search_engine, 
                    pages, 
                    use_api
                ): keyword for keyword in keywords
            }
            
            for future in future_to_keyword:
                keyword = future_to_keyword[future]
                try:
                    results[keyword] = future.result()
                except Exception as e:
                    results[keyword] = {'error': str(e)}
        
        return results
    
    def get_ranking_history(self, keyword, domain, search_engine='google', days=30):
        """
        الحصول على تاريخ تصنيف كلمة مفتاحية لنطاق معين
        
        Args:
            keyword (str): الكلمة المفتاحية
            domain (str): النطاق
            search_engine (str, optional): محرك البحث
            days (int, optional): عدد الأيام للحصول على البيانات
            
        Returns:
            list: تاريخ التصنيف مع التاريخ والموقع
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # الحصول على معرف الكلمة المفتاحية
            cursor.execute(
                "SELECT id FROM keywords WHERE keyword = ? AND domain = ?",
                (keyword, domain)
            )
            keyword_data = cursor.fetchone()
            
            if not keyword_data:
                return []
            
            keyword_id = keyword_data['id']
            
            # الحصول على تاريخ التصنيف
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute(
                """
                SELECT position, url, date_checked 
                FROM rankings 
                WHERE keyword_id = ? AND domain = ? AND search_engine = ? AND date_checked >= ?
                ORDER BY date_checked ASC
                """,
                (keyword_id, domain, search_engine, start_date)
            )
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'date': row['date_checked'],
                    'position': row['position'],
                    'url': row['url']
                })
            
            conn.close()
            return history
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تاريخ التصنيف: {str(e)}")
            return []
    
    def get_top_keywords(self, domain, limit=10, search_engine='google'):
        """
        الحصول على أفضل الكلمات المفتاحية المتصدرة لنطاق معين
        
        Args:
            domain (str): النطاق
            limit (int, optional): الحد الأقصى للنتائج
            search_engine (str, optional): محرك البحث
            
        Returns:
            list: قائمة بأفضل الكلمات المفتاحية
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT k.keyword, MIN(r.position) as best_position, r.url, MAX(r.date_checked) as last_checked
                FROM keywords k
                JOIN rankings r ON k.id = r.keyword_id
                WHERE k.domain = ? AND r.search_engine = ?
                GROUP BY k.keyword
                ORDER BY best_position ASC
                LIMIT ?
                """,
                (domain, search_engine, limit)
            )
            
            top_keywords = []
            for row in cursor.fetchall():
                top_keywords.append({
                    'keyword': row['keyword'],
                    'position': row['best_position'],
                    'url': row['url'],
                    'last_checked': row['last_checked']
                })
            
            conn.close()
            return top_keywords
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على أفضل الكلمات المفتاحية: {str(e)}")
            return []
    
    def discover_ranking_keywords(self, domain, search_engine='google', use_api=False):
        """
        اكتشاف الكلمات المفتاحية التي يتصدرها النطاق
        
        Args:
            domain (str): النطاق
            search_engine (str, optional): محرك البحث
            use_api (bool, optional): استخدام API
            
        Returns:
            list: قائمة بالكلمات المفتاحية المكتشفة
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        discovered_keywords = []
        
        try:
            # استخدام API إذا كان متاحاً
            if use_api:
                if self.api_keys['semrush']:
                    discovered_keywords.extend(self._discover_with_semrush(domain))
                
                if self.api_keys['ahrefs']:
                    discovered_keywords.extend(self._discover_with_ahrefs(domain))
            
            # استخدام التنقيب إذا كان API غير متاح
            if not discovered_keywords:
                discovered_keywords = self._discover_with_scraping(domain)
            
            # تخزين الكلمات المفتاحية المكتشفة
            for keyword in discovered_keywords:
                self._add_keyword(keyword, domain)
            
            return discovered_keywords
            
        except Exception as e:
            self.logger.error(f"خطأ في اكتشاف الكلمات المفتاحية: {str(e)}")
            return []
    
    def export_rankings(self, domain, format='csv', filename=None):
        """
        تصدير بيانات التصنيف لنطاق معين
        
        Args:
            domain (str): النطاق
            format (str, optional): تنسيق التصدير (csv, json, excel)
            filename (str, optional): اسم الملف
            
        Returns:
            str: مسار الملف المصدر
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rankings_{domain}_{timestamp}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT k.keyword, r.position, r.url, r.search_engine, r.date_checked
            FROM keywords k
            JOIN rankings r ON k.id = r.keyword_id
            WHERE k.domain = ?
            ORDER BY r.date_checked DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(domain,))
            
            if format == 'csv':
                filepath = f"{filename}.csv"
                df.to_csv(filepath, index=False)
            elif format == 'json':
                filepath = f"{filename}.json"
                df.to_json(filepath, orient='records')
            elif format == 'excel':
                filepath = f"{filename}.xlsx"
                df.to_excel(filepath, index=False)
            else:
                conn.close()
                return None
            
            conn.close()
            return filepath
            
        except Exception as e:
            self.logger.error(f"خطأ في تصدير بيانات التصنيف: {str(e)}")
            return None
    
    # أساليب مساعدة
    def _add_keyword(self, keyword, domain):
        """إضافة كلمة مفتاحية إلى قاعدة البيانات وإرجاع معرفها"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود الكلمة المفتاحية
            cursor.execute(
                "SELECT id FROM keywords WHERE keyword = ? AND domain = ?",
                (keyword, domain)
            )
            existing = cursor.fetchone()
            
            if existing:
                keyword_id = existing[0]
            else:
                # إضافة كلمة مفتاحية جديدة
                cursor.execute(
                    "INSERT INTO keywords (keyword, domain) VALUES (?, ?)",
                    (keyword, domain)
                )
                keyword_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return keyword_id
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة الكلمة المفتاحية: {str(e)}")
            return None
    
    def _save_ranking(self, keyword_id, results):
        """حفظ بيانات التصنيف في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO rankings 
                (keyword_id, domain, position, url, search_engine, date_checked) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    keyword_id,
                    results['domain'],
                    results['position'],
                    results['url'],
                    results['search_engine'],
                    results['date_checked']
                )
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ بيانات التصنيف: {str(e)}")
