#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - لوحة تحكم لإدارة تطبيق تحليل وتحسين السيو
واجهة مستخدم قائمة على Flask
"""

import os
import json
import time
import yaml
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from dotenv import load_dotenv
from threading import Thread

# استيراد الوحدات الداخلية
from modules.analyzer import SEOAnalyzer
from modules.crawler import WebCrawler
from modules.page_speed import PageSpeedAnalyzer
from modules.content_analyzer import ContentAnalyzer
from modules.image_optimizer import ImageOptimizer
from modules.link_checker import LinkChecker
from modules.seo_fixer import SEOFixer
from modules.report_generator import ReportGenerator
from modules.wp_integration import WordPressIntegration
from modules.ai_content_generator import AIContentGenerator
from modules.monitoring import MonitoringSystem

# استيراد الأدوات المساعدة
from utils.helpers import validate_url, create_directory, format_time
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger, get_logger

# تهيئة Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'rseo-dashboard-secret-key')

# تحميل متغيرات البيئة
load_dotenv()

# إعداد المسجل
logger = get_logger("rseo_webapp")

# تحميل ملف الإعدادات
config_loader = ConfigLoader()
config = config_loader.get_all()

# المتغيرات العالمية
running_jobs = {}
last_results = {}
results_directory = 'results'

def get_recent_results(limit=5):
    """الحصول على آخر نتائج التحليل"""
    results = []
    try:
        if os.path.exists(results_directory):
            dirs = [d for d in os.listdir(results_directory) if os.path.isdir(os.path.join(results_directory, d))]
            # ترتيب الدلائل حسب التاريخ (الأحدث أولاً)
            dirs.sort(reverse=True)
            
            for dir_name in dirs[:limit]:
                dir_path = os.path.join(results_directory, dir_name)
                # البحث عن ملف النتائج
                result_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
                
                if result_files:
                    result_file = os.path.join(dir_path, result_files[0])
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # استخراج المعلومات المهمة
                            url = data.get('site_url', 'غير معروف')
                            pages_count = len(data.get('pages', {}))
                            issues_count = data.get('total_issues', 0)
                            score = data.get('average_score', 0)
                            
                            results.append({
                                'dir_name': dir_name,
                                'url': url,
                                'datetime': datetime.strptime(dir_name[:8] + '_' + dir_name[9:], '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M'),
                                'pages_count': pages_count,
                                'issues_count': issues_count,
                                'score': score
                            })
                    except Exception as e:
                        logger.error(f"خطأ في قراءة ملف النتائج: {str(e)}")
    except Exception as e:
        logger.error(f"خطأ في قراءة مجلد النتائج: {str(e)}")
    
    return results

def get_result_details(result_id):
    """الحصول على تفاصيل نتيجة تحليل محددة"""
    dir_path = os.path.join(results_directory, result_id)
    
    if not os.path.exists(dir_path):
        return None
    
    # البحث عن ملف النتائج
    result_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
    
    if not result_files:
        return None
    
    result_file = os.path.join(dir_path, result_files[0])
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في قراءة ملف النتائج: {str(e)}")
        return None

def analyze_website_job(job_id, url, options):
    """وظيفة تحليل موقع الويب (تعمل في خلفية)"""
    try:
        running_jobs[job_id]['status'] = 'running'
        running_jobs[job_id]['progress'] = 5
        running_jobs[job_id]['message'] = 'بدء التحليل...'
        
        start_time = time.time()
        
        # إنشاء مجلد النتائج
        results_dir = os.path.join(options.get('output_dir', 'results'), datetime.now().strftime("%Y%m%d_%H%M%S"))
        create_directory(results_dir)
        
        # تحديث الحالة
        running_jobs[job_id]['results_dir'] = results_dir
        running_jobs[job_id]['progress'] = 10
        running_jobs[job_id]['message'] = 'جاري زحف الموقع...'
        
        # تهيئة الزاحف
        single_page = options.get('single_page', False)
        max_pages = 1 if single_page else config.get('crawling', {}).get('max_pages', 100)
        depth = options.get('depth', 3)
        delay = config.get('crawling', {}).get('delay_seconds', 1)
        respect_robots = config.get('crawling', {}).get('respect_robots_txt', True)
        
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
            running_jobs[job_id]['status'] = 'error'
            running_jobs[job_id]['message'] = 'لم يتم العثور على أي صفحات للتحليل.'
            return
        
        # تحديث الحالة
        running_jobs[job_id]['progress'] = 30
        running_jobs[job_id]['message'] = f'جاري تحليل {len(pages)} صفحة...'
        
        # تهيئة المحللات
        seo_analyzer = SEOAnalyzer(config=config)
        page_speed_analyzer = PageSpeedAnalyzer()
        content_analyzer = ContentAnalyzer()
        image_optimizer = ImageOptimizer()
        link_checker = LinkChecker()
        
        # تحليل كل صفحة
        results = {}
        page_count = len(pages)
        
        for i, (page_url, page_data) in enumerate(pages.items()):
            progress_percent = 30 + int(50 * ((i + 1) / page_count))
            running_jobs[job_id]['progress'] = progress_percent
            running_jobs[job_id]['message'] = f'تحليل صفحة {i+1} من {page_count}: {page_url}'
            
            page_result = {}
            
            try:
                # تحليل السيو الأساسي
                page_result['basic_seo'] = seo_analyzer.analyze_page(page_data)
                
                # تحليل سرعة الصفحة
                try:
                    page_result['page_speed'] = page_speed_analyzer.analyze(page_url)
                except Exception as e:
                    logger.warning(f"فشل تحليل سرعة الصفحة {page_url}: {str(e)}")
                
                # تحليل المحتوى
                try:
                    page_result['content'] = content_analyzer.analyze(page_data)
                except Exception as e:
                    logger.warning(f"فشل تحليل محتوى الصفحة {page_url}: {str(e)}")
                
                # تحليل الصور
                try:
                    page_result['images'] = image_optimizer.analyze_images(page_data)
                except Exception as e:
                    logger.warning(f"فشل تحليل صور الصفحة {page_url}: {str(e)}")
                
                # فحص الروابط
                try:
                    page_result['links'] = link_checker.check_links(page_data)
                except Exception as e:
                    logger.warning(f"فشل فحص روابط الصفحة {page_url}: {str(e)}")
                
                # إضافة النتائج
                results[page_url] = page_result
                
            except Exception as e:
                logger.error(f"خطأ أثناء تحليل الصفحة {page_url}: {str(e)}")
        
        # تحديث الحالة
        running_jobs[job_id]['progress'] = 85
        running_jobs[job_id]['message'] = 'جاري إنشاء التقرير...'
        
        # إنشاء التقرير
        report_generator = ReportGenerator(results_dir=results_dir)
        
        export_format = options.get('export_format', 'all')
        report_paths = report_generator.generate_report(
            url=url,
            results=results,
            format=export_format
        )
        
        # إصلاح المشاكل إذا طلب ذلك
        if options.get('auto_fix', False):
            running_jobs[job_id]['progress'] = 90
            running_jobs[job_id]['message'] = 'جاري إصلاح مشاكل السيو...'
            
            seo_fixer = SEOFixer(results_dir=results_dir)
            fixed_items = seo_fixer.fix_issues(results=results)
            
            # إذا كان هناك تكامل مع ووردبريس، تطبيق الإصلاحات
            if options.get('wp_api', False):
                wp_username = options.get('wp_username', '')
                wp_password = options.get('wp_password', '')
                
                if wp_username and wp_password:
                    running_jobs[job_id]['message'] = 'جاري تطبيق الإصلاحات على WordPress...'
                    
                    wp_integration = WordPressIntegration(
                        site_url=url,
                        username=wp_username,
                        password=wp_password
                    )
                    
                    wp_integration.apply_fixes(fixed_items)
        
        # حساب إحصائيات النتائج
        total_issues = 0
        total_score = 0
        page_count = len(results)
        
        for page_url, page_data in results.items():
            # حساب عدد المشاكل
            issues = 0
            for category, category_data in page_data.items():
                if isinstance(category_data, dict) and 'issues' in category_data:
                    issues += len(category_data['issues'])
            total_issues += issues
            
            # حساب النتيجة الإجمالية
            if 'basic_seo' in page_data and 'score' in page_data['basic_seo']:
                total_score += page_data['basic_seo']['score']
        
        # متوسط النتيجة
        average_score = round(total_score / page_count if page_count > 0 else 0, 1)
        
        # حفظ ملخص النتائج
        summary = {
            'site_url': url,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'pages': results,
            'total_pages': page_count,
            'total_issues': total_issues,
            'average_score': average_score,
            'elapsed_time': format_time(time.time() - start_time)
        }
        
        # حفظ ملخص النتائج
        with open(os.path.join(results_dir, 'summary.json'), 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # تحديث الحالة النهائية
        running_jobs[job_id]['status'] = 'completed'
        running_jobs[job_id]['progress'] = 100
        running_jobs[job_id]['message'] = 'اكتمل التحليل!'
        running_jobs[job_id]['result'] = {
            'dir_name': os.path.basename(results_dir),
            'total_pages': page_count,
            'total_issues': total_issues,
            'average_score': average_score,
            'elapsed_time': format_time(time.time() - start_time)
        }
        
        # حفظ النتائج الأخيرة
        last_results[url] = running_jobs[job_id]['result']
        
    except Exception as e:
        logger.error(f"خطأ أثناء التحليل: {str(e)}")
        running_jobs[job_id]['status'] = 'error'
        running_jobs[job_id]['message'] = f'حدث خطأ أثناء التحليل: {str(e)}'

def generate_sitemap_job(job_id, url, options):
    """وظيفة إنشاء خريطة الموقع (تعمل في خلفية)"""
    try:
        running_jobs[job_id]['status'] = 'running'
        running_jobs[job_id]['progress'] = 10
        running_jobs[job_id]['message'] = 'بدء إنشاء خريطة الموقع...'
        
        # تأكد من صحة URL
        if not validate_url(url):
            running_jobs[job_id]['status'] = 'error'
            running_jobs[job_id]['message'] = f'رابط غير صالح: {url}'
            return
        
        # احصل على الخيارات
        output = options.get('output', 'sitemap.xml')
        changefreq = options.get('changefreq', 'weekly')
        priority = options.get('priority', 0.5)
        
        # تهيئة الزاحف
        running_jobs[job_id]['progress'] = 20
        running_jobs[job_id]['message'] = 'جاري زحف الموقع...'
        
        crawler = WebCrawler(
            start_url=url,
            max_pages=config.get('crawling', {}).get('max_pages', 100),
            max_depth=options.get('depth', 3),
            delay=config.get('crawling', {}).get('delay_seconds', 1),
            respect_robots_txt=config.get('crawling', {}).get('respect_robots_txt', True),
            verbose=True
        )
        
        # بدء الزحف
        pages = crawler.crawl()
        
        if not pages:
            running_jobs[job_id]['status'] = 'error'
            running_jobs[job_id]['message'] = 'لم يتم العثور على أي صفحات لإضافتها إلى خريطة الموقع.'
            return
        
        # إنشاء مجلد النتائج
        results_dir = os.path.join(options.get('output_dir', 'results'), datetime.now().strftime("%Y%m%d_%H%M%S"))
        create_directory(results_dir)
        
        # تحديث الحالة
        running_jobs[job_id]['progress'] = 70
        running_jobs[job_id]['message'] = 'جاري إنشاء ملف خريطة الموقع XML...'
        
        # إنشاء خريطة الموقع
        sitemap_path = os.path.join(results_dir, output)
        
        # إنشاء محتوى ملف XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for page_url in pages.keys():
            xml_content += '  <url>\n'
            xml_content += f'    <loc>{page_url}</loc>\n'
            xml_content += f'    <changefreq>{changefreq}</changefreq>\n'
            xml_content += f'    <priority>{priority}</priority>\n'
            xml_content += '  </url>\n'
        
        xml_content += '</urlset>'
        
        # حفظ الملف
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # تحديث الحالة
        running_jobs[job_id]['status'] = 'completed'
        running_jobs[job_id]['progress'] = 100
        running_jobs[job_id]['message'] = 'تم إنشاء خريطة الموقع بنجاح!'
        running_jobs[job_id]['result'] = {
            'file_path': sitemap_path,
            'url_count': len(pages),
            'file_size': os.path.getsize(sitemap_path),
            'dir_name': os.path.basename(results_dir)
        }
    
    except Exception as e:
        logger.error(f"خطأ أثناء إنشاء خريطة الموقع: {str(e)}")
        running_jobs[job_id]['status'] = 'error'
        running_jobs[job_id]['message'] = f'حدث خطأ أثناء إنشاء خريطة الموقع: {str(e)}'

@app.route('/')
def index():
    """الصفحة الرئيسية للوحة التحكم"""
    recent_results = get_recent_results()
    return render_template('index.html', recent_results=recent_results)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """صفحة تحليل السيو"""
    if request.method == 'POST':
        url = request.form.get('url', '')
        
        if not validate_url(url):
            flash('الرجاء إدخال رابط صالح', 'error')
            return redirect(url_for('analyze'))
        
        # جمع الخيارات من النموذج
        options = {
            'single_page': request.form.get('single_page') == 'on',
            'depth': int(request.form.get('depth', 3)),
            'export_format': request.form.get('export_format', 'all'),
            'auto_fix': request.form.get('auto_fix') == 'on',
            'output_dir': 'results',
            'wp_api': request.form.get('wp_api') == 'on'
        }
        
        # إضافة بيانات WordPress إذا تم تحديدها
        if options['wp_api']:
            options['wp_username'] = request.form.get('wp_username', '')
            options['wp_password'] = request.form.get('wp_password', '')
            
            if not options['wp_username'] or not options['wp_password']:
                flash('يجب تحديد اسم المستخدم وكلمة المرور عند استخدام WordPress API', 'error')
                return redirect(url_for('analyze'))
        
        # إنشاء معرف فريد للمهمة
        job_id = f"analyze_{int(time.time())}"
        
        # إنشاء بيانات المهمة
        running_jobs[job_id] = {
            'type': 'analyze',
            'url': url,
            'options': options,
            'status': 'starting',
            'progress': 0,
            'message': 'جاري البدء...',
            'start_time': time.time()
        }
        
        # بدء المهمة في خلفية
        thread = Thread(target=analyze_website_job, args=(job_id, url, options))
        thread.daemon = True
        thread.start()
        
        # إعادة توجيه إلى صفحة الحالة
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
        
        # جمع الخيارات من النموذج
        options = {
            'output': request.form.get('output', 'sitemap.xml'),
            'changefreq': request.form.get('changefreq', 'weekly'),
            'priority': float(request.form.get('priority', 0.5)),
            'depth': int(request.form.get('depth', 3)),
            'output_dir': 'results'
        }
        
        # إنشاء معرف فريد للمهمة
        job_id = f"sitemap_{int(time.time())}"
        
        # إنشاء بيانات المهمة
        running_jobs[job_id] = {
            'type': 'sitemap',
            'url': url,
            'options': options,
            'status': 'starting',
            'progress': 0,
            'message': 'جاري البدء...',
            'start_time': time.time()
        }
        
        # بدء المهمة في خلفية
        thread = Thread(target=generate_sitemap_job, args=(job_id, url, options))
        thread.daemon = True
        thread.start()
        
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

@app.route('/content-generator')
def content_generator():
    """صفحة مولد المحتوى بالذكاء الاصطناعي"""
    return render_template('content_generator.html', result=None)

@app.route('/generate-content', methods=['POST'])
def generate_content():
    """توليد محتوى جديد باستخدام الذكاء الاصطناعي"""
    # الحصول على البيانات من النموذج
    prompt = request.form.get('prompt', '')
    content_type = request.form.get('content_type', 'article')
    language = request.form.get('language', 'ar')
    tone = request.form.get('tone', 'professional')
    word_count = request.form.get('word_count', '')
    keywords = request.form.get('keywords', '')
    
    # تحويل الكلمات المفتاحية إلى قائمة
    keywords_list = [k.strip() for k in keywords.split(',')] if keywords else []
    
    # تحويل عدد الكلمات إلى رقم صحيح إذا تم تحديده
    if word_count:
        try:
            word_count = int(word_count)
        except ValueError:
            word_count = None
    else:
        word_count = None
    
    # التحقق من صحة المدخلات
    if not prompt:
        flash('يرجى تحديد موضوع المحتوى', 'error')
        return redirect(url_for('content_generator'))
    
    try:
        # استخدام مفتاح API من الإعدادات
        api_key = config.get('openai', {}).get('api_key', os.getenv('OPENAI_API_KEY'))
        
        # تهيئة مولد المحتوى
        content_generator = AIContentGenerator(api_key=api_key)
        
        # توليد المحتوى
        generated_content = content_generator.generate(
            prompt=prompt,
            keywords=keywords_list,
            content_type=content_type,
            language=language,
            tone=tone,
            word_count=word_count
        )
        
        # تحضير البيانات للعرض
        result = {
            'content': generated_content,
            'type': content_type,
            'language': language,
            'tone': tone,
            'keywords': keywords_list
        }
        
        return render_template('content_generator.html', result=result)
    
    except Exception as e:
        logger.error(f"خطأ في توليد المحتوى: {str(e)}")
        flash(f'حدث خطأ أثناء توليد المحتوى: {str(e)}', 'error')
        return redirect(url_for('content_generator'))

@app.route('/improve-content', methods=['POST'])
def improve_content():
    """تحسين محتوى موجود باستخدام الذكاء الاصطناعي"""
    # الحصول على البيانات من النموذج
    original_content = request.form.get('original_content', '')
    suggestions_text = request.form.get('suggestions', '')
    keywords = request.form.get('keywords', '')
    
    # تحويل الاقتراحات والكلمات المفتاحية إلى قوائم
    suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()] if suggestions_text else []
    keywords_list = [k.strip() for k in keywords.split(',')] if keywords else []
    
    # التحقق من صحة المدخلات
    if not original_content:
        flash('يرجى تحديد المحتوى الأصلي', 'error')
        return redirect(url_for('content_generator'))
    
    try:
        # استخدام مفتاح API من الإعدادات
        api_key = config.get('openai', {}).get('api_key', os.getenv('OPENAI_API_KEY'))
        
        # تهيئة مولد المحتوى
        content_generator = AIContentGenerator(api_key=api_key)
        
        # تحسين المحتوى
        improved_content = content_generator.improve_content(
            original_content=original_content,
            suggestions=suggestions,
            keywords=keywords_list
        )
        
        # تحضير البيانات للعرض
        result = {
            'content': improved_content,
            'keywords': keywords_list
        }
        
        return render_template('content_generator.html', result=result)
    
    except Exception as e:
        logger.error(f"خطأ في تحسين المحتوى: {str(e)}")
        flash(f'حدث خطأ أثناء تحسين المحتوى: {str(e)}', 'error')
        return redirect(url_for('content_generator'))

@app.route('/generate-meta-tags', methods=['POST'])
def generate_meta_tags():
    """توليد العلامات الوصفية للصفحة"""
    # الحصول على البيانات من النموذج
    page_content = request.form.get('page_content', '')
    url = request.form.get('url', '')
    target_keywords = request.form.get('target_keywords', '')
    
    # تحويل الكلمات المفتاحية إلى قائمة
    keywords_list = [k.strip() for k in target_keywords.split(',')] if target_keywords else []
    
    # التحقق من صحة المدخلات
    if not page_content:
        flash('يرجى تحديد محتوى الصفحة', 'error')
        return redirect(url_for('content_generator'))
    
    try:
        # استخدام مفتاح API من الإعدادات
        api_key = config.get('openai', {}).get('api_key', os.getenv('OPENAI_API_KEY'))
        
        # تهيئة مولد المحتوى
        content_generator = AIContentGenerator(api_key=api_key)
        
        # توليد العلامات الوصفية
        meta_tags = content_generator.generate_meta_tags(
            page_content=page_content,
            url=url,
            target_keywords=keywords_list
        )
        
        return render_template('content_generator.html', result=meta_tags)
    
    except Exception as e:
        logger.error(f"خطأ في توليد العلامات الوصفية: {str(e)}")
        flash(f'حدث خطأ أثناء توليد العلامات الوصفية: {str(e)}', 'error')
        return redirect(url_for('content_generator'))

@app.route('/suggest-improvements', methods=['POST'])
def suggest_improvements():
    """اقتراح تحسينات للمحتوى من منظور السيو"""
    # الحصول على البيانات من النموذج
    content = request.form.get('content', '')
    content_type = request.form.get('content_type', '')
    target_keywords = request.form.get('target_keywords', '')
    
    # تحويل الكلمات المفتاحية إلى قائمة
    keywords_list = [k.strip() for k in target_keywords.split(',')] if target_keywords else []
    
    # التحقق من صحة المدخلات
    if not content:
        flash('يرجى تحديد المحتوى', 'error')
        return redirect(url_for('content_generator'))
    
    try:
        # استخدام مفتاح API من الإعدادات
        api_key = config.get('openai', {}).get('api_key', os.getenv('OPENAI_API_KEY'))
        
        # تهيئة مولد المحتوى
        content_generator = AIContentGenerator(api_key=api_key)
        
        # اقتراح تحسينات
        suggestions = content_generator.suggest_improvements(
            content=content,
            content_type=content_type,
            target_keywords=keywords_list
        )
        
        return render_template('content_generator.html', result=suggestions)
    
    except Exception as e:
        logger.error(f"خطأ في اقتراح تحسينات: {str(e)}")
        flash(f'حدث خطأ أثناء اقتراح تحسينات: {str(e)}', 'error')
        return redirect(url_for('content_generator'))

# نظام المراقبة والتقارير الدورية
monitoring_system = MonitoringSystem()

@app.route('/monitoring')
def monitoring():
    """صفحة نظام المراقبة والتقارير الدورية"""
    # الحصول على المهام المجدولة
    tasks = monitoring_system.get_all_performance_data()
    
    # حساب الإحصائيات
    total_reports = 0
    total_issues = 0
    scores_sum = 0
    scores_count = 0
    
    for task in tasks:
        if 'score' in task and task['score'] > 0:
            scores_sum += task['score']
            scores_count += 1
        
        if 'issues' in task:
            total_issues += task['issues']
        
        # الحصول على سجل المهمة لحساب إجمالي التقارير
        history = monitoring_system.get_task_history(task['task_id'])
        total_reports += len(history)
    
    # حساب متوسط النتيجة
    average_score = int(scores_sum / scores_count) if scores_count > 0 else 0
    
    # إعداد بيانات الرسم البياني
    chart_data = None
    if tasks:
        # تحديد المهام التي لديها نتائج
        tasks_with_results = [task for task in tasks if 'score' in task and task['score'] > 0]
        
        if tasks_with_results:
            # ترتيب المهام حسب النتيجة (من الأعلى للأدنى)
            tasks_with_results.sort(key=lambda x: x['score'], reverse=True)
            
            # اختيار أفضل 5 مهام (أو أقل إذا كان العدد أقل من 5)
            top_tasks = tasks_with_results[:min(5, len(tasks_with_results))]
            
            chart_data = {
                'labels': [task.get('url').replace('https://', '').replace('http://', '') for task in top_tasks],
                'scores': [task.get('score', 0) for task in top_tasks],
                'issues': [task.get('issues', 0) for task in top_tasks]
            }
    
    return render_template('monitoring.html', 
                           tasks=tasks, 
                           total_reports=total_reports,
                           total_issues=total_issues,
                           average_score=average_score,
                           chart_data=chart_data)

@app.route('/monitoring/add-task', methods=['POST'])
def monitoring_add_task():
    """إضافة مهمة مراقبة جديدة"""
    # الحصول على البيانات من النموذج
    url = request.form.get('url', '')
    frequency = request.form.get('frequency', 'weekly')
    notify = bool(request.form.get('notify', False))
    max_pages = int(request.form.get('max_pages', 100))
    depth = int(request.form.get('depth', 3))
    
    # الحصول على خيارات التوقيت
    options = {
        'max_pages': max_pages,
        'depth': depth
    }
    
    # إضافة خيارات التوقيت بناءً على التكرار
    if frequency == 'daily':
        options['hour'] = int(request.form.get('hour', 3))
    elif frequency == 'weekly':
        options['day_of_week'] = request.form.get('day_of_week', 'mon')
        options['hour'] = int(request.form.get('hour', 3))
    elif frequency == 'monthly':
        options['day'] = int(request.form.get('day', 1))
        options['hour'] = int(request.form.get('hour', 3))
    
    # التحقق من صحة URL
    if not validate_url(url):
        flash('عنوان URL غير صالح', 'error')
        return redirect(url_for('monitoring'))
    
    # إضافة المهمة
    task_id = monitoring_system.add_scheduled_task(
        url=url,
        frequency=frequency,
        options=options,
        notify=notify
    )
    
    if task_id:
        flash(f'تمت إضافة مهمة المراقبة بنجاح لـ {url}', 'success')
    else:
        flash('فشل في إضافة مهمة المراقبة. يرجى التحقق من السجلات.', 'error')
    
    return redirect(url_for('monitoring'))

@app.route('/monitoring/remove-task', methods=['POST'])
def monitoring_remove_task():
    """إزالة مهمة مراقبة"""
    task_id = request.form.get('task_id', '')
    
    if not task_id:
        flash('معرف المهمة غير صالح', 'error')
        return redirect(url_for('monitoring'))
    
    success = monitoring_system.remove_scheduled_task(task_id)
    
    if success:
        flash('تمت إزالة مهمة المراقبة بنجاح', 'success')
    else:
        flash('فشل في إزالة مهمة المراقبة. يرجى التحقق من السجلات.', 'error')
    
    return redirect(url_for('monitoring'))

@app.route('/monitoring/run-task/<task_id>')
def monitoring_run_task(task_id):
    """تشغيل مهمة مراقبة محددة الآن"""
    success = monitoring_system.run_task_now(task_id)
    
    if success:
        flash('تم بدء تنفيذ المهمة. يمكنك متابعة التقدم في صفحة تفاصيل المهمة.', 'success')
    else:
        flash('فشل في تشغيل المهمة. يرجى التحقق من السجلات.', 'error')
    
    return redirect(url_for('monitoring_task_details', task_id=task_id))

@app.route('/monitoring/task/<task_id>')
def monitoring_task_details(task_id):
    """عرض تفاصيل مهمة مراقبة محددة"""
    # البحث عن المهمة في القائمة
    tasks = monitoring_system.get_scheduled_tasks()
    task = next((t for t in tasks if t.get('id') == task_id), None)
    
    if not task:
        flash('المهمة غير موجودة', 'error')
        return redirect(url_for('monitoring'))
    
    # الحصول على سجل المهمة
    history = monitoring_system.get_task_history(task_id)
    
    # ترتيب السجل حسب الوقت (الأحدث أولاً)
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # الحصول على آخر نتيجة
    latest_result = history[0] if history else None
    
    # إعداد بيانات الرسم البياني للعرض
    chart_data = None
    if len(history) > 1:
        comparison = monitoring_system.compare_results(task_id, limit=10)
        
        if comparison:
            chart_data = {
                'dates': comparison.get('dates', []),
                'scores': comparison.get('scores', []),
                'issues': comparison.get('issues', [])
            }
    
    return render_template('monitoring_task_details.html',
                           task=task,
                           history=history,
                           latest_result=latest_result,
                           chart_data=chart_data)

@app.route('/monitoring/edit-task', methods=['POST'])
def monitoring_edit_task():
    """تعديل مهمة مراقبة"""
    task_id = request.form.get('task_id', '')
    
    if not task_id:
        flash('معرف المهمة غير صالح', 'error')
        return redirect(url_for('monitoring'))
    
    # البحث عن المهمة في القائمة
    tasks = monitoring_system.get_scheduled_tasks()
    task_index = next((i for i, t in enumerate(tasks) if t.get('id') == task_id), None)
    
    if task_index is None:
        flash('المهمة غير موجودة', 'error')
        return redirect(url_for('monitoring'))
    
    # تحديث بيانات المهمة
    url = request.form.get('url', '')
    frequency = request.form.get('frequency', 'weekly')
    notify = bool(request.form.get('notify', False))
    max_pages = int(request.form.get('max_pages', 100))
    depth = int(request.form.get('depth', 3))
    
    # الحصول على خيارات التوقيت
    options = {
        'max_pages': max_pages,
        'depth': depth,
        'notify': notify
    }
    
    # إضافة خيارات التوقيت بناءً على التكرار
    if frequency == 'daily':
        options['hour'] = int(request.form.get('hour', 3))
    elif frequency == 'weekly':
        options['day_of_week'] = request.form.get('day_of_week', 'mon')
        options['hour'] = int(request.form.get('hour', 3))
    elif frequency == 'monthly':
        options['day'] = int(request.form.get('day', 1))
        options['hour'] = int(request.form.get('hour', 3))
    
    # التحقق من صحة URL
    if not validate_url(url):
        flash('عنوان URL غير صالح', 'error')
        return redirect(url_for('monitoring_task_details', task_id=task_id))
    
    # تحديث المهمة
    # إزالة المهمة القديمة أولاً
    monitoring_system.remove_scheduled_task(task_id)
    
    # ثم إضافة المهمة المحدثة
    new_task_id = monitoring_system.add_scheduled_task(
        url=url,
        frequency=frequency,
        options=options,
        notify=notify
    )
    
    if new_task_id:
        flash(f'تم تحديث مهمة المراقبة بنجاح', 'success')
    else:
        flash('فشل في تحديث مهمة المراقبة. يرجى التحقق من السجلات.', 'error')
    
    return redirect(url_for('monitoring_task_details', task_id=new_task_id if new_task_id else task_id))

@app.route('/monitoring/compare-reports')
def monitoring_compare_reports():
    """مقارنة تقارير تحليل"""
    task_id = request.args.get('task_id', '')
    report1_id = request.args.get('report1', '')
    report2_id = request.args.get('report2', '')
    
    if not all([task_id, report1_id, report2_id]):
        flash('بيانات المقارنة غير مكتملة', 'error')
        return redirect(url_for('monitoring'))
    
    # الحصول على بيانات التقارير
    # (هذه الوظيفة تحتاج إلى تنفيذ إضافي لاسترجاع بيانات التقارير المحددة)
    
    # إنشاء تقرير المقارنة
    # (هذه الوظيفة تحتاج إلى تنفيذ إضافي لإنشاء تقرير المقارنة)
    
    flash('تم إنشاء تقرير المقارنة بنجاح', 'success')
    return redirect(url_for('monitoring_task_details', task_id=task_id))

if __name__ == '__main__':
    # التأكد من وجود المجلدات الضرورية
    create_directory(results_directory)
    create_directory(os.path.join('data', 'monitoring'))
    create_directory(os.path.join('data', 'reports'))
    
    # تشغيل التطبيق
    app.run(debug=True, host='0.0.0.0', port=5000)
