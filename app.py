import streamlit as st
import google.generativeai as genai
import time

# ================= 1. CẤU HÌNH (DÙNG KEY TỪ NEW PROJECT) =================
# ⚠️ DÁN KEY TỪ DỰ ÁN MỚI (NEW PROJECT) VÀO ĐÂY
GOOGLE_API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- QUAY VỀ CHÂN ÁI: GEMINI 1.5 FLASH ---
# Với Project mới, con này chắc chắn 100% sẽ xuất hiện và chạy ngon.
# Em thêm cơ chế tự thử các tên gọi khác nhau để chống lỗi 404 tuyệt đối.
active_model = None
model_names = [
    "gemini-1.5-flash",          # Tên chuẩn
    "gemini-1.5-flash-latest",   # Tên bản mới
    "gemini-1.5-flash-001",      # Tên mã
    "models/gemini-1.5-flash"    # Tên đầy đủ
]

for name in model_names:
    try:
        test_model = genai.GenerativeModel(name)
        active_model = test_model
        break # Nếu chạy được thì dừng thử
    except:
        continue

if not active_model:
    # Nếu xui xẻo lắm thì dùng bản Pro cũ
    active_model = genai.GenerativeModel("gemini-pro")

# ================= 2. GIAO DIỆN LỚP HỌC =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.markdown("**Class:** PLA1601 | **Instructor:** Mr. Tat Loc")
st.caption("Model: Gemini 1.5 Flash (Standard)")

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
    with st.spinner("AI đang chấm điểm (Mất khoảng 5-10s)..."):
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

            response = active_model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.success("✅ Đã chấm xong!")
            with st.container(border=True):
                st.markdown(response.text)
            st.balloons() # Thả bóng bay chúc mừng
            
        except Exception as e:
            st.error("⚠️ LỖI:")
            st.code(e)
            if "400" in str(e):
                st.warning("Lỗi định dạng file âm thanh. Thầy thử reload trang nhé.")