import os
import streamlit as st
from PyPDF2 import PdfReader
import requests

# قراءة رمز API من متغير البيئة
API_TOKEN = os.getenv("API_TOKEN")

# إذا لم يوجد في متغيرات البيئة، اطلبه من المستخدم
if not API_TOKEN:
    st.warning("⚠️ لم يتم العثور على API Token في إعدادات التطبيق")
    API_TOKEN = st.text_input(
        "أدخل Hugging Face API Token:", 
        type="password",
        help="احصل على الـ Token من huggingface.co/settings/tokens"
    )
    
    if not API_TOKEN:
        st.info("💡 يمكنك الحصول على Token مجاني من: https://huggingface.co/settings/tokens")
        st.stop()

# دالة لاستدعاء API توليد الأسئلة من Hugging Face
def generate_questions(text, api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # نموذج لتوليد النصوص العربية
    api_url = "https://api-inference.huggingface.co/models/aub
