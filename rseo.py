#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - أداة شاملة لتحليل وتحسين السيو

نقطة الدخول الرئيسية للبرنامج التي تتعامل مع واجهة سطر الأوامر
وتنسق العمليات المختلفة بين وحدات البرنامج.
"""

import os
import sys
import time
import click
import yaml
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import init, Fore, Style
from tqdm import tqdm

# تعيين ترميز stdout لدعم النصوص العربية
if sys.stdout.encoding != 'utf-8':
    # محاولة لإعادة توجيه المخرجات لدعم UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # للتوافق مع إصدارات Python الأقدم
        pass

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

# تهيئة colorama للتلوين في الطرفية
init(autoreset=True)

# تحميل متغيرات البيئة
load_dotenv()

# إعداد المسجل
logger = get_logger("rseo")

# تحميل ملف الإعدادات
config_loader = ConfigLoader()
config = config_loader.get_all()

def print_safe(text):
    """
    طباعة نص بشكل آمن مع معالجة أخطاء الترميز
    
    Args:
        text (str): النص المراد طباعته
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # تحويل النص إلى ASCII مع تجاهل الأحرف غير القابلة للترميز
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)

def show_banner():
    """عرض شعار البرنامج في الطرفية"""
    banner = f"""
{Fore.GREEN}
    ╭━━━╮╱╱╱╱╱╱╱╱╱╱╭━━━━╮╱╱╱╱╱╱╱╱╭━━━╮
    ┃╭━╮┃╱╱╱╱╱╱╱╱╱╱┃╭╮╭╮┃╱╱╱╱╱╱╱╱┃╭━╮┃
    ┃╰━╯┣━━┳━━┳━━╮╱╰╯┃┃╰┻━━┳━━┳━╮┃┃╱┃┃
    ┃╭╮╭┫┃━┫╭╮┃┃━┫╱╱╱┃┃╭┫╭╮┃┃━┫╭╮┫┃╱┃┃
    ┃┃┃╰┫┃━┫╰╯┃┃━┫╱╱╱┃┃┃┃╰╯┃┃━┫┃┃┃╰━╯┃
    ╰╯╰━┻━━┻━╮┣━━╯╱╱╱╰╯╰┻━━┻━━┻╯╰┻━━━╯
    ╱╱╱╱╱╱╱╭━╯┃
    ╱╱╱╱╱╱╱╰━━╯    
{Style.RESET_ALL}
🔍 {Fore.CYAN}أداة شاملة لتحليل وتحسين السيو - الإصدار 1.0.0{Style.RESET_ALL}
📅 {datetime.now().strftime('%Y-%m-%d')}
"""
    print_safe(banner)

@click.group()
def cli():
    """أداة RSEO لتحليل وتحسين السيو لمواقع الويب"""
    show_banner()

