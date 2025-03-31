#!/usr/bin/env python
# -*- coding: utf-8 -*-

# استيراد الوحدات المطلوبة من مكتبات بايثون
import os
import sys
import time
import json
import yaml
import logging
import requests
import datetime
import hashlib
import threading
from threading import Thread
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_mail import Mail

from modules.analyzer import SEOAnalyzer
from modules.crawler import WebCrawler
from modules.report_generator import ReportGenerator
from modules.content_analyzer import ContentAnalyzer
from modules.youtube_seo import YouTubeSEO
from modules.ai_content_generator import AIContentGenerator
from modules.monitoring import MonitoringSystem
from modules.rank_tracker import RankTracker
from modules.backlink_analyzer import BacklinkAnalyzer

from utils.helpers import validate_url, format_time, create_directory
from utils.config_loader import get_config

# تهيئة السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# تهيئة تطبيق Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rseo-dev-secret-key')

# تهيئة خدمة البريد الإلكتروني
mail = Mail(app)

# تحميل الإعدادات من ملف التكوين
config = get_config().get_all()

# إضافة متغير now لجميع القوالب
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# مجلد لتخزين نتائج التحليل
results_directory = os.path.join('data', 'results')

# تحقق من توفر وحدات الذكاء الاصطناعي المتقدمة
try:
    # محاولة استيراد الوحدات المتقدمة
    from modules.semantic_seo_analyzer import SemanticSEOAnalyzer
    from modules.search_intent_detector import SearchIntentDetector
    from modules.smart_cta_generator import SmartCTAGenerator
    from modules.content_evaluator import ContentEvaluator
    
    # تهيئة الوحدات
    semantic_seo_analyzer = SemanticSEOAnalyzer()
    search_intent_detector = SearchIntentDetector()
    smart_cta_generator = SmartCTAGenerator()
    content_evaluator = ContentEvaluator()
    
    ADVANCED_AI_MODULES_AVAILABLE = True
    logger.info("تم تحميل وحدات الذكاء الاصطناعي المتقدمة بنجاح")
except ImportError:
    ADVANCED_AI_MODULES_AVAILABLE = False
    logger.warning("وحدات الذكاء الاصطناعي المتقدمة غير متوفرة")

# تهيئة نظام المراقبة
monitoring_system = MonitoringSystem()

# قاموس لتخزين حالة المهام الجارية
running_jobs = {}

# ==========================================
# الوظائف المساعدة
# ==========================================

def get_recent_results(limit=5):
    """الحصول على أحدث نتائج التحليل"""
    if not os.path.exists(results_directory):
        return []
    
    results = []
    try:
        # قراءة المجلدات وترتيبها حسب تاريخ التعديل
        dirs = os.listdir(results_directory)
        dirs = [d for d in dirs if os.path.isdir(os.path.join(results_directory, d))]
        dirs.sort(key=lambda d: os.path.getmtime(os.path.join(results_directory, d)), reverse=True)
        
        # اقتصار العدد حسب الحد المطلوب
        dirs = dirs[:limit]
        
        for dir_name in dirs:
            dir_path = os.path.join(results_directory, dir_name)
            summary_file = os.path.join(dir_path, 'summary.json')
            
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append({
                        'dir_name': dir_name,
                        'url': data.get('url', 'غير معروف'),
                        'datetime': data.get('datetime', 'غير معروف'),
                        'issue_count': data.get('issue_count', 0),
                        'score': data.get('score', 0)
                    })
            else:
                # إذا لم يوجد ملف ملخص، نستخدم معلومات أساسية
                results.append({
                    'dir_name': dir_name,
                    'url': 'غير معروف',
                    'datetime': datetime.datetime.fromtimestamp(os.path.getmtime(dir_path)).strftime('%Y-%m-%d %H:%M'),
                    'issue_count': 0,
                    'score': 0
                })
    except Exception as e:
        logger.error(f"خطأ في الحصول على النتائج الأخيرة: {str(e)}")
    
    return results

