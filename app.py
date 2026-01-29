import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH KỸ THUẬT (GIỮ NGUYÊN ĐỂ KHÔNG LỖI) =================
# ⚠️ DÁN KEY CỦA BẠN VÀO ĐÂY
GOOGLE_API_KEY = "AIzaSyDIMjMbKU3lXMsJ6Exb9q3D1h3cDhkqFzg"

# Cấu hình kết nối
genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- AUTO-DETECT MODEL (LOGIC ĐÃ CHẠY MƯỢT) ---
try:
    valid_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            valid_models.append(m.name)
    
    # Ưu tiên lấy model đầu tiên tìm thấy
    if valid_models:
        active_model_name = valid_models[0]
    else:
        active_model_name = "gemini-1.5-flash"
        
    model = genai.GenerativeModel(active_model_name)
    
except Exception:
    active_model_name = "gemini-1.5-flash"
    model = genai.GenerativeModel(active_model_name)

# ================= 2. GIAO DIỆN CHUYÊN NGHIỆP (PROFESSIONAL UI) =================
st.set_page_config(page_title="IELTS Assessment - Mr. Tat Loc", page_icon="🎓", layout="centered")

# CSS: Trang trí giao diện đẹp, hiện đại, clean
st.markdown("""
    <style>
        /* Ẩn menu mặc định của Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Màu nền tổng thể dịu mắt */
        .stApp {background-color: #f4f6f9;}
        
        /* Tiêu đề chính */
        h1 {
            color: #1e3a8a; /* Xanh Navy chuyên nghiệp */
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-weight: 700;
            padding-bottom: 10px;
        }
        
        /* Khung hướng dẫn (Card Style) */
        .instruction-card {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 25px;
            border-left: 6px solid #1e3a8a;
        }
        
        /* Chỉnh font chữ nội dung */
        p {font-size: 16px; color: #333;}
        
        /* Nút thu âm */
        .stAudioInput {margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("IELTS Speaking Assessment")
st.markdown("**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601 &nbsp;|&nbsp; <span style='color:grey; font-size:0.8em'>System Online ✅</span>", unsafe_allow_html=True)

# --- HƯỚNG DẪN (CARD STYLE) ---
st.markdown("""
<div class="instruction-card">
    <h3 style="margin-top:0; color:#1e3a8a;">👋 Instructions</h3>
    <p>Chào mừng các bạn lớp <b>PLA1601</b>. Để hoàn thành bài tập về nhà, hãy làm theo 3 bước:</p>
    <ol>
        <li>Chọn chủ đề (Topic) bên dưới.</li>
        <li>Bấm nút <b>Record</b> và trả lời (Khuyên dùng: 20-40 giây).</li>
        <li>Chụp màn hình kết quả Feedback nộp vào nhóm lớp.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# --- CHỌN CÂU HỎI ---
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

# --- THU ÂM ---
st.write("🎙️ **Your Answer (Record in English):**")
audio_value = st.audio_input("Record")

if audio_value:
    # Spinner đẹp hơn
    with st.spinner("Analyzing your pronunciation & vocabulary..."):
        try:
            # Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 100:
                st.error("⚠️ File ghi âm lỗi hoặc quá ngắn. Vui lòng thử lại.")
                st.stop()

            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            # --- PROMPT CHUẨN MỰC (LOGIC LEVEL-BASED) ---
            # Giữ nguyên Prompt tiếng Anh để tránh lỗi code
            prompt = f"""
            Role: Professional IELTS Examiner.
            Task: Assess student's speaking for: "{selected_q}".
            
            INSTRUCTIONS:
            1. Analyze the audio to determine the student's CURRENT Level (approximate Band Score).
            2. Provide feedback strictly in VIETNAMESE.
            
            3. LEVEL-ADAPTIVE FEEDBACK (Crucial logic):
               - If Student is Band < 5.0: Suggest simple, precise improvements (Band 6.0 level). DO NOT suggest complex idioms.
               - If Student is Band 6.0+: Suggest advanced vocabulary (Band 7.5+ Idioms/Collocations).
            
            OUTPUT FORMAT (Vietnamese):
            **1. Đánh giá tổng quan (Estimated Band):** [Score]
            
            **2. Nhận xét chi tiết (Strengths & Weaknesses):**
            - **Phát âm & Ngữ điệu:** [Specific comments]
            - **Ngữ pháp & Từ vựng:** [Specific comments]
            
            **3. Đề xuất cải thiện (Phù hợp trình độ):**
            - [Original phrase] -> [Better phrase +1 Band level]
            - [Correction of grammatical errors]
            
            **4. Tổng kết:** [A professional, objective concluding sentence regarding their performance].
            """

            # Gửi đi (Stream=False)
            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            # --- HIỂN THỊ KẾT QUẢ ĐẸP ---
            st.divider()
            st.success("✅ Assessment Completed!")
            
            # Dùng container để đóng khung kết quả
            with st.container(border=True):
                st.markdown(response.text)
            
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài (Screenshot this result).")
            
        except Exception as e:
            st.error("⚠️ Connection Error / Lỗi kết nối.")
            st.warning("Vui lòng tải lại trang (F5) và thử lại.")
            # Chỉ hiện lỗi chi tiết trong khung đóng mở
            with st.expander("Technical Details (Send to Admin if needed)"):
                st.write(e)