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
            for page_num in range(start_page - 1, end_page):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    full_text += f"--- صفحة {page_num + 1} ---\n{text}\n\n"
            
            return full_text, total_pages, None
    except Exception as e:
        return "", 0, str(e)

st.title("مولد الأسئلة من ملفات PDF")
st.markdown("ارفع ملف PDF واختر نطاق الصفحات التي تريد توليد أسئلة منها")

uploaded_file = st.file_uploader("ارفع ملف PDF", type=["pdf"])

if uploaded_file is not None:
    # استخراج معلومات أساسية عن الملف
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            total_pages = len(pdf.pages)
        
        st.success(f"تم رفع الملف بنجاح! عدد الصفحات: {total_pages}")
        
        # خيارات نطاق الصفحات
        st.subheader("اختر نطاق الصفحات:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_page = st.number_input(
                "الصفحة الأولى:", 
                min_value=1, 
                max_value=total_pages, 
                value=1,
                help=f"اختر من 1 إلى {total_pages}"
            )
        
        with col2:
            end_page = st.number_input(
                "الصفحة الأخيرة:", 
                min_value=1, 
                max_value=total_pages, 
                value=min(5, total_pages),
                help=f"اختر من 1 إلى {total_pages}"
            )
        
        # التأكد من صحة النطاق
        if start_page > end_page:
            st.warning("⚠️ الصفحة الأولى يجب أن تكون أقل من أو تساوي الصفحة الأخيرة")
        else:
            pages_count = end_page - start_page + 1
            st.info(f"سيتم استخراج النص من {pages_count} صفحة (من صفحة {start_page} إلى صفحة {end_page})")
            
            # زر معاينة النص
            if st.button("معاينة النص المستخرج"):
                with st.spinner("جاري استخراج النص..."):
                    extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                    
                    if error:
                        st.error(f"حدث خطأ أثناء استخراج النص: {error}")
                    elif extracted_text:
                        st.text_area(
                            f"النص المستخرج من الصفحات {start_page}-{end_page}:", 
                            extracted_text, 
                            height=300,
                            help="راجع النص قبل توليد الأسئلة"
                        )
                        
                        # حفظ النص في session state للاستخدام لاحقاً
                        st.session_state.extracted_text = extracted_text
                    else:
                        st.warning("لم يتم العثور على نص في الصفحات المحددة")
            
            # زر توليد الأسئلة
            st.subheader("توليد الأسئلة:")
            
            if st.button("🤖 توليد الأسئلة من النطاق المحدد", type="primary"):
                with st.spinner("جاري استخراج النص وتوليد الأسئلة..."):
                    # استخراج النص إذا لم يكن محفوظاً مسبقاً
                    if 'extracted_text' not in st.session_state:
                        extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                        if error:
                            st.error(f"حدث خطأ أثناء استخراج النص: {error}")
                            st.stop()
                    else:
                        extracted_text = st.session_state.extracted_text
                    
                    if extracted_text:
                        # توليد الأسئلة
                        result = generate_questions(extracted_text, API_TOKEN)
                        
                        if "error" in result:
                            st.error(f"خطأ في API: {result['error']}")
                        else:
                            st.success("تم توليد الأسئلة بنجاح!")
                            questions = result.get("generated_text", "لم يتم توليد أسئلة")
                            
                            # عرض الأسئلة في صندوق منفصل
                            st.markdown("### 📝 الأسئلة المولدة:")
                            st.markdown("---")
                            st.write(questions)
                            
                            # خيار تحميل الأسئلة كملف نصي
                            st.download_button(
                                label="📥 تحميل الأسئلة كملف نصي",
                                data=f"الأسئلة المولدة من الصفحات {start_page}-{end_page}:\n\n{questions}",
                                file_name=f"questions_pages_{start_page}-{end_page}.txt",
                                mime="text/plain"
                            )
                    else:
                        st.warning("لم يتم العثور على نص في النطاق المحدد")
    
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف PDF: {e}")

# معلومات إضافية في الشريط الجانبي
with st.sidebar:
    st.markdown("### ℹ️ كيفية الاستخدام:")
    st.markdown("""
    1. ارفع ملف PDF
    2. اختر نطاق الصفحات
    3. اعاين النص (اختياري)
    4. اضغط على توليد الأسئلة
    """)
    
    st.markdown("### 💡 نصائح:")
    st.markdown("""
    - ابدأ بنطاق صغير للاختبار
    - تأكد من وضوح النص في الصفحات
    - يمكنك تحميل الأسئلة كملف نصي
    """)