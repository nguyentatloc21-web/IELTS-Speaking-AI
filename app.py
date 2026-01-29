import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH =================
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Chưa nhập API Key. Hãy vào Settings -> Secrets để nhập.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- SỬA LỖI 404: THỬ CÁC TÊN GỌI KHÁC NHAU ---
# Máy chủ đôi khi hiểu tên này, đôi khi hiểu tên kia. Ta thử cả 2.
try:
    # Thử tên ngắn gọn trước (Thường dùng cho bản mới)
    model = genai.GenerativeModel("gemini-1.5-flash")
except:
    try:
        # Nếu lỗi, thử thêm tiền tố models/
        model = genai.GenerativeModel("models/gemini-1.5-flash")
    except:
        # Đường cùng: Dùng bản Pro cũ (Chắc chắn chạy nhưng hạn mức ít hơn chút)
        model = genai.GenerativeModel("gemini-pro")

# ================= 2. GIAO DIỆN (UI) =================
st.set_page_config(page_title="IELTS Assessment", page_icon="🎙️")

st.markdown("""
    <style>
        .stApp {background-color: #f4f6f9;}
        .instruction-box {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1e3a8a; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {color: #1e3a8a;}
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Class:** PLA1601 | **Instructor:** Mr. Tat Loc")

st.markdown("""
<div class="instruction-box">
    <strong>👋 Hướng dẫn (Instructions):</strong>
    <ol>
        <li>Chọn Topic bên dưới.</li>
        <li>Bấm <b>Record</b> và trả lời (20-40s).</li>
        <li>Chụp màn hình kết quả nộp bài.</li>
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
                st.error("⚠️ File quá ngắn. Vui lòng thử lại.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess speaking for: "{selected_q}".
            
            INSTRUCTIONS:
            1. Determine Band Score.
            2. Provide feedback strictly in VIETNAMESE.
            3. LEVEL-ADAPTIVE:
               - If Band < 5.0: Suggest simple improvements (Band 6.0). NO idioms.
               - If Band 6.0+: Suggest advanced vocabulary (Band 7.5+).
            
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá (Estimated Band):** [Score]
            **2. Nhận xét:** [Pros/Cons]
            **3. Sửa lỗi & Nâng cấp:** [Correction -> Better Phrase]
            **4. Tổng kết:** [Conclusion]
            """

            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.divider()
            st.success("✅ Assessment Completed!")
            with st.container(border=True):
                st.markdown(response.text)
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            st.error("⚠️ LỖI KẾT NỐI (Vui lòng thử lại sau 30s):")
            # Chỉ hiện mã lỗi ngắn gọn để không làm rối mắt
            st.code(str(e)[0:100] + "...")