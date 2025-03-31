#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import random
import re
import time
from datetime import datetime, timedelta
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class YouTubeSEO:
    """فئة لتحليل وتحسين سيو اليوتيوب"""
    
    def __init__(self, api_key=None):
        """تهيئة فئة تحسين سيو اليوتيوب"""
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.search_url = "https://www.youtube.com/results"
    
    def analyze_keywords(self, topic, language="ar", use_api=False):
        """تحليل الكلمات المفتاحية للفيديوهات بناءً على موضوع معين"""
        if use_api and self.api_key:
            # استخدام YouTube API للبحث عن الكلمات المفتاحية
            return self._analyze_keywords_api(topic, language)
        else:
            # استخدام محاكاة لبيانات الكلمات المفتاحية
            return self._simulate_keyword_data(topic, language)
    
    def _simulate_keyword_data(self, topic, language="ar"):
        """محاكاة بيانات الكلمات المفتاحية للعرض التوضيحي"""
        # أمثلة على الكلمات المفتاحية بناءً على الموضوع
        base_keywords = {
            "تحسين السيو": [
                "تحسين محركات البحث", "سيو للمبتدئين", "تعلم السيو", 
                "تحسين ظهور الموقع", "ترتيب الموقع في جوجل"
            ],
            "برمجة": [
                "تعلم البرمجة", "البرمجة للمبتدئين", "تعلم جافا سكريبت",
                "برمجة تطبيقات الويب", "البرمجة بلغة بايثون"
            ],
            "التسويق الإلكتروني": [
                "استراتيجيات التسويق", "التسويق عبر مواقع التواصل", "تحسين معدل التحويل",
                "التسويق بالمحتوى", "جذب العملاء المحتملين"
            ]
        }
        
        # إذا كان الموضوع ليس في القائمة المعدة مسبقًا، نستخدم كلمات عامة
        keywords = []
        if topic in base_keywords:
            keywords = base_keywords[topic]
        else:
            # توليد كلمات مفتاحية بناءً على الموضوع المدخل
            keywords = [
                f"{topic} للمبتدئين", f"تعلم {topic}", f"دليل {topic}",
                f"أساسيات {topic}", f"كيفية {topic}", f"شرح {topic}",
                f"{topic} خطوة بخطوة", f"نصائح {topic}", f"أفضل {topic}"
            ]
        
        # إنشاء بيانات الكلمات المفتاحية مع بيانات تنافسية ومعدل البحث
        keyword_data = []
        for kw in keywords:
            # توليد بيانات وهمية
            search_volume = random.randint(1000, 50000)
            competition = round(random.uniform(0.1, 0.9), 2)
            cpc = round(random.uniform(0.5, 5.0), 2)
            trend = random.choice(["up", "down", "stable"])
            
            keyword_data.append({
                "keyword": kw,
                "search_volume": search_volume,
                "competition": competition,
                "cpc": cpc,
                "trend": trend,
                "score": round((search_volume / 1000) * (1 - competition) * 10, 1)
            })
        
        # ترتيب الكلمات المفتاحية حسب الدرجة
        keyword_data.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "topic": topic,
            "language": language,
            "keywords": keyword_data,
            "related_topics": ["فيديوهات تعليمية", "محتوى عربي", "دروس أونلاين"]
        }
    
    def analyze_video_ranking(self, video_url, keywords, use_api=False):
        """تحليل تصنيف فيديو معين للكلمات المفتاحية المحددة"""
        video_id = self._extract_video_id(video_url)
        if not video_id:
            return {"error": "رابط الفيديو غير صالح"}
        
        if use_api and self.api_key:
            # استخدام YouTube API لتحليل تصنيف الفيديو
            return self._analyze_ranking_api(video_id, keywords)
        else:
            # استخدام محاكاة لبيانات تصنيف الفيديو
            return self._simulate_ranking_data(video_id, keywords)
    
    def _extract_video_id(self, video_url):
        """استخراج معرف الفيديو من رابط يوتيوب"""
        pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, video_url)
        return match.group(1) if match else None
    
    def _simulate_ranking_data(self, video_id, keywords):
        """محاكاة بيانات تصنيف الفيديو للعرض التوضيحي"""
        video_title = "عنوان الفيديو التوضيحي"
        channel_name = "اسم القناة التوضيحي"
        
        # تحويل الكلمات المفتاحية إلى قائمة إذا كانت نصًا
        if isinstance(keywords, str):
            keywords_list = [k.strip() for k in keywords.split("\n") if k.strip()]
        elif isinstance(keywords, list):
            keywords_list = keywords
        else:
            keywords_list = []
        
        # بيانات تصنيف وهمية لكل كلمة مفتاحية
        keyword_rankings = []
        for keyword in keywords_list:
            if not keyword.strip():
                continue
                
            # توليد بيانات وهمية
            position = random.randint(1, 100)
            position_30d_ago = position + random.randint(-20, 20)
            position_change = position_30d_ago - position
            
            keyword_rankings.append({
                "keyword": keyword.strip(),
                "position": position,
                "position_30d_ago": position_30d_ago,
                "position_change": position_change,
                "search_volume": random.randint(500, 20000),
                "in_title": keyword.lower() in video_title.lower(),
                "in_description": random.choice([True, False]),
                "top_competitors": [
                    {"title": f"فيديو منافس 1 لـ {keyword}", "position": random.randint(1, 5)},
                    {"title": f"فيديو منافس 2 لـ {keyword}", "position": random.randint(1, 10)}
                ]
            })
        
        # ترتيب الكلمات المفتاحية حسب الترتيب
        keyword_rankings.sort(key=lambda x: x["position"])
        
        # بيانات الفيديو الوهمية
        video_data = {
            "video_id": video_id,
            "title": video_title,
            "channel": channel_name,
            "views": random.randint(1000, 1000000),
            "likes": random.randint(100, 10000),
            "comments": random.randint(10, 1000),
            "keywords": keyword_rankings,
            "estimated_traffic": sum(k["search_volume"] // k["position"] for k in keyword_rankings if k["position"] > 0),
            "seo_score": random.randint(50, 95),
            "improvement_tips": [
                "تضمين الكلمات المفتاحية الرئيسية في العنوان",
                "كتابة وصف أكثر تفصيلاً يتضمن الكلمات المفتاحية",
                "إضافة وسوم (tags) مناسبة للفيديو",
                "استخدام صورة مصغرة مخصصة وجذابة",
                "تشجيع المشاهدين على التفاعل والتعليق"
            ]
        }
        
        return video_data
    
    def analyze_competitor(self, channel_url, video_count=10, use_api=False):
        """تحليل منافسي اليوتيوب"""
        channel_id = self._extract_channel_id(channel_url)
        if not channel_id:
            return {"error": "رابط القناة غير صالح"}
        
        if use_api and self.api_key:
            # استخدام YouTube API لتحليل المنافس
            return self._analyze_competitor_api(channel_id, video_count)
        else:
            # استخدام محاكاة لبيانات تحليل المنافس
            return self._simulate_competitor_data(channel_id, video_count)
    
    def _extract_channel_id(self, channel_url):
        """استخراج معرف القناة من رابط يوتيوب"""
        patterns = [
            r'youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
            r'youtube\.com\/c\/([a-zA-Z0-9_-]+)',
            r'youtube\.com\/@([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, channel_url)
            if match:
                return match.group(1)
        
        # إذا لم يتم العثور على معرف، نستخدم اسم القناة كمعرف
        return channel_url.split('/')[-1]
    
    def _simulate_competitor_data(self, channel_id, video_count):
        """محاكاة بيانات تحليل المنافس للعرض التوضيحي"""
        channel_name = f"قناة {channel_id}"
        
        # توليد بيانات القناة الوهمية
        subscribers = random.randint(1000, 1000000)
        total_views = subscribers * random.randint(5, 50)
        
        # توليد بيانات الفيديوهات الوهمية
        video_data = []
        for i in range(int(video_count)):
            publish_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
            views = random.randint(1000, 100000)
            likes = int(views * random.uniform(0.01, 0.2))
            comments = int(views * random.uniform(0.001, 0.05))
            
            # توليد كلمات مفتاحية وهمية للفيديو
            video_keywords = []
            for j in range(random.randint(3, 8)):
                video_keywords.append(f"كلمة مفتاحية {j+1}")
            
            video_data.append({
                "title": f"فيديو {i+1}: {' '.join(random.sample(video_keywords, min(3, len(video_keywords))))}",
                "video_id": f"video{i+1}",
                "publish_date": publish_date,
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": round((likes + comments) / views * 100, 2),
                "keywords": video_keywords,
                "seo_score": random.randint(50, 95)
            })
        
        # ترتيب الفيديوهات حسب عدد المشاهدات
        video_data.sort(key=lambda x: x["views"], reverse=True)
        
        # استخراج الكلمات المفتاحية الأكثر استخداماً
        all_keywords = []
        for video in video_data:
            all_keywords.extend(video["keywords"])
        
        # حساب تكرار كل كلمة مفتاحية
        keyword_counts = {}
        for keyword in all_keywords:
            if keyword in keyword_counts:
                keyword_counts[keyword] += 1
            else:
                keyword_counts[keyword] = 1
        
        # ترتيب الكلمات المفتاحية حسب التكرار
        top_keywords = [{"keyword": k, "count": v, "percentage": round(v / len(video_data) * 100, 2)} 
                       for k, v in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True)]
        
        # بيانات تحليل المنافس
        competitor_data = {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "subscribers": subscribers,
            "total_views": total_views,
            "videos_analyzed": len(video_data),
            "top_videos": video_data[:5],
            "all_videos": video_data,
            "top_keywords": top_keywords[:10],
            "avg_views": int(sum(v["views"] for v in video_data) / len(video_data)),
            "avg_engagement": round(sum(v["engagement_rate"] for v in video_data) / len(video_data), 2),
            "publishing_frequency": random.choice(["يومي", "أسبوعي", "شهري"]),
            "seo_insights": [
                "استخدام الكلمات المفتاحية بشكل متكرر في العناوين",
                "الفيديوهات الأطول تحقق مشاهدات أكثر",
                "استخدام صور مصغرة مخصصة لجميع الفيديوهات",
                "التفاعل مع التعليقات بشكل منتظم",
                "استخدام المحتوى المنظم في أوصاف الفيديوهات"
            ]
        }
        
        return competitor_data
    
    def optimize_video_content(self, topic=None, current_title=None, current_description=None, target_keywords=None, title=None, description=None, keywords=None, target_audience=None):
        """تحسين محتوى الفيديو من عنوان ووصف"""
        # دعم تنسيق المعلمات المختلف من optimize_video و video_content
        title_to_use = title if title is not None else current_title
        description_to_use = description if description is not None else current_description
        keywords_to_use = keywords if keywords is not None else target_keywords
        
        # تحويل الكلمات المفتاحية إلى قائمة إذا كانت نصًا
        if isinstance(keywords_to_use, str):
            keywords_list = [k.strip() for k in keywords_to_use.split('\n') if k.strip()]
        elif isinstance(keywords_to_use, list):
            keywords_list = keywords_to_use
        else:
            keywords_list = []
        
        # تحليل العنوان الحالي إذا تم تقديمه
        title_analysis = None
        if title_to_use:
            title_analysis = self._analyze_title(title_to_use, keywords_list)
        
        # تحليل الوصف الحالي إذا تم تقديمه
        description_analysis = None
        if description_to_use:
            description_analysis = self._analyze_description(description_to_use, keywords_list)
        
        # توليد عناوين محسنة
        improved_titles = self._generate_improved_titles(topic, keywords_list, title_to_use)
        
        # توليد وصف محسن
        improved_description = self._generate_improved_description(topic, keywords_list, description_to_use)
        
        return {
            "topic": topic,
            "target_keywords": keywords_list,
            "title_analysis": title_analysis,
            "description_analysis": description_analysis,
            "improved_titles": improved_titles,
            "improved_description": improved_description
        }
    
    def _analyze_title(self, title, target_keywords):
        """تحليل عنوان الفيديو الحالي"""
        # تحليل طول العنوان
        length = len(title)
        
        # تحليل تضمين الكلمات المفتاحية
        keywords_included = 0
        for kw in target_keywords:
            if kw.lower() in title.lower():
                keywords_included += 1
        
        # تحليل وجود أرقام
        has_numbers = bool(re.search(r'\d', title))
        
        # تحليل وجود عبارات عاطفية
        emotion_words = [
            "أفضل", "رائع", "خطير", "مذهل", "لا يصدق", "حصري", "مميز", 
            "سريع", "سهل", "صادم", "مثير", "حصري", "مجاني", "فوري"
        ]
        has_emotion = any(word in title.lower() for word in emotion_words)
        
        # حساب درجة التحسين
        improvement_score = 0
        if length <= 60:
            improvement_score += 25
        elif length <= 70:
            improvement_score += 15
        else:
            improvement_score += 5
        
        improvement_score += min(keywords_included * 15, 30)
        
        if has_numbers:
            improvement_score += 15
        
        if has_emotion:
            improvement_score += 15
        
        improvement_score = min(improvement_score, 100)
        
        return {
            "length": length,
            "keywords_included": keywords_included,
            "has_numbers": has_numbers,
            "has_emotion": has_emotion,
            "improvement_score": improvement_score
        }
    
    def _analyze_description(self, description, target_keywords):
        """تحليل وصف الفيديو الحالي"""
        # تحليل طول الوصف
        length = len(description)
        
        # تحليل تضمين الكلمات المفتاحية
        keywords_included = 0
        for kw in target_keywords:
            if kw.lower() in description.lower():
                keywords_included += 1
        
        # تحليل وجود فهرس زمني
        has_timestamps = bool(re.search(r'\d+:\d+', description))
        
        # تحليل وجود روابط
        has_links = bool(re.search(r'https?://', description))
        
        # تحليل وجود هاشتاجات
        has_hashtags = bool(re.search(r'#\w+', description))
        
        return {
            "length": length,
            "keywords_included": keywords_included,
            "has_timestamps": has_timestamps,
            "has_links": has_links,
            "has_hashtags": has_hashtags
        }
    
    def _generate_improved_titles(self, topic, target_keywords, current_title=None):
        """توليد عناوين محسنة للفيديو"""
        emotion_words = ["أفضل", "رائع", "خطير", "مذهل", "لا يصدق", "حصري", "مميز"]
        numbers = ["3", "5", "7", "10", "15"]
        
        title_templates = [
            "{emotion} {number} {keyword} لـ {topic} | شرح مفصل",
            "{number} أسرار لـ {keyword} ستغير طريقة {topic} لديك",
            "دليل {topic} الشامل | {keyword} بكل احترافية",
            "كيف {keyword} بطريقة {emotion} في {number} خطوات فقط",
            "{topic} للمبتدئين: {keyword} بطريقة سهلة",
            "تعلم {keyword} في {number} دقائق فقط | {topic} بشكل مبسط",
            "{emotion} نصائح لـ {topic} | {keyword} شرح كامل"
        ]
        
        improved_titles = []
        for _ in range(5):  # توليد 5 عناوين مقترحة
            template = random.choice(title_templates)
            title = template.format(
                emotion=random.choice(emotion_words),
                number=random.choice(numbers),
                keyword=random.choice(target_keywords),
                topic=topic
            )
            
            # التأكد من أن العنوان لا يتجاوز 60 حرفًا
            if len(title) > 60:
                title = title[:57] + "..."
            
            improved_titles.append(title)
        
        return improved_titles
    
    def _generate_improved_description(self, topic, target_keywords, current_description=None):
        """توليد وصف محسن للفيديو"""
        primary_keyword = target_keywords[0] if target_keywords else topic
        
        # بناء وصف محسن يتضمن الكلمات المفتاحية
        description = f"""🔍 {topic} | {primary_keyword}

في هذا الفيديو سنتعرف على {topic} بشكل مفصل، وكيف يمكنك {primary_keyword} بطريقة احترافية.

📌 محتويات الفيديو:
00:00 مقدمة عن {topic}
01:30 لماذا {primary_keyword} مهم؟
03:45 خطوات {primary_keyword} الأساسية
07:20 نصائح وحيل متقدمة
12:10 تجنب الأخطاء الشائعة
15:30 ملخص وختام

🔥 النقاط الرئيسية التي ستتعلمها:
- كيفية {target_keywords[1] if len(target_keywords) > 1 else primary_keyword} بطريقة صحيحة
- أفضل الممارسات لـ {target_keywords[2] if len(target_keywords) > 2 else primary_keyword}
- أدوات تساعدك في {target_keywords[3] if len(target_keywords) > 3 else primary_keyword}
- كيفية تجنب المشاكل الشائعة في {topic}

🔗 روابط مفيدة:
موقعنا: https://example.com
دورتنا التدريبية: https://example.com/course
مقالات مفيدة: https://example.com/blog

📱 تابعونا على:
انستغرام: https://instagram.com/example
تويتر: https://twitter.com/example
فيسبوك: https://facebook.com/example

💬 اترك تعليقك أدناه إذا كان لديك أي سؤال أو استفسار حول {topic}. لا تنسى الإعجاب بالفيديو والاشتراك في القناة لمشاهدة المزيد من المحتوى المفيد!

#{ ''.join(primary_keyword.split()) } #{ ''.join(topic.split()) } #{ ''.join(target_keywords[1].split()) if len(target_keywords) > 1 else '' }"""
        
        return description

    def analyze_channel_performance(self, channel_url, period=30, use_api=False):
        """تحليل أداء قناة اليوتيوب"""
        channel_id = self._extract_channel_id(channel_url)
        if not channel_id:
            return {"error": "رابط القناة غير صالح"}
        
        if use_api and self.api_key:
            # استخدام YouTube API لتحليل أداء القناة
            return self._analyze_channel_api(channel_id, period)
        else:
            # استخدام محاكاة لبيانات أداء القناة
            return self._simulate_channel_performance(channel_id, period)
    
    def _simulate_channel_performance(self, channel_id, period):
        """محاكاة بيانات أداء القناة للعرض التوضيحي"""
        channel_name = f"قناة {channel_id}"
        
        # توليد بيانات إحصائية للقناة
        subscribers = random.randint(1000, 1000000)
        subscribers_growth = f"{random.randint(1, 15)}%"
        total_views = subscribers * random.randint(5, 50)
        total_videos = random.randint(10, 500)
        avg_views_per_video = total_views // total_videos
        
        # توليد بيانات النمو على مدار الفترة المحددة
        growth_data = []
        for i in range(period):
            date = (datetime.now() - timedelta(days=period-i)).strftime("%Y-%m-%d")
            views = random.randint(avg_views_per_video // 4, avg_views_per_video // 2)
            subs = random.randint(5, 100)
            growth_data.append({
                "date": date,
                "views": views,
                "subscribers": subs
            })
        
        # توليد بيانات أداء الفيديوهات
        video_performance = []
        for i in range(5):  # توليد بيانات لـ5 فيديوهات
            video_performance.append({
                "title": f"فيديو {i+1} - عنوان توضيحي",
                "views": random.randint(avg_views_per_video // 2, avg_views_per_video * 2),
                "watch_time": random.randint(100, 5000),
                "retention": random.randint(20, 85),
                "ctr": round(random.uniform(1.5, 15.0), 1),
                "engagement_rate": round(random.uniform(1.0, 10.0), 1)
            })
        
        # توليد بيانات تحليل الكلمات المفتاحية
        keyword_analysis = []
        keywords = ["مصطلح توضيحي 1", "مصطلح توضيحي 2", "مصطلح توضيحي 3", "مصطلح توضيحي 4"]
        for keyword in keywords:
            keyword_analysis.append({
                "keyword": keyword,
                "impressions": random.randint(1000, 50000),
                "views": random.randint(100, 5000),
                "ctr": round(random.uniform(1.0, 10.0), 1),
                "avg_view_duration": round(random.uniform(1.0, 10.0), 1),
                "videos_ranking": random.randint(1, 10)
            })
        
        # توليد توصيات تحسين سيو القناة
        seo_recommendations = [
            "إضافة الكلمات المفتاحية المستهدفة في بداية عناوين الفيديوهات",
            "تحسين أوصاف الفيديوهات لتتضمن كلمات مفتاحية أكثر وبشكل طبيعي",
            "استخدام صور مصغرة جذابة ومتناسقة لجميع الفيديوهات",
            "زيادة عدد الفيديوهات التي تستهدف الكلمة المفتاحية الرئيسية",
            "إنشاء قوائم تشغيل مخصصة للموضوعات المرتبطة",
            "تشجيع المشاهدين على التفاعل والتعليق لزيادة مشاركة الفيديو",
            "نشر محتوى بشكل منتظم ومتسق لتحسين تفاعل المشتركين",
            "تحسين الكلمات المفتاحية في وصف القناة ومعلوماتها",
            "إنشاء روابط متبادلة بين الفيديوهات ذات الصلة"
        ]
        
        # درجة سيو القناة
        seo_score = random.randint(50, 95)
        
        return {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "period": period,
            "seo_score": seo_score,
            "channel_stats": {
                "subscribers": subscribers,
                "subscribers_growth": subscribers_growth,
                "total_views": total_views,
                "total_videos": total_videos,
                "avg_views_per_video": avg_views_per_video
            },
            "growth_data": growth_data,
            "video_performance": video_performance,
            "keyword_analysis": keyword_analysis,
            "seo_recommendations": seo_recommendations
        }
