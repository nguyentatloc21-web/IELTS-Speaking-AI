import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH (QUAN TRỌNG: DÙNG KEY MỚI) =================
# ⚠️ Thay Key mới vào đây (Key cũ đã bị khóa hôm nay)
GOOGLE_API_KEY = "AIzaSyA7Rn_kvSEZ63ZEfIsrTGnZEh57aVCZvEM"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- CHỌN MODEL "LITE" (MIỄN PHÍ 1500 LƯỢT/NGÀY) ---
# Tuyệt đối không dùng 'latest' nữa. Dùng đích danh con này:
try:
    model = genai.GenerativeModel("models/gemini-2.0-flash-lite-001")
except:
    # Dự phòng
    model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")

# ================= 2. GIAO DIỆN LỚP HỌC =================
st.set_page_config(page_title="IELTS Speaking Assessment", page_icon="🎙️")

st.markdown("""
    <style>
        .stApp {background-color: #f4f6f9;}
        .instruction-box {
            background-color: white; padding: 20px; border-radius: 12px;
            border-left: 6px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        h1 {color: #1e3a8a; font-family: 'Helvetica', sans-serif;}
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601")

st.markdown("""
<div class="instruction-box">
    <strong style="color:#1e3a8a;">👋 Hướng dẫn nộp bài:</strong>
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
                st.error("⚠️ File ghi âm quá ngắn hoặc lỗi.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Task: Assess speaking for "{selected_q}".
            
            INSTRUCTIONS:
            1. Determine Band Score (0-9.0).
            2. Provide feedback strictly in VIETNAMESE.
            3. LEVEL-ADAPTIVE:
               - If Band < 5.0: Suggest simple improvements.
               - If Band 6.0+: Suggest advanced vocabulary.
            
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá (Band Score):** [Score]
            **2. Nhận xét (Ưu/Nhược điểm):** [Pronunciation, Grammar, Fluency]
            **3. Sửa lỗi & Nâng cấp:** [Original -> Better Version]
            **4. Tổng kết:** [Conclusion]
            """

            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.divider()
            st.success("✅ Đã chấm xong!")
            with st.container(border=True):
                st.markdown(response.text)
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            st.error("⚠️ Lỗi kết nối (Vui lòng thử lại sau 30s).")
            # st.code(e) # Ẩn lỗi