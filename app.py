import os
import streamlit as st
import pdfplumber
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
    api_url = "https://api-inference.huggingface.co/models/your-model-name"
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API request failed with status {response.status_code}"}

# دالة لاستخراج النص من نطاق صفحات محدد
def extract_text_from_pages(pdf_file, start_page, end_page):
    full_text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            
            # التأكد من صحة نطاق الصفحات
            start_page = max(1, min(start_page, total_pages))
            end_page = max(start_page, min(end_page, total_pages))
            
            # استخراج النص من الصفحات المحددة (تحويل إلى فهرس يبدأ من 0)