#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
وحدة محلل السيو - المكون الرئيسي للتحليل الشامل لعناصر السيو في الصفحة

تقوم هذه الوحدة بتحليل مختلف عناصر السيو في صفحة الويب وتوفير تقييم شامل
للمشاكل والتوصيات استنادًا إلى أفضل الممارسات.
"""

import re
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class SEOAnalyzer:
    """فئة تحليل السيو الرئيسية للتحقق من عناصر SEO المختلفة وتقييمها"""
    
    def __init__(self, config=None):
        """
        تهيئة محلل السيو
        
        Args:
            config (dict): إعدادات التحليل من ملف التكوين
        """
        self.config = config or {}
        self.logger = logging.getLogger('rseo.analyzer')
        
        # تحميل حدود التقييم من الإعدادات
        self.title_min_length = self.config.get('seo_analysis', {}).get('title', {}).get('min_length', 30)
        self.title_max_length = self.config.get('seo_analysis', {}).get('title', {}).get('max_length', 60)
        self.meta_desc_min_length = self.config.get('seo_analysis', {}).get('meta_description', {}).get('min_length', 70)
        self.meta_desc_max_length = self.config.get('seo_analysis', {}).get('meta_description', {}).get('max_length', 160)
        self.min_words = self.config.get('seo_analysis', {}).get('content', {}).get('min_words', 300)
    
    def analyze_page(self, page_data):
        """
        تحليل صفحة ويب لعناصر السيو
        
        Args:
            page_data (dict): بيانات الصفحة المحتوية على HTML والعنوان URL
            
        Returns:
            dict: نتائج التحليل متضمنة المشاكل والتوصيات
        """
        url = page_data.get('url', '')
        html_content = page_data.get('html', '')
        
        if not html_content:
            self.logger.error(f"لا يوجد محتوى HTML للتحليل: {url}")
            return {
                'url': url,
                'status': 'error',
                'message': 'لا يوجد محتوى HTML للتحليل',
                'issues': []
            }
        
        # تحليل HTML باستخدام BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # تجميع النتائج
        result = {
            'url': url,
            'status': 'success',
            'issues': [],
            'score': 0
        }
        
        # تحليل العنوان
        title_analysis = self._analyze_title(soup, url)
        result['title'] = title_analysis
        if title_analysis.get('issues'):
            result['issues'].extend(title_analysis['issues'])
        
        # تحليل الوصف
        meta_analysis = self._analyze_meta_description(soup, url)
        result['meta_description'] = meta_analysis
        if meta_analysis.get('issues'):
            result['issues'].extend(meta_analysis['issues'])
        
        # تحليل الترويسات
        headings_analysis = self._analyze_headings(soup, url)
        result['headings'] = headings_analysis
        if headings_analysis.get('issues'):
            result['issues'].extend(headings_analysis['issues'])
        
        # تحليل المحتوى
        content_analysis = self._analyze_content(soup, url)
        result['content'] = content_analysis
        if content_analysis.get('issues'):
            result['issues'].extend(content_analysis['issues'])
        
        # تحليل الصور
        images_analysis = self._analyze_images(soup, url)
        result['images'] = images_analysis
        if images_analysis.get('issues'):
            result['issues'].extend(images_analysis['issues'])
        
        # تحليل روبوتس وخريطة الموقع
        robots_analysis = self._check_robots_sitemap(url)
        result['robots_sitemap'] = robots_analysis
        if robots_analysis.get('issues'):
            result['issues'].extend(robots_analysis['issues'])
        
        # تحليل الإشارات الهيكلية (Structured Data)
        structured_data = self._analyze_structured_data(soup, url)
        result['structured_data'] = structured_data
        if structured_data.get('issues'):
            result['issues'].extend(structured_data['issues'])
        
        # حساب النتيجة الإجمالية
        result['score'] = self._calculate_page_score(result)
        
        return result
    
    def _analyze_title(self, soup, url):
        """تحليل عنوان الصفحة"""
        title_tag = soup.find('title')
        result = {
            'exists': title_tag is not None,
            'issues': []
        }
        
        if not title_tag:
            result['issues'].append({
                'type': 'error',
                'message': 'لا يوجد عنوان للصفحة',
                'impact': 'high',
                'recommendation': 'أضف عنوانًا للصفحة يصف محتواها بشكل دقيق'
            })
            return result
        
        title_text = title_tag.text.strip()
        result['content'] = title_text
        result['length'] = len(title_text)
        
        # التحقق من طول العنوان
        if len(title_text) < self.title_min_length:
            result['issues'].append({
                'type': 'warning',
                'message': f'عنوان الصفحة قصير جدًا ({len(title_text)} حرف)',
                'impact': 'medium',
                'recommendation': f'زيادة طول العنوان ليكون بين {self.title_min_length} و {self.title_max_length} حرف'
            })
        elif len(title_text) > self.title_max_length:
            result['issues'].append({
                'type': 'warning',
                'message': f'عنوان الصفحة طويل جدًا ({len(title_text)} حرف)',
                'impact': 'medium',
                'recommendation': f'تقليل طول العنوان ليكون بين {self.title_min_length} و {self.title_max_length} حرف'
            })
        
        # التحقق من تكرار الكلمات المفتاحية
        word_count = {}
        for word in re.findall(r'\w+', title_text.lower()):
            if len(word) > 2:  # تجاهل الكلمات القصيرة
                word_count[word] = word_count.get(word, 0) + 1
        
        repeated_keywords = [word for word, count in word_count.items() if count > 1]
        if repeated_keywords:
            result['issues'].append({
                'type': 'info',
                'message': f'تكرار الكلمات في العنوان: {", ".join(repeated_keywords)}',
                'impact': 'low',
                'recommendation': 'تجنب تكرار الكلمات في العنوان لتحسين جاذبيته'
            })
        
        # التحقق من وجود اسم الموقع في العنوان
        domain = urlparse(url).netloc
        site_name = domain.split('.')[0] if '.' in domain else domain
        
        if site_name.lower() not in title_text.lower():
            result['issues'].append({
                'type': 'info',
                'message': 'لا يوجد اسم الموقع في العنوان',
                'impact': 'low',
                'recommendation': 'ضع في اعتبارك إضافة اسم الموقع في نهاية العنوان (مثال: عنوان الصفحة | اسم الموقع)'
            })
        
        return result
    
    def _analyze_meta_description(self, soup, url):
        """تحليل الوصف التعريفي للصفحة"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        result = {
            'exists': meta_desc is not None,
            'issues': []
        }
        
        if not meta_desc or not meta_desc.get('content'):
            result['issues'].append({
                'type': 'error',
                'message': 'لا يوجد وصف تعريفي للصفحة',
                'impact': 'high',
                'recommendation': 'أضف وصفًا تعريفيًا للصفحة يلخص محتواها بشكل جذاب'
            })
            return result
        
        description = meta_desc['content'].strip()
        result['content'] = description
        result['length'] = len(description)
        
        # التحقق من طول الوصف
        if len(description) < self.meta_desc_min_length:
            result['issues'].append({
                'type': 'warning',
                'message': f'الوصف التعريفي قصير جدًا ({len(description)} حرف)',
                'impact': 'medium',
                'recommendation': f'زيادة طول الوصف ليكون بين {self.meta_desc_min_length} و {self.meta_desc_max_length} حرف'
            })
        elif len(description) > self.meta_desc_max_length:
            result['issues'].append({
                'type': 'warning',
                'message': f'الوصف التعريفي طويل جدًا ({len(description)} حرف)',
                'impact': 'medium',
                'recommendation': f'تقليل طول الوصف ليكون بين {self.meta_desc_min_length} و {self.meta_desc_max_length} حرف'
            })
        
        # التحقق من وجود كلمات دعوة للعمل
        call_to_actions = ['اقرأ', 'اكتشف', 'تعلم', 'تصفح', 'اشترك', 'حمل', 'جرب', 'شاهد']
        has_cta = any(cta.lower() in description.lower() for cta in call_to_actions)
        
        if not has_cta:
            result['issues'].append({
                'type': 'info',
                'message': 'لا يوجد دعوة للعمل في الوصف',
                'impact': 'low',
                'recommendation': 'أضف كلمات حث على العمل لتحسين نسبة النقر (مثل: اكتشف، تعلم، اقرأ، إلخ)'
            })
        
        return result
    
    def _analyze_headings(self, soup, url):
        """تحليل الترويسات في الصفحة"""
        headings = {
            'h1': soup.find_all('h1'),
            'h2': soup.find_all('h2'),
            'h3': soup.find_all('h3'),
            'h4': soup.find_all('h4'),
            'h5': soup.find_all('h5'),
            'h6': soup.find_all('h6')
        }
        
        result = {
            'counts': {tag: len(elements) for tag, elements in headings.items()},
            'issues': []
        }
        
        # التحقق من وجود H1
        if not headings['h1']:
            result['issues'].append({
                'type': 'error',
                'message': 'لا يوجد عنوان رئيسي H1 في الصفحة',
                'impact': 'high',
                'recommendation': 'أضف عنوانًا رئيسيًا H1 يعكس الموضوع الرئيسي للصفحة'
            })
        elif len(headings['h1']) > 1:
            result['issues'].append({
                'type': 'warning',
                'message': f'يوجد أكثر من عنوان H1 في الصفحة ({len(headings["h1"])})',
                'impact': 'medium',
                'recommendation': 'استخدم عنوانًا رئيسيًا H1 واحدًا فقط لكل صفحة'
            })
        
        # التحقق من تسلسل الترويسات
        if headings['h1'] and not headings['h2'] and (headings['h3'] or headings['h4'] or headings['h5'] or headings['h6']):
            result['issues'].append({
                'type': 'warning',
                'message': 'تخطي مستويات الترويسات (الانتقال من H1 إلى H3/H4 مباشرة)',
                'impact': 'medium',
                'recommendation': 'حافظ على تسلسل هرمي صحيح للترويسات: H1 → H2 → H3 → ...'
            })
        
        # جمع محتوى الترويسات للتحليل
        all_headings_content = []
        for tag, elements in headings.items():
            for heading in elements:
                text = heading.text.strip()
                if text:
                    all_headings_content.append({
                        'tag': tag,
                        'content': text,
                        'length': len(text)
                    })
        
        result['headings_content'] = all_headings_content
        
        # التحقق من طول الترويسات
        for heading in all_headings_content:
            if heading['length'] < 10:
                result['issues'].append({
                    'type': 'info',
                    'message': f'عنوان {heading["tag"]} قصير جدًا: "{heading["content"]}"',
                    'impact': 'low',
                    'recommendation': 'استخدم عناوين أكثر وصفية وتفصيلية'
                })
            elif heading['length'] > 70:
                result['issues'].append({
                    'type': 'info',
                    'message': f'عنوان {heading["tag"]} طويل جدًا: "{heading["content"][:50]}..."',
                    'impact': 'low',
                    'recommendation': 'اجعل العناوين قصيرة ومركزة (أقل من 70 حرفًا)'
                })
        
        return result
    
    def _analyze_content(self, soup, url):
        """تحليل محتوى الصفحة"""
        # استخراج النص المرئي من الصفحة (استبعاد السكريبت والستايل)
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header']):
            script_or_style.decompose()
        
        main_content = soup.find('main') or soup.find('article') or soup.body
        
        if not main_content:
            main_content = soup
        
        text = main_content.get_text(separator=" ")
        words = re.findall(r'\w+', text)
        
        result = {
            'word_count': len(words),
            'issues': []
        }
        
        # التحقق من عدد الكلمات
        if len(words) < self.min_words:
            result['issues'].append({
                'type': 'warning',
                'message': f'محتوى الصفحة قصير جدًا ({len(words)} كلمة)',
                'impact': 'medium',
                'recommendation': f'أضف المزيد من المحتوى النصي ليصل إلى {self.min_words} كلمة على الأقل'
            })
        
        # التحقق من وجود فقرات طويلة
        paragraphs = main_content.find_all('p')
        long_paragraphs = 0
        
        for p in paragraphs:
            p_words = len(re.findall(r'\w+', p.get_text()))
            if p_words > 100:  # أكثر من 100 كلمة تعتبر فقرة طويلة
                long_paragraphs += 1
        
        if long_paragraphs > 0:
            result['issues'].append({
                'type': 'info',
                'message': f'يوجد {long_paragraphs} فقرة طويلة في الصفحة',
                'impact': 'low',
                'recommendation': 'قسم الفقرات الطويلة إلى فقرات أقصر لتحسين القراءة'
            })
        
        # التحقق من تباعد الفقرات والترويسات
        if len(paragraphs) < 3 and len(words) > 300:
            result['issues'].append({
                'type': 'info',
                'message': 'عدد الفقرات قليل بالنسبة لحجم المحتوى',
                'impact': 'low',
                'recommendation': 'قسم المحتوى إلى فقرات أكثر مع استخدام العناوين الفرعية'
            })
        
        return result
    
    def _analyze_images(self, soup, url):
        """تحليل الصور في الصفحة"""
        images = soup.find_all('img')
        
        result = {
            'count': len(images),
            'missing_alt': 0,
            'empty_alt': 0,
            'large_images': 0,
            'issues': []
        }
        
        for img in images:
            # تجاهل الصور الصغيرة والأيقونات
            if img.get('width') and img.get('height'):
                try:
                    if int(img['width']) < 50 or int(img['height']) < 50:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # التحقق من وجود النص البديل
            if not img.has_attr('alt'):
                result['missing_alt'] += 1
            elif img['alt'].strip() == '':
                result['empty_alt'] += 1
            
            # التحقق من حجم الصورة (إذا كان متوفرًا في الوسوم)
            if img.has_attr('src') and (img['src'].endswith('.jpg') or img['src'].endswith('.jpeg') or img['src'].endswith('.png')):
                if img.has_attr('width') and img.has_attr('height'):
                    try:
                        width = int(img['width'])
                        height = int(img['height'])
                        if width > 1000 or height > 1000:
                            result['large_images'] += 1
                    except (ValueError, TypeError):
                        pass
        
        # إضافة المشاكل المكتشفة
        if result['missing_alt'] > 0:
            result['issues'].append({
                'type': 'error',
                'message': f'{result["missing_alt"]} صورة بدون نص بديل',
                'impact': 'high',
                'recommendation': 'أضف نصًا بديلًا وصفيًا لجميع الصور المهمة للوصول وتحسين السيو'
            })
        
        if result['empty_alt'] > 0:
            result['issues'].append({
                'type': 'warning',
                'message': f'{result["empty_alt"]} صورة بنص بديل فارغ',
                'impact': 'medium',
                'recommendation': 'أضف نصًا بديلًا وصفيًا بدلاً من تركه فارغًا'
            })
        
        if result['large_images'] > 0:
            result['issues'].append({
                'type': 'warning',
                'message': f'{result["large_images"]} صورة كبيرة الحجم',
                'impact': 'medium',
                'recommendation': 'ضغط وتحسين حجم الصور الكبيرة لتحسين سرعة التحميل'
            })
        
        return result
    
    def _check_robots_sitemap(self, url):
        """التحقق من وجود ملف robots.txt وsitemap.xml"""
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        robots_url = f"{base_url}/robots.txt"
        sitemap_url = f"{base_url}/sitemap.xml"
        
        import requests
        
        result = {
            'robots_exists': False,
            'sitemap_exists': False,
            'sitemap_in_robots': False,
            'issues': []
        }
        
        # التحقق من وجود ملف robots.txt
        try:
            robots_response = requests.get(robots_url, timeout=10)
            result['robots_exists'] = robots_response.status_code == 200
            
            if result['robots_exists']:
                # التحقق من وجود إشارة لخريطة الموقع في robots.txt
                result['sitemap_in_robots'] = 'sitemap:' in robots_response.text.lower()
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من ملف robots.txt: {str(e)}")
        
        # التحقق من وجود ملف sitemap.xml
        try:
            sitemap_response = requests.get(sitemap_url, timeout=10)
            result['sitemap_exists'] = sitemap_response.status_code == 200
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من ملف sitemap.xml: {str(e)}")
        
        # إضافة المشاكل المكتشفة
        if not result['robots_exists']:
            result['issues'].append({
                'type': 'warning',
                'message': 'لا يوجد ملف robots.txt',
                'impact': 'medium',
                'recommendation': 'إنشاء ملف robots.txt لتوجيه محركات البحث'
            })
        
        if not result['sitemap_exists']:
            result['issues'].append({
                'type': 'warning',
                'message': 'لا يوجد ملف sitemap.xml',
                'impact': 'medium',
                'recommendation': 'إنشاء خريطة موقع XML لتسهيل فهرسة محركات البحث للموقع'
            })
        
        if result['robots_exists'] and not result['sitemap_in_robots']:
            result['issues'].append({
                'type': 'info',
                'message': 'ملف robots.txt لا يشير إلى خريطة الموقع',
                'impact': 'low',
                'recommendation': 'أضف إشارة لخريطة الموقع في ملف robots.txt: Sitemap: https://example.com/sitemap.xml'
            })
        
        return result
    
    def _analyze_structured_data(self, soup, url):
        """تحليل البيانات المنظمة (Schema.org)"""
        structured_data_tags = soup.find_all('script', type='application/ld+json')
        
        result = {
            'exists': len(structured_data_tags) > 0,
            'count': len(structured_data_tags),
            'types': [],
            'issues': []
        }
        
        # التحقق من وجود بيانات منظمة
        if not structured_data_tags:
            result['issues'].append({
                'type': 'info',
                'message': 'لا توجد بيانات منظمة (Structured Data)',
                'impact': 'low',
                'recommendation': 'أضف بيانات منظمة باستخدام Schema.org لتحسين ظهور النتائج المميزة'
            })
            return result
        
        # تحليل أنواع البيانات المنظمة
        import json
        
        for script in structured_data_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    result['types'].append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            result['types'].append(item['@type'])
            except (json.JSONDecodeError, AttributeError):
                result['issues'].append({
                    'type': 'error',
                    'message': 'خطأ في تنسيق البيانات المنظمة JSON-LD',
                    'impact': 'medium',
                    'recommendation': 'تصحيح بنية JSON في البيانات المنظمة'
                })
        
        return result
    
    def _calculate_page_score(self, result):
        """حساب نتيجة سيو الصفحة بناءً على المشاكل المكتشفة"""
        # نظام التقييم البسيط: 100 نقطة بداية، ثم خصم النقاط حسب المشاكل
        score = 100
        
        # تصنيف المشاكل حسب التأثير
        high_impact = sum(1 for issue in result['issues'] if issue.get('impact') == 'high')
        medium_impact = sum(1 for issue in result['issues'] if issue.get('impact') == 'medium')
        low_impact = sum(1 for issue in result['issues'] if issue.get('impact') == 'low')
        
        # خصم النقاط بناءً على تأثير المشكلة
        score -= high_impact * 10  # -10 نقاط لكل مشكلة عالية التأثير
        score -= medium_impact * 5  # -5 نقاط لكل مشكلة متوسطة التأثير
        score -= low_impact * 2  # -2 نقاط لكل مشكلة منخفضة التأثير
        
        # التأكد من أن النتيجة بين 0 و 100
        return max(0, min(100, score))
    
    def calculate_overall_score(self, results):
        """
        حساب النتيجة الإجمالية لصفحة بناءً على جميع التحليلات
        
        Args:
            results (dict): نتائج تحليل السيو للصفحة
            
        Returns:
            int: نتيجة إجمالية بين 0 و 100
        """
        # وزن لكل نوع من التحليل
        weights = {
            'basic_seo': 0.4,      # السيو الأساسي
            'page_speed': 0.2,     # سرعة الصفحة
            'content': 0.2,        # جودة المحتوى
            'images': 0.1,         # تحسين الصور
            'links': 0.1           # جودة الروابط
        }
        
        overall_score = 0
        total_weight = 0
        
        # حساب معدل موزون بشكل آمن
        for key, weight in weights.items():
            score = None
            
            # محاولة الحصول على النتيجة
            if key in results:
                if isinstance(results[key], dict) and 'score' in results[key]:
                    score = results[key]['score']
            elif key == 'basic_seo' and 'score' in results:
                # إذا كانت النتيجة الأساسية موجودة مباشرة
                score = results['score']
            
            # إضافة النتيجة إذا كانت متاحة
            if score is not None:
                overall_score += score * weight
                total_weight += weight
        
        # في حالة عدم وجود أي نتائج أو أوزان
        if total_weight == 0:
            return 0
            
        # تعديل النتيجة النهائية بناء على الأوزان المتاحة
        adjusted_score = overall_score / total_weight if total_weight > 0 else 0
        
        return round(adjusted_score)
