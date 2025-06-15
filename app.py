import os
import streamlit as st
from PyPDF2 import PdfReader
import requests

# This MUST be the first Streamlit command
st.set_page_config(
    page_title="مولد الأسئلة من PDF",
    page_icon="📚",
    layout="wide"
)

# قراءة رمز API من secrets أو متغير البيئة
API_TOKEN = st.secrets.get("API_TOKEN") or os.getenv("API_TOKEN")

# إذا لم يوجد، اطلبه من المستخدم
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

# النماذج العربية المتاحة في Inference API
ARABIC_MODELS = {
    "microsoft/DialoGPT-medium": "DialoGPT Medium - نموذج المحادثة",
    "gpt2": "GPT-2 - نموذج توليد النصوص (يدعم العربية)",
    "facebook/blenderbot-400M-distill": "BlenderBot - نموذج محادثة ذكي",
    "microsoft/DialoGPT-small": "DialoGPT Small - نموذج محادثة مبسط"
}

# دالة لاستدعاء API توليد الأسئلة من Hugging Face
def generate_questions(text, api_token, question_types, selected_model):
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # استخدام النموذج المختار
    api_url = f"https://api-inference.huggingface.co/models/{selected_model}"
    
    # تحضير النص للنموذج (تبسيط الـ prompt)
    prompt = f"أنشئ أسئلة من النص التالي:\n\n{text[:1000]}\n\nالأسئلة:"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# دالة لتوليد أسئلة افتراضية محسنة
def generate_default_questions(text, question_types):
    # استخراج العنوان المحتمل من النص
    lines = text.split('\n')
    topic = "المحتوى المستخرج"
    
    # البحث عن عنوان مناسب
    for line in lines[:10]:
        if line.strip() and len(line.strip()) > 5 and len(line.strip()) < 100:
            # تجنب الأرقام والرموز
            if not line.strip().isdigit() and not line.strip().startswith('---'):
                topic = line.strip()[:60]
                break
    
    # استخراج الكلمات المفتاحية
    words = text.replace('\n', ' ').split()
    keywords = []
    for word in words[:50]:  # أول 50 كلمة
        if len(word) > 3 and word.isalpha():
            keywords.append(word)
    
    # ملخص قصير
    sentences = text.split('.')
    summary = ""
    for sentence in sentences[:3]:
        if len(sentence.strip()) > 10:
            summary += sentence.strip() + ". "
    
    if not summary:
        summary = text[:150].replace('\n', ' ').strip() + "..."
    
    # بناء الأسئلة المنظمة
    questions_structure = f"""
الموضوع: {topic}
الملخص: {summary}

الأسئلة المولدة:
========================
"""
    
    question_count = 1
    
    # إضافة أسئلة حسب النوع المختار
    if "اختيار من متعدد" in question_types:
        questions_structure += f"""
{question_count}. النوع: اختيار من متعدد
   السؤال: ما هو الموضوع الرئيسي المتناول في النص؟
   الخيارات:
   أ) {keywords[0] if len(keywords) > 0 else 'الخيار الأول'}
   ب) {keywords[1] if len(keywords) > 1 else 'الخيار الثاني'}
   ج) {keywords[2] if len(keywords) > 2 else 'الخيار الثالث'}
   د) جميع ما سبق
   الإجابة الصحيحة: د

"""
        question_count += 1
    
    if "صح أو خطأ" in question_types:
        questions_structure += f"""
{question_count}. النوع: صح أو خطأ
   السؤال: النص يحتوي على معلومات تفصيلية ومفيدة حول الموضوع
   الإجابة: صحيح
   التبرير: النص يقدم معلومات شاملة ومفصلة

"""
        question_count += 1
    
    if "مطابقة" in question_types:
        questions_structure += f"""
{question_count}. النوع: مطابقة
   اربط بين المصطلحات والتعريفات:
   المصطلحات: {', '.join(keywords[:3]) if len(keywords) >= 3 else 'المصطلح الأول، المصطلح الثاني، المصطلح الثالث'}
   التعريفات: [تعريف مفصل لكل مصطلح بناءً على السياق]

"""
        question_count += 1
    
    if "كلمات متقاطعة" in question_types:
        questions_structure += f"""
{question_count}. النوع: كلمات متقاطعة
   شبكة الكلمات المتقاطعة: [شبكة 7×7]
   الكلمات المستخدمة: {', '.join(keywords[:5]) if len(keywords) >= 5 else 'كلمات مفتاحية من النص'}
   
   التعريفات:
   أفقياً:
   - 1. {keywords[0] if len(keywords) > 0 else 'مصطلح من النص'} (4 أحرف)
   - 3. {keywords[1] if len(keywords) > 1 else 'مفهوم مهم'} (6 أحرف)
   
   عمودياً:
   - 2. {keywords[2] if len(keywords) > 2 else 'كلمة رئيسية'} (5 أحرف)
   - 4. {keywords[3] if len(keywords) > 3 else 'موضوع فرعي'} (7 أحرف)

"""
    
    # إضافة معلومات إضافية
    questions_structure += f"""
========================
معلومات إضافية:
- عدد الكلمات في النص: {len(text.split())}
- عدد الأحرف: {len(text)}
- الكلمات المفتاحية المستخرجة: {', '.join(keywords[:10])}
- تاريخ الإنشاء: {st.session_state.get('generation_time', 'غير محدد')}
"""
    
    return questions_structure

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

