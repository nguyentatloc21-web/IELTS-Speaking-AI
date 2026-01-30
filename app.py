import streamlit as st
import requests
import json
import base64
from datetime import datetime

# ================= 1. KHU VỰC NHẬP LIỆU CỦA GIÁO VIÊN (TEACHER INPUT ZONE) =================

# Cấu hình lớp học
CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Nền tảng (Pre-IELTS)"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite (Chuyên sâu)"}
}

# Dữ liệu SPEAKING
SPEAKING_DATA = {
    "Lesson 1: Work & Study": [
        "Q1: Do you work or are you a student?",
        "Q2: Is your daily routine busy?",
        "Q3: Is there anything you dislike about your work/study?",
        "Q4: Why did you choose your current job / major?",
        "Q5: What are your plans for the future?"
    ],
    "Lesson 2: Habits & Lifestyle": [
        "1. What is your daily routine like?",
        "2. Are you a morning person or a night person?",
        "3. Do you often eat breakfast at home or outside?",
        "4. Do you have a healthy lifestyle?",
        "5. What do you usually do in your free time?",
        "6. Do you prefer spending time alone or with friends?",
        "7. Is there any new hobby you want to try in the future?",
        "8. How do you relax after a stressful day?"
    ],
    # Các lesson khác để trống theo yêu cầu
    "Lesson 3: (Coming Soon)": [],
    "Lesson 4: (Coming Soon)": [],
    "Lesson 5: (Coming Soon)": [],
    "Lesson 6: (Coming Soon)": [],
    "Lesson 7: (Coming Soon)": [],
    "Lesson 8: (Coming Soon)": [],
    "Lesson 9: (Coming Soon)": [],
    "Lesson 10: (Coming Soon)": []
}

