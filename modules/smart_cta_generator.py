"""
وحدة توليد دعوات العمل الذكية
تستخدم تقنيات الذكاء الاصطناعي لتوليد نصوص تحفيزية مناسبة لنوع المحتوى
"""

import random
from typing import List, Dict, Any, Union


class SmartCTAGenerator:
    """مولد دعوات العمل الذكية يقوم بإنشاء عبارات تحفيزية مناسبة لنوع المحتوى والكلمات المفتاحية"""
    
    def __init__(self):
        """تهيئة المولد"""
        # قوالب العناوين
        self.title_templates = {
            'informational': [
                "دليل شامل: {topic} - كل ما تحتاج معرفته",
                "{topic}: الدليل الكامل خطوة بخطوة",
                "كيف {action}؟ دليلك النهائي لـ {topic}",
                "أفضل استراتيجيات {topic} للمبتدئين في عام {year}",
                "{number} نصيحة احترافية حول {topic} ستغير طريقة {action}",
                "كل ما تحتاج معرفته عن {topic} - دليل {year} المحدث"
            ],
            'commercial': [
                "أفضل {number} {products} لـ {topic} - مراجعة وتقييم",
                "مقارنة أفضل {products} لـ {topic} - الدليل الشامل",
                "كيف تختار أفضل {product} لـ {topic}؟ مقارنة {year}",
                "دليل شراء {product}: كيف تختار الأفضل لاحتياجاتك",
                "مراجعة شاملة: أفضل {products} لـ {action} في {year}",
                "تقييم {number} من أفضل حلول {topic} في السوق - مقارنة شاملة"
            ],
            'navigational': [
                "خدمات {topic} الشاملة - كل ما تحتاج معرفته",
                "دليل استخدام {product} - {number} نصائح لتحقيق أقصى استفادة",
                "كيفية استخدام {product} لـ {action} - دليل المستخدم الكامل",
                "دليل خدمات {topic}: كل ما تحتاج معرفته للبدء",
                "تعرف على منصة {product} - الميزات، الاستخدامات، والإمكانات",
                "كيف تستفيد من خدمات {topic} لتطوير {action}؟"
            ],
            'transactional': [
                "احصل على خصم {number}% على {product} - عرض محدود!",
                "اشترك الآن في {service} واحصل على {benefit} مجاناً",
                "خصم حصري على {product} - اغتنم الفرصة اليوم!",
                "عرض لفترة محدودة: {product} بسعر استثنائي",
                "تخفيضات نهاية الموسم على {product} - وفر حتى {number}%",
                "اطلب {product} الآن واحصل على {benefit} مجاناً"
            ]
        }
        
        # قوالب دعوات العمل للبداية
        self.start_cta_templates = {
            'informational': [
                "هل تريد معرفة المزيد عن {topic}؟ تابع القراءة لاكتشاف أهم النصائح والاستراتيجيات.",
                "تبحث عن دليل شامل حول {topic}؟ سنشرح لك كل ما تحتاج معرفته خطوة بخطوة.",
                "هل تواجه صعوبة في {action}؟ في هذه المقالة سنوضح لك أفضل الطرق للتغلب على هذه التحديات.",
                "إذا كنت مهتمًا بتعلم {topic} بشكل احترافي، فهذا الدليل سيكون مرجعك الأساسي.",
                "اكتشف أحدث الاستراتيجيات في مجال {topic} التي يمكنك تطبيقها فورًا لتحسين نتائجك."
            ],
            'commercial': [
                "هل تبحث عن أفضل {product} لـ {action}؟ لقد قمنا بمراجعة أفضل الخيارات المتاحة في السوق.",
                "قبل أن تستثمر في {product}، تعرف على مقارنتنا الشاملة لأفضل {number} خيارات متاحة في {year}.",
                "إذا كنت تخطط لشراء {product} جديد، فهذا الدليل سيساعدك في اتخاذ القرار الصحيح وتوفير المال.",
                "استكشف معنا أفضل {products} المتوفرة حاليًا للـ {topic} والتي تناسب مختلف الميزانيات والاحتياجات.",
                "قبل أن تتخذ قرار الشراء، تعرف على الفروق الرئيسية بين أشهر {products} في مجال {topic}."
            ],
            'navigational': [
                "تعرف معنا على كيفية الاستفادة القصوى من {product} لتحسين {action} وتحقيق نتائج أفضل.",
                "هل بدأت للتو في استخدام {product}؟ إليك الدليل الشامل لكل الميزات والإمكانيات التي يوفرها.",
                "اكتشف كيف يمكن لـ {product} أن يساعدك في تحقيق أهدافك في مجال {topic} بكفاءة أعلى.",
                "سواء كنت مبتدئًا أو محترفًا، ستجد في هذا الدليل كل ما تحتاجه لإتقان استخدام {product}.",
                "تعلم كيفية تخصيص وضبط إعدادات {product} لتناسب احتياجاتك الخاصة في مجال {topic}."
            ],
            'transactional': [
                "لفترة محدودة: احصل على خصم {number}% عند شرائك {product} اليوم. لا تفوت هذه الفرصة!",
                "العرض ينتهي قريبًا! اشترك الآن في {service} واحصل على {benefit} دون أي تكلفة إضافية.",
                "فرصة ذهبية: اطلب {product} الآن واستفد من عرضنا الحصري لفترة محدودة فقط.",
                "هل أنت جاهز للارتقاء بمستوى {action}؟ استثمر في {product} بأفضل الأسعار المتاحة الآن.",
                "عرض خاص للقراء فقط: استخدم الكود الترويجي '{code}' واحصل على خصم فوري عند شرائك {product}."
            ]
        }
        
        # قوالب دعوات العمل للوسط
        self.middle_cta_templates = {
            'informational': [
                "ألق نظرة على هذه الاستراتيجية لـ {action} والتي حققت نتائج مذهلة لعملائنا.",
                "جرب هذه التقنية في {topic} وشاهد كيف ستتضاعف نتائجك بسرعة مذهلة.",
                "اطلع على دراسة الحالة أدناه لترى كيف حققت شركة {company} نجاحًا في {topic}.",
                "الآن بعد أن فهمت أساسيات {topic}، دعنا نتعمق أكثر في تقنيات {action} المتقدمة.",
                "تذكر: الاستمرارية هي مفتاح النجاح في {topic}. استمر في تطبيق هذه النصائح بانتظام لرؤية النتائج."
            ],
            'commercial': [
                "قارن بين الميزات الرئيسية لكل {product} في الجدول أدناه لاتخاذ القرار المناسب لاحتياجاتك.",
                "شاهد تقييمات المستخدمين الحقيقيين لـ {product} وكيف ساعدهم في تحسين {action}.",
                "تصفح مجموعة صور {product} أدناه لمعرفة التفاصيل الدقيقة قبل الشراء.",
                "استكشف كيف يمكن لميزات {product} المتقدمة أن توفر لك الوقت والجهد في {action}.",
                "هل تبحث عن {product} بميزانية محدودة؟ تحقق من توصياتنا لأفضل القيمة مقابل المال."
            ],
            'navigational': [
                "تعرف على الخطوات التفصيلية لإعداد {product} للحصول على أفضل أداء لـ {topic}.",
                "شاهد الفيديو التوضيحي أدناه لفهم كيفية استخدام ميزة {feature} في {product}.",
                "استكشف واجهة {product} بالتفصيل من خلال الصور التوضيحية في القسم التالي.",
                "اطلع على الأسئلة الشائعة حول {product} لفهم كيفية التعامل مع المشكلات الشائعة.",
                "هل تريد استكشاف المزيد من إمكانيات {product}؟ تحقق من الموارد الإضافية في نهاية المقالة."
            ],
            'transactional': [
                "لا تتردد - المخزون محدود! اطلب {product} الآن وسيصلك خلال {number} أيام.",
                "احجز الآن واحصل على خصم إضافي بقيمة {number}٪ - استخدم الكود: {code}.",
                "انضم إلى أكثر من {number} عميل سعيد اشتروا {product} وحققوا نتائج مذهلة في {topic}.",
                "ماذا تنتظر؟ اشترك في {service} اليوم واستمتع بـ {benefit} لمدة {number} أيام مجانًا.",
                "اطلع على شهادات العملاء أدناه واكتشف كيف غير {product} طريقة {action} لديهم."
            ]
        }
        
        # قوالب دعوات العمل للنهاية
        self.end_cta_templates = {
            'informational': [
                "هل استفدت من هذا الدليل حول {topic}؟ شاركه مع زملائك الذين قد يستفيدون منه أيضًا.",
                "لتعميق معرفتك في مجال {topic}، سجل في ندوتنا عبر الإنترنت القادمة - انقر هنا للتسجيل.",
                "هل لديك أسئلة حول {topic}؟ اترك تعليقًا أدناه وسنجيب عليك في أقرب وقت ممكن.",
                "للمزيد من المعلومات المفصلة حول {topic}، اشترك في نشرتنا الإخبارية لتصلك آخر المستجدات.",
                "تحميل دليلنا المجاني الشامل عن {topic} للاحتفاظ به كمرجع دائم - اضغط على الزر أدناه."
            ],
            'commercial': [
                "جاهز لتجربة أفضل {product} في {year}؟ اطلبه الآن واستمتع بخصم {number}٪ لفترة محدودة.",
                "استفد من ضمان استرداد الأموال لمدة {number} يومًا عند شراء {product} - اطلب الآن بدون مخاطر.",
                "قم بترقية تجربتك في {topic} اليوم - اشترِ {product} واحصل على {benefit} كهدية مجانية.",
                "لا تفوت العرض - استخدم الكود '{code}' عند الدفع للحصول على خصم إضافي على {product}.",
                "احصل على النتائج التي تستحقها - اطلب {product} الآن وابدأ في تحسين {action} خلال أيام."
            ],
            'navigational': [
                "هل تحتاج إلى مساعدة في إعداد {product}؟ تواصل مع فريق الدعم على الرقم {phone}.",
                "استكشف المزيد من خدماتنا المتعلقة بـ {topic} - انقر على 'استكشاف الخدمات' أدناه.",
                "سجل الآن في حساب تجريبي مجاني لـ {product} واكتشف كيف يمكنه تحسين {action}.",
                "تفضل بزيارة مركز المساعدة الخاص بنا للعثور على إجابات لجميع أسئلتك حول {product}.",
                "هل أنت جاهز للبدء؟ تواصل معنا اليوم لجدولة جلسة تدريبية مجانية حول كيفية استخدام {product}."
            ],
            'transactional': [
                "اطلب الآن! استخدم الكود '{code}' للحصول على خصم {number}٪ + شحن مجاني على {product}.",
                "العرض ينتهي الليلة! احصل على {product} بخصم {number}٪ - السعر سيعود إلى وضعه الطبيعي غدًا.",
                "كن أول من يحصل على {product} الجديد - اطلب مسبقًا اليوم واحصل على {benefit} حصرية.",
                "احصل على {product} الآن بأقساط شهرية ميسرة تبدأ من ${price} فقط - بدون فوائد!",
                "اطلب {product} الآن واحصل على {benefit} بقيمة ${value} مجانًا - العرض ينتهي عند نفاد الكمية."
            ]
        }
        
        # الكلمات الحركية الشائعة للمواضيع
        self.topic_actions = {
            'تسويق': ['التسويق', 'زيادة المبيعات', 'جذب العملاء'],
            'سيو': ['تحسين موقعك', 'رفع ترتيب موقعك', 'زيادة الزيارات'],
            'تصميم': ['تصميم', 'إنشاء', 'تطوير'],
            'تطوير': ['برمجة', 'تطوير', 'إنشاء'],
            'تعليم': ['تعلم', 'دراسة', 'إتقان'],
            'ريادة': ['بدء مشروعك', 'تنمية أعمالك', 'زيادة أرباحك'],
            'صحة': ['تحسين صحتك', 'العناية بصحتك', 'المحافظة على لياقتك'],
            'تقنية': ['استخدام التكنولوجيا', 'تطبيق التقنيات', 'الاستفادة من التقنيات الحديثة']
        }
    
    def _get_action_for_topic(self, topic: str) -> str:
        """استخراج فعل حركي مناسب للموضوع"""
        for key, actions in self.topic_actions.items():
            if key in topic:
                return random.choice(actions)
        return "تحسين نتائجك"
    
    def _format_template(self, template: str, topic: str, keywords: List[str]) -> str:
        """تنسيق قالب باستخدام الموضوع والكلمات المفتاحية"""
        action = self._get_action_for_topic(topic)
        product = keywords[0] if keywords else topic
        products = topic
        year = datetime.now().year
        number = random.choice([3, 5, 7, 10, 15, 20])
        company = "الشركة الرائدة"
        feature = f"ميزة {topic} المتقدمة"
        service = f"خدمة {topic}"
        benefit = f"ميزة إضافية"
        code = f"RSEO{year}"
        phone = "+123456789"
        price = random.choice([99, 149, 199, 249, 299])
        value = random.choice([49, 99, 149, 199])
        
        return template.format(
            topic=topic,
            action=action,
            product=product,
            products=products,
            year=year,
            number=number,
            company=company,
            feature=feature,
            service=service,
            benefit=benefit,
            code=code,
            phone=phone,
            price=price,
            value=value
        )
    
    def generate_title(self, content_type: str, topic: str, keywords: List[str]) -> str:
        """توليد عنوان جذاب ومحسن للسيو حسب نوع المحتوى والموضوع"""
        templates = self.title_templates.get(content_type, self.title_templates['informational'])
        template = random.choice(templates)
        return self._format_template(template, topic, keywords)
    
    def generate_start_cta(self, content_type: str, topic: str, keywords: List[str]) -> str:
        """توليد دعوة عمل للبداية حسب نوع المحتوى والموضوع"""
        templates = self.start_cta_templates.get(content_type, self.start_cta_templates['informational'])
        template = random.choice(templates)
        return self._format_template(template, topic, keywords)
    
    def generate_middle_ctas(self, content_type: str, topic: str, keywords: List[str], num: int = 3) -> List[str]:
        """توليد عدة دعوات عمل للوسط حسب نوع المحتوى والموضوع"""
        templates = self.middle_cta_templates.get(content_type, self.middle_cta_templates['informational'])
        selected_templates = random.sample(templates, min(num, len(templates)))
        return [self._format_template(template, topic, keywords) for template in selected_templates]
    
    def generate_end_cta(self, content_type: str, topic: str, keywords: List[str]) -> str:
        """توليد دعوة عمل للنهاية حسب نوع المحتوى والموضوع"""
        templates = self.end_cta_templates.get(content_type, self.end_cta_templates['informational'])
        template = random.choice(templates)
        return self._format_template(template, topic, keywords)
    
    def generate_multiple_ctas(self, content_type: str, topic: str, num_ctas: int = 3, keywords: List[str] = None) -> Dict[str, Any]:
        """توليد مجموعة متكاملة من دعوات العمل لمقال كامل"""
        if keywords is None:
            keywords = []
        
        title = self.generate_title(content_type, topic, keywords)
        start_cta = self.generate_start_cta(content_type, topic, keywords)
        middle_ctas = self.generate_middle_ctas(content_type, topic, keywords, num_ctas - 2)
        end_cta = self.generate_end_cta(content_type, topic, keywords)
        
        return {
            "title": title,
            "start": start_cta,
            "middle": middle_ctas,
            "end": end_cta
        }
