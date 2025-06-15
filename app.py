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
    api_url = "https://api-inference.huggingface.co/models/aubmindlab/bert-base-arabertv02"
    
    # تحضير النص للنموذج
    prompt = f"بناءً على النص التالي، قم بتوليد أسئلة مفيدة:\n\n{text[:2000]}..."
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# دالة لاستخراج النص من نطاق صفحات محدد
def extract_text_from_pages(pdf_file, start_page, end_page):
    full_text = ""
    try:
        pdf = PdfReader(pdf_file)
        total_pages = len(pdf.pages)
        
        # التأكد من صحة نطاق الصفحات
        start_page = max(1, min(start_page, total_pages))
        end_page = max(start_page, min(end_page, total_pages))
        
        # استخراج النص من الصفحات المحددة
        for page_num in range(start_page - 1, end_page):
            page = pdf.pages[page_num]
            text = page.extract_text()
            if text:
                full_text += f"--- صفحة {page_num + 1} ---\n{text}\n\n"
        
        return full_text, total_pages, None
    except Exception as e:
        return "", 0, str(e)

# واجهة التطبيق
st.set_page_config(
    page_title="مولد الأسئلة من PDF",
    page_icon="📚",
    layout="wide"
)

st.title("📚 مولد الأسئلة من ملفات PDF")
st.markdown("ارفع ملف PDF واختر نطاق الصفحات التي تريد توليد أسئلة منها")

# عرض معلومات الـ Token
if API_TOKEN:
    st.success("✅ تم العثور على API Token")
else:
    st.error("❌ لم يتم إدخال API Token")

uploaded_file = st.file_uploader(
    "ارفع ملف PDF", 
    type=["pdf"],
    help="حد أقصى: 200MB"
)

if uploaded_file is not None and API_TOKEN:
    # استخراج معلومات أساسية عن الملف
    try:
        pdf = PdfReader(uploaded_file)
        total_pages = len(pdf.pages)
        
        st.success(f"✅ تم رفع الملف بنجاح! عدد الصفحات: {total_pages}")
        
        # خيارات نطاق الصفحات
        st.subheader("🔖 اختر نطاق الصفحات:")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
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
                value=min(3, total_pages),
                help=f"اختر من 1 إلى {total_pages}"
            )
        
        with col3:
            if start_page > end_page:
                st.error("⚠️ الصفحة الأولى يجب أن تكون أقل من أو تساوي الصفحة الأخيرة")
            else:
                pages_count = end_page - start_page + 1
                st.info(f"📄 سيتم معالجة {pages_count} صفحة")
        
        if start_page <= end_page:
            # الأزرار
            col1, col2 = st.columns(2)
            
            with col1:
                preview_btn = st.button("👁️ معاينة النص المستخرج", use_container_width=True)
            
            with col2:
                generate_btn = st.button("🤖 توليد الأسئلة", type="primary", use_container_width=True)
            
            # معاينة النص
            if preview_btn:
                with st.spinner("🔄 جاري استخراج النص..."):
                    extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                    
                    if error:
                        st.error(f"❌ حدث خطأ أثناء استخراج النص: {error}")
                    elif extracted_text:
                        st.subheader("📄 النص المستخرج:")
                        st.text_area(
                            f"النص من الصفحات {start_page}-{end_page}:", 
                            extracted_text, 
                            height=400,
                            help="راجع النص قبل توليد الأسئلة"
                        )
                        
                        # حفظ النص في session state
                        st.session_state.extracted_text = extracted_text
                        st.session_state.page_range = f"{start_page}-{end_page}"
                        
                        # إحصائيات النص
                        word_count = len(extracted_text.split())
                        char_count = len(extracted_text)
                        st.metric("📊 إحصائيات النص", f"{word_count} كلمة، {char_count} حرف")
                    else:
                        st.warning("⚠️ لم يتم العثور على نص في الصفحات المحددة")
            
            # توليد الأسئلة
            if generate_btn:
                with st.spinner("🔄 جاري استخراج النص وتوليد الأسئلة..."):
                    # استخراج النص
                    extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                    
                    if error:
                        st.error(f"❌ حدث خطأ أثناء استخراج النص: {error}")
                    elif extracted_text:
                        # توليد الأسئلة
                        with st.spinner("🤖 جاري توليد الأسئلة..."):
                            result = generate_questions(extracted_text, API_TOKEN)
                            
                            if isinstance(result, dict) and "error" in result:
                                st.error(f"❌ خطأ في API: {result['error']}")
                                
                                # أسئلة افتراضية في حالة فشل API
                                st.warning("💡 سيتم عرض أسئلة افتراضية:")
                                default_questions = f"""
### أسئلة مقترحة بناءً على المحتوى:

1. ما هي النقاط الرئيسية المذكورة في النص؟
2. ما هي التفاصيل المهمة التي يجب التركيز عليها؟
3. كيف يمكن تطبيق المعلومات المذكورة عملياً؟
4. ما هي الاستنتاجات التي يمكن استخلاصها؟
5. ما هي التحديات أو المشاكل المطروحة؟

---
**ملاحظة:** هذه أسئلة عامة. لأسئلة أكثر تخصصاً، تحقق من إعدادات API أو جرب نموذج مختلف.
                                """
                                st.markdown(default_questions)
                            else:
                                st.success("✅ تم توليد الأسئلة بنجاح!")
                                
                                # معالجة استجابة API
                                if isinstance(result, list) and len(result) > 0:
                                    questions = result[0].get("generated_text", "لم يتم توليد أسئلة")
                                else:
                                    questions = str(result)
                                
                                # عرض الأسئلة
                                st.subheader("📝 الأسئلة المولدة:")
                                st.markdown("---")
                                st.write(questions)
                                
                                # زر التحميل
                                download_data = f"الأسئلة المولدة من الصفحات {start_page}-{end_page}:\n\n{questions}"
                                st.download_button(
                                    label="📥 تحميل الأسئلة كملف نصي",
                                    data=download_data,
                                    file_name=f"questions_pages_{start_page}-{end_page}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                    else:
                        st.warning("⚠️ لم يتم العثور على نص في النطاق المحدد")
    
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة ملف PDF: {e}")
        st.info("💡 تأكد من أن الملف ليس محمي بكلمة مرور وأنه قابل للقراءة")

# الشريط الجانبي
with st.sidebar:
    st.markdown("### ℹ️ كيفية الاستخدام:")
    st.markdown("""
    1. أدخل Hugging Face API Token
    2. ارفع ملف PDF
    3. اختر نطاق الصفحات
    4. اعاين النص (اختياري)
    5. اضغط على توليد الأسئلة
    """)
    
    st.markdown("### 💡 نصائح:")
    st.markdown("""
    - ابدأ بنطاق صغير (2-3 صفحات)
    - تأكد من وضوح النص في PDF
    - النماذج تعمل بشكل أفضل مع النصوص الواضحة
    - يمكن تحميل الأسئلة كملف نصي
    """)
    
    st.markdown("### 🔗 روابط مفيدة:")
    st.markdown("""
    - [الحصول على API Token](https://huggingface.co/settings/tokens)
    - [نماذج Hugging Face](https://huggingface.co/models)
    """)
