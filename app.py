import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
from streamlit_lottie import st_lottie
from fpdf import FPDF
import time
import base64
from io import BytesIO

# إعدادات الصفحة
st.set_page_config(
    page_title="RAFIQ Medical AI",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# المفاتيح والإعدادات
THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "2BBOKAZ1XELK87Q9"
GEMINI_API_KEY = "AIzaSyCAMslvAW1xKMIDL2jAgbJVT1UipR8ip2s"

# تحديد الألوان الرئيسية للتطبيق
PRIMARY_COLOR = "#4361EE"
SECONDARY_COLOR = "#3A0CA3"
ACCENT_COLOR = "#F72585"
BG_COLOR = "#F0F8FF"
CARD_BG_COLOR = "#FFFFFF"
SIDEBAR_COLOR = "#EBF2FA"

# تطبيق نمط CSS عام
st.markdown(f"""
<style>
    /* تنسيقات عامة */
    body {{
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        background-color: {BG_COLOR};
        color: #333;
    }}
    
    /* العنوان الرئيسي */
    .main-title {{
        font-size: 3.2rem;
        font-weight: 700;
        color: {PRIMARY_COLOR};
        text-align: center;
        margin-bottom: 0;
        padding-bottom: 0;
        letter-spacing: -0.5px;
        text-shadow: 0px 2px 2px rgba(0,0,0,0.1);
    }}
    
    .subtitle {{
        font-size: 1.2rem;
        color: {SECONDARY_COLOR};
        text-align: center;
        margin-top: 0;
        font-weight: 400;
    }}
    
    /* بطاقات المؤشرات */
    .metric-card {{
        background-color: {CARD_BG_COLOR};
        border-radius: 15px;
        padding: 20px 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border-right: 5px solid {PRIMARY_COLOR};
    }}
    
    .metric-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }}
    
    .metric-value {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {PRIMARY_COLOR};
        margin: 10px 0;
    }}
    
    .metric-label {{
        font-size: 1rem;
        color: #555;
        font-weight: 500;
    }}
    
    .metric-delta {{
        font-size: 1rem;
        background-color: rgba(67, 97, 238, 0.1);
        padding: 5px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 5px;
    }}
    
    /* حاوية التحليل */
    .analysis-container {{
        background-color: {CARD_BG_COLOR};
        border-radius: 15px;
        padding: 25px;
        direction: rtl;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 5px solid {ACCENT_COLOR};
    }}
    
    /* لوحة جانبية */
    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_COLOR};
        padding-top: 2rem;
        border-left: 1px solid #eee;
    }}
    
    /* أزرار */
    .custom-button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 10px;
        padding: 12px 20px;
        text-align: center;
        font-weight: 600;
        border: none;
        cursor: pointer;
        display: inline-block;
        width: 100%;
        margin: 5px 0;
        transition: all 0.3s ease;
    }}
    
    .custom-button:hover {{
        background-color: {SECONDARY_COLOR};
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }}
    
    /* أقسام */
    .section-header {{
        font-size: 1.8rem;
        color: {SECONDARY_COLOR};
        margin-top: 30px;
        margin-bottom: 15px;
        font-weight: 600;
        border-bottom: 2px solid {PRIMARY_COLOR};
        padding-bottom: 8px;
        display: inline-block;
    }}
    
    /* الرسوم البيانية */
    .chart-container {{
        background-color: {CARD_BG_COLOR};
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    
    /* شريط التقدم */
    .stProgress .st-bo {{
        background-color: {PRIMARY_COLOR};
    }}
    
    /* التذييل */
    .footer {{
        text-align: center;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #eee;
        color: #777;
        font-size: 0.9rem;
    }}
    
    /* إخفاء عنصر التحرير */
    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0);
    }}
    
    div.block-container {{
        padding-top: 2rem;
    }}
</style>
""", unsafe_allow_html=True)

# دالة تحميل الخط العربي
def add_arabic_font():
    font_url = "https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap"
    st.markdown(f'<link href="{font_url}" rel="stylesheet">', unsafe_allow_html=True)

add_arabic_font()

# دالة جلب رسوم Lottie
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        st.error(f"خطأ في تحميل الرسوم المتحركة: {e}")
        return None

# دالة لإضافة حركة نبض
def add_pulse_effect():
    st.markdown("""
    <style>
    @keyframes pulse {
        0% {transform: scale(1);}
        50% {transform: scale(1.05);}
        100% {transform: scale(1);}
    }
    .pulse {
        animation: pulse 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

# دالة جلب بيانات ThingSpeak
def fetch_thingspeak_data(channel_id, api_key, results=100):
    """جلب البيانات من قناة ThingSpeak مع التحسينات"""
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={api_key}&results={results}"

    try:
        with st.spinner("جاري تحميل البيانات..."):
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

# دالة تكوين Gemini AI
def configure_gemini_model(api_key):
    """تكوين نموذج Gemini AI مع إعدادات متقدمة"""
    try:
        genai.configure(api_key=api_key)

        generation_config = {
            "temperature": 0.7,
            "top_p": 0.85,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        system_prompt = """أنت مساعد طبي خبير متصل بجهاز مراقبة طبية. قم بتحليل البيانات الواردة من الجهاز وقدم تقريرًا صحيًا مفصلًا للطبيب.
        
تحليلك يجب أن يكون شاملاً، بما في ذلك:
- ملخص لاستقرار الحالة الصحية العامة للمريض (هل المريض مستقر أم لا؟)
- الأوقات التي حدثت فيها تغيرات صحية، وتفاصيل حول التوقيت والسبب.
- التأثير المحتمل لأي مشكلات مستمرة على صحة المريض إذا استمرت المشكلة.
- تقديم توصية واضحة لحل المشكلة.
- تفصيل الرعاية التي يحتاجها المريض مستقبلًا.
- ذكر الأمراض المحتملة إذا استمرت الحالة كما هي الآن أو إذا لم تحدث أي مشاكل لأن الحالة مستقرة.

تأكد من أن ردك باللغة العربية، واستخدم التنسيق التالي:
- تحليل طبي مفصل للبيانات والحالة الصحية تشمل (هل الحالة مستقرة أم لا)
- أوقات التغير الصحي ومتى وأين حدث هذا التغير، وشرح السبب
- التبعات المحتملة إذا استمرت المشكلة
- نصيحة محددة لحل المشكلة
- ما هي الأمراض المحتملة إذا استمرت الحالة كما هي الآن أم لن يحدث أي مشاكل لأن الحالة مستقرة ولن يحدث أي مشكلة

حافظ على نبرة متعاطفة ودقيقة. تحدث بطريقة يمكن للطبيب فهمها وتطبيقها بسهولة في اتخاذ قراراته."""

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            system_instruction=system_prompt
        )

        return model
    except Exception as e:
        st.error(f"خطأ في تكوين نموذج Gemini: {e}")
        return None

# دالة تحليل البيانات الطبية
def analyze_medical_data(model, data):
    """تحليل البيانات الطبية باستخدام AI مع تحسينات"""
    if not data or not model:
        return "لا توجد بيانات كافية للتحليل"

    # تنسيق البيانات للعرض في البرومبت
    data_entries = []
    for entry in data:
        timestamp = entry['created_at']
        field1 = entry.get('field1', 'غير متوفر')
        field2 = entry.get('field2', 'غير متوفر')
        field3 = entry.get('field3', 'غير متوفر')
        field4 = entry.get('field4', 'غير متوفر')
        data_entries.append(f"البيانات في {timestamp}: درجة الحرارة={field1}°C، الرطوبة={field2}٪، معدل نبضات القلب={field3} نبضة/دقيقة، حرارة الجسم={field4}°C.")

    all_data_text = "\n".join(data_entries)

    input_text = f"""قم بتحليل البيانات الطبية التالية بالتفصيل والتركيز على السلامة:

{all_data_text}

قدم تحليلًا طبيًا شاملاً وفقًا للتعليمات التالية:
1. تقييم الحالة الصحية العامة للمريض (هل الحالة مستقرة أم لا؟)
2. تحديد الأوقات التي حدثت فيها تغيرات صحية، وشرح السبب وراءها.
3. مناقشة التبعات المحتملة إذا استمرت المشاكل الصحية الحالية.
4. تقديم نصيحة محددة لحل المشاكل الصحية المكتشفة.
5. تفصيل الرعاية التي يحتاجها المريض مستقبلاً.
6. ذكر الأمراض المحتملة إذا استمرت الحالة كما هي الآن أو إذا كانت الحالة مستقرة فلن تحدث أي مشاكل، مع ذكر الأسباب العلمية لهذه الأمراض بناءً على البيانات المقدمة."""

    try:
        # إظهار شريط التقدم
        progress_bar = st.progress(0)
        for percent_complete in range(101):
            time.sleep(0.02)
            progress_bar.progress(percent_complete)
        
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(input_text)
        return response.text
    except Exception as e:
        st.error(f"خطأ في التحليل: {e}")
        return "حدث خطأ أثناء التحليل الطبي"

# دالة إنشاء الرسوم البيانية المتقدمة
def create_advanced_charts(df):
    """إنشاء رسوم بيانية تفاعلية محسنة"""
    # تعيين نمط موحد
    chart_template = dict(
        layout=dict(
            paper_bgcolor=CARD_BG_COLOR,
            plot_bgcolor=CARD_BG_COLOR,
            font=dict(family="Tajawal", size=14),
            margin=dict(l=10, r=10, t=50, b=10),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1),
            height=350
        )
    )
    
    # إضافة النطاقات الطبيعية والحرجة
    temp_chart = px.line(
        df, 
        x='created_at', 
        y='field1', 
        title='<b>درجة الحرارة المحيطة</b>',
        labels={'field1': 'درجة الحرارة (°C)', 'created_at': 'الوقت'},
        template=chart_template
    )
    
    temp_chart.add_hrect(
        y0=18, y1=25, 
        fillcolor="green", opacity=0.15, 
        line_width=0, annotation_text="نطاق مثالي"
    )
    
    temp_chart.add_hrect(
        y0=25, y1=35, 
        fillcolor="orange", opacity=0.15, 
        line_width=0, annotation_text="نطاق مرتفع"
    )
    
    temp_chart.update_traces(line_color=PRIMARY_COLOR, line_width=3)
    
    # رسم بياني للرطوبة
    humidity_chart = px.line(
        df, 
        x='created_at', 
        y='field2', 
        title='<b>مستوى الرطوبة</b>',
        labels={'field2': 'الرطوبة (%)', 'created_at': 'الوقت'},
        template=chart_template
    )
    
    humidity_chart.add_hrect(
        y0=40, y1=60, 
        fillcolor="green", opacity=0.15, 
        line_width=0, annotation_text="نطاق مثالي"
    )
    
    humidity_chart.update_traces(line_color=SECONDARY_COLOR, line_width=3)
    
    # رسم بياني لنبضات القلب
    heart_rate_chart = px.line(
        df, 
        x='created_at', 
        y='field3', 
        title='<b>معدل نبضات القلب</b>',
        labels={'field3': 'نبضات/دقيقة', 'created_at': 'الوقت'},
        template=chart_template
    )
    
    heart_rate_chart.add_hrect(
        y0=60, y1=100, 
        fillcolor="green", opacity=0.15, 
        line_width=0, annotation_text="نطاق طبيعي"
    )
    
    heart_rate_chart.add_hrect(
        y0=100, y1=120, 
        fillcolor="orange", opacity=0.15, 
        line_width=0, annotation_text="تسارع معتدل"
    )
    
    heart_rate_chart.add_hrect(
        y0=120, y1=150, 
        fillcolor="red", opacity=0.15, 
        line_width=0, annotation_text="تسارع شديد"
    )
    
    heart_rate_chart.update_traces(line_color=ACCENT_COLOR, line_width=3)
    
    # رسم بياني لحرارة الجسم
    body_temp_chart = px.line(
        df, 
        x='created_at', 
        y='field4', 
        title='<b>حرارة الجسم</b>',
        labels={'field4': 'حرارة الجسم (°C)', 'created_at': 'الوقت'},
        template=chart_template
    )
    
    body_temp_chart.add_hrect(
        y0=36.5, y1=37.5, 
        fillcolor="green", opacity=0.15, 
        line_width=0, annotation_text="طبيعي"
    )
    
    body_temp_chart.add_hrect(
        y0=37.5, y1=38.5, 
        fillcolor="orange", opacity=0.15, 
        line_width=0, annotation_text="حمى خفيفة"
    )
    
    body_temp_chart.add_hrect(
        y0=38.5, y1=40, 
        fillcolor="red", opacity=0.15, 
        line_width=0, annotation_text="حمى شديدة"
    )
    
    body_temp_chart.update_traces(line_color=PRIMARY_COLOR, line_width=3)
    
    # إضافة تحسينات مشتركة للرسوم البيانية
    for chart in [temp_chart, humidity_chart, heart_rate_chart, body_temp_chart]:
        chart.update_layout(
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(0,0,0,0.05)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(0,0,0,0.05)'
            )
        )
    
    return temp_chart, humidity_chart, heart_rate_chart, body_temp_chart

# دالة إنشاء وتنزيل PDF
def generate_pdf_report(analysis_text, data_df):
    """إنشاء تقرير PDF احترافي"""
    # إنشاء PDF باللغة العربية
    pdf = FPDF()
    pdf.add_page()
    
    # استخدام خط الأميري لدعم اللغة العربية
    pdf.add_font('Amiri', '', 'Amiri-Regular.ttf', uni=True)
    pdf.add_font('Amiri', 'B', 'Amiri-Bold.ttf', uni=True)
    
    # إضافة العنوان والشعار
    pdf.set_font('Amiri', 'B', 24)
    pdf.cell(0, 15, 'تقرير الحالة الصحية', 0, 1, 'C')
    
    pdf.set_font('Amiri', '', 12)
    pdf.cell(0, 10, f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    pdf.ln(5)
    
    # إضافة ملخص البيانات
    pdf.set_font('Amiri', 'B', 16)
    pdf.cell(0, 10, 'ملخص البيانات الحيوية:', 0, 1, 'R')
    pdf.ln(5)
    
    # الحصول على أحدث قيم
    latest = data_df.iloc[-1]
    
    # جدول البيانات الحيوية
    pdf.set_font('Amiri', '', 12)
    pdf.cell(40, 10, f'{latest["field1"]} °C', 1, 0, 'C')
    pdf.cell(0, 10, 'درجة الحرارة المحيطة', 1, 1, 'R')
    
    pdf.cell(40, 10, f'{latest["field2"]} %', 1, 0, 'C')
    pdf.cell(0, 10, 'الرطوبة', 1, 1, 'R')
    
    pdf.cell(40, 10, f'{latest["field3"]} نبضة/دقيقة', 1, 0, 'C')
    pdf.cell(0, 10, 'معدل ضربات القلب', 1, 1, 'R')
    
    pdf.cell(40, 10, f'{latest["field4"]} °C', 1, 0, 'C')
    pdf.cell(0, 10, 'حرارة الجسم', 1, 1, 'R')
    
    pdf.ln(10)
    
    # إضافة التحليل الطبي
    pdf.set_font('Amiri', 'B', 16)
    pdf.cell(0, 10, 'التحليل الطبي:', 0, 1, 'R')
    pdf.ln(5)
    
    pdf.set_font('Amiri', '', 12)
    
    # تقسيم النص إلى أسطر لضمان العرض الصحيح
    lines = analysis_text.split('\n')
    for line in lines:
        pdf.multi_cell(0, 10, line, 0, 'R')
    
    pdf.ln(5)
    
    # إضافة التذييل
    pdf.set_font('Amiri', '', 10)
    pdf.set_y(-20)
    pdf.cell(0, 10, 'تم إنشاء هذا التقرير بواسطة نظام مراقبة الحالة الصحية الذكي - رفيق AI', 0, 0, 'C')
    
    pdf_file = "medical_report.pdf"
    pdf.output(pdf_file)
    return pdf_file

# دالة إنشاء بطاقة قياس
def metric_card(icon, title, value, suffix="", trend=None):
    """إنشاء بطاقة قياس متحركة"""
    trend_html = ""
    if trend:
        if "up" in trend.lower():
            trend_color = "#FF4560"
            trend_icon = "↑"
        else:
            trend_color = "#00E396"
            trend_icon = "↓"
        trend_html = f'<span style="color: {trend_color};">{trend_icon} {trend}</span>'
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{icon} {title}</div>
        <div class="metric-value">{value}{suffix}</div>
        <div class="metric-delta">{trend_html}</div>
    </div>
    """

def main():
    # إضافة تأثير النبض
    add_pulse_effect()
    
    # تحميل رسوم Lottie
    medical_lottie = load_lottie_url(
        "https://lottie.host/4e8b1815-8b64-4852-9199-987ac70c3392/5GBmHUXcpJ.json"
    )
    
    # العنوان والمقدمة
    st.markdown('<h1 class="main-title pulse">نظام رفيق AI للمراقبة الطبية</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">مراقبة ذكية للحالة الصحية مع تحليل متقدم للبيانات</p>', unsafe_allow_html=True)
    
    # عرض الرسوم المتحركة
    if medical_lottie:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st_lottie(medical_lottie, speed=1, width=300, height=200)
    
    # تهيئة نموذج Gemini
    model = configure_gemini_model(GEMINI_API_KEY)
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("""
        <h2 style="color: #4361EE; text-align: center; margin-bottom: 20px;">لوحة التحكم</h2>
        <hr style="margin-bottom: 30px;">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            patient_icon = "👨‍⚕️"
        with col2:
            st.markdown(f"<h3 style='text-align: right;'>معلومات المريض</h3>", unsafe_allow_html=True)
        
        patient_name = st.text_input("اسم المريض", "أحمد محمد")
        patient_id = st.text_input("رقم المريض", "PT-2024-001")
        patient_age = st.number_input("العمر", 18, 120, 45)
        
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: right;'>خيارات النظام</h3>", unsafe_allow_html=True)
        
        # إنشاء أزرار مخصصة
        st.markdown('<button class="custom-button" id="refresh_button">🔄 تحديث البيانات</button>', unsafe_allow_html=True)
        refresh_data = st.button("تحديث البيانات", key="refresh_hidden", help="تحديث البيانات من القناة")
        
        st.markdown('<button class="custom-button" id="analysis_button" style="background-color: #3A0CA3;">🧠 إنشاء تحليل AI</button>', unsafe_allow_html=True)
        generate_report = st.button("إنشاء تحليل", key="analysis_hidden")
        
        data_options = st.expander("خيارات عرض البيانات")
        with data_options:
            show_raw_data = st.checkbox("📊 عرض البيانات الخام")
            smoothing = st.slider("تنعيم الرسوم البيانية", 0, 10, 0)
            records_limit = st.select_slider("عدد السجلات", options=[20, 50, 100, 150, 200], value=100)
            
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: rgba(67, 97, 238, 0.1); border-radius: 10px;">
            <p style="font-size: 14px; color: #555;">
                <b>نظام رفيق الطبي AI</b><br>
                الإصدار 2.7.0<br>
                جميع الحقوق محفوظة © 2024
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # جلب وتحليل البيانات
    if refresh_data or 'thingspeak_data' not in st.session_state:
        # جلب بيانات ThingSpeak
