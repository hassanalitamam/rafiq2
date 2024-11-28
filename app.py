import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_extras.stylable_container import stylable_container
from streamlit_lottie import st_lottie
from fpdf import FPDF

# إعدادات الأمان والتكوين
st.set_page_config(
  page_title="RAFIQ AI نظام مراقبة الصحة الذكي",
  page_icon="❤️",
  layout="wide",
  initial_sidebar_state="expanded"
)

THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "2BBOKAZ1XELK87Q9"
GEMINI_API_KEY = "AIzaSyDtAObnL5hUJXgLyPXxBUUhnGFKLW6wj14"

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

      system_prompt = """أنت مساعد طبي محترف يقدم تحليلات دقيقة وواضحة للبيانات الصحية."""

      model = genai.GenerativeModel(
          model_name="gemini-1.5-pro",
          generation_config=generation_config,
          system_instruction=system_prompt
      )

      return model
  except Exception as e:
      st.error(f"خطأ في تكوين نموذج Gemini: {e}")
      return None

def analyze_medical_data(model, data):
  """تحليل البيانات الطبية باستخدام AI مع تحسينات"""
  if not data or not model:
      return "لا توجد بيانات كافية للتحليل"

  input_text = f"""حلل البيانات الطبية التالية بالتفصيل والتركيز على السلامة:
  - درجة الحرارة: {data['field1']} درجة
  - الرطوبة: {data['field2']}%
  - معدل نبضات القلب: {data['field3']} نبضة/دقيقة
  - درجة حرارة الجسم: {data['field4']} درجة

  قدم تحليلًا طبيًا شاملًا مع:
  1. تقييم الحالة الصحية
  2. المخاطر المحتملة
  3. توصيات عامة للرعاية الصحية"""

  try:
      chat_session = model.start_chat(history=[])
      response = chat_session.send_message(input_text)
      return response.text
  except Exception as e:
      st.error(f"خطأ في التحليل: {e}")
      return "حدث خطأ أثناء التحليل الطبي"

def create_charts(df):
  """إنشاء رسوم بيانية تفاعلية"""
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

def generate_pdf_report(analysis_text):
  """إنشاء تقرير PDF"""
  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", size=12)
  pdf.multi_cell(0, 10, analysis_text)
  pdf_file = "medical_report.pdf"
  pdf.output(pdf_file)
  return pdf_file

def main():
  # تحميل رسوم Lottie الطبية
  medical_lottie = load_lottie_url(
      "https://lottie.host/4e8b1815-8b64-4852-9199-987ac70c3392/5GBmHUXcpJ.json"
  )

  # العنوان والمقدمة
  st.markdown("""
  <style>
  .big-title {
      font-size: 3rem;
      color: #2c3e50;
      text-align: center;
      margin-bottom: 20px;
  }
  </style>
  """, unsafe_allow_html=True)

  st.markdown('<h1 class="big-title">نظام مراقبة الحالة الصحية الذكي 🩺</h1>', unsafe_allow_html=True)

  # عرض الرسوم المتحركة
  if medical_lottie:
      col1, col2, col3 = st.columns([1,2,1])
      with col2:
          st_lottie(medical_lottie, speed=1, width=300, height=300)

  # تهيئة نموذج Gemini
  model = configure_gemini_model(GEMINI_API_KEY)

  # الشريط الجانبي
  with st.sidebar:
      st.header("قائمة التحكم")
      st.markdown("---")
      refresh_data = st.button("🔄 تحديث البيانات", use_container_width=True)
      show_raw_data = st.checkbox("📊 عرض البيانات للمريض")
      generate_report = st.button("📄 إنشاء تقرير الذكاء الاصطناعي")

  if refresh_data or 'thingspeak_data' not in st.session_state:
      # جلب بيانات ThingSpeak
      thingspeak_data = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_API_KEY)

      if thingspeak_data:
          st.session_state.thingspeak_data = thingspeak_data

          # تحويل البيانات إلى DataFrame
          df = pd.DataFrame(thingspeak_data['feeds'])
          df['created_at'] = pd.to_datetime(df['created_at'])
          df.set_index('created_at', inplace=True)

          # معالجة DataFrame
          df['field1'] = pd.to_numeric(df['field1'], errors='coerce')
          df['field2'] = pd.to_numeric(df['field2'], errors='coerce')
          df['field3'] = pd.to_numeric(df['field3'], errors='coerce')
          df['field4'] = pd.to_numeric(df['field4'], errors='coerce')

          st.session_state.processed_df = df

  if 'thingspeak_data' in st.session_state:
      # أحدث إدخال
      latest_entry = st.session_state.thingspeak_data['feeds'][-1]

      # مؤشرات صحية
      col1, col2, col3, col4 = st.columns(4)

      with col1:
          with stylable_container(key="metric1", css_styles="""
              {background-color: #e8f4f8; border-radius: 10px; padding: 15px; text-align: center;}
          """):
              st.metric("درجة الحرارة", f"{latest_entry['field1']} °C", delta="🌡️")

      with col2:
          with stylable_container(key="metric2", css_styles="""
              {background-color: #e8f4f8; border-radius: 10px; padding: 15px; text-align: center;}
          """):
              st.metric("الرطوبة", f"{latest_entry['field2']}%", delta="💧")

      with col3:
          with stylable_container(key="metric3", css_styles="""
              {background-color: #e8f4f8; border-radius: 10px; padding: 15px; text-align: center;}
          """):
              st.metric("نبضات القلب", f"{latest_entry['field3']} نبضة/د", delta="❤️")

      with col4:
          with stylable_container(key="metric4", css_styles="""
              {background-color: #e8f4f8; border-radius: 10px; padding: 15px; text-align: center;}
          """):
              st.metric("حرارة الجسم", f"{latest_entry['field4']} °C", delta="🌈")

      # التحليل الطبي
      if generate_report:
          st.subheader("التحليل الطبي AI")
          with st.spinner("جاري التحليل..."):
              medical_analysis = analyze_medical_data(model, latest_entry)

          # تنسيق التحليل
          st.markdown(f"""
          <div style="background-color: #f0f8ff; border-radius: 10px; padding: 20px; direction: rtl;">
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

st.markdown("""
<style>
[data-testid="stHeader"] {
  background-color: rgba(0,0,0,0);
}
[data-testid="stSidebar"] {
  background-color: #f0f8ff;
}
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
  main()
