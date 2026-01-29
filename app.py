import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (DÙNG BẢN CŨ CHO AN TOÀN) =================
try:
    if "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("⚠️ Chưa nhận được API Key.")
        st.stop()
        
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
    
    # --- DÙNG GEMINI PRO (BẢN 1.0) ---
    # Con này tuy cũ hơn Flash nhưng siêu ổn định, không bao giờ lỗi 404
    model = genai.GenerativeModel("gemini-pro")
    
except Exception as e:
    st.error(f"Lỗi khởi tạo: {e}")
    st.stop()

# ================= 2. GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")

st.markdown("""
    <style>
        .stApp {background-color: #f4f6f9;}
        .instruction-box {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1e3a8a; margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.caption("Model: Gemini Pro (Stable)")

st.markdown("""
<div class="instruction-box">
    <strong>Hướng dẫn:</strong> Chọn chủ đề, bấm Record và trả lời trong 30s.
</div>
""", unsafe_allow_html=True)

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
selected_q = st.selectbox("Topic:", questions)

audio_value = st.audio_input("Record Answer")

if audio_value:
    with st.spinner("Analyzing..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.warning("Ghi âm quá ngắn.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess: "{selected_q}".
            Feedback in VIETNAMESE.
            Output: Band Score, Pros/Cons, Fixes, Conclusion.
            """

            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.success("✅ Done!")
            with st.container(border=True):
                st.markdown(response.text)
            
        except Exception as e:
            st.error("Lỗi:")
            st.code(e)