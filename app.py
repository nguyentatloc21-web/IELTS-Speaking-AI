import streamlit as st
import requests
import json
import base64
from datetime import datetime

# ================= 1. KHU VỰC NHẬP LIỆU CỦA GIÁO VIÊN (TEACHER INPUT ZONE) =================
# Thầy Lộc chỉ cần chỉnh sửa nội dung trong khu vực này.

# Cấu hình lớp học và trình độ tương ứng (Để AI chấm điểm chuẩn xác)
CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Nền tảng (Pre-IELTS)"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite (Chuyên sâu)"}
}

# Dữ liệu bài tập SPEAKING (Lesson 1 -> 10)
# Thầy thêm Lesson mới bằng cách copy dòng dưới và sửa số.
SPEAKING_DATA = {
    "Lesson 1: Introduction": [
        "Do you work or are you a student?",
        "Why did you choose your major?",
        "What do you like about your studies?"
    ],
    "Lesson 2: Hobbies & Interests": [
        "Do you have any hobbies?",
        "Do you prefer spending time alone or with friends?",
        "What do you usually do on weekends?"
    ],
    "Lesson 3: Hometown": [
        "Where is your hometown?",
        "Is your hometown a good place for young people?",
        "Has your hometown changed much since you were a child?"
    ]
    # Thầy có thể thêm Lesson 4, 5... tại đây
}

# Dữ liệu bài tập READING (Kiểm tra từ vựng)
# Cấu trúc: Tên bài -> Văn bản xác nhận -> Bộ câu hỏi trắc nghiệm
READING_DATA = {
    "Passage 1: Urbanization": {
        "confirm_text": "Bài này kiểm tra 10 từ vựng cốt lõi trong chủ đề Đô thị hóa. Thời gian khuyến nghị: 3 phút.",
        "quiz": [
            {
                "question": "Choose the synonym of 'Congestion':",
                "options": ["Empty", "Traffic Jam", "Cleanliness", "Expansion"],
                "answer": "Traffic Jam"
            },
            {
                "question": "What does 'Rural' mean?",
                "options": ["City center", "Countryside", "Industrial area", "Suburbs"],
                "answer": "Countryside"
            }
            # Thêm câu hỏi tại đây...
        ]
    },
    "Passage 2: The History of Tea": {
        "confirm_text": "Bài này tập trung vào các từ vựng chỉ quy trình và lịch sử.",
        "quiz": [
            {
                "question": "Meaning of 'Consumption':",
                "options": ["Production", "Eating/Drinking", "Selling", "Planting"],
                "answer": "Eating/Drinking"
            }
        ]
    }
}

# ================= 2. CẤU HÌNH HỆ THỐNG (SYSTEM CONFIG) =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🏫", layout="wide")

# CSS Tối giản - Chuyên nghiệp (Không màu mè)
st.markdown("""
    <style>
    .main {background-color: #ffffff; color: #333;}
    h1 {font-family: 'Segoe UI', sans-serif; color: #2c3e50; font-size: 2.2rem; font-weight: 600;}
    h2 {font-family: 'Segoe UI', sans-serif; color: #34495e; font-size: 1.5rem; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px;}
    .stButton button {background-color: #2c3e50; color: white; border-radius: 4px; font-weight: bold;}
    .stButton button:hover {background-color: #34495e;}
    .stAlert {background-color: #f8f9fa; border: 1px solid #ddd; color: #444;}
    div[data-testid="stMarkdownContainer"] p {line-height: 1.6; font-size: 16px;}
    </style>
""", unsafe_allow_html=True)

# Lấy API Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi hệ thống: Chưa cấu hình API Key.")
    st.stop()

# ================= 3. HÀM XỬ LÝ LOGIC (BACKEND) =================

