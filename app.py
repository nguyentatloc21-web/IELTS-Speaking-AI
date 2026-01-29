import streamlit as st
import google.generativeai as genai
import time

# ================= 1. CẤU HÌNH AN TOÀN =================
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Chưa nhập API Key trên hệ thống.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- QUAN TRỌNG: CỐ ĐỊNH MODEL 1.5 FLASH (Miễn phí 1500 lượt/ngày) ---
# Không dùng code tự động dò tìm nữa để tránh chọn nhầm model giới hạn
model = genai.GenerativeModel("models/gemini-1.5-flash")

# ================= 2. GIAO DIỆN CHUYÊN NGHIỆP =================
st.set_page_config(page_title="IELTS Assessment - Mr. Tat Loc", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stApp {background-color: #f4f6f9;}
        .instruction-card {
            background-color: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;
            border-left: 6px solid #1e3a8a;
        }
        h1 {color: #1e3a8a; font-family: 'Helvetica', sans-serif; font-weight: 700;}
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601")

st.markdown("""
<div class="instruction-card">
    <h3 style="margin-top:0; color:#1e3a8a;">👋 Instructions</h3>
    <ol>
        <li>Chọn chủ đề (Topic) bên dưới.</li>
        <li>Bấm nút <b>Record</b> và trả lời (20-40 giây).</li>
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
    with st.spinner("AI is analyzing your speaking performance..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500: # Lọc file quá ngắn/lỗi
                st.error("⚠️ File ghi âm lỗi hoặc quá ngắn. Vui lòng thử lại.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Task: Assess speaking answer for "{selected_q}".
            
            INSTRUCTIONS:
            1. Analyze audio to determine the student's CURRENT Band Score.
            2. Provide feedback strictly in VIETNAMESE.
            3. LEVEL-ADAPTIVE FEEDBACK:
               - If Band < 5.0: Suggest simple improvements (Target Band 6.0). Avoid complex idioms.
               - If Band 6.0+: Suggest advanced vocabulary (Target Band 7.5+).
            
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá (Estimated Band):** [Score]
            **2. Nhận xét (Pros & Cons):** [Pronunciation, Fluency, Grammar]
            **3. Sửa lỗi & Nâng cấp:** [Original -> Better Version]
            **4. Tổng kết:** [Professional encouraging conclusion]
            """

            # Gửi yêu cầu
            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            # Hiển thị kết quả
            st.divider()
            st.success("✅ Assessment Completed!")
            with st.container(border=True):
                st.markdown(response.text)
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            # Xử lý lỗi đẹp để học viên không hoang mang
            err_msg = str(e)
            if "429" in err_msg:
                st.warning("⚠️ Hệ thống đang bận (Quá nhiều người nộp cùng lúc). Vui lòng đợi 1 phút rồi thử lại!")
            else:
                st.error("⚠️ Lỗi kết nối mạng. Hãy bấm F5 (Tải lại trang) và thử lại.")
                # st.write(e) # Ẩn lỗi kỹ thuật đi