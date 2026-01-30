import streamlit as st
import requests
import json
import base64

# ================= 1. DỮ LIỆU & CẤU HÌNH (TEACHER INPUT) =================

# Cấu hình Lớp học
CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Nền tảng"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite"}
}

# Danh sách Chủ đề Listening (Cho học viên chọn)
LISTENING_TOPICS = [
    "Công nghệ & AI (Technology)",
    "Sức khỏe & Tinh thần (Health & Mental)",
    "Kinh doanh & Khởi nghiệp (Business)",
    "Văn hóa & Du lịch (Culture & Travel)",
    "Tâm lý học (Psychology)",
    "Vụ án & Trinh thám (True Crime)",
    "Môi trường (Environment)",
    "Giáo dục (Education)",
    "Thể thao (Sports)"
]

# --- DỮ LIỆU SPEAKING ---
SPEAKING_CONTENT = {
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
    ]
}

# --- DỮ LIỆU READING (FULL PASSAGE & EXPLANATION) ---
READING_CONTENT = {
    "Lesson 2: Marine Chronometer": {
        "status": "Active",
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
        # Phần câu hỏi & Giải thích chi tiết
        "questions_fill": [
            {"id": "q1", "q": "1. Sailors were able to use the position of the Sun to calculate [.........].", "a": "local time", "exp": "Vị trí thông tin đoạn 4: 'A comparison with the local time (easily identified by checking the position of the Sun)...' -> Giờ địa phương được xác định nhờ mặt trời."},
            {"id": "q2", "q": "2. An invention that could win the competition would lose no more than [.........] every day.", "a": "2.8 seconds", "exp": "Vị trí thông tin đoạn 5: '...needed to be within 2.8 seconds a day...' -> Sai số cho phép là 2.8 giây/ngày."},
            {"id": "q3", "q": "3. John and James Harrison’s clock worked accurately without [.........].", "a": "lubrication", "exp": "Vị trí thông tin đoạn 6: '...revolutionary because it required no lubrication.' -> Không cần bôi trơn."},
            {"id": "q4", "q": "4. Harrison’s main competitor’s invention was known as [.........].", "a": "sextant", "exp": "Vị trí thông tin đoạn 7: '...John Hadley, who developed sextant.' -> Đối thủ chính phát triển kính lục phân."},
            {"id": "q5", "q": "5. Hadley’s instrument can use [.........] to make a calculation of location of ships or planes.", "a": "angles", "exp": "Vị trí thông tin đoạn 7: 'The sextant is the tool that people adopt to measure angles...' -> Dùng để đo góc."},
            {"id": "q6", "q": "6. The modern version of Harrison’s invention is called [.........].", "a": "marine chronometer", "exp": "Vị trí thông tin đoạn 8: '...turns it into a genuine modem commercial product... marine chronometer...' -> Đồng hồ hàng hải."}
        ]
    }
}

# Tạo Menu (Lesson 1-10)
SPEAKING_MENU = list(SPEAKING_CONTENT.keys()) + [f"Lesson {i}" for i in range(3, 11)]
READING_MENU = [f"Lesson {i}" if i != 2 else "Lesson 2: Marine Chronometer" for i in range(1, 11)]