@cli.command()
@click.option('--url', required=True, help='رابط الموقع المراد تحليله')
@click.option('--single-page', is_flag=True, help='تحليل صفحة واحدة فقط بدلاً من الموقع بأكمله')
@click.option('--depth', default=3, help='عمق الزحف للموقع (عدد الصفحات المتتابعة)')
@click.option('--export', type=click.Choice(['json', 'pdf', 'html', 'all']), help='تصدير النتائج بتنسيق محدد')
@click.option('--wp-api', is_flag=True, help='استخدام WordPress API للتحليل والتحسين')
@click.option('--username', help='اسم المستخدم لـ WordPress')
@click.option('--password', help='كلمة المرور لـ WordPress')
@click.option('--auto-fix', is_flag=True, help='إصلاح مشاكل السيو تلقائياً عند اكتشافها')
@click.option('--output-dir', default='results', help='مسار حفظ نتائج التحليل')
@click.option('--verbose', '-v', is_flag=True, help='طباعة معلومات تفصيلية أثناء التنفيذ')
def analyze(url, single_page, depth, export, wp_api, username, password, auto_fix, output_dir, verbose):
    """تحليل موقع ويب للكشف عن مشاكل السيو وتقديم التوصيات"""
    try:
        start_time = time.time()
        
        # التحقق من صحة الرابط
        if not validate_url(url):
            logger.error(f"الرابط غير صالح: {url}")
            click.echo(f"{Fore.RED}الرابط غير صالح: {url}{Style.RESET_ALL}")
            return
        
        # إنشاء مجلد النتائج إذا لم يكن موجوداً
        results_dir = os.path.join(output_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
        create_directory(results_dir)
        
        click.echo(f"{Fore.CYAN}بدء تحليل: {url}{Style.RESET_ALL}")
        
        # تحميل الإعدادات الافتراضية إذا كان ملف التكوين فارغًا
        if not config:
            config.update({
                'crawling': {
                    'max_pages': 100,
                    'delay_seconds': 1,
                    'respect_robots_txt': True,
                    'timeout_seconds': 30
                },
                'seo_analysis': {
                    'title': {
                        'min_length': 30,
                        'max_length': 60
                    },
                    'meta_description': {
                        'min_length': 70,
                        'max_length': 160
                    }
                }
            })
        
        # تهيئة الزاحف
        max_pages = 1 if single_page else config.get('crawling', {}).get('max_pages', 100)
        delay = config.get('crawling', {}).get('delay_seconds', 1)
        respect_robots = config.get('crawling', {}).get('respect_robots_txt', True)
        
        crawler = WebCrawler(
            start_url=url,
            max_pages=max_pages,
            max_depth=depth,
            delay=delay,
            respect_robots_txt=respect_robots,
            verbose=verbose
        )
        
        # بدء الزحف
        click.echo(f"{Fore.YELLOW}جاري زحف الموقع...{Style.RESET_ALL}")
        pages = crawler.crawl()
        
        if not pages:
            click.echo(f"{Fore.RED}لم يتم العثور على أي صفحات للتحليل.{Style.RESET_ALL}")
            return
        
        # تحليل السيو لكل صفحة
        seo_analyzer = SEOAnalyzer(config=config)
        page_speed_analyzer = PageSpeedAnalyzer()
        content_analyzer = ContentAnalyzer()
        image_optimizer = ImageOptimizer()
        link_checker = LinkChecker()
        
        # إعداد تكامل ووردبريس إذا تم تحديده
        if wp_api:
            if not username or not password:
                click.echo(f"{Fore.RED}يجب تحديد اسم المستخدم وكلمة المرور عند استخدام WordPress API{Style.RESET_ALL}")
                return
            
            wp_integration = WordPressIntegration(
                site_url=url,
                username=username,
                password=password
            )
        
        # تحليل كل صفحة تم العثور عليها
        results = {}
        click.echo(f"{Fore.YELLOW}جاري تحليل {len(pages)} صفحة...{Style.RESET_ALL}")
        
        for page_url, page_data in tqdm(pages.items(), desc="تحليل الصفحات"):
            page_result = {}
            
            try:
                # تحليل السيو الأساسي
                page_result['basic_seo'] = seo_analyzer.analyze_page(page_data)
                
                # تحليل سرعة الصفحة
                try:
                    page_result['page_speed'] = page_speed_analyzer.analyze(page_url)
                except Exception as e:
                    logger.warning(f"فشل تحليل سرعة الصفحة {page_url}: {str(e)}")
                    page_result['page_speed'] = {'score': 0, 'error': str(e)}
                
                # تحليل المحتوى
                page_result['content'] = content_analyzer.analyze(page_data)
                
                # تحليل الصور
                page_result['images'] = image_optimizer.analyze_images(page_data)
                
                # تحليل الروابط
                page_result['links'] = link_checker.check_links(page_data)
                
                # حساب النتيجة الإجمالية
                page_result['score'] = seo_analyzer.calculate_overall_score(page_result)
                
                # الحفظ في النتائج
                results[page_url] = page_result
                
                # إصلاح تلقائي إذا تم تفعيله
                if auto_fix:
                    seo_fixer = SEOFixer(config=config)
                    fixes = seo_fixer.fix_issues(page_url, page_result)
                    page_result['fixes'] = fixes
                    
                    # تطبيق التغييرات على ووردبريس إذا تم تحديده
                    if wp_api:
                        wp_integration.apply_fixes(page_url, fixes)
            
            except Exception as e:
                logger.error(f"فشل تحليل الصفحة {page_url}: {str(e)}")
                click.echo(f"{Fore.RED}فشل تحليل الصفحة {page_url}: {str(e)}{Style.RESET_ALL}")
                # إضافة معلومات الخطأ للنتائج
                results[page_url] = {'error': str(e)}
        
        # توليد التقرير
        report_generator = ReportGenerator(config=config)
        
        if export:
            if export == 'json' or export == 'all':
                json_path = os.path.join(results_dir, 'seo_report.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                click.echo(f"{Fore.GREEN}تم حفظ التقرير بتنسيق JSON: {json_path}{Style.RESET_ALL}")
                
            if export == 'pdf' or export == 'all':
                pdf_path = os.path.join(results_dir, 'seo_report.pdf')
                try:
                    report_generator.generate_pdf(results, pdf_path)
                    click.echo(f"{Fore.GREEN}تم إنشاء تقرير PDF: {pdf_path}{Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"فشل إنشاء تقرير PDF: {str(e)}")
                    click.echo(f"{Fore.RED}فشل إنشاء تقرير PDF: {str(e)}{Style.RESET_ALL}")
                
            if export == 'html' or export == 'all':
                html_path = os.path.join(results_dir, 'seo_report.html')
                try:
                    report_generator.generate_html(results, html_path)
                    click.echo(f"{Fore.GREEN}تم إنشاء تقرير HTML: {html_path}{Style.RESET_ALL}")
                except Exception as e:
                    logger.error(f"فشل إنشاء تقرير HTML: {str(e)}")
                    click.echo(f"{Fore.RED}فشل إنشاء تقرير HTML: {str(e)}{Style.RESET_ALL}")
        
        # عرض ملخص النتائج
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        total_issues = sum(len(page.get('basic_seo', {}).get('issues', [])) for page in valid_results.values())
        
        if valid_results:
            avg_score = sum(page.get('score', 0) for page in valid_results.values()) / len(valid_results)
        else:
            avg_score = 0
            
        print("\n" + "=" * 60)
        print_safe(f"{Fore.CYAN}✅ اكتمل التحليل!{Style.RESET_ALL}")
        print_safe(f"📊 تم تحليل {len(results)} صفحة")
        print_safe(f"⚠️ تم اكتشاف {total_issues} مشكلة")
        print_safe(f"🎯 متوسط نتيجة السيو: {avg_score:.1f}/100")
        print_safe(f"⏱️ استغرق التحليل: {format_time(time.time() - start_time)}")
        print_safe(f"📁 تم حفظ النتائج في: {results_dir}")
        print("=" * 60)
    
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء التحليل: {str(e)}")
        click.echo(f"{Fore.RED}خطأ غير متوقع أثناء التحليل: {str(e)}{Style.RESET_ALL}")

@cli.command()
@click.option('--url', required=True, help='رابط الموقع المراد إصلاحه')
@click.option('--report', required=True, help='مسار تقرير JSON الذي تم إنشاؤه سابقاً')
@click.option('--wp-api', is_flag=True, help='استخدام WordPress API للتحسين')
@click.option('--username', help='اسم المستخدم لـ WordPress')
@click.option('--password', help='كلمة المرور لـ WordPress')
def fix(url, report, wp_api, username, password):
    """إصلاح مشاكل السيو استناداً إلى تقرير تم إنشاؤه سابقاً"""
    try:
        if not os.path.exists(report):
            click.echo(f"{Fore.RED}ملف التقرير غير موجود: {report}{Style.RESET_ALL}")
            return
        
        try:
            with open(report, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            click.echo(f"{Fore.RED}خطأ في قراءة ملف التقرير: {str(e)}{Style.RESET_ALL}")
            return
        
        seo_fixer = SEOFixer(config=config)
        
        # إعداد تكامل ووردبريس إذا تم تحديده
        if wp_api:
            if not username or not password:
                click.echo(f"{Fore.RED}يجب تحديد اسم المستخدم وكلمة المرور عند استخدام WordPress API{Style.RESET_ALL}")
                return
            
            wp_integration = WordPressIntegration(
                site_url=url,
                username=username,
                password=password
            )
        
        click.echo(f"{Fore.YELLOW}جاري إصلاح المشاكل...{Style.RESET_ALL}")
        
        fixed_count = 0
        for page_url, page_result in tqdm(results.items(), desc="إصلاح الصفحات"):
            fixes = seo_fixer.fix_issues(page_url, page_result)
            fixed_count += len(fixes)
            
            # تطبيق التغييرات على ووردبريس إذا تم تحديده
            if wp_api:
                wp_integration.apply_fixes(page_url, fixes)
        
        click.echo(f"{Fore.GREEN}✅ تم إصلاح {fixed_count} مشكلة!{Style.RESET_ALL}")
    
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء الإصلاح: {str(e)}")
        click.echo(f"{Fore.RED}خطأ غير متوقع أثناء الإصلاح: {str(e)}{Style.RESET_ALL}")

@cli.command()
@click.option('--url', required=True, help='رابط الموقع المراد إنشاء خريطة الموقع له')
@click.option('--output', default='sitemap.xml', help='مسار حفظ ملف خريطة الموقع')
@click.option('--changefreq', default='weekly', help='تردد التغيير الافتراضي للصفحات')
@click.option('--priority', default=0.5, help='الأولوية الافتراضية للصفحات')
def sitemap(url, output, changefreq, priority):
    """إنشاء ملف خريطة موقع XML"""
    try:
        # التحقق من صحة الرابط
        if not validate_url(url):
            logger.error(f"الرابط غير صالح: {url}")
            click.echo(f"{Fore.RED}الرابط غير صالح: {url}{Style.RESET_ALL}")
            return
        
        # تهيئة الزاحف
        crawler = WebCrawler(
            start_url=url,
            max_pages=config.get('crawling', {}).get('max_pages', 100),
            max_depth=config.get('crawling', {}).get('max_depth', 3),
            delay=config.get('crawling', {}).get('delay_seconds', 1),
            respect_robots_txt=config.get('crawling', {}).get('respect_robots_txt', True)
        )
        
        # بدء الزحف
        click.echo(f"{Fore.YELLOW}جاري زحف الموقع لإنشاء خريطة الموقع...{Style.RESET_ALL}")
        pages = crawler.crawl()
        
        from modules.seo_fixer import SEOFixer
        seo_fixer = SEOFixer(config=config)
        
        # إنشاء خريطة الموقع
        click.echo(f"{Fore.YELLOW}جاري إنشاء خريطة الموقع...{Style.RESET_ALL}")
        sitemap_path = seo_fixer.generate_sitemap(url, list(pages.keys()), output, changefreq, priority)
        
        click.echo(f"{Fore.GREEN}✅ تم إنشاء خريطة الموقع: {sitemap_path}{Style.RESET_ALL}")
    
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء إنشاء خريطة الموقع: {str(e)}")
        click.echo(f"{Fore.RED}خطأ غير متوقع أثناء إنشاء خريطة الموقع: {str(e)}{Style.RESET_ALL}")

@cli.command()
def gui():
    """تشغيل واجهة المستخدم الرسومية (Streamlit)"""
    try:
        click.echo(f"{Fore.YELLOW}جاري تشغيل واجهة المستخدم الرسومية...{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}اضغط Ctrl+C للإيقاف{Style.RESET_ALL}")
        
        # تنفيذ أمر تشغيل Streamlit
        import subprocess
        try:
            subprocess.run(["streamlit", "run", "app.py"])
        except FileNotFoundError:
            click.echo(f"{Fore.RED}خطأ: تأكد من تثبيت Streamlit باستخدام 'pip install streamlit'{Style.RESET_ALL}")
        except KeyboardInterrupt:
            click.echo(f"{Fore.YELLOW}تم إيقاف واجهة المستخدم الرسومية{Style.RESET_ALL}")
    
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء تشغيل واجهة المستخدم الرسومية: {str(e)}")
        click.echo(f"{Fore.RED}خطأ غير متوقع أثناء تشغيل واجهة المستخدم الرسومية: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        print_safe(f"\n{Fore.YELLOW}تم إلغاء العملية بواسطة المستخدم.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        print_safe(f"{Fore.RED}خطأ غير متوقع: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
