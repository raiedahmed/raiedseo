#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - أداة تحليل الروابط الخلفية (الباك لينك)

تحليل، تتبع، وإنشاء تقارير الروابط الخلفية للمواقع
"""

import os
import time
import json
import re
import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # استخدام المحرك غير التفاعلي

from utils.config_loader import ConfigLoader
from utils.helpers import validate_url, create_directory

class BacklinkAnalyzer:
    """
    أداة تحليل الروابط الخلفية (الباك لينك) للمواقع
    """
    
    def __init__(self, config=None, db_path="data/rank_tracker.db"):
        """
        تهيئة محلل الروابط الخلفية
        
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
        
        # تكوين المتغيرات
        self.proxies = self.config.get('proxies', [])
        self.api_keys = {
            'ahrefs': os.environ.get('AHREFS_KEY', ''),
            'majestic': os.environ.get('MAJESTIC_KEY', ''),
            'moz': os.environ.get('MOZ_KEY', '')
        }
        
        # إنشاء UserAgent متغير
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
    
    def analyze_backlinks(self, domain, use_api=False, max_results=100):
        """
        تحليل الروابط الخلفية لنطاق معين
        
        Args:
            domain (str): النطاق المراد تحليله
            use_api (bool, optional): استخدام API بدلاً من الزحف. الافتراضي False.
            max_results (int, optional): الحد الأقصى لعدد النتائج. الافتراضي 100.
            
        Returns:
            dict: نتائج تحليل الروابط الخلفية
        """
        # تنظيف النطاق
        domain = domain.lower()
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        results = {
            'domain': domain,
            'date_analyzed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'backlinks_count': 0,
            'referring_domains_count': 0,
            'backlinks': [],
            'referring_domains': {},
            'anchor_text': {},
            'follow_ratio': 0,
            'top_backlinks': []
        }
        
        try:
            # استخدام API إذا كان متاحًا
            if use_api:
                if self.api_keys['ahrefs']:
                    backlinks_data = self._analyze_with_ahrefs(domain, max_results)
                elif self.api_keys['majestic']:
                    backlinks_data = self._analyze_with_majestic(domain, max_results)
                elif self.api_keys['moz']:
                    backlinks_data = self._analyze_with_moz(domain, max_results)
                else:
                    # استخدام الزحف إذا لم تكن API متاحة
                    backlinks_data = self._analyze_with_scraping(domain, max_results)
            else:
                # استخدام الزحف دائمًا
                backlinks_data = self._analyze_with_scraping(domain, max_results)
            
            # تحديث النتائج بالبيانات المحللة
            if backlinks_data:
                results.update(backlinks_data)
            
            # حفظ البيانات في قاعدة البيانات
            self._save_backlinks(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل الروابط الخلفية: {str(e)}")
            return {'error': str(e)}
    
    def check_backlink(self, source_url, target_domain):
        """
        التحقق من وجود رابط خلفي من URL المصدر إلى النطاق الهدف
        
        Args:
            source_url (str): رابط المصدر
            target_domain (str): النطاق الهدف
            
        Returns:
            dict: نتيجة التحقق من الرابط الخلفي
        """
        # تنظيف النطاق الهدف
        if target_domain.startswith(('http://', 'https://')):
            target_domain = urlparse(target_domain).netloc
        
        result = {
            'source_url': source_url,
            'target_domain': target_domain,
            'has_backlink': False,
            'target_url': None,
            'anchor_text': None,
            'is_follow': False,
            'date_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # الحصول على المحتوى
            headers = {'User-Agent': self._get_user_agent()}
            response = requests.get(source_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return result
            
            # تحليل المحتوى
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن جميع الروابط التي تشير إلى النطاق الهدف
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                
                # تجاهل الروابط الفارغة
                if not href:
                    continue
                
                # تحويل الرابط النسبي إلى رابط مطلق
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(source_url, href)
                
                # التحقق مما إذا كان الرابط يشير إلى النطاق الهدف
                link_domain = urlparse(href).netloc
                
                if link_domain == target_domain:
                    result['has_backlink'] = True
                    result['target_url'] = href
                    result['anchor_text'] = link.get_text(strip=True)
                    
                    # التحقق مما إذا كان الرابط follow
                    rel = link.get('rel', '')
                    result['is_follow'] = 'nofollow' not in rel
                    
                    # حفظ الرابط الخلفي في قاعدة البيانات
                    self._save_backlink(source_url, href, result['anchor_text'], result['is_follow'])
                    
                    break
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من الرابط الخلفي: {str(e)}")
            return {'error': str(e)}
    
    def generate_backlink_report(self, domain, output_dir="results", format="html"):
        """
        إنشاء تقرير شامل للروابط الخلفية
        
        Args:
            domain (str): النطاق المراد تحليله
            output_dir (str, optional): مجلد الإخراج. الافتراضي "results".
            format (str, optional): تنسيق التقرير (html, pdf, json). الافتراضي "html".
            
        Returns:
            str: مسار ملف التقرير
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        # التأكد من وجود المجلد
        output_path = os.path.join(output_dir, "backlinks")
        create_directory(output_path)
        
        # الحصول على بيانات الروابط الخلفية
        backlinks_data = self.get_backlink_data(domain)
        
        if not backlinks_data or 'error' in backlinks_data:
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backlinks_{domain}_{timestamp}"
        
        try:
            if format == "json":
                # تصدير بتنسيق JSON
                filepath = os.path.join(output_path, f"{filename}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backlinks_data, f, ensure_ascii=False, indent=4)
                
                return filepath
                
            elif format == "html":
                # إنشاء تقرير HTML
                filepath = os.path.join(output_path, f"{filename}.html")
                
                # إنشاء رسم بياني للروابط
                chart_path = self._generate_backlink_chart(domain, backlinks_data, output_path)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self._generate_html_report(domain, backlinks_data, chart_path))
                
                return filepath
                
            elif format == "pdf":
                # إنشاء تقرير PDF (يتطلب تثبيت مكتبات إضافية مثل WeasyPrint)
                html_path = self.generate_backlink_report(domain, output_dir, "html")
                
                if not html_path:
                    return None
                
                pdf_path = os.path.join(output_path, f"{filename}.pdf")
                
                # هنا يمكن استخدام مكتبة لتحويل HTML إلى PDF
                return pdf_path
                
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء تقرير الروابط الخلفية: {str(e)}")
            return None
    
    def get_backlink_data(self, domain):
        """
        الحصول على بيانات الروابط الخلفية المخزنة في قاعدة البيانات
        
        Args:
            domain (str): النطاق
            
        Returns:
            dict: بيانات الروابط الخلفية
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # الحصول على جميع الروابط الخلفية للنطاق
            cursor.execute(
                """
                SELECT source_url, target_url, anchor_text, follow, date_discovered
                FROM backlinks
                WHERE target_url LIKE ? OR target_url LIKE ?
                ORDER BY date_discovered DESC
                """,
                (f"http://{domain}%", f"https://{domain}%")
            )
            
            backlinks = []
            referring_domains = set()
            anchor_texts = {}
            follow_count = 0
            
            for row in cursor.fetchall():
                source_domain = urlparse(row['source_url']).netloc
                referring_domains.add(source_domain)
                
                # إحصاء النصوص المرساة
                anchor = row['anchor_text']
                if anchor in anchor_texts:
                    anchor_texts[anchor] += 1
                else:
                    anchor_texts[anchor] = 1
                
                # عدد الروابط المتابعة
                if row['follow']:
                    follow_count += 1
                
                backlinks.append({
                    'source_url': row['source_url'],
                    'target_url': row['target_url'],
                    'source_domain': source_domain,
                    'anchor_text': row['anchor_text'],
                    'is_follow': row['follow'],
                    'date_discovered': row['date_discovered']
                })
            
            # حساب نسبة المتابعة
            follow_ratio = 0
            if backlinks:
                follow_ratio = follow_count / len(backlinks)
            
            # تجميع الروابط حسب النطاق المرجعي
            domains_data = {}
            for link in backlinks:
                domain = link['source_domain']
                if domain in domains_data:
                    domains_data[domain]['count'] += 1
                else:
                    domains_data[domain] = {
                        'count': 1,
                        'urls': []
                    }
                domains_data[domain]['urls'].append(link['source_url'])
            
            # ترتيب النطاقات المرجعية حسب العدد
            sorted_domains = sorted(domains_data.items(), key=lambda x: x[1]['count'], reverse=True)
            
            conn.close()
            
            return {
                'domain': domain,
                'backlinks_count': len(backlinks),
                'referring_domains_count': len(referring_domains),
                'backlinks': backlinks,
                'referring_domains': dict(sorted_domains),
                'anchor_text': anchor_texts,
                'follow_ratio': follow_ratio,
                'top_backlinks': sorted(backlinks, key=lambda x: x['is_follow'], reverse=True)[:10]
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على بيانات الروابط الخلفية: {str(e)}")
            return {'error': str(e)}
    
    def find_backlink_opportunities(self, domain, keywords=None, max_results=50):
        """
        العثور على فرص لإنشاء روابط خلفية جديدة
        
        Args:
            domain (str): النطاق
            keywords (list, optional): قائمة الكلمات المفتاحية ذات الصلة
            max_results (int, optional): الحد الأقصى لعدد النتائج
            
        Returns:
            list: قائمة فرص الروابط الخلفية
        """
        # تنظيف النطاق
        if domain.startswith(('http://', 'https://')):
            domain = urlparse(domain).netloc
        
        opportunities = []
        
        try:
            # الحصول على قائمة المواقع التي عليها روابط خلفية للمنافسين ولكن ليس للنطاق
            competitor_backlinks = self._find_competitor_backlinks(domain, max_results)
            opportunities.extend(competitor_backlinks)
            
            # البحث عن فرص بناءً على الكلمات المفتاحية
            if keywords:
                keyword_opportunities = self._find_keyword_opportunities(domain, keywords, max_results)
                opportunities.extend(keyword_opportunities)
            
            # إزالة التكرار
            unique_opportunities = []
            seen_urls = set()
            
            for opp in opportunities:
                if opp['source_url'] not in seen_urls:
                    seen_urls.add(opp['source_url'])
                    unique_opportunities.append(opp)
            
            # ترتيب الفرص حسب الأهمية
            sorted_opportunities = sorted(unique_opportunities, key=lambda x: x['score'], reverse=True)
            
            return sorted_opportunities[:max_results]
            
        except Exception as e:
            self.logger.error(f"خطأ في البحث عن فرص الروابط الخلفية: {str(e)}")
            return []
    
    # أساليب مساعدة
    def _save_backlinks(self, results):
        """حفظ بيانات الروابط الخلفية في قاعدة البيانات"""
        try:
            for backlink in results.get('backlinks', []):
                self._save_backlink(
                    backlink['source_url'],
                    backlink['target_url'],
                    backlink.get('anchor_text', ''),
                    backlink.get('is_follow', True)
                )
        except Exception as e:
            self.logger.error(f"خطأ في حفظ بيانات الروابط الخلفية: {str(e)}")
    
    def _save_backlink(self, source_url, target_url, anchor_text, follow):
        """حفظ رابط خلفي واحد في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق مما إذا كان الرابط موجودًا بالفعل
            cursor.execute(
                "SELECT id FROM backlinks WHERE source_url = ? AND target_url = ?",
                (source_url, target_url)
            )
            existing = cursor.fetchone()
            
            if not existing:
                # إضافة رابط خلفي جديد
                cursor.execute(
                    """
                    INSERT INTO backlinks 
                    (domain, source_url, target_url, anchor_text, follow, date_discovered) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        urlparse(target_url).netloc,
                        source_url,
                        target_url,
                        anchor_text,
                        follow,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الرابط الخلفي: {str(e)}")
    
    def _get_user_agent(self):
        """الحصول على User-Agent عشوائي"""
        if self.ua:
            return self.ua.random
        else:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def _analyze_with_scraping(self, domain, max_results=100):
        """تحليل الروابط الخلفية باستخدام التنقيب"""
        # هذه وظيفة معقدة تحتاج إلى تنفيذ متقدم
        # هنا نحن نستخدم نهجًا مبسطًا للتوضيح
        
        backlinks = []
        referring_domains = set()
        anchor_texts = {}
        follow_count = 0
        
        # استخدام مواقع مجانية لاستخلاص الروابط الخلفية
        sources = [
            f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey",
            f"https://www.google.com/search?q=link:{domain}&num=100",
            f"https://www.bing.com/search?q=link:{domain}&count=100"
        ]
        
        for source in sources:
            try:
                headers = {'User-Agent': self._get_user_agent()}
                response = requests.get(source, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    continue
                
                # استخراج URLs التي تشير إلى النطاق
                if 'web.archive.org' in source:
                    data = response.json()
                    if data and len(data) > 1:
                        for item in data[1:]:  # تجاهل الصف الأول (العناوين)
                            referring_url = item[0]
                            backlinks.append({
                                'source_url': referring_url,
                                'target_url': f"https://{domain}",
                                'source_domain': urlparse(referring_url).netloc,
                                'anchor_text': '',
                                'is_follow': True
                            })
                else:
                    # تحليل نتائج البحث
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        
                        # تصفية روابط محرك البحث نفسه
                        if 'google.com' in href or 'bing.com' in href:
                            continue
                        
                        if href.startswith(('http://', 'https://')) and domain not in href:
                            backlinks.append({
                                'source_url': href,
                                'target_url': f"https://{domain}",
                                'source_domain': urlparse(href).netloc,
                                'anchor_text': link.get_text(strip=True),
                                'is_follow': 'nofollow' not in link.get('rel', '')
                            })
            except Exception as e:
                self.logger.warning(f"خطأ في معالجة المصدر {source}: {str(e)}")
        
        # تحليل عينة من الروابط التي تم العثور عليها للتحقق من دقتها
        verified_backlinks = []
        source_urls = [link['source_url'] for link in backlinks[:max_results]]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(self.check_backlink, source_url, domain): source_url
                for source_url in source_urls
            }
            
            for future in future_to_url:
                source_url = future_to_url[future]
                try:
                    result = future.result()
                    if result.get('has_backlink', False):
                        verified_backlinks.append({
                            'source_url': result['source_url'],
                            'target_url': result['target_url'],
                            'source_domain': urlparse(result['source_url']).netloc,
                            'anchor_text': result['anchor_text'],
                            'is_follow': result['is_follow']
                        })
                except Exception as e:
                    self.logger.warning(f"خطأ في التحقق من الرابط {source_url}: {str(e)}")
        
        # معالجة البيانات التي تم التحقق منها
        for link in verified_backlinks:
            referring_domains.add(link['source_domain'])
            
            anchor = link['anchor_text']
            if anchor in anchor_texts:
                anchor_texts[anchor] += 1
            else:
                anchor_texts[anchor] = 1
            
            if link['is_follow']:
                follow_count += 1
        
        # حساب نسبة المتابعة
        follow_ratio = 0
        if verified_backlinks:
            follow_ratio = follow_count / len(verified_backlinks)
        
        # تجميع الروابط حسب النطاق المرجعي
        domains_data = {}
        for link in verified_backlinks:
            domain = link['source_domain']
            if domain in domains_data:
                domains_data[domain]['count'] += 1
            else:
                domains_data[domain] = {
                    'count': 1,
                    'urls': []
                }
            domains_data[domain]['urls'].append(link['source_url'])
        
        # ترتيب النطاقات المرجعية حسب العدد
        sorted_domains = sorted(domains_data.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            'backlinks_count': len(verified_backlinks),
            'referring_domains_count': len(referring_domains),
            'backlinks': verified_backlinks,
            'referring_domains': dict(sorted_domains),
            'anchor_text': anchor_texts,
            'follow_ratio': follow_ratio,
            'top_backlinks': sorted(verified_backlinks, key=lambda x: x['is_follow'], reverse=True)[:10]
        }