# ================= 2. CẤU HÌNH HỆ THỐNG =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #ffffff; font-family: 'Segoe UI', sans-serif;}
    h1 {color: #003366; font-size: 24px; font-weight: 700;}
    h2 {color: #004080; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 20px;}
    .stButton button {background-color: #004080; color: white; border-radius: 4px;}
    .stAlert {background-color: #f0f8ff; border: 1px solid #d6e9c6; color: #3c763d;}
    .explanation-box {background-color: #f9f9f9; padding: 10px; border-left: 3px solid #004080; margin-top: 5px; font-size: 0.9rem;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa có API Key.")
    st.stop()

# ================= 3. LOGIC FUNCTIONS =================
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        else: return "Hệ thống đang bận, vui lòng thử lại."
    except: return "Lỗi kết nối mạng."

def login():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            name = st.text_input("Họ tên học viên:")
            class_code = st.selectbox("Chọn Mã Lớp:", ["-- Chọn lớp --"] + list(CLASS_CONFIG.keys()))
            if st.form_submit_button("Vào Lớp Học"):
                if name and class_code != "-- Chọn lớp --":
                    st.session_state['user'] = {"name": name, "class": class_code, "level": CLASS_CONFIG[class_code]}
                    st.rerun()
                else: st.warning("Vui lòng điền đủ thông tin.")

def logout():
    st.session_state['user'] = None
    st.rerun()

# ================= 4. GIAO DIỆN CHÍNH =================
if 'user' not in st.session_state or st.session_state['user'] is None:
    login()
else:
    user = st.session_state['user']
    
    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Lớp: {user['class']} | Level: {user['level']['level']}")
        st.divider()
        menu = st.radio("CHỌN KỸ NĂNG:", ["🗣️ Speaking", "📖 Reading", "🎧 Listening"])
        st.divider()
        if st.button("Đăng xuất"): logout()

    # --- 1. SPEAKING ---
    if menu == "🗣️ Speaking":
        st.title("Luyện Tập Speaking")
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson_choice = st.selectbox("Chọn bài học:", SPEAKING_MENU)
        
        # Nếu bài học có dữ liệu
        if lesson_choice in SPEAKING_CONTENT:
            with col2:
                q_list = SPEAKING_CONTENT[lesson_choice]
                question = st.selectbox("Câu hỏi:", q_list)
            
            st.info(f"🎙️ **Topic:** {question}")
            audio = st.audio_input("Ghi âm câu trả lời:", key=f"rec_{question}")
            
            if audio:
                with st.spinner("AI đang chấm điểm..."):
                    audio_b64 = base64.b64encode(audio.read()).decode('utf-8')
                    prompt = f"""
                    Role: IELTS Examiner. Student Level: {user['level']['level']}.
                    Task: Assess speaking response for "{question}".
                    Output: Vietnamese markdown.
                    Structure:
                    - **Band Score Estimate**
                    - **Feedback** (Fluency, Vocab, Grammar)
                    - **Correction** (Original vs Better version)
                    """
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                    payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                    try:
                        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                        if resp.status_code == 200:
                            st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                    except: st.error("Lỗi hệ thống.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- 2. READING ---
    elif menu == "📖 Reading":
        st.title("Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        if "Marine Chronometer" in lesson_choice: # Chỉ Lesson 2 có nội dung
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["📝 Bài Đọc & Điền Từ", "🤖 Luyện Từ Vựng (AI)"])
            
            # Tab 1: Bài đọc chính + Chấm điểm
            with tab1:
                with st.expander("📄 HIỂN THỊ BÀI ĐỌC (FULL TEXT)", expanded=True):
                    st.markdown(data['text'])
                
                st.subheader("Questions 1-6: Fill in the blanks")
                with st.form("read_fill"):
                    user_answers = {}
                    for q in data['questions_fill']:
                        user_answers[q['id']] = st.text_input(q['q'])
                    
                    submitted = st.form_submit_button("Nộp bài & Xem Giải Thích")
                    
                    if submitted:
                        score = 0
                        for q in data['questions_fill']:
                            u_ans = user_answers[q['id']].strip().lower()
                            c_ans = q['a'].lower()
                            
                            # Hiển thị kết quả từng câu
                            if u_ans == c_ans:
                                st.success(f"✅ **Đúng:** {q['a']}")
                                score += 1
                            else:
                                st.error(f"❌ **Sai:** Bạn điền '{user_answers[q['id']]}' -> Đáp án: '{q['a']}'")
                            
                            # HIỂN THỊ GIẢI THÍCH (CHO CẢ ĐÚNG VÀ SAI)
                            st.markdown(f"<div class='explanation-box'>💡 <b>Giải thích:</b> {q['exp']}</div>", unsafe_allow_html=True)
                        
                        st.divider()
                        st.info(f"📊 **Tổng điểm: {score}/{len(data['questions_fill'])}**")

            # Tab 2: AI Generate bài tập
            with tab2:
                st.info("Bấm nút bên dưới để AI tạo ra các bài tập từ vựng mới dựa trên bài đọc này.")
                
                col_gen1, col_gen2 = st.columns(2)
                with col_gen1:
                    if st.button("✨ Tạo bài tập Trắc nghiệm (Multiple Choice)"):
                        with st.spinner("AI đang soạn đề..."):
                            prompt = f"Create 5 multiple choice vocabulary questions based on this text: \n{data['text']}\n Format: Question, 4 Options, Answer Key. Output in Vietnamese."
                            st.markdown(call_gemini(prompt))
                
                with col_gen2:
                    if st.button("🧩 Tạo bài tập Nối từ (Matching)"):
                        with st.spinner("AI đang soạn đề..."):
                            prompt = f"Create a matching exercise (5 words) with definitions based on this text: \n{data['text']}\n Output in Vietnamese."
                            st.markdown(call_gemini(prompt))

        else:
            st.info("Bài học này chưa cập nhật.")

    # --- 3. LISTENING ---
    elif menu == "🎧 Listening":
        st.title("Luyện Nghe Chủ Động")
        st.info("Chọn chủ đề bạn thích, hệ thống sẽ đề xuất kênh phù hợp.")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox("Chọn chủ đề:", LISTENING_TOPICS)
        with col2:
            duration = st.selectbox("Thời lượng:", ["Ngắn (3-5 phút)", "Trung bình (10-15 phút)", "Dài (> 30 phút)"])
            
        if st.button("🔍 Tìm nguồn nghe"):
            with st.spinner("AI đang tìm kiếm..."):
                prompt = f"""
                Role: IELTS Teacher. Student Level: {user['level']['level']}.
                Task: Suggest 3 Youtube Channels or Podcasts for topic "{topic}" with duration "{duration}".
                Output Language: Vietnamese.
                Format:
                1. **[Tên Kênh]**
                   - Tại sao phù hợp: [Giải thích]
                   - Từ khóa tìm kiếm: [Keyword]
                """
                st.markdown(call_gemini(prompt))

        st.divider()
        st.subheader("Phân tích Script & Dịch Song Ngữ")
        script_input = st.text_area("Dán Script (lời thoại) video bạn tìm được vào đây:", height=200)
        
        if st.button("Dịch & Giải thích Từ Vựng"):
            if script_input:
                with st.spinner("AI đang phân tích..."):
                    prompt = f"""
                    Role: IELTS Teacher. Level: {user['level']['level']}.
                    Task:
                    1. Translate to Vietnamese (Sentence by sentence).
                    2. Highlight 5-7 useful words for band {user['level']['level']}.
                    Script: {script_input[:3000]}
                    """
                    st.markdown(call_gemini(prompt))
            else:
                st.warning("Vui lòng dán script vào trước.")