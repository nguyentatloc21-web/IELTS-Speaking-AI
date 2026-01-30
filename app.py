import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (DÙNG KEY MỚI) =================
# ⚠️ DÁN KEY MỚI VÀO ĐÂY
GOOGLE_API_KEY = "DÁN_KEY_MỚI_CỦA_THẦY_VÀO_ĐÂY"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- DÙNG GEMINI 1.5 FLASH (BẢN CHUẨN) ---
# Con này mới nghe được âm thanh. Code dưới sẽ xử lý lỗi 404.
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
except:
    # Dự phòng nếu máy chủ chưa cập nhật kịp
    model = genai.GenerativeModel("models/gemini-1.5-flash")

# ================= 2. GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.markdown("**Class:** PLA1601 | **Instructor:** Mr. Tat Loc")

# Hướng dẫn
st.info("👋 Hướng dẫn: Chọn chủ đề -> Bấm Record -> Chờ AI chấm điểm.")

questions = [
    "Part 1: What is your daily routine like?",
    "Part 1: Are you a morning person or a night person?",
    "Part 1: Do you often eat breakfast at home or outside?",
    "Part 1: Do you have a healthy lifestyle?",
    "Part 1: What do you usually do in your free time?",
    "Part 1: Do you prefer spending time alone or with friends?",
    "Part 1: Is there any new hobby you want to try in the future?",
    "Part 1: How do you relax after a stressful day?"
]
selected_q = st.selectbox("📌 Select a Topic:", questions)

st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("AI đang chấm điểm..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess speaking for: "{selected_q}".
            Feedback in VIETNAMESE.
            Output: Band Score, Pros/Cons, Fixes, Conclusion.
            """

            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.success("✅ Đã xong!")
            with st.container(border=True):
                st.markdown(response.text)
            
        except Exception as e:
            st.error("⚠️ LỖI KỸ THUẬT:")
            st.code(e)
            st.warning("👉 Nếu thấy lỗi 404: Thầy hãy làm Bước 3 (Xóa Cache) bên dưới.")