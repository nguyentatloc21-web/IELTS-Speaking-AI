import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH HỆ THỐNG =================
# Giới hạn số lượt trả lời CHO MỖI CÂU HỎI
MAX_ATTEMPTS_PER_QUESTION = 3

st.set_page_config(page_title="Lớp IELTS Thầy Lộc", page_icon="🎓", layout="centered")

# CSS giao diện sạch, tối giản
st.markdown("""
    <style>
    .main {
        background-color: #fdfdfd;
    }
    h1 {
        color: #1a5276;
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2rem;
    }
    .stSelectbox label {
        color: #34495e;
        font-weight: bold;
    }
    .stAlert {
        border: 1px solid #d5dbdb;
    }
    </style>
""", unsafe_allow_html=True)

# Lấy Key từ Secrets
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Hệ thống chưa nhận diện được Key. Vui lòng liên hệ Thầy Lộc.")
    st.stop()

# ================= QUẢN LÝ TRẠNG THÁI (SESSION STATE) =================
# Tạo một từ điển để lưu số lần nộp của TỪNG câu hỏi
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
st.title("Luyện Tập Speaking - Lớp Thầy Lộc")
st.caption("Trợ lý AI hỗ trợ chấm bài và feedback chi tiết")
st.markdown("---")

# 1. Chọn câu hỏi
selected_q = st.selectbox("📌 Chọn câu hỏi bạn muốn luyện tập:", questions)

# 2. Kiểm tra số lượt còn lại của câu hỏi này
current_usage = st.session_state['attempts_history'].get(selected_q, 0)
remaining_attempts = MAX_ATTEMPTS_PER_QUESTION - current_usage

# Hiển thị thông báo lượt
if remaining_attempts > 0:
    st.info(f"⚡ Bạn còn **{remaining_attempts}** lượt trả lời cho câu hỏi này.")
else:
    st.warning(f"⛔ Bạn đã dùng hết {MAX_ATTEMPTS_PER_QUESTION} lượt cho câu hỏi này. Hãy chuyển sang câu khác nhé!")

# 3. Khu vực ghi âm
st.write("🎙️ **Ghi âm câu trả lời của bạn:**")
audio_value = st.audio_input("Nhấn để bắt đầu nói")

# ================= XỬ LÝ LOGIC =================
if audio_value:
    # Chặn nếu hết lượt
    if remaining_attempts <= 0:
        st.error("Rất tiếc, để đảm bảo tài nguyên lớp học, bạn vui lòng chọn câu hỏi khác hoặc quay lại sau nhé.")
        st.stop()

    with st.spinner("Trợ lý Thầy Lộc đang nghe và nhận xét..."):
        try:
            # Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 800: # Lọc file quá ngắn (< 1 giây)
                st.warning("⚠️ Âm thanh quá ngắn. Bạn vui lòng nói dài hơn một chút nhé.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Gọi API Gemini 2.0 Flash
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            
            # Prompt tối ưu hóa cho feedback
            prompt_text = f"""
            Vai trò: Bạn là Trợ lý giảng dạy thân thiện của Thầy Lộc (Lớp IELTS Speaking).
            Nhiệm vụ: Đánh giá câu trả lời của học viên cho câu hỏi: "{selected_q}".
            
            YÊU CẦU FEEDBACK (Quan trọng):
            1. **Nhận diện trình độ:** - Nếu nói yếu/ngập ngừng: Dùng giọng điệu khích lệ, chỉ sửa lỗi ngữ pháp cơ bản để bạn không nản.
               - Nếu nói trôi chảy: Góp ý kỹ hơn về từ vựng (collocations) và độ tự nhiên để nâng band.
            2. **Định dạng trả về (Tiếng Việt, dùng Markdown):**
               - 🎯 **Band điểm ước lượng:** (Khoảng điểm, ví dụ 5.0 - 5.5)
               - ✨ **Điểm cộng:** (Khen 1-2 điểm tốt nhất về phát âm hoặc ý tưởng)
               - 🔧 **Cần cải thiện:** (Chỉ ra tối đa 2 lỗi quan trọng nhất kèm cách sửa. Đừng liệt kê quá nhiều)
               - 💡 **Gợi ý nâng cấp:** (Viết lại một câu của bạn cho hay hơn/"tây" hơn)
               - 💬 **Lời nhắn:** (Một câu động viên ngắn gọn từ trợ lý).
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
                
                # CẬP NHẬT SỐ LƯỢT DÙNG (Trừ đi 1 lượt của câu hỏi này)
                st.session_state['attempts_history'][selected_q] = current_usage + 1
                
                # Hiển thị kết quả
                st.success("✅ Đã có kết quả!")
                with st.container(border=True):
                    st.markdown(text_response)
            else:
                st.error("⚠️ Kết nối thất bại. Bạn thử lại nhé.")

        except Exception as e:
            st.error("⚠️ Hệ thống đang bận, vui lòng thử lại sau.")