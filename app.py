import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (SETUP) =================
# Lấy Key từ Secrets
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Chưa nhập API Key. Hãy vào Settings -> Secrets để nhập.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# Dùng Model chuẩn "Ngon-Bổ-Rẻ" (Gemini 1.5 Flash)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ================= 2. GIAO DIỆN (UI) =================
st.set_page_config(page_title="IELTS Assessment", page_icon="🎙️")

st.markdown("""
    <style>
        .stApp {background-color: #f4f6f9;}
        .instruction-box {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1e3a8a; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Class:** PLA1601 | **Instructor:** Mr. Tat Loc")

# Hướng dẫn
st.markdown("""
<div class="instruction-box">
    <strong>👋 Hướng dẫn (Instructions):</strong>
    <ol>
        <li>Chọn Topic bên dưới.</li>
        <li>Bấm <b>Record</b> và trả lời (30s).</li>
        <li>Chụp màn hình kết quả nộp bài.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Chọn câu hỏi
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

# Thu âm
st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("Analyzing..."):
        try:
            # Xử lý âm thanh
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn hoặc lỗi.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess speaking for: "{selected_q}".
            Instructions:
            1. Determine Band Score.
            2. Feedback in VIETNAMESE.
            3. Level-adaptive suggestions (Band 4->6, Band 6->7.5).
            
            Output:
            **1. Band Score:** [Score]
            **2. Nhận xét:** [Pros/Cons]
            **3. Sửa lỗi:** [Fixes]
            **4. Tổng kết:** [Conclusion]
            """

            # Gọi AI
            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            # Kết quả
            st.success("✅ Done!")
            with st.container(border=True):
                st.markdown(response.text)
            
        except Exception as e:
            # --- ĐÂY LÀ PHẦN QUAN TRỌNG ĐỂ BẮT LỖI ---
            st.error("⚠️ CÓ LỖI KỸ THUẬT (Gửi ảnh này cho Admin):")
            st.code(e) # Hiện nguyên văn lỗi tiếng Anh
            st.info("Thầy hãy chụp dòng chữ đỏ trong khung ở trên gửi cho em nhé!")