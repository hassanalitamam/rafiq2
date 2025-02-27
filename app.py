import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
from streamlit_extras.stylable_container import stylable_container
from streamlit_lottie import st_lottie
from fpdf import FPDF

# إعدادات الأمان والتكوين
st.set_page_config(
    page_title="RAFIQ AI",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# المفاتيح والإعدادات
THINGSPEAK_CHANNEL_ID = 2743941
THINGSPEAK_API_KEY = "2BBOKAZ1XELK87Q9"
GEMINI_API_KEY = "AIzaSyCAMslvAW1xKMIDL2jAgbJVT1UipR8ip2s"

# تعريف كلاس للتعامل مع LocalStorage
class LocalStorage:
    def __init__(self):
        self.storage_key = "patient_data"
    
    def save_data(self, data):
        """حفظ البيانات في LocalStorage باستخدام SessionState"""
        st.session_state[self.storage_key] = data
        # تخزين البيانات أيضًا باستخدام JavaScript
        js_code = f"""
        <script>
            localStorage.setItem('{self.storage_key}', JSON.stringify({json.dumps(data)}));
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)
    
    def load_data(self):
        """تحميل البيانات من LocalStorage"""
        # محاولة تحميل البيانات من SessionState أولاً
        if self.storage_key in st.session_state:
            return st.session_state[self.storage_key]
        
        # إذا لم تكن البيانات موجودة، إرجاع بيانات افتراضية
        return {
            "name": "",
            "age": 50,
            "sex": "1",
            "phone": "",
            "medical_history": "",
            "cigs_per_day": 0,
            "tot_chol": 200,
            "sys_bp": 120,
            "glucose": 100,
            "heart_disease_prediction": None
        }

# تهيئة كائن LocalStorage
local_storage = LocalStorage()

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
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(input_text)
        return response.text
    except Exception as e:
        st.error(f"خطأ في التحليل: {e}")
        return "حدث خطأ أثناء التحليل الطبي"

def create_charts(df):
    """إنشاء رسوم بيانية تفاعلية"""
    # رسم بياني لدرجة الحرارة
    temp_chart = px.line(
        df, 
        x='created_at', 
        y='field1', 
        title='التغيرات في درجة الحرارة',
        labels={'field1': 'درجة الحرارة (°C)', 'created_at': 'الوقت'}
    )

    # رسم بياني للرطوبة
    humidity_chart = px.line(
        df, 
        x='created_at', 
        y='field2', 
        title='التغيرات في الرطوبة',
        labels={'field2': 'الرطوبة (%)', 'created_at': 'الوقت'}
    )

    # رسم بياني لنبضات القلب
    heart_rate_chart = px.line(
        df, 
        x='created_at', 
        y='field3', 
        title='معدل نبضات القلب',
        labels={'field3': 'نبضات/دقيقة', 'created_at': 'الوقت'}
    )

    # رسم بياني لحرارة الجسم
    body_temp_chart = px.line(
        df, 
        x='created_at', 
        y='field4', 
        title='حرارة الجسم',
        labels={'field4': 'حرارة الجسم (°C)', 'created_at': 'الوقت'}
    )

    return temp_chart, humidity_chart, heart_rate_chart, body_temp_chart

def generate_pdf_report(patient_data, analysis_text):
    """إنشاء تقرير PDF مع معلومات المريض"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Amiri', '', 'Amiri-Regular.ttf', uni=True)
    pdf.set_font('Amiri', '', 14)
    
    # إضافة معلومات المريض
    pdf.cell(0, 10, f"اسم المريض: {patient_data['name']}", ln=True)
    pdf.cell(0, 10, f"العمر: {patient_data['age']}", ln=True)
    pdf.cell(0, 10, f"الجنس: {'ذكر' if patient_data['sex'] == '1' else 'أنثى'}", ln=True)
    pdf.cell(0, 10, f"رقم الهاتف: {patient_data['phone']}", ln=True)
    
    # إضافة التاريخ الطبي
    pdf.cell(0, 10, "التاريخ الطبي:", ln=True)
    pdf.multi_cell(0, 10, patient_data['medical_history'])
    
    # إضافة نتائج تحليل أمراض القلب إذا كانت متوفرة
    if patient_data['heart_disease_prediction']:
        pdf.cell(0, 10, "نتيجة تحليل مخاطر أمراض القلب:", ln=True)
        pdf.multi_cell(0, 10, patient_data['heart_disease_prediction'])
    
    # إضافة التحليل الطبي
    pdf.cell(0, 10, "التحليل الطبي:", ln=True)
    pdf.multi_cell(0, 10, analysis_text)
    
    pdf_file = "medical_report.pdf"
    pdf.output(pdf_file)
    return pdf_file

def predict_heart_disease(age, sex_male, cigs_per_day, tot_chol, sys_bp, glucose):
    """استدعاء واجهة برمجة التطبيقات للتنبؤ بأمراض القلب"""
    try:
        # محاكاة استدعاء API - يمكن استبدال هذا بالاستدعاء الفعلي للـ API
        # في بيئة حقيقية، يمكنك استخدام gradio_client كما في النموذج المقدم
        
        # مثال على التقييم المنطقي البسيط
        risk_factors = 0
        
        if age > 60:
            risk_factors += 1
        
        if sex_male == "1":  # ذكر
            risk_factors += 1
            
        if cigs_per_day > 0:
            risk_factors += 1
            
        if tot_chol > 240:
            risk_factors += 1
            
        if sys_bp > 140:
            risk_factors += 1
            
        if glucose > 110:
            risk_factors += 1
            
        # تحديد النتيجة بناءً على عوامل الخطر
        if risk_factors <= 1:
            return "مخاطر منخفضة لأمراض القلب (أقل من 10%)"
        elif risk_factors <= 3:
            return "مخاطر متوسطة لأمراض القلب (10-20%)"
        else:
            return "مخاطر عالية لأمراض القلب (أكثر من 20%)"
            
        # في بيئة الإنتاج، استخدم الكود التالي بدلاً من ذلك:
        # from gradio_client import Client
        # client = Client("hassanalivip28/Heart-Dises_Model")
        # result = client.predict(
        #     age=age,
        #     sex_male=sex_male,
        #     cigs_per_day=cigs_per_day,
        #     tot_chol=tot_chol,
        #     sys_bp=sys_bp,
        #     glucose=glucose,
        #     api_name="/predict_heart_disease"
        # )
        # return result
        
    except Exception as e:
        st.error(f"خطأ في التنبؤ بأمراض القلب: {e}")
        return "حدث خطأ أثناء التنبؤ بأمراض القلب"

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
    .form-container {
        background-color: #f5f9ff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .heart-prediction {
        background-color: #ffefef;
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px;
        direction: rtl;
        text-align: right;
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
        
        # أزرار التنقل
        page = st.radio(
            "القسم",
            ["بيانات المريض", "مراقبة المؤشرات الحيوية", "تحليل مخاطر القلب"]
        )
        
        st.markdown("---")
        
        # أزرار إضافية حسب الصفحة
        if page == "مراقبة المؤشرات الحيوية":
            refresh_data = st.button("🔄 تحديث البيانات", use_container_width=True)
            show_raw_data = st.checkbox("📊 عرض البيانات للمريض")
            generate_report = st.button("📄 إنشاء تقرير الذكاء الاصطناعي")
        else:
            refresh_data = False
            show_raw_data = False
            generate_report = False

    # تحميل بيانات المريض
    patient_data = local_storage.load_data()

    # عرض الصفحة المناسبة
    if page == "بيانات المريض":
        st.header("معلومات المريض")
        
        with st.form("patient_info_form"):
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                patient_data["name"] = st.text_input("الاسم", value=patient_data.get("name", ""))
                patient_data["age"] = st.number_input("العمر", min_value=1, max_value=120, value=patient_data.get("age", 50))
                patient_data["cigs_per_day"] = st.number_input("عدد السجائر في اليوم", min_value=0, max_value=100, value=patient_data.get("cigs_per_day", 0))
                patient_data["tot_chol"] = st.number_input("مستوى الكولسترول الكلي (mg/dL)", min_value=100, max_value=500, value=patient_data.get("tot_chol", 200))
            
            with col2:
                patient_data["sex"] = st.radio("الجنس", options=["1", "0"], format_func=lambda x: "ذكر" if x == "1" else "أنثى", index=0 if patient_data.get("sex", "1") == "1" else 1)
                patient_data["phone"] = st.text_input("رقم الهاتف", value=patient_data.get("phone", ""))
                patient_data["sys_bp"] = st.number_input("ضغط الدم الانقباضي (mmHg)", min_value=80, max_value=220, value=patient_data.get("sys_bp", 120))
                patient_data["glucose"] = st.number_input("مستوى السكر في الدم (mg/dL)", min_value=70, max_value=300, value=patient_data.get("glucose", 100))
            
            patient_data["medical_history"] = st.text_area("التاريخ الطبي", value=patient_data.get("medical_history", ""), height=150)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            submitted = st.form_submit_button("حفظ المعلومات")
            
            if submitted:
                local_storage.save_data(patient_data)
                st.success("تم حفظ معلومات المريض بنجاح!")

    elif page == "تحليل مخاطر القلب":
        st.header("تحليل مخاطر أمراض القلب")
        
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.write(f"المريض: {patient_data['name']}, العمر: {patient_data['age']}, الجنس: {'ذكر' if patient_data['sex'] == '1' else 'أنثى'}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.slider("العمر", min_value=20, max_value=100, value=patient_data["age"])
            sex_male = st.radio("الجنس", options=["1", "0"], format_func=lambda x: "ذكر" if x == "1" else "أنثى", index=0 if patient_data["sex"] == "1" else 1)
            cigs_per_day = st.slider("عدد السجائر في اليوم", min_value=0, max_value=70, value=patient_data["cigs_per_day"])
        
        with col2:
            tot_chol = st.slider("مستوى الكولسترول الكلي (mg/dL)", min_value=120, max_value=400, value=patient_data["tot_chol"])
            sys_bp = st.slider("ضغط الدم الانقباضي (mmHg)", min_value=90, max_value=200, value=patient_data["sys_bp"])
            glucose = st.slider("مستوى السكر في الدم (mg/dL)", min_value=70, max_value=250, value=patient_data["glucose"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("تحليل مخاطر القلب"):
            with st.spinner("جاري تحليل المخاطر..."):
                prediction = predict_heart_disease(age, sex_male, cigs_per_day, tot_chol, sys_bp, glucose)
                
                # تحديث بيانات المريض بنتيجة التحليل
                patient_data["heart_disease_prediction"] = prediction
                local_storage.save_data(patient_data)
                
                st.markdown(f"""
                <div class="heart-prediction">
                <h3>نتيجة التحليل:</h3>
                <p>{prediction}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # عرض توصيات بناءً على النتيجة
                st.subheader("التوصيات الطبية:")
                
                if "عالية" in prediction:
                    st.warning("""
                    - ينصح بمراجعة طبيب القلب في أقرب وقت ممكن
                    - متابعة مستويات ضغط الدم والكولسترول بانتظام
                    - الإقلاع عن التدخين فورًا
                    - اتباع نظام غذائي قليل الدسم والصوديوم
                    - ممارسة الرياضة المعتدلة بانتظام بعد استشارة الطبيب
                    """)
                elif "متوسطة" in prediction:
                    st.info("""
                    - يوصى بزيارة طبيب القلب للمتابعة خلال الشهر القادم
                    - تقليل استهلاك الملح والدهون المشبعة
                    - زيادة النشاط البدني تدريجياً
                    - الإقلاع عن التدخين
                    - مراقبة مستويات الكولسترول وضغط الدم
                    """)
                else:
                    st.success("""
                    - الحفاظ على نمط حياة صحي
                    - متابعة الفحص الدوري سنوياً
                    - المحافظة على ممارسة الرياضة بانتظام
                    - تناول غذاء متوازن
                    - تجنب التدخين
                    """)

    elif page == "مراقبة المؤشرات الحيوية":
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
            # عرض معلومات المريض
            if patient_data["name"]:
                st.write(f"المريض: {patient_data['name']}, العمر: {patient_data['age']}, الجنس: {'ذكر' if patient_data['sex'] == '1' else 'أنثى'}")

            # جميع الإدخالات
            all_entries = st.session_state.thingspeak_data['feeds']

            # مؤشرات صحية (استخدام أحدث إدخال)
            latest_entry = all_entries[-1]

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
                    medical_analysis = analyze_medical_data(model, all_entries)

                # تنسيق التحليل
                st.markdown(f"""
                <div class="analysis-container">
                {medical_analysis}
                </div>
                """, unsafe_allow_html=True)

                # إنشاء تقرير PDF
                pdf_file = generate_pdf_report(patient_data, medical_analysis)
                with open(pdf_file, "rb") as file:
                    st.download_button(
                        label="📥 تحميل التقرير كملف PDF",
                        data=file,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )

            # الرسوم البيانية التفاعلية
            st.subheader("التقارير البيانية")
            temp_chart, humidity_chart, heart_rate_chart, body_temp_chart = create_charts(st.session_state.processed_df.reset_index())

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(temp_chart, use_container_width=True)
                st.plotly_chart(humidity_chart, use_container_width=True)
            with col2:
                st.plotly_chart(heart_rate_chart, use_container_width=True)
                st.plotly_chart(body_temp_chart, use_container_width=True)

            # عرض البيانات الخام
            if show_raw_data:
                st.subheader("البيانات الخام")
                st.dataframe(st.session_state.processed_df)

        else:
            st.warning("الرجاء الضغط على زر تحديث البيانات 🔄")

    # إضافة التعليمات البرمجية للتعامل مع LocalStorage
    st.markdown("""
    <script>
        // استرجاع بيانات المريض من LocalStorage عند تحميل الصفحة
        document.addEventListener('DOMContentLoaded', function() {
            const storedData = localStorage.getItem('patient_data');
            if (storedData) {
                // إرسال البيانات إلى Streamlit (تحتاج إلى تنفيذ معالج خاص بذلك)
                console.log('تم استرجاع بيانات المريض من LocalStorage');
            }
        });
    </script>
    """, unsafe_allow_html=True)

# تغيير نمط الواجهة
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
