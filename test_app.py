#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
تطبيق اختبار شامل لعرض لوحة التحكم الجديدة لنظام RSEO
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import os
import json
import random

app = Flask(__name__)
app.secret_key = 'rseo-dashboard-advanced-secret-key'

# إنشاء المجلدات المطلوبة إذا لم تكن موجودة
os.makedirs(os.path.join('static', 'css'), exist_ok=True)
os.makedirs(os.path.join('static', 'js'), exist_ok=True)
os.makedirs(os.path.join('data'), exist_ok=True)

# إضافة متغير now لجميع القوالب
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# وظائف مساعدة
def generate_dummy_data():
    """توليد بيانات وهمية للعرض"""
    # بيانات تتبع التصنيف
    keywords = [
        "تحسين محركات البحث", "السيو التقني", "بناء الروابط الخلفية", 
        "تحليل المنافسين", "استراتيجية المحتوى", "تحسين التجربة", 
        "استراتيجية السيو", "تحسين سرعة الموقع", "تصميم المواقع", "كلمات مفتاحية"
    ]
    
    domains = ["example.com", "mysite.org", "digitalmarketing.net", "seoarabic.com"]
    
    # توليد تاريخ تصنيف عشوائي
    ranking_history = {}
    for keyword in keywords[:5]:
        history = []
        position = random.randint(15, 30)
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d")
            change = random.randint(-3, 5)
            position = max(1, position - change)
            
            history.append({
                "date": date,
                "position": position,
                "change": change,
                "url": f"https://example.com/page{random.randint(1, 5)}"
            })
        
        ranking_history[keyword] = history
    
    # توليد بيانات الروابط الخلفية
    backlinks = []
    source_domains = [
        "blog.example.org", "news.example.net", "techblog.example.io", "marketing.example.co",
        "digital.example.com", "seo.example.info", "arabictech.example.net", "media.example.org"
    ]
    
    for i in range(20):
        domain = random.choice(source_domains)
        backlinks.append({
            "source": domain,
            "title": f"مقال {i+1} حول تحسين محركات البحث والسيو",
            "url": f"https://{domain}/post-{random.randint(100, 999)}",
            "target_url": f"https://example.com/page{random.randint(1, 5)}",
            "anchor_text": random.choice(["تحسين السيو", "محركات البحث", "استراتيجية المحتوى", "تصميم المواقع"]),
            "type": "dofollow" if random.random() > 0.3 else "nofollow",
            "da": random.randint(20, 55),
            "date_found": (datetime.now() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d")
        })
    
    # حفظ البيانات في ملفات
    data_dir = os.path.join('data')
    os.makedirs(data_dir, exist_ok=True)
    
    with open(os.path.join(data_dir, 'ranking_history.json'), 'w', encoding='utf-8') as f:
        json.dump(ranking_history, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(data_dir, 'backlinks.json'), 'w', encoding='utf-8') as f:
        json.dump(backlinks, f, ensure_ascii=False, indent=2)
    
    return {
        "keywords": keywords,
        "domains": domains,
        "ranking_history": ranking_history,
        "backlinks": backlinks
    }

def load_dummy_data():
    """تحميل البيانات الوهمية من الملفات"""
    data = {
        "keywords": [],
        "domains": [],
        "ranking_history": {},
        "backlinks": []
    }
    
    data_dir = os.path.join('data')
    
    # تحميل بيانات تتبع التصنيف
    ranking_history_path = os.path.join(data_dir, 'ranking_history.json')
    if os.path.exists(ranking_history_path):
        with open(ranking_history_path, 'r', encoding='utf-8') as f:
            data["ranking_history"] = json.load(f)
            data["keywords"] = list(data["ranking_history"].keys())
    
    # تحميل بيانات الروابط الخلفية
    backlinks_path = os.path.join(data_dir, 'backlinks.json')
    if os.path.exists(backlinks_path):
        with open(backlinks_path, 'r', encoding='utf-8') as f:
            data["backlinks"] = json.load(f)
            domains = set()
            for backlink in data["backlinks"]:
                if "target_url" in backlink:
                    domains.add(backlink["target_url"].split('/')[2])
            data["domains"] = list(domains)
    
    return data

# التحقق من وجود البيانات الوهمية عند بدء التشغيل
if not os.path.exists(os.path.join('data', 'ranking_history.json')):
    dummy_data = generate_dummy_data()
else:
    dummy_data = load_dummy_data()

# المسارات
@app.route('/')
def index():
    """الصفحة الرئيسية - لوحة المعلومات"""
    # إحصائيات عامة
    stats = {
        "keywords_count": len(dummy_data["keywords"]),
        "domains_count": len(dummy_data["domains"]),
        "backlinks_count": len(dummy_data["backlinks"]),
        "top10_count": sum(1 for keyword, history in dummy_data["ranking_history"].items() 
                         if history[-1]["position"] <= 10),
        "dofollow_count": sum(1 for backlink in dummy_data["backlinks"] 
                            if backlink["type"] == "dofollow")
    }
    
    # أفضل 5 كلمات مفتاحية
    top_keywords = []
    for keyword, history in dummy_data["ranking_history"].items():
        if history:
            top_keywords.append({
                "keyword": keyword,
                "position": history[-1]["position"],
                "change": history[-1]["change"],
                "url": history[-1]["url"]
            })
    
    top_keywords = sorted(top_keywords, key=lambda x: x["position"])[:5]
    
    # أحدث 5 روابط
    recent_backlinks = sorted(dummy_data["backlinks"], 
                             key=lambda x: x["date_found"], 
                             reverse=True)[:5]
    
    # بيانات تطور التصنيف
    ranking_trend = {}
    if dummy_data["ranking_history"]:
        # اختيار كلمة عشوائية للعرض
        sample_keyword = list(dummy_data["ranking_history"].keys())[0]
        history = dummy_data["ranking_history"][sample_keyword]
        
        dates = [entry["date"] for entry in history]
        positions = [entry["position"] for entry in history]
        
        ranking_trend = {
            "keyword": sample_keyword,
            "dates": dates,
            "positions": positions
        }
    
    # بيانات نمو الروابط
    backlink_growth = {}
    if dummy_data["backlinks"]:
        # تجميع الروابط حسب الشهر
        months = {}
        for backlink in dummy_data["backlinks"]:
            date = datetime.strptime(backlink["date_found"], "%Y-%m-%d")
            month_key = date.strftime("%Y-%m")
            
            if month_key not in months:
                months[month_key] = 0
            
            months[month_key] += 1
        
        # ترتيب الأشهر
        sorted_months = sorted(months.items())
        
        backlink_growth = {
            "months": [item[0] for item in sorted_months],
            "counts": [item[1] for item in sorted_months]
        }
    
    return render_template('dashboard.html', 
                          stats=stats,
                          top_keywords=top_keywords,
                          recent_backlinks=recent_backlinks,
                          ranking_trend=ranking_trend,
                          backlink_growth=backlink_growth)

@app.route('/rank-tracker')
def rank_tracker():
    """صفحة تتبع التصنيف"""
    return render_template('rank_tracker.html', 
                          keywords=dummy_data["keywords"],
                          domains=dummy_data["domains"])

@app.route('/track-keyword', methods=['POST'])
def track_keyword():
    """متابعة كلمة مفتاحية"""
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        domain = request.form.get('domain')
        
        if not keyword or not domain:
            flash('يرجى إدخال الكلمة المفتاحية والنطاق', 'error')
            return redirect(url_for('rank_tracker'))
        
        # محاكاة متابعة الكلمة المفتاحية (في التطبيق الفعلي ستكون هناك عملية فعلية)
        flash(f'تم بدء متابعة الكلمة المفتاحية "{keyword}" للنطاق {domain}', 'success')
        return redirect(url_for('rank_history', keyword=keyword, domain=domain))
    
    return redirect(url_for('rank_tracker'))

@app.route('/rank-history/<keyword>/<domain>')
def rank_history(keyword, domain):
    """صفحة تاريخ التصنيف"""
    days = request.args.get('days', 30, type=int)
    
    # الحصول على بيانات الكلمة المفتاحية
    history_data = []
    if keyword in dummy_data["ranking_history"]:
        history_data = dummy_data["ranking_history"][keyword][-days:]
    
    return render_template('rank_history.html', 
                          keyword=keyword, 
                          domain=domain, 
                          days=days,
                          history=history_data)

@app.route('/backlinks')
def backlinks():
    """صفحة تحليل الروابط الخلفية"""
    return render_template('backlink_analyzer.html',
                          domains=dummy_data["domains"])

@app.route('/analyze-backlinks', methods=['POST'])
def analyze_backlinks():
    """تحليل الروابط الخلفية"""
    if request.method == 'POST':
        domain = request.form.get('domain')
        max_results = int(request.form.get('max_results', 100))
        
        if not domain:
            flash('يرجى إدخال النطاق', 'error')
            return redirect(url_for('backlinks'))
        
        # محاكاة تحليل الروابط الخلفية
        filtered_backlinks = dummy_data["backlinks"][:max_results]
        
        # تجميع الإحصائيات
        stats = {
            "total": len(filtered_backlinks),
            "dofollow": sum(1 for b in filtered_backlinks if b["type"] == "dofollow"),
            "nofollow": sum(1 for b in filtered_backlinks if b["type"] == "nofollow"),
            "unique_domains": len(set(b["source"] for b in filtered_backlinks)),
            "avg_da": sum(b["da"] for b in filtered_backlinks) / len(filtered_backlinks) if filtered_backlinks else 0
        }
        
        # توزيع جودة الروابط
        quality_distribution = {
            "high": sum(1 for b in filtered_backlinks if b["da"] >= 40),
            "medium": sum(1 for b in filtered_backlinks if 20 <= b["da"] < 40),
            "low": sum(1 for b in filtered_backlinks if b["da"] < 20)
        }
        
        return render_template('backlink_results.html',
                              domain=domain,
                              backlinks=filtered_backlinks,
                              stats=stats,
                              quality_distribution=quality_distribution)
    
    return redirect(url_for('backlinks'))

@app.route('/api/keywords')
def api_keywords():
    """واجهة برمجة تطبيقات لبيانات الكلمات المفتاحية"""
    domain = request.args.get('domain')
    days = request.args.get('days', 30, type=int)
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # إعداد البيانات للرد
    result = {}
    for keyword, history in dummy_data["ranking_history"].items():
        result[keyword] = history[-days:]
    
    return jsonify(result)

@app.route('/api/backlinks')
def api_backlinks():
    """واجهة برمجة تطبيقات لبيانات الروابط الخلفية"""
    domain = request.args.get('domain')
    limit = request.args.get('limit', 100, type=int)
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    return jsonify(dummy_data["backlinks"][:limit])

@app.route('/api/dashboard')
def api_dashboard():
    """واجهة برمجة تطبيقات لبيانات لوحة المعلومات"""
    # تجميع البيانات الإحصائية
    stats = {
        "keywords_count": len(dummy_data["keywords"]),
        "domains_count": len(dummy_data["domains"]),
        "backlinks_count": len(dummy_data["backlinks"]),
        "top10_count": sum(1 for keyword, history in dummy_data["ranking_history"].items() 
                         if history[-1]["position"] <= 10)
    }
    
    return jsonify(stats)

@app.route('/regenerate-data')
def regenerate_data():
    """إعادة توليد البيانات الوهمية للعرض"""
    global dummy_data
    dummy_data = generate_dummy_data()
    flash('تم إعادة توليد البيانات بنجاح', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    """معالجة خطأ 404"""
    return render_template('404.html'), 404

if __name__ == '__main__':
    print("تشغيل تطبيق اختبار RSEO المتطور...")
    print("قم بزيارة:  http://127.0.0.1:5000/")
    app.run(debug=True)