def get_result_details(result_id):
    """الحصول على تفاصيل نتيجة تحليل محددة"""
    dir_path = os.path.join(results_directory, result_id)
    
    if not os.path.exists(dir_path):
        return None
    
    try:
        # قراءة ملف التقرير الرئيسي
        report_file = os.path.join(dir_path, 'report.json')
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # إذا لم يوجد ملف تقرير رئيسي، نبحث عن أي ملف JSON
            json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
            if json_files:
                with open(os.path.join(dir_path, json_files[0]), 'r', encoding='utf-8') as f:
                    return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في الحصول على تفاصيل النتيجة: {str(e)}")
    
    return None

# ============================
# المسارات
# ============================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    try:
        # الحصول على آخر النتائج
        recent_results = get_recent_results()
        
        return render_template('index.html', recent_results=recent_results)
    except Exception as e:
        app.logger.error(f"خطأ في عرض الصفحة الرئيسية: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """صفحة لوحة المعلومات"""
    try:
        # الحصول على آخر النتائج
        recent_results = get_recent_results()
        
        return render_template('dashboard.html', recent_results=recent_results)
    except Exception as e:
        app.logger.error(f"خطأ في عرض لوحة المعلومات: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """صفحة تحليل موقع جديد"""
    if request.method == 'POST':
        url = request.form.get('url', '')
        
        if not validate_url(url):
            flash('الرجاء إدخال رابط صالح', 'error')
            return redirect(url_for('analyze'))
        
        # إنشاء معرف فريد للمهمة
        job_id = str(uuid.uuid4())
        
        # تحضير بيانات الخيارات
        options = {
            'single_page': request.form.get('single_page') == 'on',
            'depth': int(request.form.get('depth', 3)),
            'max_pages': int(request.form.get('max_pages', 100)),
            'check_schema': request.form.get('check_schema') == 'on',
            'check_speed': request.form.get('check_speed') == 'on',
            'check_core_web_vitals': request.form.get('check_core_web_vitals') == 'on',
            'check_mobile': request.form.get('check_mobile') == 'on',
            'export_format': request.form.get('export_format', 'html')
        }
        
        # إضافة المهمة إلى قائمة المهام الجارية
        running_jobs[job_id] = {
            'status': 'pending',
            'url': url,
            'options': options,
            'start_time': time.time(),
            'progress': 0,
            'message': 'جاري التحضير للتحليل...'
        }
        
        # بدء المهمة في خلفية
        thread = Thread(target=analyze_website_job, args=(job_id, url, options))
        thread.daemon = True
        thread.start()
        
        # إعادة توجيه إلى صفحة حالة المهمة
        return redirect(url_for('job_status', job_id=job_id))
    
    return render_template('analyze.html')

@app.route('/sitemap', methods=['GET', 'POST'])
def sitemap():
    """صفحة إنشاء خريطة الموقع"""
    if request.method == 'POST':
        url = request.form.get('url', '')
        
        if not validate_url(url):
            flash('الرجاء إدخال رابط صالح', 'error')
            return redirect(url_for('sitemap'))
        
        # إنشاء معرف فريد للمهمة
        job_id = str(uuid.uuid4())
        
        # تحضير بيانات الخيارات
        options = {
            'changefreq': request.form.get('changefreq', 'weekly'),
            'priority': float(request.form.get('priority', 0.5)),
            'save_to_server': request.form.get('save_to_server') == 'on',
            'ping_search_engines': request.form.get('ping_search_engines') == 'on'
        }
        
        # إضافة المهمة إلى قائمة المهام الجارية
        running_jobs[job_id] = {
            'status': 'pending',
            'url': url,
            'options': options,
            'start_time': time.time(),
            'progress': 0,
            'message': 'جاري التحضير لإنشاء خريطة الموقع...'
        }
        
        # إعادة توجيه إلى صفحة الحالة
        return redirect(url_for('job_status', job_id=job_id))
    
    return render_template('sitemap.html')

@app.route('/fix', methods=['GET', 'POST'])
def fix():
    """صفحة إصلاح مشاكل السيو"""
    recent_results = get_recent_results()
    
    if request.method == 'POST':
        url = request.form.get('url', '')
        report_id = request.form.get('report_id', '')
        
        if not validate_url(url):
            flash('الرجاء إدخال رابط صالح', 'error')
            return redirect(url_for('fix'))
        
        if not report_id:
            flash('الرجاء اختيار تقرير لإصلاح مشاكله', 'error')
            return redirect(url_for('fix'))
        
        # بداية الإصلاح
        # هنا يمكن إضافة الكود الخاص بإصلاح المشاكل
        
        flash('تم بدء عملية الإصلاح بنجاح', 'success')
        return redirect(url_for('index'))
    
    return render_template('fix.html', recent_results=recent_results)

@app.route('/job/<job_id>')
def job_status(job_id):
    """صفحة حالة المهمة"""
    if job_id not in running_jobs:
        flash('المهمة غير موجودة', 'error')
        return redirect(url_for('index'))
    
    job = running_jobs[job_id]
    
    return render_template('job_status.html', job_id=job_id, job=job)

@app.route('/api/job/<job_id>')
def job_status_api(job_id):
    """واجهة برمجة التطبيقات لحالة المهمة"""
    if job_id not in running_jobs:
        return jsonify({'error': 'المهمة غير موجودة'}), 404
    
    job = running_jobs[job_id]
    
    return jsonify({
        'status': job.get('status'),
        'progress': job.get('progress', 0),
        'message': job.get('message', ''),
        'result': job.get('result'),
        'elapsed_time': format_time(time.time() - job.get('start_time', time.time()))
    })

@app.route('/results/<result_id>')
def view_result(result_id):
    """عرض نتيجة تحليل محددة"""
    result_data = get_result_details(result_id)
    
    if not result_data:
        flash('النتيجة غير موجودة', 'error')
        return redirect(url_for('index'))
    
    return render_template('result_details.html', result_id=result_id, result=result_data)

@app.route('/download/<result_id>/<filename>')
def download_file(result_id, filename):
    """تنزيل ملف من مجلد النتائج"""
    dir_path = os.path.join(results_directory, result_id)
    
    if not os.path.exists(dir_path):
        flash('المجلد غير موجود', 'error')
        return redirect(url_for('index'))
    
    return send_from_directory(directory=dir_path, filename=filename)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """صفحة الإعدادات"""
    if request.method == 'POST':
        # تحديث الإعدادات
        updated_config = {
            'crawling': {
                'max_pages': int(request.form.get('max_pages', 100)),
                'delay_seconds': float(request.form.get('delay_seconds', 1)),
                'respect_robots_txt': request.form.get('respect_robots_txt') == 'on',
                'timeout_seconds': int(request.form.get('timeout_seconds', 30))
            },
            'seo_analysis': {
                'title': {
                    'min_length': int(request.form.get('title_min_length', 30)),
                    'max_length': int(request.form.get('title_max_length', 60))
                },
                'meta_description': {
                    'min_length': int(request.form.get('description_min_length', 70)),
                    'max_length': int(request.form.get('description_max_length', 160))
                }
            },
            'api_keys': {
                'pagespeed': request.form.get('pagespeed_api_key', ''),
                'openai': request.form.get('openai_api_key', '')
            }
        }
        
        # حفظ الإعدادات في ملف
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f, default_flow_style=False, allow_unicode=True)
        
        # إعادة تحميل الإعدادات
        config.update(updated_config)
        
        flash('تم حفظ الإعدادات بنجاح', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', config=config)

@app.route('/youtube_seo')
def youtube_seo():
    """صفحة تحسين السيو لليوتيوب"""
    try:
        return render_template('youtube_seo.html')
    except Exception as e:
        app.logger.error(f"خطأ في عرض صفحة يوتيوب سيو: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/youtube_keywords', methods=['GET', 'POST'])
def youtube_keywords():
    """تحليل الكلمات المفتاحية للفيديوهات"""
    if request.method == 'POST':
        topic = request.form.get('topic', '')
        language = request.form.get('language', 'ar')
        use_api = request.form.get('use_api') == 'on'
        
        if not topic:
            flash('الرجاء إدخال موضوع الفيديو', 'danger')
            return render_template('youtube_keywords.html', error="الرجاء إدخال موضوع الفيديو")
        
        youtube_seo = YouTubeSEO()
        results = youtube_seo.analyze_keywords(topic, language, use_api)
        
        return render_template('youtube_keywords_results.html', results=results, topic=topic, language=language)
    
    return render_template('youtube_keywords.html', error=None)

@app.route('/video_ranking', methods=['GET', 'POST'])
def video_ranking():
    """تحليل تصنيف الفيديو في نتائج البحث"""
    if request.method == 'POST':
        video_url = request.form.get('video_url', '')
        keywords = request.form.get('keywords', '')
        use_api = request.form.get('use_api') == 'on'
        
        if not video_url or not keywords:
            flash('الرجاء إدخال رابط الفيديو والكلمات المفتاحية', 'danger')
            return render_template('youtube_ranking.html', error='الرجاء إدخال رابط الفيديو والكلمات المفتاحية')
        
        api_key = os.getenv('YOUTUBE_API_KEY', None) if use_api else None
        youtube_seo = YouTubeSEO(api_key=api_key)
        results = youtube_seo.analyze_video_ranking(video_url, keywords, use_api)
        
        if 'error' in results:
            flash(results['error'], 'danger')
            return render_template('youtube_ranking.html', error=results['error'])
        
        # التأكد من وجود كافة البيانات المطلوبة في النتائج
        if 'keywords' not in results:
            results['keywords'] = []
            
        if 'improvement_tips' not in results:
            results['improvement_tips'] = []
        
        return render_template('youtube_ranking_results.html', 
                              results=results, 
                              video_url=video_url, 
                              keywords=keywords)
    
    return render_template('youtube_ranking.html', error=None)

@app.route('/youtube_competitor', methods=['GET', 'POST'])
def youtube_competitor():
    """تحليل منافسي اليوتيوب"""
    if request.method == 'GET':
        return render_template('youtube_competitor.html', error=None)
    
    if request.method == 'POST':
        channel_url = request.form.get('channel_url')
        video_count = int(request.form.get('video_count', 10))
        api_key = request.form.get('api_key', '')
        use_api = True if api_key else False
        
        try:
            youtube_seo = YouTubeSEO(api_key=api_key)
            results = youtube_seo.analyze_competitor(channel_url, video_count, use_api)
            
            # إضافة معرف القناة إذا لم يكن موجوداً في النتائج
            if 'channel_id' not in results:
                results['channel_id'] = youtube_seo._extract_channel_id(channel_url)
                
            # إضافة عدد الفيديوهات المحللة إذا لم يكن موجوداً
            if 'videos_analyzed' not in results:
                results['videos_analyzed'] = video_count
                
            return render_template('youtube_competitor_results.html', 
                                  results=results, 
                                  channel_url=channel_url, 
                                  video_count=video_count)
        except Exception as e:
            return render_template('youtube_competitor.html', error=str(e))

@app.route('/channel_analysis', methods=['GET', 'POST'])
def channel_analysis():
    """تحليل أداء قناة اليوتيوب"""
    if request.method == 'POST':
        channel_url = request.form.get('channel_url', '')
        period = int(request.form.get('period', '30'))
        analysis_type = request.form.get('analysis_type', 'comprehensive')
        use_api = request.form.get('use_api') == 'on'
        
        if not channel_url:
            flash('الرجاء إدخال رابط القناة', 'danger')
            return render_template('channel_analysis.html', error='الرجاء إدخال رابط القناة')
        
        api_key = os.getenv('YOUTUBE_API_KEY', None) if use_api else None
        youtube_seo = YouTubeSEO(api_key=api_key)
        results = youtube_seo.analyze_channel_performance(channel_url, period, use_api)
        
        if 'error' in results:
            flash(results['error'], 'danger')
            return render_template('channel_analysis.html', error=results['error'])
        
        return render_template('channel_analysis_results.html', 
                              results=results, 
                              channel_url=channel_url, 
                              period=period,
                              analysis_type=analysis_type)
    
    return render_template('channel_analysis.html', error=None)

@app.route('/video_content', methods=['GET', 'POST'])
def video_content():
    """تحسين محتوى الفيديو"""
    if request.method == 'POST':
        topic = request.form.get('topic', '')
        current_title = request.form.get('current_title', '')
        current_description = request.form.get('current_description', '')
        target_keywords = request.form.get('target_keywords', '')
        
        if not topic:
            flash('الرجاء إدخال موضوع الفيديو', 'danger')
            return render_template('video_content.html', error='الرجاء إدخال موضوع الفيديو')
        
        youtube_seo = YouTubeSEO()
        results = youtube_seo.optimize_video_content(
            topic=topic,
            current_title=current_title,
            current_description=current_description,
            target_keywords=target_keywords
        )
        
        # التأكد من وجود جميع المفاتيح المطلوبة في النتائج
        expected_keys = ['improved_titles', 'improved_description', 'title_analysis', 'description_analysis']
        for key in expected_keys:
            if key not in results:
                results[key] = None
        
        return render_template(
            'video_content_results.html',
            results=results,
            topic=topic,
            current_title=current_title,
            current_description=current_description,
            target_keywords=target_keywords
        )
    
    return render_template('video_content.html', error=None)

@app.route('/monitoring')
def monitoring():
    """صفحة المراقبة والتقارير"""
    try:
        app.logger.info("بدء تحميل صفحة المراقبة")
        
        # الحصول على بيانات المراقبة
        app.logger.info("جاري استدعاء get_monitoring_data")
        monitoring_data = monitoring_system.get_monitoring_data()
        app.logger.info(f"تم الحصول على بيانات المراقبة: {monitoring_data}")
        
        return render_template('monitoring.html', monitoring_data=monitoring_data)
    except Exception as e:
        app.logger.error(f"خطأ في عرض صفحة المراقبة: {str(e)}")
        app.logger.exception("تفاصيل الخطأ:")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/monitoring/task/<task_id>')
def monitoring_task_details(task_id):
    """عرض تفاصيل مهمة مراقبة محددة"""
    try:
        # البحث عن المهمة
        task = None
        for t in monitoring_system.get_scheduled_tasks():
            if t.get('id') == task_id:
                task = t
                break
        
        if not task:
            flash('المهمة غير موجودة', 'danger')
            return redirect(url_for('monitoring'))
        
        # الحصول على سجل المهمة
        task_history = monitoring_system.get_task_history(task_id)
        
        # تحضير بيانات الرسم البياني
        chart_data = {
            'labels': [],
            'scores': [],
            'issues': []
        }
        
        for entry in task_history:
            chart_data['labels'].append(entry.get('timestamp', ''))
            result = entry.get('result', {})
            chart_data['scores'].append(result.get('score', 0))
            chart_data['issues'].append(len(result.get('issues', [])))
        
        return render_template('monitoring_task_details.html', task=task, history=task_history, chart_data=chart_data)
    except Exception as e:
        app.logger.error(f"خطأ في عرض تفاصيل المهمة: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('monitoring'))

@app.route('/monitoring/run/<task_id>')
def monitoring_run_task(task_id):
    """تشغيل مهمة مراقبة يدوياً"""
    try:
        # البحث عن المهمة
        task = None
        for t in monitoring_system.get_scheduled_tasks():
            if t.get('id') == task_id:
                task = t
                break
        
        if not task:
            flash('المهمة غير موجودة', 'danger')
            return redirect(url_for('monitoring'))
        
        # تشغيل المهمة
        monitoring_system.run_task_now(task_id)
        
        flash(f'تم بدء تنفيذ المهمة لموقع {task.get("url")}', 'success')
        return redirect(url_for('monitoring_task_details', task_id=task_id))
    except Exception as e:
        app.logger.error(f"خطأ في تشغيل المهمة: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('monitoring'))

@app.route('/monitoring/add', methods=['POST'])
def monitoring_add_task():
    """إضافة مهمة مراقبة جديدة"""
    try:
        url = request.form.get('url')
        frequency = request.form.get('frequency', 'weekly')
        
        if not url:
            flash('يرجى إدخال رابط الموقع', 'warning')
            return redirect(url_for('monitoring'))
        
        # إضافة المهمة
        task_id = monitoring_system.add_scheduled_task(url, frequency=frequency)
        
        flash(f'تمت إضافة مهمة مراقبة جديدة للموقع {url}', 'success')
        return redirect(url_for('monitoring'))
    except Exception as e:
        app.logger.error(f"خطأ في إضافة مهمة مراقبة: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('monitoring'))

@app.route('/monitoring/delete/<task_id>', methods=['POST'])
def monitoring_delete_task(task_id):
    """حذف مهمة مراقبة"""
    try:
        # حذف المهمة
        result = monitoring_system.delete_scheduled_task(task_id)
        
        if result:
            flash('تم حذف المهمة بنجاح', 'success')
        else:
            flash('فشل في حذف المهمة', 'danger')
            
        return redirect(url_for('monitoring'))
    except Exception as e:
        app.logger.error(f"خطأ في حذف المهمة: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('monitoring'))

@app.route('/content_generator', methods=['GET', 'POST'])
def content_generator():
    """مولد المحتوى بالذكاء الاصطناعي"""
    try:
        if request.method == 'POST':
            topic = request.form.get('topic', '')
            content_type = request.form.get('content_type', 'article')
            keywords = request.form.get('keywords', '')
            tone = request.form.get('tone', 'informative')
            language = request.form.get('language', 'ar')
            
            if not topic:
                flash('الرجاء إدخال موضوع المحتوى', 'danger')
                return render_template('content_generator.html', error='الرجاء إدخال موضوع المحتوى')
            
            ai_generator = AIContentGenerator()
            results = ai_generator.generate_content(
                topic=topic,
                content_type=content_type,
                keywords=keywords,
                tone=tone,
                language=language
            )
            
            return render_template(
                'content_generator.html',
                results=results,
                topic=topic,
                content_type=content_type,
                keywords=keywords,
                tone=tone,
                language=language
            )
        
        return render_template('content_generator.html')
    except Exception as e:
        app.logger.error(f"خطأ في صفحة مولد المحتوى: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/generate_content', methods=['POST'])
def generate_content():
    """توليد محتوى جديد"""
    try:
        prompt = request.form.get('prompt', '')
        content_type = request.form.get('content_type', 'article')
        language = request.form.get('language', 'ar')
        tone = request.form.get('tone', 'professional')
        word_count = request.form.get('word_count', '')
        keywords = request.form.get('keywords', '')
        
        if not prompt:
            flash('الرجاء إدخال موضوع المحتوى', 'danger')
            return redirect(url_for('content_generator'))
        
        ai_generator = AIContentGenerator()
        results = ai_generator.generate_content(
            topic=prompt,
            content_type=content_type,
            keywords=keywords,
            tone=tone,
            language=language,
            word_count=word_count
        )
        
        return render_template(
            'content_generator.html',
            results=results,
            prompt=prompt,
            content_type=content_type,
            keywords=keywords,
            tone=tone,
            language=language,
            active_tab='generate'
        )
    except Exception as e:
        app.logger.error(f"خطأ في توليد المحتوى: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('content_generator'))

@app.route('/improve_content', methods=['POST'])
def improve_content():
    """تحسين محتوى موجود"""
    try:
        original_content = request.form.get('original_content', '')
        suggestions = request.form.get('suggestions', '')
        keywords = request.form.get('keywords', '')
        
        if not original_content:
            flash('الرجاء إدخال المحتوى الأصلي', 'danger')
            return redirect(url_for('content_generator'))
        
        ai_generator = AIContentGenerator()
        results = ai_generator.improve_content(
            content=original_content,
            suggestions=suggestions,
            keywords=keywords
        )
        
        return render_template(
            'content_generator.html',
            improved_results=results,
            original_content=original_content,
            suggestions=suggestions,
            keywords=keywords,
            active_tab='improve'
        )
    except Exception as e:
        app.logger.error(f"خطأ في تحسين المحتوى: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('content_generator'))

@app.route('/generate_meta_tags', methods=['POST'])
def generate_meta_tags():
    """توليد وسوم وصفية"""
    try:
        page_content = request.form.get('page_content', '')
        
        if not page_content:
            flash('الرجاء إدخال محتوى الصفحة', 'danger')
            return redirect(url_for('content_generator'))
        
        ai_generator = AIContentGenerator()
        results = ai_generator.generate_meta_tags(content=page_content)
        
        return render_template(
            'content_generator.html',
            meta_results=results,
            page_content=page_content,
            active_tab='meta'
        )
    except Exception as e:
        app.logger.error(f"خطأ في توليد الوسوم الوصفية: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('content_generator'))

@app.route('/rank_tracker', methods=['GET', 'POST'])
def rank_tracker_page():
    """صفحة متابعة الترتيب في نتائج البحث"""
    try:
        if request.method == 'POST':
            domain = request.form.get('domain', '')
            keywords = request.form.get('keywords', '')
            
            if not domain or not keywords:
                flash('الرجاء إدخال النطاق والكلمات المفتاحية', 'danger')
                return render_template('rank_tracker.html', error='الرجاء إدخال النطاق والكلمات المفتاحية')
            
            tracker = RankTracker()
            results = tracker.check_rankings(domain, keywords.split(','))
            
            return render_template(
                'rank_tracker.html',
                results=results,
                domain=domain,
                keywords=keywords
            )
        
        return render_template('rank_tracker.html')
    except Exception as e:
        app.logger.error(f"خطأ في صفحة متابعة الترتيب: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/backlinks', methods=['GET', 'POST'])
def backlinks_page():
    """صفحة تحليل الروابط الخلفية"""
    try:
        if request.method == 'POST':
            domain = request.form.get('domain', '')
            
            if not domain:
                flash('الرجاء إدخال النطاق', 'danger')
                return render_template('backlink_analyzer.html', error='الرجاء إدخال النطاق')
            
            backlink_analyzer = BacklinkAnalyzer()
            results = backlink_analyzer.analyze_backlinks(domain)
            
            return render_template(
                'backlink_results.html',
                results=results,
                domain=domain
            )
        
        return render_template('backlink_analyzer.html')
    except Exception as e:
        app.logger.error(f"خطأ في صفحة تحليل الروابط الخلفية: {str(e)}")
        return f"حدث خطأ: {str(e)}", 500

@app.route('/keyword-analysis')
def keyword_analysis():
    """صفحة تحليل الكلمات المفتاحية"""
    return render_template('keyword_analysis.html')

@app.route('/video-analysis')
def video_analysis():
    """صفحة تحليل تصنيف الفيديو"""
    return render_template('video_analysis.html')

@app.route('/competitors')
def competitors():
    """صفحة تحليل المنافسين"""
    return render_template('competitors.html')

if __name__ == '__main__':
    # التأكد من وجود المجلدات الضرورية
    create_directory(results_directory)
    create_directory(os.path.join('data', 'monitoring'))
    
    # تشغيل المهام الدورية للمراقبة في خلفية
    # monitor_thread = Thread(target=monitoring_system.run_scheduled_tasks, daemon=True)
    # monitor_thread.start()
    
    # تشغيل التطبيق
    app.run(host='0.0.0.0', port=5000, debug=True)
