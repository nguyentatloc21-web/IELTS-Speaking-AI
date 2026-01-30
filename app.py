import streamlit as st
import google.generativeai as genai
import time

# ================= 1. CẤU HÌNH (DÙNG KEY MỚI) =================
# ⚠️ DÁN KEY MỚI VÀO ĐÂY
GOOGLE_API_KEY = "AIzaSyA7Rn_kvSEZ63ZEfIsrTGnZEh57aVCZvEM"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- CHIẾN THUẬT "BẮN LIÊN THANH" (SHOTGUN STRATEGY) ---
# Thử lần lượt các tên gọi khác nhau của dòng 1.5 Flash
# Con nào chạy được thì lấy luôn, không quan tâm tên gì.
candidate_models = [
    "gemini-1.5-flash",          # Tên chuẩn
    "models/gemini-1.5-flash",   # Tên đầy đủ
    "gemini-1.5-flash-latest",   # Tên bản mới nhất
    "gemini-1.5-flash-001",      # Tên mã hiệu
    "gemini-1.5-flash-002"       # Tên bản nâng cấp
]

active_model = None
error_log = []

for m_name in candidate_models:
    try:
        # Thử khởi tạo
        test_model = genai.GenerativeModel(m_name)
        active_model = test_model
        # Nếu dòng này chạy qua mà không lỗi -> Thành công!
        break 
    except Exception as e:
        error_log.append(str(e))
        continue

# Nếu thử hết 5 cái tên mà vẫn xịt -> Do thư viện quá cũ
if not active_model:
    st.error("⚠️ LỖI PHIÊN BẢN CŨ (Cần cập nhật requirements.txt)")
    st.warning("Máy chủ chưa chịu cập nhật phần mềm. Thầy hãy làm Bước 3 (Xóa Cache) nhé!")
    st.stop()

# ================= 2. GIAO DIỆN LỚP HỌC =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc | **Model:** Gemini 1.5 Flash")

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
            
        except Exception as e:
            st.error("⚠️ CÓ LỖI XẢY RA:")
            st.code(e)