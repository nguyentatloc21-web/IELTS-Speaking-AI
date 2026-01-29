import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH KỸ THUẬT =================
# Lấy Key từ hệ thống Secrets (Đã kết nối thành công)
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Dự phòng nếu chạy trên máy cá nhân
    GOOGLE_API_KEY = "AIzaSyDIMjMbKU3lXMsJ6Exb9q3D1h3cDhkqFzg"

# Cấu hình kết nối (Bắt buộc dùng REST)
genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- CHỌN MODEL THÔNG MINH (SMART SELECTION) ---
# Logic mới: Chỉ đích danh model "Ngon-Bổ-Rẻ" để không bị giới hạn 20 lần/ngày
def get_working_model():
    try:
        # Danh sách ưu tiên (Tránh xa bản 2.5 experimental giới hạn 20 request)
        priority_models = [
            "models/gemini-1.5-flash",          # Bản chuẩn (1500 req/ngày)
            "models/gemini-1.5-flash-latest",   # Bản mới nhất ổn định
            "models/gemini-pro",                # Bản Pro cũ
            "models/gemini-1.5-pro"             # Bản Pro mới (50 req/ngày - dùng khi cần thiết)
        ]
        
        # Lấy danh sách model mà Key của bạn được phép dùng
        available_models = [m.name for m in genai.list_models()]
        
        # Tìm xem có cái nào trong danh sách ưu tiên khớp với cái bạn có không
        for model_name in priority_models:
            if model_name in available_models:
                return genai.GenerativeModel(model_name), model_name
        
        # Nếu không tìm thấy cái nào ngon, đành lấy cái đầu tiên (Fall back)
        if available_models:
            return genai.GenerativeModel(available_models[0]), available_models[0]
            
    except Exception:
        pass
    
    # Đường cùng: Cứ thử gọi đại bản Flash chuẩn
    return genai.GenerativeModel("models/gemini-1.5-flash"), "gemini-1.5-flash (Forced)"

model, active_model_name = get_working_model()

# ================= 2. GIAO DIỆN CHUYÊN NGHIỆP =================
st.set_page_config(page_title="IELTS Assessment - Mr. Tat Loc", page_icon="🎓", layout="centered")

# CSS: Giao diện sạch sẽ
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background-color: #f4f6f9;}
        h1 {color: #1e3a8a; font-family: 'Helvetica', sans-serif;}
        .instruction-card {
            background-color: white; padding: 20px; border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
            border-left: 5px solid #1e3a8a;
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("IELTS Speaking Assessment")
st.markdown(f"**Instructor:** Mr. Tat Loc &nbsp;|&nbsp; **Class:** PLA1601 &nbsp;|&nbsp; <span style='color:green; font-size:0.8em'>System Ready ({active_model_name})</span>", unsafe_allow_html=True)

# --- HƯỚNG DẪN ---
st.markdown("""
<div class="instruction-card">
    <h3 style="margin-top:0; color:#1e3a8a;">👋 Instructions</h3>
    <p>Chào mừng các bạn lớp <b>PLA1601</b>. Các bước làm bài tập về nhà:</p>
    <ol>
        <li>Chọn chủ đề (Topic) bên dưới.</li>
        <li>Bấm nút <b>Record</b> và trả lời (Khoảng 30 giây).</li>
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
    with st.spinner("AI is analyzing your speaking..."):
        try:
            # Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 100:
                st.error("⚠️ File ghi âm quá ngắn.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            # --- PROMPT TIẾNG ANH (AN TOÀN) ---
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
            **2. Nhận xét:** [Strengths/Weaknesses in Pronunciation & Grammar]
            **3. Sửa lỗi & Nâng cấp:** [Correction -> Better Phrase]
            **4. Tổng kết:** [Professional encouraging conclusion]
            """

            # Gửi đi (Stream=False)
            response = model.generate_content([prompt, gemini_audio_input], stream=False)
            
            # Kết quả
            st.divider()
            st.success("✅ Assessment Completed!")
            with st.container(border=True):
                st.markdown(response.text)
            st.info("💡 Tip: Chụp màn hình kết quả này để nộp bài.")
            
        except Exception as e:
            # Xử lý lỗi đẹp
            err_msg = str(e)
            if "429" in err_msg:
                st.error("⚠️ Hệ thống đang quá tải (Hết quota trong ngày). Vui lòng đợi mai thử lại.")
            else:
                st.error("⚠️ Lỗi kết nối. Vui lòng bấm F5 và thử lại.")
                with st.expander("Chi tiết lỗi (Gửi Admin)"):
                    st.write(e)