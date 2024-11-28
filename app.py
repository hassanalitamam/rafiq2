import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# إعدادات API
GEMINI_API_KEY = "ضع_مفتاح_API_هنا"
THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "ضع_مفتاح_API_هنا"
genai.configure(api_key=GEMINI_API_KEY)

# وظيفة جلب البيانات من ThingSpeak
def fetch_thingspeak_data(channel_id, api_key, results=100):
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

# وظيفة لتحليل البيانات الطبية
def analyze_medical_data(data):
    if not data:
        return "لا توجد بيانات كافية للتحليل."
    
    # إعداد النص الذي سيتم إرساله للنموذج
    input_text = f"""
    You are a medical expert assistant connected to a medical monitor device. Analyze the incoming data from the monitor and provide a detailed health report to the physician.

    Your analysis must be comprehensive, including:
    - A summary of the patient's overall health stability (is the patient stable or not?).
    - Times when health changes occurred, and details about the timing and reason.
    - Potential impact of any ongoing issues on the patient's health if the problem persists.
    - Clearly provide a recommendation for resolving the problem.
    - Detail what care the patient needs moving forward.

    **Input Data:**
    {data}
    """
    
    try:
        # إرسال البيانات إلى نموذج AI لتحليلها
        response = genai.generate_text(
            prompt=input_text,
            temperature=0.7,
            max_output_tokens=1000
        )
        return response.text
    except Exception as e:
        st.error(f"حدث خطأ أثناء التحليل: {e}")
        return "خطأ في التحليل الطبي."

# وظيفة لإنشاء التقرير بصيغة PDF
def generate_pdf_report(analysis_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Amiri', '', 'Amiri-Regular.ttf', uni=True)
    pdf.set_font('Amiri', '', 14)
    pdf.multi_cell(0, 10, analysis_text)
    pdf_file = "medical_report.pdf"
    pdf.output(pdf_file)
    return pdf_file

# وظيفة لإنشاء الرسوم البيانية التفاعلية
def create_charts(df):
    # رسم بياني للحرارة
    temp_chart = px.line(
        df, 
        x='created_at', 
        y='field1', 
        title='التغيرات في درجة الحرارة',
        labels={'field1': 'درجة الحرارة', 'created_at': 'الوقت'}
    )

    # رسم بياني لنبضات القلب
    heart_rate_chart = px.line(
        df, 
        x='created_at', 
        y='field3', 
        title='معدل نبضات القلب',
        labels={'field3': 'النبضات/الدقيقة', 'created_at': 'الوقت'}
    )

    return temp_chart, heart_rate_chart

# واجهة المستخدم باستخدام streamlit
def main():
    st.set_page_config(page_title="RAFIQ AI نظام مراقبة الصحة الذكي", page_icon="❤️", layout="wide")
    st.markdown("""
    <style>
    .big-title {
        font-size: 3rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #e8f4f8;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
    .analysis-container {
        background-color: #f0f8ff;
        border-radius: 10px;
        padding: 20px;
        direction: rtl;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="big-title">نظام مراقبة الحالة الصحية الذكي 🩺</h1>', unsafe_allow_html=True)

    # الشريط الجانبي
    with st.sidebar:
        st.header("قائمة التحكم")
        st.markdown("---")
        refresh_data = st.button("🔄 تحديث البيانات", use_container_width=True)
        show_raw_data = st.checkbox("📊 عرض البيانات للمريض")
        generate_report = st.button("📄 إنشاء تقرير الذكاء الاصطناعي")

    # جلب البيانات من ThingSpeak
    if refresh_data or 'thingspeak_data' not in st.session_state:
        thingspeak_data = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_API_KEY)

        if thingspeak_data:
            st.session_state.thingspeak_data = thingspeak_data

            # تحويل البيانات إلى DataFrame
            df = pd.DataFrame(thingspeak_data['feeds'])
            df['created_at'] = pd.to_datetime(df['created_at'])
            df.set_index('created_at', inplace=True)

            # معالجة البيانات
            df['field1'] = pd.to_numeric(df['field1'], errors='coerce')
            df['field2'] = pd.to_numeric(df['field2'], errors='coerce')
            df['field3'] = pd.to_numeric(df['field3'], errors='coerce')
            df['field4'] = pd.to_numeric(df['field4'], errors='coerce')

            st.session_state.processed_df = df

    # إذا كانت البيانات متاحة
    if 'thingspeak_data' in st.session_state:
        # أحدث إدخال
        latest_entry = st.session_state.thingspeak_data['feeds'][-1]

        # مؤشرات صحية
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("درجة الحرارة", f"{latest_entry['field1']} °C", delta="🌡️")

        with col2:
            st.metric("الرطوبة", f"{latest_entry['field2']}%", delta="💧")

        with col3:
            st.metric("نبضات القلب", f"{latest_entry['field3']} نبضة/د", delta="❤️")

        with col4:
            st.metric("حرارة الجسم", f"{latest_entry['field4']} °C", delta="🌈")

        # التحليل الطبي
        if generate_report:
            st.subheader("التحليل الطبي AI")
            with st.spinner("جاري التحليل..."):
                medical_analysis = analyze_medical_data(latest_entry)

            # عرض التحليل الطبي
            st.markdown(f"""
            <div class="analysis-container">
            {medical_analysis}
            </div>
            """, unsafe_allow_html=True)

            # إنشاء تقرير PDF
            pdf_file = generate_pdf_report(medical_analysis)
            with open(pdf_file, "rb") as file:
                st.download_button(
                    label="📥 تحميل التقرير كملف PDF",
                    data=file,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

        # الرسوم البيانية التفاعلية
        st.subheader("التقارير البيانية")
        temp_chart, heart_rate_chart = create_charts(st.session_state.processed_df.reset_index())

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(temp_chart, use_container_width=True)
        with col2:
            st.plotly_chart(heart_rate_chart, use_container_width=True)

        # عرض البيانات الخام
        if show_raw_data:
            st.subheader("البيانات الخام")
            st.dataframe(st.session_state.processed_df)

    else:
        st.warning("الرجاء الضغط على زر تحديث البيانات")

if __name__ == "__main__":
    main()
