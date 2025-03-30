#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
واجهة Streamlit لأداة RSEO - أداة شاملة لتحليل وتحسين السيو
"""

import streamlit as st
import time
import os
from datetime import datetime

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

# استيراد الأدوات المساعدة
from utils.helpers import validate_url, create_directory, format_time
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger, get_logger

# تحميل الإعدادات
config_loader = ConfigLoader()
config = config_loader.get_all()

# إعداد المسجل
logger = get_logger("rseo_streamlit")

# تعيين عنوان التطبيق
st.set_page_config(
    page_title="RSEO - أداة تحليل وتحسين السيو",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # عرض شعار البرنامج
    st.title("🔍 RSEO - أداة شاملة لتحليل وتحسين السيو")
    st.write("أداة متكاملة لفحص وتحسين السيو للمواقع الإلكترونية")
    
    # إضافة شريط جانبي للخيارات
    st.sidebar.title("الخيارات")
    
    # اختيار الوظيفة
    function = st.sidebar.radio(
        "اختر الوظيفة",
        ["تحليل موقع", "إصلاح مشاكل السيو", "إنشاء خريطة موقع"]
    )
    
    if function == "تحليل موقع":
        analyze_website()
    elif function == "إصلاح مشاكل السيو":
        fix_seo_issues()
    elif function == "إنشاء خريطة موقع":
        generate_sitemap()

def analyze_website():
    st.header("تحليل موقع للكشف عن مشاكل السيو")
    
    # إدخال رابط الموقع
    url = st.text_input("أدخل رابط الموقع المراد تحليله", placeholder="https://example.com")
    
    # خيارات متقدمة
    with st.expander("خيارات متقدمة"):
        col1, col2 = st.columns(2)
        with col1:
            single_page = st.checkbox("تحليل صفحة واحدة فقط", value=False)
            depth = st.number_input("عمق الزحف", min_value=1, max_value=10, value=3)
            export_format = st.selectbox("تنسيق التصدير", ["json", "pdf", "html", "all"])
        
        with col2:
            auto_fix = st.checkbox("إصلاح المشاكل تلقائياً", value=False)
            verbose = st.checkbox("عرض معلومات تفصيلية", value=True)
            output_dir = st.text_input("مجلد حفظ النتائج", value="results")
    
    # خيارات ووردبريس
    wp_options = st.expander("خيارات WordPress")
    with wp_options:
        wp_api = st.checkbox("استخدام WordPress API", value=False)
        if wp_api:
            wp_username = st.text_input("اسم المستخدم لـ WordPress")
            wp_password = st.text_input("كلمة المرور لـ WordPress", type="password")
    
    # زر البدء
    if st.button("بدء التحليل"):
        if not url or not validate_url(url):
            st.error("الرجاء إدخال رابط صالح")
            return
        
        start_time = time.time()
        
        # إنشاء شريط التقدم
        progress_bar = st.progress(0)
        progress_status = st.empty()
        
        # إنشاء مجلد النتائج
        results_dir = os.path.join(output_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        create_directory(results_dir)
        
        # تهيئة الزاحف
        max_pages = 1 if single_page else config.get('crawling', {}).get('max_pages', 100)
        delay = config.get('crawling', {}).get('delay_seconds', 1)
        respect_robots = config.get('crawling', {}).get('respect_robots_txt', True)
        
        progress_status.write("جاري الزحف...")
        crawler = WebCrawler(
            start_url=url,
            max_pages=max_pages,
            max_depth=depth,
            delay=delay,
            respect_robots_txt=respect_robots,
            verbose=verbose
        )
        
        # بدء الزحف
        pages = crawler.crawl()
        progress_bar.progress(0.2)
        
        if not pages:
            st.error("لم يتم العثور على أي صفحات للتحليل.")
            return
        
        # تحليل السيو
        progress_status.write(f"جاري تحليل {len(pages)} صفحة...")
        
        # تهيئة المحللات
        seo_analyzer = SEOAnalyzer(config=config)
        page_speed_analyzer = PageSpeedAnalyzer()
        content_analyzer = ContentAnalyzer()
        image_optimizer = ImageOptimizer()
        link_checker = LinkChecker()
        
        # إعداد تكامل ووردبريس إذا تم تحديده
        if wp_api:
            if not wp_username or not wp_password:
                st.error("يجب تحديد اسم المستخدم وكلمة المرور عند استخدام WordPress API")
                return
            
            wp_integration = WordPressIntegration(
                site_url=url,
                username=wp_username,
                password=wp_password
            )
        
        # تحليل كل صفحة
        results = {}
        page_count = len(pages)
        for i, (page_url, page_data) in enumerate(pages.items()):
            progress_status.write(f"تحليل صفحة {i+1} من {page_count}: {page_url}")
            progress_bar.progress(0.2 + 0.6 * (i / page_count))
            
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
                st.error(f"خطأ أثناء تحليل الصفحة {page_url}: {str(e)}")
        
        # توليد التقرير
        progress_status.write("جاري إنشاء التقرير...")
        progress_bar.progress(0.9)
        
        report_generator = ReportGenerator(results_dir=results_dir)
        report_path = report_generator.generate_report(
            url=url,
            results=results,
            format=export_format
        )
        
        # إصلاح المشاكل إذا تم تحديد الخيار
        if auto_fix:
            progress_status.write("جاري إصلاح مشاكل السيو...")
            seo_fixer = SEOFixer(results_dir=results_dir)
            fixed_items = seo_fixer.fix_issues(results=results)
            
            # إذا كان هناك تكامل مع ووردبريس، قم بتطبيق الإصلاحات
            if wp_api:
                progress_status.write("جاري تطبيق الإصلاحات على WordPress...")
                wp_integration.apply_fixes(fixed_items)
        
        # انتهاء العملية
        elapsed_time = time.time() - start_time
        progress_bar.progress(1.0)
        progress_status.write(f"اكتمل التحليل في {format_time(elapsed_time)}")
        
        # عرض النتائج
        st.subheader("نتائج التحليل")
        if os.path.exists(report_path):
            st.success(f"تم إنشاء التقرير بنجاح: {report_path}")
            if export_format == "html" or export_format == "all":
                html_path = os.path.join(results_dir, "report.html")
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=600, scrolling=True)
            elif export_format == "json":
                json_path = os.path.join(results_dir, "report.json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        st.json(f.read())

def fix_seo_issues():
    st.header("إصلاح مشاكل السيو")
    
    # إدخال رابط الموقع
    url = st.text_input("أدخل رابط الموقع", placeholder="https://example.com")
    
    # اختيار ملف التقرير
    report_file = st.file_uploader("اختر ملف تقرير JSON", type=["json"])
    
    # خيارات ووردبريس
    wp_options = st.expander("خيارات WordPress")
    with wp_options:
        wp_api = st.checkbox("استخدام WordPress API", value=False)
        if wp_api:
            wp_username = st.text_input("اسم المستخدم لـ WordPress")
            wp_password = st.text_input("كلمة المرور لـ WordPress", type="password")
    
    # زر البدء
    if st.button("بدء الإصلاح"):
        if not url or not validate_url(url):
            st.error("الرجاء إدخال رابط صالح")
            return
        
        if not report_file:
            st.error("الرجاء اختيار ملف تقرير")
            return
        
        st.write("جاري إصلاح مشاكل السيو...")
        # هنا يمكن إضافة كود الإصلاح الفعلي

def generate_sitemap():
    st.header("إنشاء خريطة موقع XML")
    
    # إدخال رابط الموقع
    url = st.text_input("أدخل رابط الموقع", placeholder="https://example.com")
    
    # خيارات متقدمة
    with st.expander("خيارات متقدمة"):
        col1, col2 = st.columns(2)
        with col1:
            output = st.text_input("مسار الملف الناتج", value="sitemap.xml")
        with col2:
            changefreq = st.selectbox(
                "تكرار التغيير",
                ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
            )
            priority = st.slider("الأولوية", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    
    # زر البدء
    if st.button("إنشاء خريطة الموقع"):
        if not url or not validate_url(url):
            st.error("الرجاء إدخال رابط صالح")
            return
        
        st.write("جاري إنشاء خريطة الموقع...")
        # هنا يمكن إضافة كود إنشاء خريطة الموقع الفعلي

if __name__ == "__main__":
    main()
