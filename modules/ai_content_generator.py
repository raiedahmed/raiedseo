#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - مولد المحتوى بالذكاء الاصطناعي
توليد محتوى عالي الجودة لتحسين السيو باستخدام نماذج اللغة المتقدمة
"""

import os
import json
import openai
import re
import time
from utils.logger import get_logger

class AIContentGenerator:
    """مولد المحتوى بالذكاء الاصطناعي - يستخدم نماذج اللغة المتقدمة لإنشاء محتوى عالي الجودة لتحسين السيو"""

    def __init__(self, api_key=None):
        """تهيئة مولد المحتوى بالذكاء الاصطناعي

        Args:
            api_key (str, optional): مفتاح API لـ OpenAI. الافتراضي None (يستخدم مفتاح البيئة).
        """
        self.logger = get_logger(__name__)
        
        # استخدام مفتاح API المقدم أو البحث عنه في متغيرات البيئة
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        # أنواع المحتوى المدعومة
        self.content_types = {
            'article': {
                'name': 'مقال',
                'min_words': 500,
                'max_words': 1500,
                'structure': ['مقدمة', 'فقرات المحتوى الرئيسي', 'خاتمة']
            },
            'blog_post': {
                'name': 'تدوينة',
                'min_words': 300,
                'max_words': 1000,
                'structure': ['عنوان جذاب', 'مقدمة', 'نقاط المحتوى', 'خاتمة', 'دعوة للتفاعل']
            },
            'product_description': {
                'name': 'وصف منتج',
                'min_words': 100,
                'max_words': 300,
                'structure': ['وصف موجز', 'المميزات والفوائد', 'المواصفات الفنية', 'دعوة للشراء']
            },
            'meta_description': {
                'name': 'وصف تعريفي',
                'min_words': 25,
                'max_words': 50,
                'structure': ['وصف موجز وجذاب للصفحة']
            },
            'landing_page': {
                'name': 'صفحة هبوط',
                'min_words': 200,
                'max_words': 500,
                'structure': ['عنوان رئيسي', 'عرض القيمة', 'المميزات والفوائد', 'شهادات', 'دعوة للتفاعل']
            }
        }
    
    def generate(self, prompt, keywords=None, content_type='article', language='ar', tone='professional', word_count=None):
        """توليد محتوى باستخدام الذكاء الاصطناعي

        Args:
            prompt (str): وصف المحتوى المطلوب
            keywords (list, optional): الكلمات المفتاحية للتضمين. الافتراضي None.
            content_type (str, optional): نوع المحتوى. الافتراضي 'article'.
            language (str, optional): لغة المحتوى. الافتراضي 'ar'.
            tone (str, optional): نبرة المحتوى. الافتراضي 'professional'.
            word_count (int, optional): عدد الكلمات المطلوبة. الافتراضي None.

        Returns:
            str: المحتوى المولد
        """
        if not self.api_key:
            self.logger.error("مفتاح API لـ OpenAI غير محدد")
            return "خطأ: مفتاح API لـ OpenAI غير محدد. يرجى تحديث الإعدادات."
        
        # التحقق من نوع المحتوى
        if content_type not in self.content_types:
            self.logger.warning(f"نوع المحتوى '{content_type}' غير مدعوم. استخدام 'article' كنوع افتراضي.")
            content_type = 'article'
        
        # تعيين عدد الكلمات بناءً على نوع المحتوى إذا لم يتم تحديده
        if not word_count:
            type_info = self.content_types[content_type]
            word_count = (type_info['min_words'] + type_info['max_words']) // 2
        
        # إعداد قائمة الكلمات المفتاحية
        keywords_str = ""
        if keywords and len(keywords) > 0:
            keywords_str = "الكلمات المفتاحية التي يجب تضمينها: " + ", ".join(keywords)
        
        # تحديد اللغة
        language_full = "العربية" if language == 'ar' else "الإنجليزية" if language == 'en' else language
        
        # إعداد توجيهات النظام
        system_message = f"""
        أنت خبير في كتابة محتوى عالي الجودة لتحسين السيو (SEO).
        مهمتك هي إنشاء محتوى من نوع "{self.content_types[content_type]['name']}" باللغة {language_full} بنبرة {tone}.
        
        اتبع هذه الإرشادات:
        1. قم بإنشاء محتوى فريد وأصلي بحوالي {word_count} كلمة.
        2. استخدم بنية جيدة تشمل: {", ".join(self.content_types[content_type]['structure'])}
        3. ضمّن الكلمات المفتاحية بشكل طبيعي بما يتناسب مع السياق.
        4. استخدم عناوين فرعية وقوائم لتحسين قابلية القراءة.
        5. اكتب بأسلوب سلس وجذاب يناسب نبرة {tone}.
        6. تأكد من أن المحتوى مفيد ويقدم قيمة للقارئ.
        7. استخدم جمل وفقرات قصيرة لتحسين قابلية القراءة.
        
        المحتوى النهائي يجب أن يكون جاهزاً للنشر مباشرة.
        """
        
        # إعداد رسالة المستخدم
        user_message = f"""
        موضوع المحتوى: {prompt}
        
        {keywords_str}
        
        نوع المحتوى: {self.content_types[content_type]['name']}
        عدد الكلمات المطلوب: حوالي {word_count} كلمة
        اللغة: {language_full}
        النبرة: {tone}
        """
        
        try:
            self.logger.info(f"جاري توليد محتوى من نوع '{content_type}' بـ {word_count} كلمة")
            
            # استدعاء واجهة API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # أو نموذج آخر مناسب
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2048,
                top_p=1.0,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # استخراج المحتوى المولد
            generated_content = response.choices[0].message['content'].strip()
            
            # تنظيف المحتوى
            generated_content = self._clean_content(generated_content)
            
            return generated_content
        
        except Exception as e:
            self.logger.error(f"خطأ في توليد المحتوى: {str(e)}")
            return f"حدث خطأ أثناء توليد المحتوى: {str(e)}"
    
    def improve_content(self, original_content, suggestions=None, keywords=None):
        """تحسين محتوى موجود

        Args:
            original_content (str): المحتوى الأصلي
            suggestions (list, optional): اقتراحات للتحسين. الافتراضي None.
            keywords (list, optional): الكلمات المفتاحية للتضمين. الافتراضي None.

        Returns:
            str: المحتوى المحسن
        """
        if not self.api_key:
            self.logger.error("مفتاح API لـ OpenAI غير محدد")
            return "خطأ: مفتاح API لـ OpenAI غير محدد. يرجى تحديث الإعدادات."
        
        # إعداد الاقتراحات
        suggestions_str = ""
        if suggestions and len(suggestions) > 0:
            suggestions_str = "اقتراحات للتحسين:\n" + "\n".join([f"- {s}" for s in suggestions])
        
        # إعداد قائمة الكلمات المفتاحية
        keywords_str = ""
        if keywords and len(keywords) > 0:
            keywords_str = "الكلمات المفتاحية التي يجب تضمينها: " + ", ".join(keywords)
        
        # إعداد توجيهات النظام
        system_message = """
        أنت خبير في تحسين المحتوى لـ SEO. مهمتك هي تحسين المحتوى المقدم مع الحفاظ على الهدف والمعنى الأصلي.
        
        اتبع هذه الإرشادات:
        1. تحسين جودة الكتابة وسلاسة النص.
        2. تنظيم المحتوى باستخدام عناوين فرعية وقوائم لتحسين قابلية القراءة.
        3. تضمين الكلمات المفتاحية بشكل طبيعي إذا تم تقديمها.
        4. إضافة معلومات قيمة حيثما أمكن.
        5. التأكد من خلو النص من الأخطاء النحوية والإملائية.
        6. تحسين العناوين لجذب الانتباه.
        7. تقصير الجمل والفقرات الطويلة لتحسين قابلية القراءة.
        
        المحتوى النهائي يجب أن يكون جاهزاً للنشر مباشرة، وأفضل من النسخة الأصلية.
        """
        
        # إعداد رسالة المستخدم
        user_message = f"""
        المحتوى الأصلي:
        ```
        {original_content}
        ```
        
        {suggestions_str}
        
        {keywords_str}
        
        يرجى تحسين هذا المحتوى مع مراعاة الاقتراحات والكلمات المفتاحية المذكورة.
        """
        
        try:
            self.logger.info("جاري تحسين المحتوى المقدم")
            
            # استدعاء واجهة API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # أو نموذج آخر مناسب
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2048,
                top_p=1.0,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # استخراج المحتوى المحسن
            improved_content = response.choices[0].message['content'].strip()
            
            # تنظيف المحتوى
            improved_content = self._clean_content(improved_content)
            
            return improved_content
        
        except Exception as e:
            self.logger.error(f"خطأ في تحسين المحتوى: {str(e)}")
            return f"حدث خطأ أثناء تحسين المحتوى: {str(e)}"
    
    def generate_meta_tags(self, page_content, url=None, target_keywords=None):
        """توليد العلامات الوصفية للصفحة (العنوان والوصف)

        Args:
            page_content (str): محتوى الصفحة
            url (str, optional): عنوان URL للصفحة. الافتراضي None.
            target_keywords (list, optional): الكلمات المفتاحية المستهدفة. الافتراضي None.

        Returns:
            dict: العلامات الوصفية المولدة (العنوان والوصف)
        """
        if not self.api_key:
            self.logger.error("مفتاح API لـ OpenAI غير محدد")
            return {
                "title": "",
                "description": "",
                "error": "مفتاح API لـ OpenAI غير محدد. يرجى تحديث الإعدادات."
            }
        
        # تحضير محتوى الصفحة (اقتصاص إذا كان طويلاً جداً)
        content_preview = page_content[:4000] + "..." if len(page_content) > 4000 else page_content
        
        # إعداد قائمة الكلمات المفتاحية
        keywords_str = ""
        if target_keywords and len(target_keywords) > 0:
            keywords_str = "الكلمات المفتاحية المستهدفة: " + ", ".join(target_keywords)
        
        # إعداد توجيهات النظام
        system_message = """
        أنت خبير في تحسين السيو. مهمتك هي إنشاء علامات وصفية (meta tags) مثالية لصفحة ويب.
        
        يجب أن تصمم:
        1. عنوان الصفحة (title): 50-60 حرف، جذاب وواضح، يتضمن الكلمات المفتاحية الرئيسية.
        2. وصف الصفحة (meta description): 150-160 حرف، يلخص محتوى الصفحة ويشجع على النقر.
        
        اتبع هذه الإرشادات:
        - ضمّن الكلمات المفتاحية المستهدفة في بداية العنوان إذا أمكن.
        - اجعل الوصف يحتوي على دعوة للتفاعل.
        - تأكد أن العنوان والوصف يعكسان محتوى الصفحة بدقة.
        - اكتب بصيغة نشطة وجذابة.
        - تجنب التكرار بين العنوان والوصف.
        
        قدم النتائج بتنسيق JSON يحتوي على title و description.
        """
        
        # إعداد رسالة المستخدم
        user_message = f"""
        محتوى الصفحة:
        ```
        {content_preview}
        ```
        
        {keywords_str}
        {"URL الصفحة: " + url if url else ""}
        
        يرجى إنشاء عنوان ووصف مثاليين لهذه الصفحة لتحسين ظهورها في نتائج البحث.
        قدم النتائج بتنسيق JSON فقط بهذا الشكل: {{"title": "العنوان المقترح", "description": "الوصف المقترح"}}
        """
        
        try:
            self.logger.info("جاري توليد العلامات الوصفية للصفحة")
            
            # استدعاء واجهة API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # أو نموذج آخر مناسب
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # استخراج الاستجابة
            result_text = response.choices[0].message['content'].strip()
            
            # محاولة تحليل JSON
            try:
                # استخراج JSON من النص إذا كان محاطًا بنص إضافي
                json_match = re.search(r'({[\s\S]*})', result_text)
                if json_match:
                    result_text = json_match.group(1)
                
                result = json.loads(result_text)
                
                # التأكد من وجود العناصر المطلوبة
                if 'title' not in result or 'description' not in result:
                    raise ValueError("النتيجة لا تحتوي على العناصر المطلوبة")
                
                return result
            
            except json.JSONDecodeError:
                # إذا فشل تحليل JSON، حاول استخراج العنوان والوصف من النص
                title_match = re.search(r'["\']title["\']\s*:\s*["\']([^"\']+)["\']', result_text)
                desc_match = re.search(r'["\']description["\']\s*:\s*["\']([^"\']+)["\']', result_text)
                
                title = title_match.group(1) if title_match else ""
                description = desc_match.group(1) if desc_match else ""
                
                return {
                    "title": title,
                    "description": description,
                    "note": "تم استخراج البيانات من النص بدلاً من JSON"
                }
        
        except Exception as e:
            self.logger.error(f"خطأ في توليد العلامات الوصفية: {str(e)}")
            return {
                "title": "",
                "description": "",
                "error": str(e)
            }
    
    def suggest_improvements(self, content, content_type=None, target_keywords=None):
        """اقتراح تحسينات للمحتوى من منظور السيو

        Args:
            content (str): المحتوى المراد تحليله
            content_type (str, optional): نوع المحتوى. الافتراضي None.
            target_keywords (list, optional): الكلمات المفتاحية المستهدفة. الافتراضي None.

        Returns:
            dict: اقتراحات التحسين
        """
        if not self.api_key:
            self.logger.error("مفتاح API لـ OpenAI غير محدد")
            return {
                "suggestions": [],
                "error": "مفتاح API لـ OpenAI غير محدد. يرجى تحديث الإعدادات."
            }
        
        # تحضير محتوى الصفحة (اقتصاص إذا كان طويلاً جداً)
        content_preview = content[:4000] + "..." if len(content) > 4000 else content
        
        # إعداد قائمة الكلمات المفتاحية
        keywords_str = ""
        if target_keywords and len(target_keywords) > 0:
            keywords_str = "الكلمات المفتاحية المستهدفة: " + ", ".join(target_keywords)
        
        # إعداد توجيهات النظام
        system_message = """
        أنت خبير في تحليل وتحسين المحتوى لأغراض السيو. مهمتك هي تحليل المحتوى المقدم وتقديم اقتراحات محددة لتحسينه.
        
        قم بتحليل المحتوى من هذه الجوانب:
        1. استخدام الكلمات المفتاحية وتوزيعها
        2. بنية المحتوى وتنظيمه (العناوين والفقرات)
        3. جودة المحتوى وقيمته للقارئ
        4. قابلية القراءة والأسلوب
        5. العناصر المفقودة أو التي يمكن إضافتها
        
        قدم اقتراحات محددة وعملية، وليست عامة أو مبهمة. كل اقتراح يجب أن يكون:
        - محدداً وقابلاً للتنفيذ
        - مرتبطاً بتحسين ترتيب الصفحة في محركات البحث
        - مشروحاً بشكل موجز
        
        قدم النتائج بتنسيق JSON يحتوي على مصفوفة من الاقتراحات، وتقييم عام لجودة المحتوى من منظور السيو.
        """
        
        # إعداد رسالة المستخدم
        user_message = f"""
        المحتوى للتحليل:
        ```
        {content_preview}
        ```
        
        {keywords_str}
        {"نوع المحتوى: " + content_type if content_type else ""}
        
        يرجى تحليل هذا المحتوى وتقديم اقتراحات محددة لتحسينه من منظور السيو.
        قدم النتائج بتنسيق JSON فقط بهذا الشكل: {{"score": 85, "suggestions": ["اقتراح 1", "اقتراح 2", ...]}}
        حيث score هي نتيجة من 0 إلى 100 تقيّم جودة المحتوى الحالية من منظور السيو.
        """
        
        try:
            self.logger.info("جاري تحليل المحتوى واقتراح تحسينات")
            
            # استدعاء واجهة API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # أو نموذج آخر مناسب
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # استخراج الاستجابة
            result_text = response.choices[0].message['content'].strip()
            
            # محاولة تحليل JSON
            try:
                # استخراج JSON من النص إذا كان محاطًا بنص إضافي
                json_match = re.search(r'({[\s\S]*})', result_text)
                if json_match:
                    result_text = json_match.group(1)
                
                result = json.loads(result_text)
                
                # التأكد من وجود العناصر المطلوبة
                if 'suggestions' not in result:
                    raise ValueError("النتيجة لا تحتوي على اقتراحات")
                
                # إضافة التاريخ والوقت إلى النتيجة
                result['timestamp'] = int(time.time())
                
                return result
            
            except json.JSONDecodeError:
                # إذا فشل تحليل JSON، حاول استخراج الاقتراحات من النص
                suggestions = re.findall(r'\d+\.\s*([^\n]+)', result_text)
                
                return {
                    "score": 0,  # غير معروف
                    "suggestions": suggestions if suggestions else ["تعذر استخراج اقتراحات محددة"],
                    "timestamp": int(time.time()),
                    "note": "تم استخراج البيانات من النص بدلاً من JSON"
                }
        
        except Exception as e:
            self.logger.error(f"خطأ في تحليل المحتوى: {str(e)}")
            return {
                "score": 0,
                "suggestions": [],
                "timestamp": int(time.time()),
                "error": str(e)
            }
    
    def _clean_content(self, content):
        """تنظيف المحتوى المولد

        Args:
            content (str): المحتوى المراد تنظيفه

        Returns:
            str: المحتوى بعد التنظيف
        """
        # إزالة علامات تنسيق زائدة
        content = re.sub(r'^```[a-z]*\n', '', content)
        content = re.sub(r'\n```$', '', content)
        
        # تنظيف الأسطر الفارغة المتكررة
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