# Dữ liệu READING (Bài đọc & Câu hỏi điền từ)
READING_DATA = {
    "Lesson 2: Marine Chronometer": {
        "title": "Timekeeper: Invention of Marine Chronometer",
        "text": """
Up to the middle of the 18th century, the navigators were still unable to exactly identify the position at sea, so they might face a great number of risks such as the shipwreck or running out of supplies before arriving at the destination. Knowing one’s position on the earth requires two simple but essential coordinates, one of which is the longitude.

The longitude is a term that can be used to measure the distance that one has covered from one’s home to another place around the world without the limitations of naturally occurring baseline like the equator. To determine longitude, navigators had no choice but to measure the angle with the naval sextant between Moon centre and a specific star— lunar distance—along with the height of both heavenly bodies. Together with the nautical almanac, Greenwich Mean Time (GMT) was determined, which could be adopted to calculate longitude because one hour in GMT means 15-degree longitude. Unfortunately, this approach laid great reliance on the weather conditions, which brought great inconvenience to the crew members. Therefore, another method was proposed, that is, the time difference between the home time and the local time served for the measurement.

Theoretically, knowing the longitude position was quite simple, even for the people in the middle of the sea with no land in sight. The key element for calculating the distance travelled was to know, at the very moment, the accurate home time. But the greatest problem is: how can a sailor know the home time at sea?

The simple and again obvious answer is that one takes an accurate clock with him, which he sets to the home time before leaving. A comparison with the local time (easily identified by checking the position of the Sun) would indicate the time difference between the home time and the local time, and thus the distance from home was obtained. The truth was that nobody in the 18th century had ever managed to create a clock that could endure the violent shaking of a ship and the fluctuating temperature while still maintaining the accuracy of time for navigation.

After 1714, as an attempt to find a solution to the problem, the British government offered a tremendous amount of £20,000, which were to be managed by the magnificently named ‘Board of Longitude’. If timekeeper was the answer (and there could be other proposed solutions, since the money wasn’t only offered for timekeeper), then the error of the required timekeeping for achieving this goal needed to be within 2.8 seconds a day, which was considered impossible for any clock or watch at sea, even when they were in their finest conditions.

This award, worth about £2 million today, inspired the self-taught Yorkshire carpenter John Harrison to attempt a design for a practical marine clock. In the later stage of his early career, he worked alongside his younger brother James. The first big project of theirs was to build a turret clock for the stables at Brockelsby Park, which was revolutionary because it required no lubrication. Harrison designed a marine clock in 1730, and he travelled to London in seek of financial aid. He explained his ideas to Edmond Halley, the Astronomer Royal, who then introduced him to George Graham, Britain’s first-class clockmaker. Graham provided him with financial aid for his early-stage work on sea clocks. It took Harrison five years to build Harrison Number One or HI. Later, he sought the improvement from alternate design and produced H4 with the giant clock appearance. Remarkable as it was, the Board of Longitude wouldn’t grant him the prize for some time until it was adequately satisfied.

Harrison had a principal contestant for the tempting prize at that time, an English mathematician called John Hadley, who developed sextant. The sextant is the tool that people adopt to measure angles, such as the one between the Sun and the horizon, for a calculation of the location of ships or planes. In addition, his invention is significant since it can help determine longitude.

Most chronometer forerunners of that particular generation were English, but that doesn’t mean every achievement was made by them. One wonderful figure in the history is the Lancastrian Thomas Earnshaw, who created the ultimate form of chronometer escapement—the spring detent escapement—and made the final decision on format and productions system for the marine chronometer, which turns it into a genuine modem commercial product, as well as a safe and pragmatic way of navigation at sea over the next century and half.
        """,
        "questions": [
            {
                "id": "q1",
                "question": "1. Sailors were able to use the position of the Sun to calculate [.........].",
                "answer": "local time",
                "explanation": "Vị trí thông tin: 'A comparison with the local time (easily identified by checking the position of the Sun)...' -> Giờ địa phương được xác định nhờ mặt trời."
            },
            {
                "id": "q2",
                "question": "2. An invention that could win the competition would lose no more than [.........] every day.",
                "answer": "2.8 seconds",
                "explanation": "Vị trí thông tin: '...needed to be within 2.8 seconds a day...' -> Sai số cho phép là 2.8 giây/ngày."
            },
            {
                "id": "q3",
                "question": "3. John and James Harrison’s clock worked accurately without [.........].",
                "answer": "lubrication",
                "explanation": "Vị trí thông tin: '...which was revolutionary because it required no lubrication.' -> Không cần bôi trơn."
            },
            {
                "id": "q4",
                "question": "4. Harrison’s main competitor’s invention was known as [.........].",
                "answer": "sextant",
                "explanation": "Vị trí thông tin: '...John Hadley, who developed sextant.' -> Đối thủ chính phát triển kính lục phân."
            },
            {
                "id": "q5",
                "question": "5. Hadley’s instrument can use [.........] to make a calculation of location of ships or planes.",
                "answer": "angles",
                "explanation": "Vị trí thông tin: 'The sextant is the tool that people adopt to measure angles...' -> Dùng để đo góc."
            },
            {
                "id": "q6",
                "question": "6. The modern version of Harrison’s invention is called [.........].",
                "answer": "marine chronometer",
                "explanation": "Vị trí thông tin: '...turns it into a genuine modem commercial product... marine chronometer...' -> Đồng hồ hàng hải."
            }
        ]
    }
}

