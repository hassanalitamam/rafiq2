import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# إعدادات الأساسية
st.set_page_config(
    page_title="RAFIQ AI نظام مراقبة الصحة الذكي",
    page_icon="❤️",
    layout="wide"
)

# مفاتيح API
THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "2BBOKAZ1XELK87Q9"
GEMINI_API_KEY = "AIzaSyB_8fZhuc_-tVrY7_1PTJPtqTQBtgmOxbc"

def configure_gemini_model(api_key):
    """تكوين نموذج Gemini AI"""
    try:
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.7,
            "top_p": 0.85,
            "top_k": 40,
            "max_output_tokens": 15000,
        }

        system_prompt = """أنت مساعد طبي محترف متصل بجهاز مراقبة طبية. 
        مهمتك تحليل جميع البيانات الواردة بشكل دقيق وتقديم تقرير طبي شامل."""

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        return model
    except Exception as e:
        st.error(f"خطأ في تكوين النموذج: {e}")
        return None

def fetch_thingspeak_data(channel_id, api_key, results=250):
    """جلب جميع البيانات من ThingSpeak"""
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={api_key}&results={results}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

def analyze_medical_data(model, thingspeak_data):
    """تحليل البيانات الطبية الكاملة"""
    if not thingspeak_data or not model:
        return "لا توجد بيانات كافية للتحليل"

    # استخراج معلومات القناة والإدخالات
    channel_info = thingspeak_data.get('channel', {})
    feeds = thingspeak_data.get('feeds', [])

    # إنشاء نص تفصيلي للتحليل
    input_text = f"""معلومات القناة الطبية:
- معرف القناة: {channel_info.get('id', 'غير محدد')}
- اسم القناة: {channel_info.get('name', 'غير محدد')}
- إجمالي الإدخالات: {len(feeds)} إدخال

التحليل الشامل للبيانات:
"""

    # إضافة تفاصيل كل إدخال
    for index, entry in enumerate(feeds, 1):
        input_text += f"""
الإدخال رقم {index}:
- وقت القياس: {entry.get('created_at', 'غير محدد')}
- درجة حرارة المحيط: {entry.get('field1', 'غير محدد')} درجة
- الرطوبة: {entry.get('field2', 'غير محدد')}%
- معدل نبضات القلب: {entry.get('field3', 'غير محدد')} نبضة/دقيقة
- درجة حرارة الجسم: {entry.get('field4', 'غير محدد')} درجة

"""

    input_text += """المطلوب من التحليل:
1. تقييم شامل للحالة الصحية
2. تحديد التغيرات والاتجاهات
3. توصيات طبية دقيقة
4. خطة متابعة مقترحة"""

    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(input_text)
        return response.text
    except Exception as e:
        st.error(f"خطأ في التحليل: {e}")
        return "حدث خطأ أثناء التحليل الطبي"

def main():
    st.title("نظام مراقبة الصحة الذكي 🩺")
    
    # تهيئة النموذج
    model = configure_gemini_model(GEMINI_API_KEY)
    
    if st.button("تحليل البيانات الكاملة"):
        with st.spinner("جارٍ جلب وتحليل البيانات..."):
            # جلب البيانات
            thingspeak_data = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_API_KEY)
            
            if thingspeak_data:
                # تحليل البيانات
                medical_analysis = analyze_medical_data(model, thingspeak_data)
                
                # عرض التحليل
                st.markdown("### نتائج التحليل الطبي:")
                st.write(medical_analysis)

if __name__ == "__main__":
    main()
