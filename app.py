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

# دالة لاستدعاء API توليد الأسئلة من Hugging Face
def generate_questions(text, api_token, question_types):
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # نموذج لتوليد النصوص العربية
    api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
    
    # تحضير النص للنموذج مع التعليمات المنظمة
    system_prompt = f"""
قم بتوليد أسئلة متنوعة من النص التالي باستخدام الصيغة المحددة:

الموضوع: [اسم الفصل أو الوحدة]
الملخص: [ملخص قصير للمحتوى]
الأسئلة:
  - النوع: اختيار من متعدد
    السؤال: ...
    الخيارات: [أ، ب، ج، د]
    الإجابة: ب
  - النوع: كلمات متقاطعة
    الشبكة: [نص أو مصفوفة للشبكة]
    التعريفات: {{أفقيًا: [...], عموديًا: [...]}}
  - النوع: صح أو خطأ
    السؤال: ...
    الإجابة: صحيح
  - النوع: مطابقة
    الأزواج: [{{مصطلح: ..., مطابق له: ...}}]

أنواع الأسئلة المطلوبة: {', '.join(question_types)}

النص المرجعي:
{text[:2000]}...

يرجى إنشاء أسئلة متنوعة وشاملة بناءً على هذا النص:
"""
    
    payload = {"inputs": system_prompt}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# دالة لتوليد أسئلة افتراضية منظمة
def generate_default_questions(text, question_types):
    # استخراج العنوان المحتمل من النص
    lines = text.split('\n')
    topic = "المحتوى المستخرج"
    for line in lines[:5]:
        if line.strip() and len(line.strip()) > 10:
            topic = line.strip()[:50] + "..."
            break
    
    # ملخص قصير
    summary = text[:200].replace('\n', ' ').strip() + "..."
    
    default_structure = f"""
الموضوع: {topic}
الملخص: {summary}
الأسئلة:
"""
    
    # إضافة أسئلة حسب النوع المختار
    if "اختيار من متعدد" in question_types:
        default_structure += """
  - النوع: اختيار من متعدد
    السؤال: ما هي الفكرة الرئيسية للنص؟
    الخيارات: [أ. المفهوم الأول، ب. المفهوم الثاني، ج. المفهوم الثالث، د. جميع ما سبق]
    الإجابة: د
"""
    
    if "صح أو خطأ" in question_types:
        default_structure += """
  - النوع: صح أو خطأ
    السؤال: النص يحتوي على معلومات مفيدة ومفصلة
    الإجابة: صحيح
"""
    
    if "مطابقة" in question_types:
        default_structure += """
  - النوع: مطابقة
    الأزواج: [{مصطلح: "المفهوم الأول", مطابق له: "التعريف الأول"}, {مصطلح: "المفهوم الثاني", مطابق له: "التعريف الثاني"}]
"""
    
    if "كلمات متقاطعة" in question_types:
        default_structure += """
  - النوع: كلمات متقاطعة
    الشبكة: [شبكة 5x5 مع الكلمات المتقاطعة]
    التعريفات: {أفقيًا: ["1. مصطلح من النص", "3. مفهوم مهم"], عموديًا: ["2. كلمة رئيسية", "4. موضوع فرعي"]}
"""
    
    return default_structure

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
                        st.metric("📊 إحصائيات النص", f"{word_count} كلمة، {char_count} حرف")
                    else:
                        st.warning("⚠️ لم يتم العثور على نص في الصفحات المحددة")
            
            # توليد الأسئلة
            if generate_btn:
                with st.spinner("🔄 جاري استخراج النص وتوليد الأسئلة المنظمة..."):
                    # استخراج النص
                    extracted_text, _, error = extract_text_from_pages(uploaded_file, start_page, end_page)
                    
                    if error:
                        st.error(f"❌ حدث خطأ أثناء استخراج النص: {error}")
                    elif extracted_text:
                        # توليد الأسئلة
                        with st.spinner("🤖 جاري توليد الأسئلة المنظمة..."):
                            result = generate_questions(extracted_text, API_TOKEN, question_types)
                            
                            if isinstance(result, dict) and "error" in result:
                                st.error(f"❌ خطأ في API: {result['error']}")
                                
                                # أسئلة افتراضية منظمة في حالة فشل API
                                st.warning("💡 سيتم عرض أسئلة منظمة افتراضية:")
                                default_questions = generate_default_questions(extracted_text, question_types)
                                st.code(default_questions, language="yaml")
                                
                                # زر التحميل للأسئلة الافتراضية
                                st.download_button(
                                    label="📥 تحميل الأسئلة المنظمة",
                                    data=default_questions,
                                    file_name=f"structured_questions_pages_{start_page}-{end_page}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            else:
                                st.success("✅ تم توليد الأسئلة المنظمة بنجاح!")
                                
                                # معالجة استجابة API
                                if isinstance(result, list) and len(result) > 0:
                                    questions = result[0].get("generated_text", "لم يتم توليد أسئلة")
                                else:
                                    questions = str(result)
                                
                                # عرض الأسئلة
                                st.subheader("📝 الأسئلة المنظمة المولدة:")
                                st.markdown("---")
                                st.code(questions, language="yaml")
                                
                                # زر التحميل
                                download_data = f"الأسئلة المنظمة المولدة من الصفحات {start_page}-{end_page}:\n\n{questions}"
                                st.download_button(
                                    label="📥 تحميل الأسئلة المنظمة",
                                    data=download_data,
                                    file_name=f"structured_questions_pages_{start_page}-{end_page}.txt",
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
    4. اختر أنواع الأسئلة المطلوبة
    5. اعاين النص (اختياري)
    6. اضغط على توليد الأسئلة المنظمة
    """)
    
    st.markdown("### 📝 أنواع الأسئلة المتاحة:")
    st.markdown("""
    - **اختيار من متعدد**: أسئلة بخيارات متعددة
    - **صح أو خطأ**: أسئلة بإجابة صحيح/خطأ
    - **مطابقة**: ربط المصطلحات بتعريفاتها
    - **كلمات متقاطعة**: شبكة كلمات متقاطعة
    """)
    
    st.markdown("### 💡 نصائح:")
    st.markdown("""
    - ابدأ بنطاق صغير (2-3 صفحات)
    - اختر 2-3 أنواع من الأسئلة للحصول على تنوع
    - تأكد من وضوح النص في PDF
    - يمكن تحميل الأسئلة بصيغة منظمة
    """)
    
    st.markdown("### 🔗 روابط مفيدة:")
    st.markdown("""
    - [الحصول على API Token](https://huggingface.co/settings/tokens)
    - [نماذج Hugging Face](https://huggingface.co/models)
    """)
