import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (DÙNG KEY MỚI) =================
# ⚠️ DÁN KEY MỚI VÀO ĐÂY
GOOGLE_API_KEY = "AIzaSyA7Rn_kvSEZ63ZEfIsrTGnZEh57aVCZvEM"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- CHỌN ĐÚNG MODEL CÓ TRONG TÀI KHOẢN THẦY ---
# Tuyệt đối không gọi 1.5 Flash nữa vì tài khoản thầy không có.
# Gọi chính xác tên này (Đã check trong list thầy gửi):
try:
    model = genai.GenerativeModel("models/gemini-2.0-flash-lite-001")
except:
    # Nếu xui quá thì thử gọi tên ngắn gọn của nó
    model = genai.GenerativeModel("gemini-2.0-flash-lite-001")

# ================= 2. GIAO DIỆN LỚP HỌC =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc | **Model:** Gemini 2.0 Flash Lite")

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
    with st.spinner("AI đang chấm điểm (Model 2.0 Lite)..."):
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
            
            st.success("✅ Đã chấm xong!")
            with st.container(border=True):
                st.markdown(response.text)
            
        except Exception as e:
            st.error("⚠️ LỖI KẾT NỐI:")
            st.code(e)
            # Kiểm tra nếu lỗi 429 (Hết lượt)
            if "429" in str(e):
                st.warning("Key này đã hết hạn mức hôm nay. Vui lòng đổi Key khác.")
            # Kiểm tra lỗi 404 (Không tìm thấy model)
            elif "404" in str(e):
                st.warning("Vẫn không tìm thấy Model. Có thể Google đang cập nhật danh sách.")