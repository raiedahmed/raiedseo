#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSEO - محلل Schema Markup

تحليل البيانات المنظمة (Schema Markup) في صفحات الويب وتقديم توصيات للتحسين
"""

import json
import logging
import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

class SchemaAnalyzer:
    """محلل البيانات المنظمة (Schema Markup) في صفحات الويب"""
    
    def __init__(self, config=None):
        """
        تهيئة محلل البيانات المنظمة
        
        Args:
            config (dict, optional): إعدادات التحليل. الافتراضي None.
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # أنواع Schema الشائعة
        self.common_types = {
            "Article": {
                "required": ["headline", "author", "datePublished"],
                "recommended": ["image", "dateModified", "publisher", "description"]
            },
            "BlogPosting": {
                "required": ["headline", "author", "datePublished"],
                "recommended": ["image", "dateModified", "publisher", "description"]
            },
            "Product": {
                "required": ["name"],
                "recommended": ["image", "description", "brand", "offers", "aggregateRating", "review"]
            },
            "LocalBusiness": {
                "required": ["name", "address"],
                "recommended": ["telephone", "openingHours", "priceRange", "geo"]
            },
            "Organization": {
                "required": ["name"],
                "recommended": ["logo", "contactPoint", "address", "sameAs"]
            },
            "Person": {
                "required": ["name"],
                "recommended": ["jobTitle", "worksFor", "sameAs", "image"]
            },
            "FAQPage": {
                "required": ["mainEntity"],
                "recommended": []
            },
            "HowTo": {
                "required": ["name", "step"],
                "recommended": ["image", "description", "tool", "supply", "totalTime"]
            },
            "Recipe": {
                "required": ["name", "recipeIngredient", "recipeInstructions"],
                "recommended": ["image", "description", "cookTime", "prepTime", "nutrition"]
            },
            "WebSite": {
                "required": ["name"],
                "recommended": ["url", "potentialAction"]
            },
            "BreadcrumbList": {
                "required": ["itemListElement"],
                "recommended": []
            },
            "Review": {
                "required": ["itemReviewed", "reviewRating"],
                "recommended": ["author", "datePublished"]
            }
        }
    
    def analyze(self, url=None, html_content=None):
        """
        تحليل البيانات المنظمة في صفحة ويب
        
        Args:
            url (str, optional): رابط الصفحة للتحليل. الافتراضي None.
            html_content (str, optional): محتوى HTML للصفحة إذا كان متاحًا. الافتراضي None.
            
        Returns:
            dict: نتائج تحليل البيانات المنظمة
        """
        results = {
            'url': url,
            'has_schema': False,
            'schema_count': 0,
            'schema_types': [],
            'schema_items': [],
            'issues': [],
            'recommendations': []
        }
        
        try:
            # الحصول على محتوى الصفحة إذا لم يتم توفيره
            if not html_content and url:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    results['issues'].append(f"فشل في الحصول على محتوى الصفحة: كود الحالة {response.status_code}")
                    return results
                html_content = response.text
            
            if not html_content:
                results['issues'].append("لم يتم توفير محتوى HTML أو رابط صالح")
                return results
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # البحث عن البيانات المنظمة بتنسيق JSON-LD
            schema_tags = soup.find_all('script', type='application/ld+json')
            
            # البحث عن البيانات المنظمة بتنسيق Microdata
            schema_microdata = self._extract_microdata(soup)
            
            # البحث عن البيانات المنظمة بتنسيق RDFa
            schema_rdfa = self._extract_rdfa(soup)
            
            # جمع كل البيانات المنظمة
            all_schemas = []
            
            # استخراج JSON-LD
            for tag in schema_tags:
                try:
                    data = json.loads(tag.string)
                    if isinstance(data, list):
                        all_schemas.extend(data)
                    else:
                        all_schemas.append(data)
                except json.JSONDecodeError:
                    results['issues'].append("تم العثور على JSON-LD غير صالح")
            
            # إضافة البيانات من Microdata و RDFa
            all_schemas.extend(schema_microdata)
            all_schemas.extend(schema_rdfa)
            
            # تحليل كل عنصر schema
            for schema in all_schemas:
                schema_type = self._get_schema_type(schema)
                if schema_type:
                    if schema_type not in results['schema_types']:
                        results['schema_types'].append(schema_type)
                    
                    schema_info = {
                        'type': schema_type,
                        'properties': self._get_schema_properties(schema),
                        'issues': self._validate_schema(schema, schema_type)
                    }
                    
                    results['schema_items'].append(schema_info)
            
            # تحديث الإحصائيات
            results['schema_count'] = len(results['schema_items'])
            results['has_schema'] = results['schema_count'] > 0
            
            # تجميع المشاكل
            for item in results['schema_items']:
                for issue in item['issues']:
                    if issue not in results['issues']:
                        results['issues'].append(issue)
            
            # تقديم التوصيات
            results['recommendations'] = self._generate_recommendations(results)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل البيانات المنظمة: {str(e)}")
            results['issues'].append(f"خطأ في التحليل: {str(e)}")
        
        return results
    
    def _extract_microdata(self, soup):
        """
        استخراج البيانات المنظمة بتنسيق Microdata
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            
        Returns:
            list: قائمة بالبيانات المنظمة
        """
        schemas = []
        
        try:
            # العناصر التي تحتوي على سمة itemtype
            microdata_elements = soup.find_all(attrs={"itemtype": True})
            
            for element in microdata_elements:
                schema_type = element.get('itemtype', '')
                
                # تحويل النوع إلى تنسيق النقطة (.)
                schema_type = schema_type.split('/')[-1]
                
                properties = {}
                # العناصر التي تحتوي على سمة itemprop
                prop_elements = element.find_all(attrs={"itemprop": True})
                
                for prop in prop_elements:
                    prop_name = prop.get('itemprop', '')
                    prop_value = self._get_microdata_value(prop)
                    
                    if prop_name and prop_value:
                        properties[prop_name] = prop_value
                
                if schema_type and properties:
                    schemas.append({
                        "@type": schema_type,
                        **properties
                    })
        
        except Exception as e:
            self.logger.error(f"خطأ في استخراج Microdata: {str(e)}")
        
        return schemas
    
    def _get_microdata_value(self, element):
        """
        الحصول على قيمة عنصر Microdata
        
        Args:
            element (Tag): عنصر HTML
            
        Returns:
            str: القيمة المستخرجة
        """
        if element.name == 'meta':
            return element.get('content', '')
        elif element.name == 'img':
            return element.get('src', '')
        elif element.name == 'a':
            return element.get('href', '')
        elif element.name == 'time':
            return element.get('datetime', '')
        else:
            return element.text.strip()
    
    def _extract_rdfa(self, soup):
        """
        استخراج البيانات المنظمة بتنسيق RDFa
        
        Args:
            soup (BeautifulSoup): كائن BeautifulSoup للصفحة
            
        Returns:
            list: قائمة بالبيانات المنظمة
        """
        schemas = []
        
        try:
            # العناصر التي تحتوي على سمة typeof
            rdfa_elements = soup.find_all(attrs={"typeof": True})
            
            for element in rdfa_elements:
                schema_type = element.get('typeof', '')
                
                properties = {}
                # العناصر التي تحتوي على سمة property
                prop_elements = element.find_all(attrs={"property": True})
                
                for prop in prop_elements:
                    prop_name = prop.get('property', '').split(':')[-1]
                    prop_value = self._get_rdfa_value(prop)
                    
                    if prop_name and prop_value:
                        properties[prop_name] = prop_value
                
                if schema_type and properties:
                    schemas.append({
                        "@type": schema_type,
                        **properties
                    })
        
        except Exception as e:
            self.logger.error(f"خطأ في استخراج RDFa: {str(e)}")
        
        return schemas
    
    def _get_rdfa_value(self, element):
        """
        الحصول على قيمة عنصر RDFa
        
        Args:
            element (Tag): عنصر HTML
            
        Returns:
            str: القيمة المستخرجة
        """
        if element.get('content'):
            return element.get('content')
        elif element.name == 'a':
            return element.get('href', '')
        else:
            return element.text.strip()
    
    def _get_schema_type(self, schema):
        """
        الحصول على نوع البيانات المنظمة
        
        Args:
            schema (dict): كائن البيانات المنظمة
            
        Returns:
            str: نوع البيانات المنظمة
        """
        if not schema:
            return None
        
        schema_type = schema.get('@type')
        
        # التعامل مع أنواع مختلفة من التنسيقات
        if not schema_type:
            schema_type = schema.get('type')
        
        if not schema_type:
            return None
        
        # تنظيف نوع البيانات المنظمة
        if isinstance(schema_type, str):
            # إذا كانت القيمة URI كاملة، استخراج الجزء الأخير
            if '/' in schema_type or '#' in schema_type:
                schema_type = schema_type.split('/')[-1].split('#')[-1]
        
        return schema_type
    
    def _get_schema_properties(self, schema):
        """
        الحصول على خصائص البيانات المنظمة
        
        Args:
            schema (dict): كائن البيانات المنظمة
            
        Returns:
            dict: خصائص البيانات المنظمة
        """
        properties = {}
        
        if not schema:
            return properties
        
        for key, value in schema.items():
            # تخطي المفاتيح الخاصة
            if key.startswith('@'):
                continue
            
            # تسجيل وجود الخاصية
            properties[key] = {
                'exists': True,
                'empty': self._is_empty_value(value)
            }
        
        return properties
    
    def _is_empty_value(self, value):
        """
        التحقق مما إذا كانت قيمة فارغة
        
        Args:
            value: القيمة المراد فحصها
            
        Returns:
            bool: صحيح إذا كانت القيمة فارغة
        """
        if value is None:
            return True
        
        if isinstance(value, str) and not value.strip():
            return True
        
        if isinstance(value, (list, dict)) and not value:
            return True
        
        return False
    
    def _validate_schema(self, schema, schema_type):
        """
        التحقق من صحة البيانات المنظمة
        
        Args:
            schema (dict): كائن البيانات المنظمة
            schema_type (str): نوع البيانات المنظمة
            
        Returns:
            list: قائمة بالمشاكل
        """
        issues = []
        
        if not schema or not schema_type:
            return issues
        
        # التحقق من الخصائص المطلوبة والموصى بها
        if schema_type in self.common_types:
            type_info = self.common_types[schema_type]
            
            # التحقق من الخصائص المطلوبة
            for required_prop in type_info['required']:
                if required_prop not in schema:
                    issues.append(f"خاصية مطلوبة مفقودة: '{required_prop}' في نوع '{schema_type}'")
                elif self._is_empty_value(schema[required_prop]):
                    issues.append(f"خاصية مطلوبة فارغة: '{required_prop}' في نوع '{schema_type}'")
            
            # التحقق من الخصائص الموصى بها
            for recommended_prop in type_info['recommended']:
                if recommended_prop not in schema:
                    issues.append(f"خاصية موصى بها مفقودة: '{recommended_prop}' في نوع '{schema_type}'")
                elif self._is_empty_value(schema[recommended_prop]):
                    issues.append(f"خاصية موصى بها فارغة: '{recommended_prop}' في نوع '{schema_type}'")
        
        return issues
    
    def _generate_recommendations(self, results):
        """
        توليد توصيات لتحسين البيانات المنظمة
        
        Args:
            results (dict): نتائج التحليل
            
        Returns:
            list: قائمة بالتوصيات
        """
        recommendations = []
        
        if not results['has_schema']:
            recommendations.append("إضافة بيانات منظمة (Schema Markup) للصفحة لتحسين ظهورها في نتائج البحث")
            recommendations.append("الأنواع الموصى بها: Article للمقالات، Product للمنتجات، LocalBusiness للأعمال المحلية")
            return recommendations
        
        # توصيات عامة
        if len(results['schema_types']) < 2:
            recommendations.append("التفكير في إضافة أنواع إضافية من البيانات المنظمة للصفحة")
        
        # التوصيات بناءً على نوع الصفحة (يمكن استنتاجه من العنوان أو النوع الحالي)
        if "Article" in results['schema_types'] or "BlogPosting" in results['schema_types']:
            if "BreadcrumbList" not in results['schema_types']:
                recommendations.append("إضافة BreadcrumbList لتوضيح موقع المقالة في هيكل الموقع")
        
        if "Product" in results['schema_types']:
            for item in results['schema_items']:
                if item['type'] == "Product":
                    props = item['properties']
                    if 'aggregateRating' not in props:
                        recommendations.append("إضافة تقييمات للمنتج (aggregateRating) لتحسين ظهوره في نتائج البحث")
                    if 'review' not in props:
                        recommendations.append("إضافة مراجعات للمنتج (review) لتحسين ظهوره في نتائج البحث")
        
        for issue in results['issues']:
            if "مطلوبة مفقودة" in issue:
                prop = re.search(r"'([^']+)'", issue).group(1)
                schema_type = re.search(r"في نوع '([^']+)'", issue).group(1)
                recommendations.append(f"إضافة خاصية {prop} لنوع {schema_type}")
        
        # توصيات إضافية بناءً على المحتوى
        if results['schema_count'] > 0 and len(results['issues']) > 5:
            recommendations.append("استخدام أداة Google's Structured Data Testing Tool للتحقق من البيانات المنظمة")
        
        # التأكد من عدم وجود توصيات مكررة
        return list(set(recommendations))
