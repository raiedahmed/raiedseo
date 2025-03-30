#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة مولد التقارير - مسؤولة عن إنشاء تقارير PDF وHTML من نتائج تحليل السيو

تقوم هذه الوحدة بإنشاء تقارير مفصلة تحتوي على جميع نتائج التحليل
والتوصيات والإحصائيات في تنسيقات مختلفة.
"""

import os
import logging
import json
from datetime import datetime
from urllib.parse import urlparse
from fpdf import FPDF
import matplotlib.pyplot as plt

class ReportGenerator:
    """
    فئة لإنشاء تقارير من نتائج تحليل السيو
    """
    
    def __init__(self, config=None):
        """
        تهيئة مولد التقارير
        
        Args:
            config (dict): إعدادات التطبيق
        """
        self.logger = logging.getLogger('rseo.report_generator')
        self.config = config or {}
        
        # تحميل إعدادات التقارير
        reports_config = self.config.get('reports', {})
        self.company_name = reports_config.get('company_name', '')
        self.company_logo = reports_config.get('company_logo', '')
        self.locale = reports_config.get('locale', 'ar')
        self.include_screenshots = reports_config.get('include_screenshots', True)
    
    def generate_pdf(self, results, output_path):
        """
        توليد تقرير PDF من نتائج التحليل
        
        Args:
            results (dict): نتائج تحليل السيو
            output_path (str): مسار حفظ التقرير
            
        Returns:
            str: مسار التقرير المنشأ
        """
        try:
            # إنشاء ملف PDF
            pdf = FPDF()
            
            # إعداد الخط للغة العربية
            pdf.add_font('Arial', '', 'arial.ttf', uni=True)
            pdf.set_font('Arial', '', 12)
            
            # إضافة صفحة الغلاف
            self._add_cover_page(pdf, results)
            
            # إضافة ملخص النتائج
            self._add_summary_page(pdf, results)
            
            # إضافة صفحات المشاكل والتوصيات
            self._add_issues_pages(pdf, results)
            
            # إضافة صفحات تفاصيل الصفحات
            self._add_pages_details(pdf, results)
            
            # حفظ ملف PDF
            pdf.output(output_path)
            
            self.logger.info(f"تم إنشاء تقرير PDF: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"فشل إنشاء تقرير PDF: {str(e)}")
            return None
    
    def _add_cover_page(self, pdf, results):
        """
        إضافة صفحة الغلاف للتقرير
        
        Args:
            pdf (FPDF): كائن PDF
            results (dict): نتائج التحليل
        """
        # إضافة صفحة جديدة
        pdf.add_page()
        
        # إضافة شعار الشركة إذا كان متاحًا
        if self.company_logo and os.path.exists(self.company_logo):
            pdf.image(self.company_logo, x=10, y=10, w=30)
        
        # عنوان الموقع
        first_url = next(iter(results.keys())) if results else ""
        domain = urlparse(first_url).netloc if first_url else ""
        
        # تاريخ التقرير
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        # العنوان الرئيسي
        pdf.set_font('Arial', '', 24)
        pdf.cell(0, 30, "", ln=True)
        pdf.cell(0, 20, "تقرير تحليل السيو", ln=True, align='C')
        
        # اسم النطاق
        pdf.set_font('Arial', '', 18)
        pdf.cell(0, 20, domain, ln=True, align='C')
        
        # اسم الشركة إذا كان متاحًا
        if self.company_name:
            pdf.set_font('Arial', '', 14)
            pdf.cell(0, 10, f"تم إعداده بواسطة: {self.company_name}", ln=True, align='C')
        
        # إضافة التاريخ
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"تاريخ التقرير: {report_date}", ln=True, align='C')
        
        # ملاحظة
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 60, "", ln=True)
        pdf.multi_cell(0, 10, "يقدم هذا التقرير تحليلًا شاملًا لعناصر تحسين محركات البحث (SEO) في موقعك، مع توصيات لتحسين الأداء والترتيب في نتائج البحث.")
    
    def _add_summary_page(self, pdf, results):
        """
        إضافة صفحة ملخص النتائج
        
        Args:
            pdf (FPDF): كائن PDF
            results (dict): نتائج التحليل
        """
        # إضافة صفحة جديدة
        pdf.add_page()
        
        # العنوان
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, "ملخص نتائج التحليل", ln=True, align='C')
        
        # حساب الإحصائيات
        total_pages = len(results)
        total_issues = sum(len(page.get('basic_seo', {}).get('issues', [])) for page in results.values())
        
        # متوسط النتيجة
        avg_score = sum(page.get('score', 0) for page in results.values()) / total_pages if total_pages else 0
        
        # المعلومات الرئيسية
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"عدد الصفحات المحللة: {total_pages}", ln=True)
        pdf.cell(0, 10, f"إجمالي المشكلات المكتشفة: {total_issues}", ln=True)
        pdf.cell(0, 10, f"متوسط نتيجة السيو: {avg_score:.1f}/100", ln=True)
        
        # إضافة خط فاصل
        pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        pdf.cell(0, 10, "", ln=True)
        
        # توزيع المشكلات حسب الأهمية
        high_issues = sum(1 for page in results.values() 
                        for issue in page.get('basic_seo', {}).get('issues', [])
                        if issue.get('impact') == 'high')
        
        medium_issues = sum(1 for page in results.values() 
                          for issue in page.get('basic_seo', {}).get('issues', [])
                          if issue.get('impact') == 'medium')
        
        low_issues = sum(1 for page in results.values() 
                        for issue in page.get('basic_seo', {}).get('issues', [])
                        if issue.get('impact') == 'low')
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "توزيع المشكلات حسب الأهمية:", ln=True)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"مشكلات عالية الأهمية: {high_issues}", ln=True)
        pdf.cell(0, 10, f"مشكلات متوسطة الأهمية: {medium_issues}", ln=True)
        pdf.cell(0, 10, f"مشكلات منخفضة الأهمية: {low_issues}", ln=True)
        
        # إضافة خط فاصل
        pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        pdf.cell(0, 10, "", ln=True)
        
        # أهم التوصيات
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "أهم التوصيات:", ln=True)
        
        pdf.set_font('Arial', '', 12)
        
        # استخراج أهم 5 توصيات (المشكلات عالية الأهمية)
        top_issues = []
        for page_url, page_data in results.items():
            for issue in page_data.get('basic_seo', {}).get('issues', []):
                if issue.get('impact') == 'high':
                    top_issues.append({
                        'message': issue.get('message', ''),
                        'recommendation': issue.get('recommendation', '')
                    })
        
        # عرض أهم 5 توصيات
        for i, issue in enumerate(top_issues[:5], 1):
            pdf.multi_cell(0, 10, f"{i}. {issue['message']}: {issue['recommendation']}")
    
    def _add_issues_pages(self, pdf, results):
        """
        إضافة صفحات المشاكل والتوصيات
        
        Args:
            pdf (FPDF): كائن PDF
            results (dict): نتائج التحليل
        """
        # تجميع جميع المشكلات
        all_issues = []
        
        for page_url, page_data in results.items():
            for issue in page_data.get('basic_seo', {}).get('issues', []):
                all_issues.append({
                    'url': page_url,
                    'message': issue.get('message', ''),
                    'impact': issue.get('impact', 'medium'),
                    'recommendation': issue.get('recommendation', '')
                })
        
        # ترتيب المشكلات حسب الأهمية
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_issues.sort(key=lambda x: priority_order.get(x['impact'], 3))
        
        # إضافة صفحة جديدة
        pdf.add_page()
        
        # العنوان
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, "المشكلات والتوصيات المفصلة", ln=True, align='C')
        
        # لون لكل مستوى أهمية
        impact_colors = {
            'high': (255, 0, 0),      # أحمر
            'medium': (255, 165, 0),  # برتقالي
            'low': (0, 128, 0)        # أخضر
        }
        
        # عرض كل مشكلة
        for issue in all_issues:
            # مستوى الأهمية
            impact_text = {
                'high': 'عالية',
                'medium': 'متوسطة',
                'low': 'منخفضة'
            }.get(issue['impact'], 'متوسطة')
            
            # عنوان URL مختصر
            url = issue['url']
            if len(url) > 60:
                url = url[:57] + "..."
            
            # عنوان المشكلة
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)  # أسود
            pdf.cell(0, 10, f"المشكلة: {issue['message']}", ln=True)
            
            # عنوان URL
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f"الصفحة: {url}", ln=True)
            
            # مستوى الأهمية
            impact_color = impact_colors.get(issue['impact'], (0, 0, 0))
            pdf.set_text_color(*impact_color)
            pdf.cell(0, 10, f"الأهمية: {impact_text}", ln=True)
            
            # التوصية
            pdf.set_text_color(0, 0, 0)  # أسود
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 10, f"التوصية: {issue['recommendation']}")
            
            # خط فاصل
            pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
            pdf.cell(0, 10, "", ln=True)
            
            # التحقق من الحاجة لصفحة جديدة
            if pdf.get_y() > 250:
                pdf.add_page()
    
    def _add_pages_details(self, pdf, results):
        """
        إضافة صفحات تفاصيل الصفحات
        
        Args:
            pdf (FPDF): كائن PDF
            results (dict): نتائج التحليل
        """
        # إضافة صفحة جديدة
        pdf.add_page()
        
        # العنوان
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, "تفاصيل تحليل الصفحات", ln=True, align='C')
        
        # عرض تفاصيل كل صفحة
        for page_url, page_data in results.items():
            # التحقق من الحاجة لصفحة جديدة
            if pdf.get_y() > 200:
                pdf.add_page()
            
            # عنوان URL
            pdf.set_font('Arial', 'B', 12)
            
            # اختصار URL إذا كان طويلاً
            display_url = page_url
            if len(display_url) > 80:
                display_url = display_url[:77] + "..."
            
            pdf.multi_cell(0, 10, f"URL: {display_url}")
            
            # نتيجة السيو
            score = page_data.get('score', 0)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 10, f"نتيجة السيو: {score}/100", ln=True)
            
            # العنوان والوصف
            title_analysis = page_data.get('basic_seo', {}).get('title', {})
            meta_analysis = page_data.get('basic_seo', {}).get('meta_description', {})
            
            if title_analysis:
                title = title_analysis.get('content', '')
                pdf.multi_cell(0, 10, f"العنوان: {title}")
            
            if meta_analysis:
                description = meta_analysis.get('content', '')
                pdf.multi_cell(0, 10, f"الوصف: {description}")
            
            # عدد المشكلات
            issues_count = len(page_data.get('basic_seo', {}).get('issues', []))
            pdf.cell(0, 10, f"عدد المشكلات: {issues_count}", ln=True)
            
            # سرعة التحميل
            loading_time = page_data.get('page_speed', {}).get('loading_time')
            if loading_time:
                pdf.cell(0, 10, f"زمن التحميل: {loading_time:.2f} ثانية", ln=True)
            
            # عدد الكلمات
            word_count = page_data.get('content', {}).get('word_count', 0)
            pdf.cell(0, 10, f"عدد الكلمات: {word_count}", ln=True)
            
            # إحصائيات الصور
            images_info = page_data.get('images', {})
            if images_info:
                pdf.cell(0, 10, f"عدد الصور: {images_info.get('total_images', 0)}", ln=True)
                
                if images_info.get('images_without_alt', 0) > 0:
                    pdf.cell(0, 10, f"صور بدون alt: {images_info.get('images_without_alt', 0)}", ln=True)
            
            # خط فاصل
            pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
            pdf.cell(0, 10, "", ln=True)
    
    def generate_html(self, results, output_path):
        """
        توليد تقرير HTML من نتائج التحليل
        
        Args:
            results (dict): نتائج تحليل السيو
            output_path (str): مسار حفظ التقرير
            
        Returns:
            str: مسار التقرير المنشأ
        """
        try:
            # الحصول على عنوان النطاق
            first_url = next(iter(results.keys())) if results else ""
            domain = urlparse(first_url).netloc if first_url else ""
            
            # حساب الإحصائيات
            total_pages = len(results)
            total_issues = sum(len(page.get('basic_seo', {}).get('issues', [])) for page in results.values())
            
            # متوسط النتيجة
            avg_score = sum(page.get('score', 0) for page in results.values()) / total_pages if total_pages else 0
            
            # إنشاء محتوى HTML
            html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير تحليل السيو - {domain}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            direction: rtl;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .section {{
            margin: 20px 0;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .issue {{
            margin: 10px 0;
            padding: 15px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .issue-high {{
            border-right: 5px solid #e74c3c;
        }}
        .issue-medium {{
            border-right: 5px solid #f39c12;
        }}
        .issue-low {{
            border-right: 5px solid #2ecc71;
        }}
        .page-details {{
            margin: 15px 0;
            padding: 15px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .progress {{
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            background-color: #4CAF50;
            text-align: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>تقرير تحليل السيو</h1>
        <h2>{domain}</h2>
        <p>تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
    
    <div class="container">
        <div class="section">
            <h2>ملخص النتائج</h2>
            <table>
                <tr>
                    <th>الصفحات المحللة</th>
                    <th>المشكلات المكتشفة</th>
                    <th>متوسط نتيجة السيو</th>
                </tr>
                <tr>
                    <td>{total_pages}</td>
                    <td>{total_issues}</td>
                    <td>{avg_score:.1f}/100</td>
                </tr>
            </table>
            
            <h3>نتيجة السيو الإجمالية</h3>
            <div class="progress">
                <div class="progress-bar" style="width:{avg_score}%">{avg_score:.1f}/100</div>
            </div>
        </div>
        
        <div class="section">
            <h2>المشكلات والتوصيات</h2>
"""
            
            # تجميع جميع المشكلات
            all_issues = []
            
            for page_url, page_data in results.items():
                for issue in page_data.get('basic_seo', {}).get('issues', []):
                    all_issues.append({
                        'url': page_url,
                        'message': issue.get('message', ''),
                        'impact': issue.get('impact', 'medium'),
                        'recommendation': issue.get('recommendation', '')
                    })
            
            # ترتيب المشكلات حسب الأهمية
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            all_issues.sort(key=lambda x: priority_order.get(x['impact'], 3))
            
            # إضافة المشكلات
            for issue in all_issues:
                impact_text = {
                    'high': 'عالية',
                    'medium': 'متوسطة',
                    'low': 'منخفضة'
                }.get(issue['impact'], 'متوسطة')
                
                html_content += f"""
            <div class="issue issue-{issue['impact']}">
                <h3>{issue['message']}</h3>
                <p><strong>الصفحة:</strong> {issue['url']}</p>
                <p><strong>الأهمية:</strong> {impact_text}</p>
                <p><strong>التوصية:</strong> {issue['recommendation']}</p>
            </div>
"""
            
            html_content += """
        </div>
        
        <div class="section">
            <h2>تفاصيل الصفحات</h2>
"""
            
            # إضافة تفاصيل كل صفحة
            for page_url, page_data in results.items():
                score = page_data.get('score', 0)
                
                title_analysis = page_data.get('basic_seo', {}).get('title', {})
                meta_analysis = page_data.get('basic_seo', {}).get('meta_description', {})
                
                title = title_analysis.get('content', '') if title_analysis else ''
                description = meta_analysis.get('content', '') if meta_analysis else ''
                
                issues_count = len(page_data.get('basic_seo', {}).get('issues', []))
                loading_time = page_data.get('page_speed', {}).get('loading_time', 0)
                word_count = page_data.get('content', {}).get('word_count', 0)
                
                html_content += f"""
            <div class="page-details">
                <h3>{page_url}</h3>
                <div class="progress">
                    <div class="progress-bar" style="width:{score}%">{score}/100</div>
                </div>
                <table>
                    <tr>
                        <th>نتيجة السيو</th>
                        <th>عدد المشكلات</th>
                        <th>زمن التحميل</th>
                        <th>عدد الكلمات</th>
                    </tr>
                    <tr>
                        <td>{score}/100</td>
                        <td>{issues_count}</td>
                        <td>{loading_time:.2f} ثانية</td>
                        <td>{word_count}</td>
                    </tr>
                </table>
                <p><strong>العنوان:</strong> {title}</p>
                <p><strong>الوصف:</strong> {description}</p>
            </div>
"""
            
            html_content += """
        </div>
    </div>
</body>
</html>
"""
            
            # حفظ ملف HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"تم إنشاء تقرير HTML: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"فشل إنشاء تقرير HTML: {str(e)}")
            return None
