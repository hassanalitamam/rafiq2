import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import google.generativeai as genai

# إعدادات الصفحة
st.set_page_config(
    page_title="RAFIQ AI - نظام مراقبة الصحة",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# إعدادات API
THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "2BBOKAZ1XELK87Q9"
GEMINI_API_KEY = "AIzaSyB_8fZhuc_-tVrY7_1PTJPtqTQBtgmOxbc"

# دالة لجلب البيانات من ThingSpeak
def fetch_thingspeak_data(channel_id, api_key, results=100):
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={api_key}&results={results}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

# تكوين نموذج Gemini
def configure_gemini_model(api_key):
    genai.configure(api_key=api_key)
    return genai

# تحليل البيانات باستخدام الذكاء الاصطناعي
def analyze_medical_data(model, data):
    if not data:
        return "لا توجد بيانات كافية للتحليل"
    
    input_text = f"""
    You are a medical expert assistant connected to a medical monitor device. Analyze the incoming data from the monitor and provide a detailed health report to the physician.

    Your analysis must be comprehensive, including:
    - A summary of the patient's overall health stability (is the patient stable or not?)
    - Times when health changes occurred, and details about the timing and reason.
    - Potential impact of any ongoing issues on the patient's health if the problem persists.
    - Clearly provide a recommendation for resolving the problem.
    - Detail what care the patient needs moving forward.

    **Input Data:**
    {data}
    """
    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(input_text)
        return response.text
    except Exception as e:
        st.error(f"خطأ أثناء التحليل: {e}")
        return "حدث خطأ أثناء التحليل الطبي"

# إنشاء تقرير PDF
def generate_pdf_report(analysis_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Amiri', '', 'Amiri-Regular.ttf', uni=True)
    pdf.set_font('Amiri', '', 14)
    pdf.multi_cell(0, 10, analysis_text)
    pdf_file = "medical_report.pdf"
    pdf.output(pdf_file)
    return pdf_file

# عرض الرسوم البيانية
def create_charts(df):
    temp_chart = px.line(
        df, x='created_at', y='field1',
        title='تغيرات درجة الحرارة',
        labels={'field1': 'درجة الحرارة', 'created_at': 'الوقت'}
    )
    heart_rate_chart = px.line(
        df, x='created_at', y='field3',
        title='تغيرات معدل نبضات القلب',
        labels={'field3': 'النبضات/الدقيقة', 'created_at': 'الوقت'}
    )
    return temp_chart, heart_rate_chart

# الوظيفة الرئيسية
def main():
    st.title("🩺 نظام مراقبة الحالة الصحية الذكي - RAFIQ AI")

    # تحميل البيانات
    if st.button("🔄 تحديث البيانات"):
        data = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_API_KEY)
        if data:
            st.session_state["thingspeak_data"] = data
            df = pd.DataFrame(data["feeds"])
            df["created_at"] = pd.to_datetime(df["created_at"])
            st.session_state["df"] = df
            st.success("تم تحديث البيانات بنجاح!")

    # عرض البيانات
    if "thingspeak_data" in st.session_state:
        df = st.session_state["df"]
        latest_data = df.iloc[-1]

        st.subheader("📊 المؤشرات الحالية")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("درجة الحرارة", f"{latest_data['field1']} °C")
        col2.metric("الرطوبة", f"{latest_data['field2']}%")
        col3.metric("نبضات القلب", f"{latest_data['field3']} نبضة/دقيقة")
        col4.metric("درجة حرارة الجسم", f"{latest_data['field4']} °C")

        st.subheader("📈 الرسوم البيانية")
        temp_chart, heart_rate_chart = create_charts(df)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(temp_chart, use_container_width=True)
        with col2:
            st.plotly_chart(heart_rate_chart, use_container_width=True)

        # التحليل الطبي
        if st.button("📄 تحليل البيانات الطبية"):
            model = configure_gemini_model(GEMINI_API_KEY)
            analysis = analyze_medical_data(model, latest_data.to_dict())
            st.subheader("📝 تقرير الذكاء الاصطناعي")
            st.markdown(analysis)

            # إنشاء تقرير PDF
            pdf_file = generate_pdf_report(analysis)
            with open(pdf_file, "rb") as file:
                st.download_button(
                    label="📥 تحميل التقرير كملف PDF",
                    data=file,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

    else:
        st.warning("لم يتم تحميل البيانات بعد. الرجاء الضغط على زر تحديث البيانات.")

# تنفيذ الوظيفة الرئيسية
if __name__ == "__main__":
    main()
