import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (BẮT BUỘC) =================
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Chưa thiết lập API Key trên Streamlit Cloud.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- ÉP DÙNG MODEL CƠ BẢN NHẤT (ĐỂ KHÔNG BỊ HẾT QUOTA) ---
# Chúng ta không dùng hàm tự động nữa. Gọi đích danh luôn.
try:
    model = genai.GenerativeModel("models/gemini-1.5-flash")
except:
    model = genai.GenerativeModel("gemini-1.5-flash")

# ================= 2. GIAO DIỆN CHUYÊN NGHIỆP =================
st.set_page_config(page_title="IELTS Assessment - Mr. Tat Loc", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stApp {background-color: #f4f6f9;}
        .instruction-card {
            background-color: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;
            border-left: 5px solid #1e3a8a;
        }
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601")

st.markdown("""
<div class="instruction-card">
    <h3 style="margin-top:0; color:#1e3a8a;">👋 Instructions</h3>
    <ol>
        <li>Chọn chủ đề (Topic) bên dưới.</li>
        <li>Bấm nút <b>Record</b> và trả lời (Khoảng 30 giây).</li>
        <li>Chụp màn hình kết quả Feedback nộp vào nhóm lớp.</li>
    </ol>
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
selected_q = st.selectbox("📌 Select a Topic:", questions)

st.write("🎙️ **Your Answer (Record in English):**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("AI is analyzing..."):
        try:
            audio_bytes = audio_value.read()
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Task: Assess speaking answer for "{selected_q}".
            INSTRUCTIONS:
            1. Analyze audio for CURRENT Level.
            2. Provide feedback strictly in VIETNAMESE.
            3. LEVEL-ADAPTIVE:
               - If Band < 5.0: Suggest simple improvements (Band 6.0). NO idioms.
               - If Band 6.0+: Suggest advanced vocabulary (Band 7.5+).
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá (Band Score):** [Score]
            **2. Nhận xét:** [Strengths/Weaknesses]
            **3. Sửa lỗi & Nâng cấp:** [Correction -> Better Phrase]
            **4. Tổng kết:** [Professional encouraging conclusion]
            """

            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.divider()
            st.success("✅ Assessment Completed!")
            with st.container(border=True):
                st.markdown(response.text)
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            st.error("⚠️ Hệ thống đang quá tải (Hết lượt miễn phí hôm nay).")
            st.info("👉 Giải pháp: Thầy Lộc vui lòng tạo API Key mới (Cách 1) để tiếp tục sử dụng ngay.")