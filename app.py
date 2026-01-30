import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (DÙNG KEY MỚI) =================
# ⚠️ DÁN KEY MỚI VÀO ĐÂY (Key cũ đã bị khóa 24h rồi)
GOOGLE_API_KEY = "DAIzaSyA7Rn_kvSEZ63ZEfIsrTGnZEh57aVCZvEM"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- CHIẾN THUẬT AN TOÀN TUYỆT ĐỐI ---
# Dùng "gemini-pro" bản chuẩn. Con này máy chủ nào cũng nhận diện được.
model = genai.GenerativeModel("gemini-pro")

# ================= 2. GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("System Status: Online (Standard Mode)")

# Hướng dẫn
st.info("👋 Hướng dẫn: Chọn chủ đề -> Bấm Record -> Chờ 5-10 giây để AI chấm điểm.")

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
    with st.spinner("Đang chấm điểm... (Mất khoảng 5 giây)"):
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
            # Hiện nguyên hình lỗi để bắt bệnh
            st.error("⚠️ LỖI:")
            st.code(e)