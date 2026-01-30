import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH HỆ THỐNG =================
MAX_ATTEMPTS_PER_QUESTION = 3

st.set_page_config(page_title="IELTS Speaking Practice", page_icon="🎓", layout="centered")

# CSS Tối giản - Chuyên nghiệp (Minimalist Design)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1 { color: #003366; font-family: 'Segoe UI', sans-serif; font-weight: 700; font-size: 1.8rem; }
    .stSelectbox label { color: #003366; font-weight: 600; }
    .stAlert { border: none; border-left: 4px solid #003366; background-color: #f4f6f9; color: #2c3e50; }
    div[data-testid="stMarkdownContainer"] p { font-family: 'Segoe UI', sans-serif; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# Lấy Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ System Error: Missing API Key.")
    st.stop()

# Quản lý lịch sử nộp bài
if 'attempts_history' not in st.session_state:
    st.session_state['attempts_history'] = {}

# ================= DANH SÁCH CÂU HỎI =================
questions = [
    "1. What is your daily routine like?",
    "2. Are you a morning person or a night person?",
    "3. Do you often eat breakfast at home or outside?",
    "4. Do you have a healthy lifestyle?",
    "5. What do you usually do in your free time?",
    "6. Do you prefer spending time alone or with friends?",
    "7. Is there any new hobby you want to try in the future?",
    "8. How do you relax after a stressful day?"
]

# ================= GIAO DIỆN CHÍNH =================
st.title("IELTS SPEAKING PRACTICE")
st.markdown("---")

# 1. Chọn câu hỏi
selected_q = st.selectbox("SELECT TOPIC:", questions)

# 2. Kiểm tra lượt (Quota Check)
current_usage = st.session_state['attempts_history'].get(selected_q, 0)
remaining = MAX_ATTEMPTS_PER_QUESTION - current_usage

col1, col2 = st.columns([3, 1])
with col1:
    if remaining > 0:
        st.info(f"Attempts remaining for this topic: **{remaining}/{MAX_ATTEMPTS_PER_QUESTION}**")
    else:
        st.warning(f"Maximum attempts reached for this topic.")

# 3. Ghi âm (FIX LỖI SWITCH CÂU HỎI)
# Kỹ thuật: Gán key của widget theo tên câu hỏi.
# Khi đổi câu hỏi -> Key thay đổi -> Widget ghi âm cũ bị hủy -> Widget mới sạch sẽ hiện ra.
if remaining > 0:
    st.write("🎙️ **Record your answer:**")
    audio_value = st.audio_input("Press to record", key=f"recorder_{selected_q}")
else:
    st.error("Please switch to another topic to continue.")
    audio_value = None

# ================= XỬ LÝ LOGIC =================
if audio_value is not None:
    with st.spinner("Analyzing response..."):
        try:
            # Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 800:
                st.warning("⚠️ Recording is too short. Please try again.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Gọi API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            
            # === PROMPT CHUYÊN NGHIỆP ===
            prompt_text = f"""
            Role: Professional IELTS Examiner assistant.
            Task: Assess student's speaking response for the question: "{selected_q}".
            
            STRICT OUTPUT REQUIREMENTS:
            1. **Relevance Check First:** If the response is completely irrelevant to "{selected_q}", output warning: "⚠️ Lạc đề (Off-topic)" and stop.
            2. **Tone:** Professional, Academic, Constructive (No childish emojis like 🌟, ✨).
            3. **Language:** Vietnamese (Feedback content).
            
            FEEDBACK STRUCTURE (Use Markdown):
            
            ### KẾT QUẢ ĐÁNH GIÁ
            * **Band Score Ước lượng:** [Range, e.g., 5.5 - 6.0]
            * **Mức độ liên quan:** [Rất tốt / Khá / Lạc đề]
            
            ### PHÂN TÍCH CHI TIẾT
            **1. Fluency & Coherence**
            * [Nhận xét về độ trôi chảy, ngập ngừng, tốc độ]
            
            **2. Lexical Resource (Từ vựng)**
            * ✅ [Liệt kê từ hay đã dùng]
            * ⚠️ [Chỉ ra từ dùng sai hoặc lặp lại nhiều]
            
            **3. Grammatical Range & Accuracy**
            * [Nhận xét lỗi ngữ pháp hoặc cấu trúc câu]
            
            ### GỢI Ý NÂNG CẤP (BAND 7.0+)
            * **Original:** "[Trích 1 câu của học viên]"
            * **Better Version:** "[Viết lại câu đó theo văn phong tự nhiên/native hơn]"
            """

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": audio_b64
                            }
                        }
                    ]
                }]
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Trừ lượt
                st.session_state['attempts_history'][selected_q] = current_usage + 1
                
                # Hiển thị kết quả (Giao diện sạch)
                st.success("Analysis Completed.")
                with st.container(border=True):
                    st.markdown(text_response)
            
            else:
                # Xử lý lỗi hiển thị rõ ràng
                st.error(f"⚠️ Error ({response.status_code}): {response.text}")

        except Exception as e:
            st.error("⚠️ System Error.")
            st.code(e)