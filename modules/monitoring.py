#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - نظام المراقبة وإنشاء التقارير الدورية
مراقبة أداء المواقع وإنشاء تقارير دورية تلقائية
"""

import os
import json
import time
import logging
import datetime
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from jinja2 import Environment, FileSystemLoader

# استيراد وحدات داخلية
from modules.analyzer import SEOAnalyzer
from modules.crawler import WebCrawler
from modules.report_generator import ReportGenerator
from utils.config_loader import ConfigLoader
from utils.logger import get_logger
from utils.helpers import create_directory

class MonitoringSystem:
    """نظام لمراقبة مواقع الويب وإنشاء تقارير دورية"""
    
    def __init__(self):
        """تهيئة نظام المراقبة"""
        self.logger = get_logger(__name__)
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_all()
        
        # إعداد مجلدات المراقبة والتقارير
        self.monitoring_dir = os.path.join('data', 'monitoring')
        self.reports_dir = os.path.join('data', 'reports')
        create_directory(self.monitoring_dir)
        create_directory(self.reports_dir)
        
        # تهيئة جدولة المهام
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # تحميل المهام المجدولة
        self.scheduled_tasks = self._load_tasks()
        
        # إعادة جدولة المهام المحفوظة سابقاً
        for task in self.scheduled_tasks:
            self._schedule_task(task)
            
        # تهيئة محرر القوالب
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'reports')
        create_directory(templates_dir)
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        
        self.logger.info("تم تهيئة نظام المراقبة")
        
    def _load_tasks(self):
        """تحميل المهام المجدولة من الملف"""
        tasks_file = os.path.join(self.monitoring_dir, 'scheduled_tasks.json')
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"خطأ في تحميل المهام المجدولة: {str(e)}")
        return []
    
    def _save_tasks(self):
        """حفظ المهام المجدولة إلى ملف"""
        tasks_file = os.path.join(self.monitoring_dir, 'scheduled_tasks.json')
        try:
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"خطأ في حفظ المهام المجدولة: {str(e)}")
            
    def _schedule_task(self, task):
        """جدولة مهمة محددة في المجدول"""
        task_id = task.get('id')
        url = task.get('url')
        frequency = task.get('frequency', 'weekly')
        options = task.get('options', {})
        
        if not url:
            self.logger.error(f"لا يمكن جدولة المهمة {task_id}: عنوان URL غير محدد")
            return False
        
        # تحديد توقيت الجدولة بناءً على التردد
        if frequency == 'daily':
            trigger = CronTrigger(hour=options.get('hour', 3), minute=options.get('minute', 0))
        elif frequency == 'weekly':
            trigger = CronTrigger(day_of_week=options.get('day_of_week', 'mon'), 
                                  hour=options.get('hour', 3), 
                                  minute=options.get('minute', 0))
        elif frequency == 'monthly':
            trigger = CronTrigger(day=options.get('day', 1), 
                                 hour=options.get('hour', 3), 
                                 minute=options.get('minute', 0))
        else:
            self.logger.error(f"تردد غير صالح: {frequency}")
            return False
        
        # إضافة المهمة إلى المجدول
        job = self.scheduler.add_job(
            func=self._run_analysis_task,
            trigger=trigger,
            args=[task_id, url, options],
            id=task_id,
            replace_existing=True
        )
        
        self.logger.info(f"تمت جدولة المهمة {task_id} للموقع {url} بتردد {frequency}")
        return True
    
    def add_scheduled_task(self, url, frequency='weekly', options=None, notify=False):
        """إضافة مهمة مجدولة جديدة"""
        if options is None:
            options = {}
            
        # تحديد ما إذا كان يجب إرسال إشعار بعد الانتهاء
        options['notify'] = notify
        
        # إنشاء معرف فريد للمهمة
        task_id = f"task_{int(time.time())}_{url.replace('://', '_').replace('/', '_').replace('.', '_')}"
        
        # إنشاء كائن المهمة
        task = {
            'id': task_id,
            'url': url,
            'frequency': frequency,
            'options': options,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # إضافة المهمة إلى القائمة وحفظها
        self.scheduled_tasks.append(task)
        self._save_tasks()
        
        # جدولة المهمة
        success = self._schedule_task(task)
        return task_id if success else None
    
    def remove_scheduled_task(self, task_id):
        """إزالة مهمة مجدولة"""
        # إزالة المهمة من المجدول
        try:
            self.scheduler.remove_job(task_id)
        except Exception as e:
            self.logger.warning(f"خطأ في إزالة المهمة من المجدول: {str(e)}")
        
        # إزالة المهمة من القائمة
        self.scheduled_tasks = [task for task in self.scheduled_tasks if task.get('id') != task_id]
        self._save_tasks()
        
        self.logger.info(f"تمت إزالة المهمة {task_id}")
        return True
    
    def get_scheduled_tasks(self):
        """الحصول على قائمة المهام المجدولة"""
        return self.scheduled_tasks
    
    def get_task_history(self, task_id):
        """الحصول على سجل تنفيذ المهمة"""
        history_file = os.path.join(self.monitoring_dir, f"{task_id}_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"خطأ في تحميل سجل المهمة: {str(e)}")
        return []
    
    def get_monitoring_data(self):
        """الحصول على بيانات المراقبة الشاملة للعرض في واجهة المستخدم"""
        monitoring_data = {
            'scheduled_tasks': self.get_scheduled_tasks(),
            'task_statistics': self._get_task_statistics(),
            'recent_reports': self._get_recent_reports(limit=5),
            'system_status': self._get_system_status()
        }
        
        return monitoring_data
    
    def _get_task_statistics(self):
        """الحصول على إحصائيات المهام المجدولة"""
        stats = {
            'total_tasks': len(self.scheduled_tasks),
            'tasks_by_frequency': {},
            'tasks_by_status': {
                'active': 0,
                'completed': 0,
                'failed': 0
            }
        }
        
        # حساب عدد المهام حسب التردد
        for task in self.scheduled_tasks:
            frequency = task.get('frequency', 'weekly')
            if frequency not in stats['tasks_by_frequency']:
                stats['tasks_by_frequency'][frequency] = 0
            stats['tasks_by_frequency'][frequency] += 1
            
            # تحديد حالة المهمة بناءً على آخر تنفيذ
            history = self.get_task_history(task.get('id'))
            if history:
                last_result = history[-1].get('result', {})
                status = last_result.get('status', 'active')
                stats['tasks_by_status'][status] += 1
            else:
                stats['tasks_by_status']['active'] += 1
        
        return stats
    
    def _get_recent_reports(self, limit=5):
        """الحصول على أحدث التقارير المنشأة"""
        reports = []
        
        try:
            # قراءة مجلد التقارير وترتيب الملفات حسب تاريخ التعديل
            if os.path.exists(self.reports_dir):
                files = os.listdir(self.reports_dir)
                report_files = [f for f in files if f.endswith('.json')]
                report_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.reports_dir, f)), reverse=True)
                
                # اقتصار العدد حسب الحد المطلوب
                report_files = report_files[:limit]
                
                for file_name in report_files:
                    file_path = os.path.join(self.reports_dir, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            reports.append({
                                'id': file_name.replace('.json', ''),
                                'url': report_data.get('url', 'غير معروف'),
                                'created_at': report_data.get('created_at', 'غير معروف'),
                                'score': report_data.get('score', 0),
                                'issues': len(report_data.get('issues', []))
                            })
                    except Exception as e:
                        self.logger.error(f"خطأ في قراءة ملف التقرير {file_name}: {str(e)}")
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على التقارير الأخيرة: {str(e)}")
        
        return reports
    
    def _get_system_status(self):
        """الحصول على حالة نظام المراقبة"""
        return {
            'status': 'active',
            'last_check': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scheduler_running': self.scheduler.running,
            'next_scheduled_tasks': self._get_next_scheduled_tasks(limit=3)
        }
    
    def _get_next_scheduled_tasks(self, limit=3):
        """الحصول على المهام المجدولة القادمة"""
        next_tasks = []
        
        try:
            jobs = self.scheduler.get_jobs()
            # ترتيب المهام حسب وقت التنفيذ القادم
            jobs.sort(key=lambda job: job.next_run_time)
            
            for i, job in enumerate(jobs):
                if i >= limit:
                    break
                    
                # البحث عن معلومات المهمة
                task_info = None
                for task in self.scheduled_tasks:
                    if task.get('id') == job.id:
                        task_info = task
                        break
                
                if task_info:
                    next_tasks.append({
                        'id': job.id,
                        'url': task_info.get('url', 'غير معروف'),
                        'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'غير محدد',
                        'frequency': task_info.get('frequency', 'weekly')
                    })
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المهام المجدولة القادمة: {str(e)}")
        
        return next_tasks
    
    def update_task_history(self, task_id, result):
        """تحديث سجل تنفيذ المهمة"""
        history = self.get_task_history(task_id)
        
        # إضافة النتيجة الجديدة إلى السجل
        history.append({
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'result': result
        })
        
        # حفظ السجل المحدث
        history_file = os.path.join(self.monitoring_dir, f"{task_id}_history.json")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"خطأ في حفظ سجل المهمة: {str(e)}")
    
    def _run_analysis_task(self, task_id, url, options):
        """تشغيل مهمة تحليل (تنفذ في الوقت المجدول)"""
        self.logger.info(f"بدء تنفيذ المهمة المجدولة {task_id} للموقع {url}")
        
        # إنشاء مجلد للنتائج
        results_dir = os.path.join(self.monitoring_dir, task_id, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        create_directory(results_dir)
        
        try:
            # تهيئة الزاحف
            single_page = options.get('single_page', False)
            max_pages = 1 if single_page else self.config.get('crawling', {}).get('max_pages', 100)
            depth = options.get('depth', 3)
            delay = self.config.get('crawling', {}).get('delay_seconds', 1)
            respect_robots = self.config.get('crawling', {}).get('respect_robots_txt', True)
            
            crawler = WebCrawler(
                start_url=url,
                max_pages=max_pages,
                max_depth=depth,
                delay=delay,
                respect_robots_txt=respect_robots,
                verbose=True
            )
            
            # بدء الزحف
            pages = crawler.crawl()
            
            if not pages:
                self.logger.error(f"لم يتم العثور على أي صفحات للتحليل من {url}")
                return None
            
            # تهيئة المحلل
            seo_analyzer = SEOAnalyzer(config=self.config)
            
            # تحليل كل صفحة
            results = {}
            page_count = len(pages)
            
            for i, (page_url, page_data) in enumerate(pages.items()):
                self.logger.info(f"تحليل صفحة {i+1} من {page_count}: {page_url}")
                
                page_result = {}
                
                try:
                    # تحليل السيو الأساسي
                    page_result['basic_seo'] = seo_analyzer.analyze_page(page_data)
                    
                    # يمكن إضافة المزيد من التحليلات حسب الحاجة
                    
                    # حفظ نتائج الصفحة
                    results[page_url] = page_result
                    
                except Exception as e:
                    self.logger.error(f"خطأ في تحليل الصفحة {page_url}: {str(e)}")
            
            # حساب الإحصائيات
            total_issues = 0
            scores = []
            
            for page_url, page_result in results.items():
                basic_seo = page_result.get('basic_seo', {})
                page_issues = basic_seo.get('issues_count', 0)
                total_issues += page_issues
                scores.append(basic_seo.get('score', 0))
            
            average_score = sum(scores) / len(scores) if scores else 0
            
            # إعداد النتائج النهائية
            final_result = {
                'task_id': task_id,
                'site_url': url,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pages_count': len(pages),
                'total_issues': total_issues,
                'average_score': average_score,
                'pages': results
            }
            
            # حفظ النتائج إلى ملف
            result_file = os.path.join(results_dir, 'result.json')
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, ensure_ascii=False, indent=4)
            
            # تحديث سجل التنفيذ
            self.update_task_history(task_id, {
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pages_count': len(pages),
                'total_issues': total_issues,
                'average_score': average_score,
                'result_file': result_file
            })
            
            # إنشاء تقرير PDF
            report_file = self._generate_report(task_id, final_result, results_dir)
            
            # إرسال إشعار إذا كان مطلوباً
            if options.get('notify', False):
                self._send_notification(task_id, final_result, report_file)
            
            self.logger.info(f"تم الانتهاء من تنفيذ المهمة المجدولة {task_id}")
            return {
                'status': 'success',
                'result_file': result_file,
                'report_file': report_file
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ المهمة {task_id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def run_task_now(self, task_id):
        """تشغيل مهمة محددة الآن"""
        # البحث عن المهمة في القائمة
        task = next((t for t in self.scheduled_tasks if t.get('id') == task_id), None)
        
        if not task:
            self.logger.error(f"المهمة {task_id} غير موجودة")
            return None
        
        # تشغيل المهمة في خيط منفصل
        thread = threading.Thread(
            target=self._run_analysis_task,
            args=[task_id, task.get('url'), task.get('options', {})]
        )
        thread.start()
        
        self.logger.info(f"تم بدء تنفيذ المهمة {task_id} يدوياً")
        return True
    
    def delete_scheduled_task(self, task_id):
        """حذف مهمة مجدولة"""
        # البحث عن المهمة في القائمة
        task_index = None
        for i, task in enumerate(self.scheduled_tasks):
            if task.get('id') == task_id:
                task_index = i
                break
        
        if task_index is None:
            self.logger.error(f"المهمة {task_id} غير موجودة")
            return False
        
        # حذف المهمة من المجدول
        try:
            self.scheduler.remove_job(task_id)
        except Exception as e:
            self.logger.error(f"خطأ في حذف المهمة من المجدول: {str(e)}")
        
        # حذف المهمة من القائمة
        del self.scheduled_tasks[task_index]
        
        # حفظ التغييرات
        self._save_tasks()
        
        self.logger.info(f"تم حذف المهمة {task_id} بنجاح")
        return True
    
    def _generate_report(self, task_id, result_data, results_dir):
        """إنشاء تقرير PDF للتحليل"""
        self.logger.info(f"بدء إنشاء تقرير للمهمة {task_id}")
        
        # استخدام مولد التقارير لإنشاء تقرير PDF
        report_generator = ReportGenerator()
        
        # تحديد اسم ملف التقرير
        report_filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report_file = os.path.join(results_dir, report_filename)
        
        # إنشاء التقرير
        try:
            # إعداد بيانات التقرير
            report_data = {
                'title': f"تقرير تحليل السيو لـ {result_data.get('site_url')}",
                'generation_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'site_url': result_data.get('site_url'),
                'pages_count': result_data.get('pages_count', 0),
                'total_issues': result_data.get('total_issues', 0),
                'average_score': result_data.get('average_score', 0),
                'task_id': task_id
            }
            
            # إنشاء التقرير
            report_generator.generate_pdf_report(report_data, report_file)
            
            self.logger.info(f"تم إنشاء التقرير بنجاح: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء التقرير: {str(e)}")
            return None
    
    def _send_notification(self, task_id, result_data, report_file=None):
        """إرسال إشعار بنتائج التحليل"""
        # التحقق من إعدادات الإشعارات
        notification_config = self.config.get('notifications', {})
        if not notification_config.get('enabled', False):
            self.logger.info("الإشعارات غير مفعلة في الإعدادات")
            return False
        
        email_config = notification_config.get('email', {})
        
        # التحقق من إعدادات البريد الإلكتروني
        if not email_config.get('enabled', False):
            self.logger.info("إشعارات البريد الإلكتروني غير مفعلة")
            return False
        
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port', 587)
        smtp_username = email_config.get('username')
        smtp_password = email_config.get('password')
        from_email = email_config.get('from_email')
        to_emails = email_config.get('to_emails', [])
        
        if not all([smtp_server, smtp_username, smtp_password, from_email, to_emails]):
            self.logger.error("إعدادات البريد الإلكتروني غير مكتملة")
            return False
        
        try:
            # إنشاء رسالة البريد
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"تقرير تحليل السيو لـ {result_data.get('site_url')}"
            
            # محتوى الرسالة
            body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; direction: rtl; text-align: right; }}
                    h1 {{ color: #333366; }}
                    .stats {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; }}
                    .score {{ font-size: 24px; font-weight: bold; color: {'green' if result_data.get('average_score', 0) >= 80 else 'orange' if result_data.get('average_score', 0) >= 60 else 'red'}; }}
                </style>
            </head>
            <body>
                <h1>تقرير تحليل السيو</h1>
                <p>تم إكمال تحليل السيو للموقع <a href="{result_data.get('site_url')}">{result_data.get('site_url')}</a>.</p>
                
                <div class="stats">
                    <p><strong>عدد الصفحات المحللة:</strong> {result_data.get('pages_count', 0)}</p>
                    <p><strong>عدد المشاكل:</strong> {result_data.get('total_issues', 0)}</p>
                    <p><strong>متوسط النتيجة:</strong> <span class="score">{result_data.get('average_score', 0):.1f}/100</span></p>
                </div>
                
                <p>يمكنك الاطلاع على التقرير المفصل في المرفقات أو من خلال لوحة التحكم.</p>
                
                <p>تم إنشاء هذا التقرير بواسطة نظام RSEO للمراقبة الدورية.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # إرفاق التقرير إذا كان متاحاً
            if report_file and os.path.exists(report_file):
                with open(report_file, 'rb') as f:
                    attachment = MIMEApplication(f.read(), _subtype='pdf')
                    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(report_file))
                    msg.attach(attachment)
            
            # إرسال البريد
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"تم إرسال الإشعار بنجاح إلى {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في إرسال الإشعار: {str(e)}")
            return False
    
    def compare_results(self, task_id, limit=5):
        """مقارنة نتائج التحليلات السابقة"""
        history = self.get_task_history(task_id)
        
        if not history:
            return None
        
        # ترتيب السجل حسب الوقت (الأحدث أولاً)
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # تحديد عدد النتائج للمقارنة
        limit = min(limit, len(history))
        results_to_compare = history[:limit]
        
        # إعداد بيانات المقارنة
        comparison = {
            'task_id': task_id,
            'dates': [],
            'scores': [],
            'issues': []
        }
        
        for result in reversed(results_to_compare):  # عكس الترتيب ليكون من الأقدم للأحدث
            comparison['dates'].append(result.get('timestamp', '').split(' ')[0])  # أخذ التاريخ فقط
            comparison['scores'].append(result.get('average_score', 0))
            comparison['issues'].append(result.get('total_issues', 0))
        
        return comparison
    
    def get_all_performance_data(self):
        """الحصول على بيانات الأداء لجميع المهام"""
        performance_data = []
        
        for task in self.scheduled_tasks:
            task_id = task.get('id')
            history = self.get_task_history(task_id)
            
            if not history:
                continue
                
            # ترتيب السجل حسب الوقت (الأحدث أولاً)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # الحصول على آخر نتيجة
            latest_result = history[0] if history else None
            
            if latest_result:
                performance_data.append({
                    'task_id': task_id,
                    'url': task.get('url'),
                    'latest_analysis': latest_result.get('timestamp'),
                    'score': latest_result.get('average_score', 0),
                    'issues': latest_result.get('total_issues', 0),
                    'pages': latest_result.get('pages_count', 0),
                    'frequency': task.get('frequency', 'weekly')
                })
        
        return performance_data
