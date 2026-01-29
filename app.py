import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH HỆ THỐNG =================
# Lấy Key từ Secrets (An toàn nhất)
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Nếu chạy local mà chưa set secrets, bạn có thể dán tạm key vào đây để test
    # Nhưng khi đưa lên GitHub Public thì NÊN dùng Secrets
    st.error("⚠️ Chưa tìm thấy API Key trong Secrets.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- CHỌN MODEL TỪ DANH SÁCH ĐẶC BIỆT CỦA BẠN ---
# Dựa trên danh sách bạn vừa quét, ta dùng con này là an toàn nhất:
try:
    model = genai.GenerativeModel("models/gemini-flash-latest")
except:
    # Nếu lỗi, thử con "Lite" đời mới (thường rất rẻ và nhanh)
    model = genai.GenerativeModel("models/gemini-2.0-flash-lite-001")

# ================= 2. GIAO DIỆN HỌC VIÊN =================
st.set_page_config(page_title="IELTS Assessment - Mr. Tat Loc", page_icon="🎓", layout="centered")

# CSS: Giao diện sạch & Chuyên nghiệp
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stApp {background-color: #f4f6f9;}
        h1 {color: #1e3a8a; font-family: 'Helvetica', sans-serif;}
        .instruction-card {
            background-color: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;
            border-left: 6px solid #1e3a8a;
        }
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601")

st.markdown("""
<div class="instruction-card">
    <strong style="color:#1e3a8a;">👋 Hướng dẫn (Instructions):</strong>
    <ol>
        <li>Chọn Topic bên dưới.</li>
        <li>Bấm <b>Record</b> và trả lời (20-40 giây).</li>
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

st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("AI is analyzing..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File ghi âm quá ngắn hoặc lỗi. Vui lòng thử lại.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            # Prompt tiếng Anh để tránh lỗi encoding
            prompt = f"""
            Role: IELTS Examiner. Task: Assess speaking for "{selected_q}".
            
            INSTRUCTIONS:
            1. Determine Band Score (0-9.0).
            2. Provide feedback strictly in VIETNAMESE.
            3. LEVEL-ADAPTIVE:
               - If Band < 5.0: Suggest simple improvements (Target Band 6.0). NO complex idioms.
               - If Band 6.0+: Suggest advanced vocabulary (Target Band 7.5+).
            
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá (Band Score):** [Score]
            **2. Nhận xét (Pros & Cons):** [Pronunciation, Grammar, Fluency]
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
            st.info("💡 Tip: Hãy chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            st.error("⚠️ Lỗi kết nối. Vui lòng thử lại sau 30 giây.")
            # st.code(e) # Đã ẩn lỗi kỹ thuật