# دالة للتحقق من حالة النموذج
def check_model_status(model_name, api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = f"https://api-inference.huggingface.co/models/{model_name}"
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

# واجهة التطبيق
st.title("📚 مولد الأسئلة المتنوعة من ملفات PDF")
st.markdown("ارفع ملف PDF واختر نطاق الصفحات وأنواع الأسئلة التي تريد توليدها")

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
        
        # اختيار النموذج مع التحقق من الحالة
        st.subheader("🤖 اختر النموذج:")
        selected_model = st.selectbox(
            "النموذج المستخدم:",
            options=list(ARABIC_MODELS.keys()),
            format_func=lambda x: ARABIC_MODELS[x],
            help="اختر النموذج الأنسب لتوليد الأسئلة"
        )
        
        # التحقق من حالة النموذج
        with st.spinner("🔍 جاري التحقق من حالة النموذج..."):
            model_available = check_model_status(selected_model, API_TOKEN)
            
        if model_available:
            st.success(f"✅ النموذج {ARABIC_MODELS[selected_model]} متاح ويعمل")
        else:
            st.warning(f"⚠️ النموذج قد يكون غير متاح حالياً، سيتم استخدام الأسئلة الافتراضية")
        
        # خيارات نطاق الصفحات مع القيم الافتراضية المحدثة
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
                value=total_pages,
                help=f"اختر من 1 إلى {total_pages}"
            )
        
        with col3:
            if start_page > end_page:
                st.error("⚠️ الصفحة الأولى يجب أن تكون أقل من أو تساوي الصفحة الأخيرة")
            else:
                pages_count = end_page - start_page + 1
                st.info(f"📄 سيتم معالجة {pages_count} صفحة")
        
        # اختيار أنواع الأسئلة
        st.subheader("📝 اختر أنواع الأسئلة:")
        question_types = st.multiselect(
            "أنواع الأسئلة المطلوبة:",
            options=["اختيار من متعدد", "صح أو خطأ", "مطابقة", "كلمات متقاطعة"],
            default=["اختيار من متعدد", "صح أو خطأ"],
            help="اختر نوع واحد أو أكثر من أنواع الأسئلة"
        )
        
        if not question_types:
            st.warning("⚠️ يرجى اختيار نوع واحد على الأقل من أنواع الأسئلة")
        
        if start_page <= end_page and question_types:
            # الأزرار
            col1, col2 = st.columns(2)
            
            with col1:
                preview_btn = st.button("👁️ معاينة النص المستخرج", use_container_width=True)
            
            with col2:
                generate_btn = st.button("🤖 توليد الأسئلة المنظمة", type="primary", use_container_width=True)
            
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
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 عدد الكلمات", word_count)
                        with col2:
                            st.metric("📝 عدد الأحرف", char_count)
                        with col3:
                            st.metric("📄 عدد الصفحات", pages_count)
                    else:
                        st.warning("⚠️ لم يتم العثور على نص في الصفحات المحددة")
            
            # توليد الأسئلة
            if generate_btn:
                import datetime
                st.session_state.generation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with st.spinner("🔄 جاري استخراج النص وتوليد الأسئلة المنظمة..."):
                    # استخراج النص
                    extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                    
                    if error:
                        st.error(f"❌ حدث خطأ أثناء استخراج النص: {error}")
                    elif extracted_text:
                        # محاولة توليد الأسئلة باستخدام API
                        api_success = False
                        if model_available:
                            with st.spinner(f"🤖 جاري توليد الأسئلة باستخدام {ARABIC_MODELS[selected_model]}..."):
                                result = generate_questions(extracted_text, API_TOKEN, question_types, selected_model)
                                
                                if isinstance(result, dict) and "error" not in result:
                                    api_success = True
                                    st.success("✅ تم توليد الأسئلة بواسطة AI بنجاح!")
                                    
                                    # معالجة استجابة API
                                    if isinstance(result, list) and len(result) > 0:
                                        questions = result[0].get
