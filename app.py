import os
import streamlit as st
from pypdf import PdfReader  # تغيير الاستيراد
import requests

# قراءة رمز API من متغير البيئة
API_TOKEN = os.getenv("API_TOKEN")

if not API_TOKEN:
    st.error("لم يتم العثور على API_TOKEN في متغيرات البيئة. الرجاء إضافته.")
    st.stop()

# دالة لاستدعاء API توليد الأسئلة من Hugging Face
def generate_questions(text, api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": text}
    api_url = "https://api-inference.huggingface.co/models/your-model-name"  # استبدل your-model-name باسم النموذج الصحيح
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API request failed with status {response.status_code}"}

st.title("مولد الأسئلة من ملفات PDF")

uploaded_file = st.file_uploader("ارفع ملف PDF", type=["pdf"])

if uploaded_file is not None:
    try:
        pdf = PdfReader(uploaded_file)
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
        st.text_area("نص المحتوى المستخرج من الملف:", full_text, height=300)
        
        if st.button("توليد الأسئلة"):
            with st.spinner("جاري توليد الأسئلة..."):
                result = generate_questions(full_text, API_TOKEN)
                if "error" in result:
                    st.error(result["error"])
                else:
                    # عرض الأسئلة بشكل مرتب (حسب شكل الاستجابة)
                    questions = result.get("generated_text", "لم يتم توليد أسئلة")
                    st.markdown(f"### الأسئلة المولدة:\n{questions}")
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف PDF: {e}")
