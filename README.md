# أداة RSEO - أداة شاملة لتحليل وتحسين السيو

## نظرة عامة
RSEO هي أداة متكاملة مطورة بلغة Python لفحص وتحسين السيو (SEO) للمواقع الإلكترونية. تقوم الأداة بتحليل عناصر تحسين محركات البحث المختلفة وتقديم توصيات وإصلاحات تلقائية للمشاكل المكتشفة.

## المميزات الرئيسية
- **فحص شامل للسيو**: تحليل عناصر الـ On-page SEO والـ Technical SEO
- **تحليل مفصل لعناصر الصفحة**: العناوين، الأوصاف، الترويسات، الصور، الروابط، إلخ
- **اكتشاف المشاكل تلقائياً**: العناوين المفقودة، الصور بدون نص بديل، الروابط المكسورة
- **إصلاح تلقائي للمشاكل**: توليد المحتوى، ضغط الصور، إنشاء خرائط المواقع
- **تكامل مع WordPress**: باستخدام REST API لتعديل المحتوى
- **تقارير مفصلة**: إنشاء تقارير PDF شاملة لنتائج الفحص والتوصيات
- **واجهات متعددة**: CLI وواجهة ويب بسيطة (Flask/Streamlit)

## متطلبات النظام
- Python 3.8 أو أحدث
- المكتبات المذكورة في ملف `requirements.txt`
- مفتاح API لـ OpenAI (اختياري للميزات المتقدمة)

## التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/yourusername/rseo.git
cd rseo

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد ملف البيئة
cp .env.example .env
# قم بتعديل ملف .env بإضافة مفاتيح API الخاصة بك
```

## الاستخدام

### واجهة سطر الأوامر (CLI)
```bash
# فحص موقع كامل
python rseo.py analyze --url https://example.com

# فحص صفحة محددة
python rseo.py analyze --url https://example.com/page --single-page

# تحليل موقع WordPress
python rseo.py analyze --url https://example.com --wp-api --username user --password pass

# تصدير تقرير PDF
python rseo.py analyze --url https://example.com --export pdf
```

### واجهة الويب
```bash
# تشغيل واجهة Streamlit
streamlit run app.py

# تشغيل خادم Flask
python webapp.py
```

## الهيكل التنظيمي
```
rseo/
├── rseo.py                 # النقطة الرئيسية للتشغيل
├── requirements.txt        # متطلبات المكتبات
├── .env.example            # نموذج ملف البيئة
├── config.yaml             # ملف الإعدادات
├── app.py                  # واجهة Streamlit
├── webapp.py               # خادم Flask
├── modules/
│   ├── analyzer.py         # وحدة تحليل السيو
│   ├── crawler.py          # زاحف الويب
│   ├── page_speed.py       # تحليل سرعة الصفحة
│   ├── content_analyzer.py # تحليل المحتوى
│   ├── image_optimizer.py  # محسن الصور
│   ├── link_checker.py     # فاحص الروابط
│   ├── seo_fixer.py        # مصلح مشاكل السيو
│   ├── report_generator.py # منشئ التقارير
│   └── wp_integration.py   # تكامل WordPress
└── utils/
    ├── helpers.py          # دوال مساعدة
    ├── config_loader.py    # محمل الإعدادات
    ├── logger.py           # مسجل الأحداث
    └── ai_utils.py         # أدوات الذكاء الاصطناعي
```

## المساهمة
نرحب بمساهماتكم! يرجى إرسال طلبات السحب أو فتح قضايا جديدة لاقتراح التحسينات.

## الترخيص
هذا المشروع مرخص تحت [MIT License](LICENSE).
