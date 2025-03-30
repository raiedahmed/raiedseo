#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - واجهة برمجة التطبيقات (API)
توفر واجهة RESTful API للوصول إلى وظائف RSEO برمجياً
"""

import os
import json
import time
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
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
from modules.competitor_analyzer import CompetitorAnalyzer
from modules.keyword_analyzer import KeywordAnalyzer
from modules.ai_content_generator import AIContentGenerator

# استيراد الأدوات المساعدة
from utils.helpers import validate_url, create_directory, format_time
from utils.config_loader import ConfigLoader
from utils.logger import get_logger

# إنشاء مسار API
api = Blueprint('api', __name__)

# إعداد المسجل
logger = get_logger("rseo_api")

# تحميل ملف الإعدادات
config_loader = ConfigLoader()
config = config_loader.get_all()

# المتغيرات العالمية
running_jobs = {}
results_directory = 'results'

# ==================
# وظائف مساعدة
# ==================

def generate_job_id():
    """توليد معرّف فريد للمهمة"""
    return str(uuid.uuid4())

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
        
        # ميزات متقدمة
        keyword_analyzer = KeywordAnalyzer()
        competitor_domains = options.get('competitor_domains', [])
        competitor_analyzer = None
        if competitor_domains:
            competitor_analyzer = CompetitorAnalyzer(config=config)
        
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
                
                # تحليل الكلمات المفتاحية
                try:
                    page_result['keywords'] = keyword_analyzer.analyze(page_data)
                except Exception as e:
                    logger.warning(f"فشل تحليل الكلمات المفتاحية للصفحة {page_url}: {str(e)}")
                
                # إضافة النتائج
                results[page_url] = page_result
                
            except Exception as e:
                logger.error(f"خطأ أثناء تحليل الصفحة {page_url}: {str(e)}")
        
        # تحليل المنافسين إذا تم تحديدهم
        if competitor_analyzer and competitor_domains:
            running_jobs[job_id]['progress'] = 85
            running_jobs[job_id]['message'] = 'جاري تحليل المنافسين...'
            
            competitors_results = {}
            for comp_domain in competitor_domains:
                if validate_url(comp_domain):
                    try:
                        competitors_results[comp_domain] = competitor_analyzer.analyze(comp_domain)
                    except Exception as e:
                        logger.error(f"خطأ أثناء تحليل المنافس {comp_domain}: {str(e)}")
            
            # إضافة نتائج المنافسين
            if competitors_results:
                results['competitors'] = competitors_results
        
        # تحديث الحالة
        running_jobs[job_id]['progress'] = 90
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
            running_jobs[job_id]['progress'] = 95
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
        page_count = len(results) - (1 if 'competitors' in results else 0)
        
        for page_url, page_data in results.items():
            if page_url == 'competitors':
                continue
                
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
        
    except Exception as e:
        logger.error(f"خطأ أثناء التحليل: {str(e)}")
        running_jobs[job_id]['status'] = 'error'
        running_jobs[job_id]['message'] = f'حدث خطأ أثناء التحليل: {str(e)}'

# ==================
# مسارات API
# ==================

@api.route('/health', methods=['GET'])
def health_check():
    """فحص حالة API"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@api.route('/auth/login', methods=['POST'])