# ================= 2. CẤU HÌNH HỆ THỐNG =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🏫", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #ffffff; color: #333;}
    h1 {font-family: 'Segoe UI', sans-serif; color: #002b5c; font-size: 2.2rem; font-weight: 700;}
    h2 {font-family: 'Segoe UI', sans-serif; color: #004080; font-size: 1.6rem; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .stButton button {background-color: #004080; color: white; border-radius: 6px; font-weight: 600;}
    .stButton button:hover {background-color: #002b5c;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    /* Highlight text */
    .highlight {background-color: #ffffcc; padding: 2px 5px; border-radius: 3px;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa cấu hình API Key.")
    st.stop()

# ================= 3. BACKEND FUNCTIONS =================

def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def login():
    st.markdown("<div style='text-align: center; margin-bottom: 40px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Đăng Nhập Học Viên")
            name = st.text_input("Họ và tên:")
            class_code = st.selectbox("Mã Lớp:", ["-- Chọn lớp --"] + list(CLASS_CONFIG.keys()))
            submitted = st.form_submit_button("Vào Lớp")
            
            if submitted:
                if name and class_code != "-- Chọn lớp --":
                    st.session_state['user'] = {
                        "name": name,
                        "class": class_code,
                        "level_info": CLASS_CONFIG[class_code]
                    }
                    st.rerun()
                else:
                    st.error("Vui lòng điền đủ thông tin.")

def logout():
    st.session_state['user'] = None
    st.rerun()

# ================= 4. FRONTEND =================

if 'user' not in st.session_state or st.session_state['user'] is None:
    login()
else:
    user = st.session_state['user']
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"Hi, {user['name']}")
        st.info(f"Class: {user['class']}\nLevel: {user['level_info']['level']}")
        st.markdown("---")
        menu = st.radio("MENU:", ["Speaking Practice", "Reading & Vocab", "Active Listening"])
        st.markdown("---")
        if st.button("Log out"):
            logout()

    # --- 1. SPEAKING ---
    if menu == "Speaking Practice":
        st.title("🗣️ Speaking Practice")
        st.markdown(f"**Level đánh giá:** {user['level_info']['level']} ({user['level_info']['desc']})")
        st.info("💡 Hướng dẫn: Chọn Lesson, chọn câu hỏi và ghi âm. Hệ thống sẽ chấm điểm ngay lập tức.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson = st.selectbox("Chọn Lesson:", list(SPEAKING_DATA.keys()))
        with col2:
            questions_list = SPEAKING_DATA[lesson]
            if not questions_list:
                st.warning("Bài học này chưa có câu hỏi (Coming Soon).")
                question_choice = None
            else:
                question_choice = st.selectbox("Chọn Câu hỏi:", questions_list)

        if question_choice:
            st.markdown(f"### 🎙️ {question_choice}")
            audio_val = st.audio_input("Nhấn để ghi âm", key=f"rec_{question_choice}")
            
            if audio_val:
                with st.spinner("Thầy Lộc AI đang chấm bài..."):
                    audio_bytes = audio_val.read()
                    if len(audio_bytes) < 1000:
                        st.warning("File quá ngắn.")
                    else:
                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        
                        prompt = f"""
                        Role: IELTS Examiner.
                        Student Level: {user['level_info']['level']}.
                        Task: Assess response for: "{question_choice}".
                        
                        STRICT OUTPUT (Vietnamese Markdown):
                        ### KẾT QUẢ
                        * **Band Score:** [Range]
                        * **Nhận xét chung:** [Tóm tắt]
                        
                        ### CHI TIẾT
                        **1. Fluency:** ...
                        **2. Vocab & Grammar:** ...
                        **3. Pronunciation:** ...
                        
                        ### CẢI THIỆN
                        * **Original:** "[Trích dẫn]"
                        * **Better:** "[Sửa lại]"
                        """
                        
                        # Call API
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                        
                        try:
                            resp = requests.post(url, headers=headers, data=json.dumps(payload))
                            if resp.status_code == 200:
                                st.success("Đã chấm xong!")
                                with st.container(border=True):
                                    st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                            else:
                                st.error("Lỗi kết nối.")
                        except:
                            st.error("Lỗi hệ thống.")

    # --- 2. READING ---
    elif menu == "Reading & Vocab":
        st.title("📖 Reading Comprehension")
        
        lesson_choice = st.selectbox("Chọn bài đọc:", list(READING_DATA.keys()))
        data = READING_DATA[lesson_choice]
        
        tab1, tab2 = st.tabs(["📝 Làm Bài Tập", "🤖 Tạo Bài Tập Từ Vựng (AI)"])
        
        with tab1:
            st.markdown(f"### {data['title']}")
            
            # Hiển thị bài đọc (có thanh cuộn nếu dài)
            with st.expander("📄 Đọc văn bản (Nhấn để mở/đóng)", expanded=True):
                st.markdown(data['text'])
            
            st.write("---")
            st.subheader("Questions 1 - 6 (No more than TWO WORDS AND/OR A NUMBER)")
            
            # Form làm bài
            with st.form("reading_form"):
                user_answers = {}
                for item in data['questions']:
                    st.write(f"**{item['question']}**")
                    user_answers[item['id']] = st.text_input(f"Your answer for {item['id']}:", key=item['id'])
                
                submitted = st.form_submit_button("Nộp Bài (Check Answers)")
                
                if submitted:
                    score = 0
                    st.write("### 📊 Kết Quả:")
                    for item in data['questions']:
                        u_ans = user_answers[item['id']].strip().lower()
                        c_ans = item['answer'].strip().lower()
                        
                        # So sánh tương đối (chấp nhận viết hoa thường)
                        if u_ans == c_ans:
                            st.success(f"✅ {item['question'].replace('[.........]', f'[{item['answer']}]')}")
                            score += 1
                        else:
                            st.error(f"❌ {item['question']}")
                            st.markdown(f"👉 **Đáp án đúng:** `{item['answer']}`")
                            with st.expander("💡 Xem giải thích"):
                                st.info(item['explanation'])
                    
                    st.markdown(f"### Tổng điểm: {score}/{len(data['questions'])}")
        
        with tab2:
            st.info("Dùng AI để tạo thêm bài tập từ vựng dựa trên bài đọc này.")
            if st.button("✨ Tạo bài tập từ vựng"):
                with st.spinner("AI đang soạn đề..."):
                    prompt = f"""
                    Role: IELTS Teacher.
                    Task: Create a vocabulary matching exercise based on this text.
                    Text: {data['text']}
                    
                    Output Format (Markdown):
                    **Match the words with definitions:**
                    1. [Word] - [Definition]
                    ...
                    
                    **Answer Key:**
                    ...
                    """
                    result = call_gemini_api(prompt)
                    st.markdown(result)

    # --- 3. LISTENING ---
    elif menu == "Active Listening":
        st.title("🎧 Active Listening")
        st.info("Hệ thống sẽ đề xuất video cụ thể từ Youtube/TED dựa trên chủ đề bạn chọn.")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox("Chủ đề:", ["Technology", "Environment", "Education", "Travel", "Health"])
        with col2:
            duration = st.selectbox("Độ dài:", ["Ngắn (< 5 phút)", "Trung bình (5-15 phút)"])
            
        if st.button("🔍 Tìm Video"):
            with st.spinner("Đang tìm kiếm link phù hợp..."):
                prompt = f"""
                Role: IELTS Teacher.
                Student Level: {user['level_info']['level']}.
                Task: Recommend 2 specific listening resources (Youtube or TED links) for topic "{topic}", duration "{duration}".
                
                Output:
                1. **[Title]** - [Platform]
                   - Link: [Insert Link]
                   - Why: [Brief reason why it fits level {user['level_info']['level']}]
                """
                rec_result = call_gemini_api(prompt)
                st.markdown(rec_result)

        st.markdown("---")
        st.subheader("Phân tích Script")
        script_in = st.text_area("Dán Script bài nghe vào đây để phân tích:")
        
        if st.button("Phân tích từ vựng"):
            if script_in:
                with st.spinner("AI đang highlight từ vựng..."):
                    prompt = f"""
                    Role: IELTS Teacher.
                    Level: {user['level_info']['level']}.
                    Task: Analyze script.
                    1. Translate to Vietnamese (Parallel text).
                    2. Highlight vocabulary suitable for band {user['level_info']['level']} (Not too easy, not too hard).
                    
                    Script: {script_in}
                    """
                    ana_result = call_gemini_api(prompt)
                    st.markdown(ana_result)