def call_gemini_api(prompt):
    """Hàm gọi AI chung cho tất cả kỹ năng"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error ({response.status_code}): {response.text}"
    except Exception as e:
        return f"System Error: {str(e)}"

def login():
    """Màn hình đăng nhập"""
    st.markdown("<div style='text-align: center; margin-bottom: 40px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Đăng Nhập Học Viên")
            name = st.text_input("Họ và tên học viên:")
            class_code = st.selectbox("Chọn Mã Lớp:", ["-- Chọn lớp --"] + list(CLASS_CONFIG.keys()))
            submitted = st.form_submit_button("Vào Lớp Học")
            
            if submitted:
                if name and class_code != "-- Chọn lớp --":
                    # Lưu thông tin vào Session
                    st.session_state['user'] = {
                        "name": name,
                        "class": class_code,
                        "level_info": CLASS_CONFIG[class_code]
                    }
                    st.rerun()
                else:
                    st.error("Vui lòng điền đầy đủ thông tin.")

def logout():
    st.session_state['user'] = None
    st.rerun()

# ================= 4. GIAO DIỆN CHÍNH (FRONTEND) =================

if 'user' not in st.session_state or st.session_state['user'] is None:
    login()
else:
    # --- THANH ĐIỀU HƯỚNG BÊN TRÁI ---
    user = st.session_state['user']
    with st.sidebar:
        st.header(f"Học viên: {user['name']}")
        st.info(f"Lớp: {user['class']}\n\nTrình độ: {user['level_info']['level']}")
        st.markdown("---")
        menu = st.radio("Chọn Kỹ Năng:", ["Speaking Practice", "Reading Vocab Test", "Active Listening", "Writing (Upcoming)"])
        st.markdown("---")
        if st.button("Đăng xuất"):
            logout()

    # --- KỸ NĂNG 1: SPEAKING ---
    if menu == "Speaking Practice":
        st.title("Speaking Practice")
        st.markdown("""
        **Hướng dẫn:**
        1. Chọn bài học (Lesson) và câu hỏi.
        2. Nhấn nút ghi âm và trả lời tự nhiên.
        3. Hệ thống sẽ chấm điểm dựa trên trình độ lớp học của bạn.
        """)
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            lesson_choice = st.selectbox("Chọn Bài học (Lesson):", list(SPEAKING_DATA.keys()))
        with col2:
            question_choice = st.selectbox("Chọn Câu hỏi:", SPEAKING_DATA[lesson_choice])

        st.write(f"🎙️ **Câu hỏi:** {question_choice}")
        audio_val = st.audio_input("Nhấn để bắt đầu ghi âm", key=f"speak_{question_choice}")

        if audio_val:
            with st.spinner("Đang phân tích bài nói..."):
                audio_bytes = audio_val.read()
                if len(audio_bytes) < 1000:
                    st.warning("File ghi âm quá ngắn.")
                else:
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    # Prompt Speaking (Đã tối ưu)
                    prompt = f"""
                    Role: Professional IELTS Examiner.
                    Student Level: {user['level_info']['level']} (Class {user['class']}).
                    Task: Assess speaking response for question: "{question_choice}".
                    
                    REQUIREMENTS:
                    1. Check Relevance: If off-topic, say "Lạc đề" and stop.
                    2. Tone: Professional, Academic, Constructive.
                    3. Output Language: Vietnamese.
                    
                    STRUCTURE (Markdown):
                    ### KẾT QUẢ ĐÁNH GIÁ
                    * **Band Score Ước lượng:** [Range]
                    * **Nhận xét chung:** [Tóm tắt điểm mạnh/yếu dựa trên level {user['level_info']['level']}]
                    
                    ### PHÂN TÍCH CHI TIẾT
                    **1. Fluency & Coherence**
                    * [Nhận xét]
                    
                    **2. Lexical Resource & Grammar**
                    * [Nhận xét]
                    
                    ### GỢI Ý CẢI THIỆN (Actionable Advice)
                    * **Original:** "[Trích dẫn câu nói của học viên]"
                    * **Better Version:** "[Câu sửa lại hay hơn]"
                    """
                    
                    # Gọi API (Dùng lại hàm call_gemini_api để code gọn hơn)
                    # Lưu ý: Hàm call_gemini_api ở trên chỉ nhận text, cần sửa nhẹ để nhận multimedia
                    # Để đơn giản cho draft này, tôi viết lại đoạn request lồng vào đây
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}
                            ]
                        }]
                    }
                    response = requests.post(url, headers=headers, data=json.dumps(payload))
                    if response.status_code == 200:
                        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                        st.success("Đã có kết quả đánh giá.")
                        with st.container(border=True):
                            st.markdown(result_text)
                    else:
                        st.error("Lỗi kết nối.")

    # --- KỸ NĂNG 2: READING ---
    elif menu == "Reading Vocab Test":
        st.title("Academic Vocabulary Test")
        
        # Chọn bài đọc
        passage_choice = st.selectbox("Chọn bài đọc (Passage):", list(READING_DATA.keys()))
        data = READING_DATA[passage_choice]

        # Trạng thái bài thi (Dùng session state để điều hướng)
        if 'reading_state' not in st.session_state:
            st.session_state['reading_state'] = "intro"
        
        # Màn hình 1: Intro
        if st.session_state['reading_state'] == "intro":
            st.info(f"ℹ️ **Thông tin:** {data['confirm_text']}")
            st.warning("⚠️ Lưu ý: Bài kiểm tra có áp lực thời gian. Vui lòng không tra từ điển.")
            
            confirm = st.checkbox("Tôi xác nhận đã học thuộc từ vựng của bài này.")
            if confirm:
                if st.button("BẮT ĐẦU LÀM BÀI"):
                    st.session_state['reading_state'] = "testing"
                    st.rerun()

        # Màn hình 2: Làm bài (Quiz)
        elif st.session_state['reading_state'] == "testing":
            st.subheader(f"📝 {passage_choice}")
            
            with st.form("vocab_quiz"):
                score = 0
                total = len(data['quiz'])
                user_answers = []

                for idx, item in enumerate(data['quiz']):
                    st.markdown(f"**Question {idx + 1}:** {item['question']}")
                    choice = st.radio(f"Select answer for Q{idx+1}:", item['options'], key=f"q_{idx}")
                    user_answers.append((choice, item['answer']))
                
                submitted = st.form_submit_button("Nộp Bài (Submit)")
                
                if submitted:
                    # Chấm điểm
                    for ans, correct in user_answers:
                        if ans == correct:
                            score += 1
                    
                    st.session_state['reading_score'] = score
                    st.session_state['reading_total'] = total
                    st.session_state['reading_state'] = "result"
                    st.rerun()

        # Màn hình 3: Kết quả
        elif st.session_state['reading_state'] == "result":
            score = st.session_state['reading_score']
            total = st.session_state['reading_total']
            
            if score == total:
                st.success(f"🎉 Xuất sắc! Bạn đạt {score}/{total} điểm.")
            elif score >= total / 2:
                st.info(f"👍 Khá tốt. Bạn đạt {score}/{total} điểm.")
            else:
                st.error(f"Cần cố gắng hơn. Bạn đạt {score}/{total} điểm.")
            
            if st.button("Làm bài khác"):
                st.session_state['reading_state'] = "intro"
                st.rerun()

    # --- KỸ NĂNG 3: LISTENING ---
    elif menu == "Active Listening":
        st.title("Active Listening Station")
        st.markdown("""
        **Quy trình luyện nghe:**
        1. Tìm một video/audio (Youtube, TED, BBC) theo chủ đề bạn thích.
        2. Tìm **Script (lời thoại)** của bài đó.
        3. Dán Script vào bên dưới để AI phân tích từ vựng theo trình độ của bạn.
        """)
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox("Chủ đề yêu thích:", ["Technology", "Environment", "Education", "Culture", "Health"])
        with col2:
            duration = st.selectbox("Độ dài bài nghe:", ["Ngắn (2-5 phút)", "Trung bình (5-10 phút)", "Dài (> 10 phút)"])

        # Nút gợi ý (Placeholder - Sau này thầy có thể thêm link thật)
        if st.button("Gợi ý nguồn nghe"):
            st.info(f"Với chủ đề **{topic}** và trình độ **{user['level_info']['level']}**, thầy đề xuất bạn tìm các kênh: TED-Ed, BBC 6 Minute English, hoặc IELTS Liz Listening.")

        st.markdown("### 📥 Phân tích Script")
        script_text = st.text_area("Dán Script bài nghe của bạn vào đây:", height=200)

        if st.button("Phân tích ngay"):
            if script_text:
                with st.spinner("Đang dịch và đánh dấu từ vựng..."):
                    # Prompt Listening thông minh
                    prompt = f"""
                    Role: IELTS Teacher.
                    Student Level: {user['level_info']['level']}.
                    Task: Analyze the listening script provided.
                    
                    OUTPUT FORMAT (Markdown):
                    1. **Bản dịch song ngữ:** (Chia thành từng đoạn nhỏ: English - Vietnamese).
                    2. **Từ vựng cần học (Vocabulary Highlight):**
                       - Only select words that are challenging for band {user['level_info']['level']}.
                       - Format: **Word** (Type): Meaning in VN context.
                    
                    Script:
                    {script_text}
                    """
                    result = call_gemini_api(prompt)
                    st.markdown(result)
                    st.session_state['listening_analyzed'] = True
            else:
                st.warning("Vui lòng dán Script vào trước.")

        # Phần Feedback sau khi học
        if st.session_state.get('listening_analyzed'):
            st.markdown("---")
            st.subheader("Đánh giá mức độ hiểu")
            percent = st.slider("Sau khi đọc phân tích, bạn hiểu được bao nhiêu % nội dung bài nghe?", 0, 100, 50)
            
            if st.button("Nhận lời khuyên luyện tập"):
                advice = ""
                if percent < 50:
                    advice = """
                    **Chiến thuật:** Nghe chép chính tả (Dictation).
                    - Nghe từng câu -> Dừng -> Chép lại.
                    - Tần suất: Nghe lại bài này ít nhất 5 lần trong tuần này.
                    """
                elif percent < 80:
                    advice = """
                    **Chiến thuật:** Shadowing (Nói đuổi).
                    - Bật audio và đọc theo speaker cùng lúc (cố gắng bắt chước ngữ điệu).
                    - Tần suất: Nghe lại 3 lần.
                    """
                else:
                    advice = """
                    **Chiến thuật:** Deep Listening.
                    - Nghe và note lại các cụm từ nối (linking words) hoặc cách nhấn âm.
                    - Tần suất: Nghe lại 1 lần để thưởng thức.
                    """
                st.success(f"💡 **Lời khuyên từ thầy Lộc:**\n{advice}")

    # --- KỸ NĂNG 4: WRITING ---
    elif menu == "Writing (Upcoming)":
        st.title("Writing Simulation")
        st.info("🚧 Tính năng đang được xây dựng.")
        st.write("Sắp ra mắt: Chế độ thi áp lực thời gian (Task 1: 20p, Task 2: 40p) và chấm bài Real-time.")