def login():
    """تسجيل الدخول والحصول على رمز JWT"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    # تحقق من بيانات الاعتماد (يجب استبداله بالتحقق الفعلي)
    if username != "admin" or password != "password":
        return jsonify({"msg": "Bad username or password"}), 401
    
    # إنشاء رمز الوصول
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

@api.route('/analyze', methods=['POST'])
@jwt_required()
def analyze():
    """تحليل موقع ويب"""
    # التحقق من البيانات المطلوبة
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    url = request.json.get('url')
    if not url or not validate_url(url):
        return jsonify({"msg": "Invalid or missing URL"}), 400
    
    # جمع الخيارات
    options = {
        'single_page': request.json.get('single_page', False),
        'depth': request.json.get('depth', 3),
        'export_format': request.json.get('export_format', 'all'),
        'auto_fix': request.json.get('auto_fix', False),
        'output_dir': 'results',
        'wp_api': request.json.get('wp_api', False),
        'competitor_domains': request.json.get('competitor_domains', [])
    }
    
    # إضافة بيانات WordPress إذا تم تحديدها
    if options['wp_api']:
        options['wp_username'] = request.json.get('wp_username', '')
        options['wp_password'] = request.json.get('wp_password', '')
        
        if not options['wp_username'] or not options['wp_password']:
            return jsonify({"msg": "WordPress credentials required when wp_api is enabled"}), 400
    
    # إنشاء معرف فريد للمهمة
    job_id = generate_job_id()
    
    # إنشاء بيانات المهمة
    running_jobs[job_id] = {
        'type': 'analyze',
        'url': url,
        'options': options,
        'status': 'starting',
        'progress': 0,
        'message': 'جاري البدء...',
        'start_time': time.time(),
        'user': get_jwt_identity()
    }
    
    # بدء المهمة في خلفية
    thread = Thread(target=analyze_website_job, args=(job_id, url, options))
    thread.daemon = True
    thread.start()
    
    # إرجاع معرف المهمة
    return jsonify({
        'job_id': job_id,
        'status': 'starting',
        'message': 'تم بدء مهمة التحليل بنجاح'
    }), 202

@api.route('/jobs/<job_id>', methods=['GET'])
@jwt_required()
def get_job_status(job_id):
    """الحصول على حالة مهمة"""
    if job_id not in running_jobs:
        return jsonify({"msg": "Job not found"}), 404
    
    job = running_jobs[job_id]
    
    # التحقق من أن المستخدم هو مالك المهمة
    if job.get('user') != get_jwt_identity():
        return jsonify({"msg": "Unauthorized access to job"}), 403
    
    return jsonify({
        'job_id': job_id,
        'type': job.get('type'),
        'url': job.get('url'),
        'status': job.get('status'),
        'progress': job.get('progress', 0),
        'message': job.get('message', ''),
        'result': job.get('result'),
        'elapsed_time': format_time(time.time() - job.get('start_time', time.time()))
    }), 200

@api.route('/reports', methods=['GET'])
@jwt_required()
def list_reports():
    """الحصول على قائمة بالتقارير"""
    try:
        reports = []
        if os.path.exists(results_directory):
            dirs = [d for d in os.listdir(results_directory) if os.path.isdir(os.path.join(results_directory, d))]
            # ترتيب الدلائل حسب التاريخ (الأحدث أولاً)
            dirs.sort(reverse=True)
            
            for dir_name in dirs:
                dir_path = os.path.join(results_directory, dir_name)
                # البحث عن ملف النتائج
                summary_file = os.path.join(dir_path, 'summary.json')
                
                if os.path.exists(summary_file):
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # استخراج المعلومات المهمة
                            reports.append({
                                'id': dir_name,
                                'url': data.get('site_url', 'غير معروف'),
                                'date': data.get('analysis_date'),
                                'total_pages': data.get('total_pages', 0),
                                'total_issues': data.get('total_issues', 0),
                                'average_score': data.get('average_score', 0)
                            })
                    except Exception as e:
                        logger.error(f"خطأ في قراءة ملف التقرير: {str(e)}")
        
        return jsonify(reports), 200
    
    except Exception as e:
        return jsonify({"msg": f"Error retrieving reports: {str(e)}"}), 500

@api.route('/reports/<report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """الحصول على تقرير محدد"""
    report_path = os.path.join(results_directory, report_id, 'summary.json')
    
    if not os.path.exists(report_path):
        return jsonify({"msg": "Report not found"}), 404
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return jsonify(report_data), 200
    
    except Exception as e:
        return jsonify({"msg": f"Error retrieving report: {str(e)}"}), 500

@api.route('/generate-content', methods=['POST'])
@jwt_required()
def generate_content():
    """توليد محتوى باستخدام الذكاء الاصطناعي"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    prompt = request.json.get('prompt')
    keywords = request.json.get('keywords', [])
    content_type = request.json.get('content_type', 'article')
    language = request.json.get('language', 'ar')
    
    if not prompt:
        return jsonify({"msg": "Prompt is required"}), 400
    
    # التحقق من وجود مفتاح API
    api_key = config.get('api_keys', {}).get('openai')
    if not api_key:
        return jsonify({"msg": "OpenAI API key is missing in configuration"}), 400
    
    try:
        # توليد المحتوى
        ai_generator = AIContentGenerator(api_key=api_key)
        content = ai_generator.generate(
            prompt=prompt,
            keywords=keywords,
            content_type=content_type,
            language=language
        )
        
        return jsonify({
            'success': True,
            'content': content
        }), 200
    
    except Exception as e:
        return jsonify({"msg": f"Error generating content: {str(e)}"}), 500

@api.route('/competitors/<domain>/analyze', methods=['GET'])
@jwt_required()
def analyze_competitor(domain):
    """تحليل موقع منافس"""
    if not validate_url(domain):
        return jsonify({"msg": "Invalid domain URL"}), 400
    
    try:
        competitor_analyzer = CompetitorAnalyzer(config=config)
        results = competitor_analyzer.analyze(domain)
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({"msg": f"Error analyzing competitor: {str(e)}"}), 500

@api.route('/keywords/analyze', methods=['POST'])
@jwt_required()
def analyze_keywords():
    """تحليل الكلمات المفتاحية"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    
    keywords = request.json.get('keywords', [])
    url = request.json.get('url')
    
    if not keywords or not isinstance(keywords, list) or len(keywords) == 0:
        return jsonify({"msg": "At least one keyword is required"}), 400
    
    if url and not validate_url(url):
        return jsonify({"msg": "Invalid URL"}), 400
    
    try:
        keyword_analyzer = KeywordAnalyzer()
        results = keyword_analyzer.analyze_keywords(keywords, url)
        
        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({"msg": f"Error analyzing keywords: {str(e)}"}), 500
