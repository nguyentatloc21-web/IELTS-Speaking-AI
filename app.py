import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH HỆ THỐNG =================
# Giới hạn số lần nộp bài trong 1 phiên làm việc để tiết kiệm tài nguyên
MAX_SUBMISSIONS = 3 

st.set_page_config(page_title="Lớp IELTS Thầy Lộc", page_icon="📚", layout="centered")

# CSS tùy chỉnh để giao diện sạch và chuyên nghiệp hơn
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2.2rem;
    }
    .stButton button {
        background-color: #2980b9;
        color: white;
        border-radius: 5px;
    }
    .stAlert {
        background-color: #ecf0f1;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo bộ đếm số lần nộp bài
if 'submission_count' not in st.session_state:
    st.session_state['submission_count'] = 0

# Lấy Key từ Secrets
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Hệ thống đang bảo trì (Chưa cấu hình API Key). Vui lòng liên hệ Thầy Lộc.")
    st.stop()

# ================= GIAO DIỆN CHÍNH =================
st.title("Nộp Bài Tập Nói - Lớp Thầy Lộc")
st.markdown("---")
st.write("Chào bạn! Đây là trợ lý AI của Thầy Lộc. Bạn hãy chọn chủ đề bên dưới và nộp bài ghi âm nhé.")
st.write(f"⚡ **Lượt nộp còn lại:** {MAX_SUBMISSIONS - st.session_state['submission_count']}/{MAX_SUBMISSIONS}")

# Danh sách câu hỏi (Thầy có thể sửa lại tiếng Việt cho thân thiện hơn)
questions = [
    "Topic 1: Kể về thói quen hàng ngày của bạn (Daily Routine)",
    "Topic 2: Bạn là người dậy sớm hay thức khuya? (Morning/Night Person)",
    "Topic 3: Bạn thường ăn sáng ở nhà hay bên ngoài?",
    "Topic 4: Bạn có lối sống lành mạnh không?",
    "Topic 5: Sở thích lúc rảnh rỗi của bạn là gì?",
    "Topic 6: Một kỹ năng mới bạn muốn học trong tương lai?",
    "Topic 7: Cách bạn thư giãn sau một ngày căng thẳng?"
]
selected_topic = st.selectbox("📌 Chọn chủ đề bài tập:", questions)

st.write("🎙️ **Ghi âm câu trả lời của bạn:**")
audio_value = st.audio_input("Nhấn để ghi âm")

# ================= XỬ LÝ LOGIC =================
if audio_value:
    # 1. Kiểm tra giới hạn lượt nộp
    if st.session_state['submission_count'] >= MAX_SUBMISSIONS:
        st.warning("⛔ Bạn đã hết lượt nộp bài hôm nay. Hãy quay lại sau hoặc liên hệ Thầy Lộc nhé!")
        st.stop()

    with st.spinner("Trợ lý đang nghe và chấm bài..."):
        try:
            # 2. Xử lý file âm thanh
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 1000: # Tăng giới hạn tối thiểu lên chút để lọc tạp âm
                st.error("⚠️ File ghi âm quá ngắn hoặc không có tiếng. Bạn vui lòng nói lại nhé.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 3. Gửi đến Gemini 2.0 Flash
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            
            # === PROMPT (LINH HỒN CỦA TRỢ LÝ) ===
            # Đây là phần chỉ đạo AI chấm điểm theo ý thầy
            prompt_text = f"""
            Vai trò: Bạn là Trợ lý AI thân thiện của lớp IELTS Thầy Lộc.
            Nhiệm vụ: Nghe và nhận xét bài nói của học viên về chủ đề: '{selected_topic}'.
            
            Yêu cầu quan trọng về Feedback:
            1. Tự động phát hiện trình độ:
               - Nếu học viên nói yếu/ngập ngừng: Dùng từ vựng đơn giản, động viên là chính, chỉ sửa lỗi ngữ pháp cơ bản.
               - Nếu học viên nói tốt: Góp ý khắt khe hơn, gợi ý từ vựng nâng cao (Idioms/Collocations).
            2. Tuyệt đối không dùng văn phong quá học thuật hay "như máy". Hãy nói chuyện tự nhiên như một người hướng dẫn tận tâm.
            3. Trả về kết quả bằng Tiếng Việt theo cấu trúc sau (Dùng Markdown):
               - 🎯 **Band điểm ước lượng:** (Đưa ra khoảng, ví dụ 5.0 - 5.5)
               - 🌟 **Điểm sáng:** (Khen ngợi 1-2 điểm tốt nhất)
               - 🛠️ **Góp ý cải thiện:** (Chỉ ra 2 lỗi quan trọng nhất cần sửa ngay, đừng liệt kê quá nhiều gây nản)
               - 💡 **Thử nói lại thế này nhé:** (Viết lại 1 câu của học viên theo cách hay hơn/tự nhiên hơn)
               - 💬 **Lời nhắn từ Trợ lý:** (Một câu động viên ngắn gọn).
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

            # 4. Gửi request
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                result = response.json()
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Tăng biến đếm số lần nộp thành công
                st.session_state['submission_count'] += 1
                
                # Hiển thị kết quả
                st.success("✅ Đã chấm xong! Dưới đây là nhận xét chi tiết:")
                with st.container(border=True):
                    st.markdown(text_response)
            else:
                st.error("⚠️ Có lỗi kết nối. Bạn vui lòng thử lại sau.")
                # (Chỉ hiện mã lỗi cho thầy xem nếu cần debug, ẩn với học viên)
                # st.write(response.text) 

        except Exception as e:
            st.error("⚠️ Hệ thống đang bận. Bạn hãy thử lại nhé.")