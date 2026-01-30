import streamlit as st
import requests
import json
import base64

# ================= 1. KHU VỰC NHẬP LIỆU CỦA GIÁO VIÊN (TEACHER INPUT ZONE) =================

# Cấu hình lớp học
CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Pre-IELTS"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Diamond Class"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Master Class"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Elite Class"}
}

# Dữ liệu Gợi ý Listening (Theo Channel/Podcast) - KHÔNG DÙNG API
LISTENING_RECOMMENDATIONS = {
    "3.0 - 4.0": [
        {"name": "Spotlight English", "type": "Podcast/Youtube", "why": "Tốc độ chậm, từ vựng cơ bản, giọng đọc rõ ràng."},
        {"name": "BBC Learning English (6 Minute English)", "type": "Website/App", "why": "Chủ đề thông dụng, có giải thích từ vựng song ngữ."}
    ],
    "4.0 - 5.0": [
        {"name": "TED-Ed", "type": "Youtube", "why": "Hình ảnh hoạt hình dễ hiểu, kiến thức đa dạng, độ dài ngắn (4-5 phút)."},
        {"name": "IELTS Liz (Listening Section)", "type": "Website", "why": "Bài tập sát với format đề thi thật."}
    ],
    "5.0 - 6.0": [
        {"name": "TED Talks (Daily)", "type": "Podcast", "why": "Nâng cao tư duy phản biện, đa dạng giọng (accents)."},
        {"name": "Luke's English Podcast", "type": "Podcast", "why": "Hội thoại tự nhiên, dài, giúp luyện nghe hiểu sâu (Deep Listening)."}
    ],
    "6.5 - 7.0": [
        {"name": "BBC Global News Podcast", "type": "Podcast", "why": "Tốc độ bản ngữ thực tế, từ vựng Academic và chính trị/xã hội."},
        {"name": "The Economist / Guardian Science", "type": "Podcast", "why": "Nguồn từ vựng C1-C2 phong phú, chủ đề chuyên sâu."}
    ]
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
    # Placeholder cho các bài sau
    "Lesson 3: (Coming Soon)": [],
    "Lesson 4: (Coming Soon)": []
}

# Dữ liệu READING (Đã bao gồm bài tập Từ vựng soạn sẵn)
READING_DATA = {
    "Lesson 2: Marine Chronometer": {
        "title": "Timekeeper: Invention of Marine Chronometer",
        "text": """
Up to the middle of the 18th century, the navigators were still unable to exactly identify the position at sea... 
(Nội dung bài đọc đã được rút gọn để hiển thị, thầy giữ nguyên text dài trong code thật nhé)
... which turns it into a genuine modem commercial product, as well as a safe and pragmatic way of navigation at sea over the next century and half.
        """,
        # Phần 1: Điền từ (Fill in the blanks)
        "questions_fill": [
            {"id": "q1", "q": "1. Sailors were able to use the position of the Sun to calculate [.........].", "a": "local time", "exp": "Dựa vào đoạn: 'A comparison with the local time (easily identified by checking the position of the Sun)...'"},
            {"id": "q2", "q": "2. An invention that could win the competition would lose no more than [.........] every day.", "a": "2.8 seconds", "exp": "Dựa vào đoạn: '...needed to be within 2.8 seconds a day...'"},
            {"id": "q3", "q": "3. John and James Harrison’s clock worked accurately without [.........].", "a": "lubrication", "exp": "Dựa vào đoạn: '...revolutionary because it required no lubrication.'"},
            {"id": "q4", "q": "4. Harrison’s main competitor’s invention was known as [.........].", "a": "sextant", "exp": "Dựa vào đoạn: '...John Hadley, who developed sextant.'"},
            {"id": "q5", "q": "5. Hadley’s instrument can use [.........] to make a calculation of location of ships or planes.", "a": "angles", "exp": "Dựa vào đoạn: 'The sextant is the tool that people adopt to measure angles...'"},
            {"id": "q6", "q": "6. The modern version of Harrison’s invention is called [.........].", "a": "marine chronometer", "exp": "Dựa vào đoạn: '...turns it into a genuine modem commercial product... marine chronometer...'"}
        ],
        # Phần 2: Nối từ (Vocabulary Matching) - SOẠN SẴN (Không cần AI tạo)
        "vocab_match": [
            {"word": "Longitude", "def": "The distance east or west of the prime meridian", "key": "A"},
            {"word": "Sextant", "def": "An instrument used for measuring angles", "key": "B"},
            {"word": "Lubrication", "def": "The act of applying oil or grease to reduce friction", "key": "C"},
            {"word": "Fluctuate", "def": "To rise and fall irregularly in number or amount", "key": "D"},
            {"word": "Pragmatic", "def": "Dealing with things sensibly and realistically", "key": "E"}
        ]
    }
}

# ================= 2. CẤU HÌNH HỆ THỐNG =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🎓", layout="wide")

# CSS Chuyên nghiệp (Professional Style)
st.markdown("""
    <style>
    .main {background-color: #ffffff; font-family: 'Segoe UI', sans-serif;}
    h1 {color: #003366; font-size: 24px; font-weight: 700; text-transform: uppercase;}
    h2 {color: #004080; font-size: 20px; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; margin-top: 20px;}
    h3 {color: #2c3e50; font-size: 16px; font-weight: 600;}
    .stButton button {background-color: #003366; color: white; border-radius: 4px; border: none; padding: 0.5rem 1rem;}
    .stButton button:hover {background-color: #002244;}
    .stAlert {background-color: #f8f9fa; border-left: 4px solid #003366; color: #444;}
    .css-1d391kg {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("System Error: API Key not found.")
    st.stop()

# ================= 3. BACKEND LOGIC =================

def login():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            name = st.text_input("Full Name")
            class_code = st.selectbox("Class Code", ["-- Select Class --"] + list(CLASS_CONFIG.keys()))
            if st.form_submit_button("Access Portal"):
                if name and class_code != "-- Select Class --":
                    st.session_state['user'] = {"name": name, "class": class_code, "level": CLASS_CONFIG[class_code]}
                    st.rerun()
                else:
                    st.warning("Please enter all details.")

def logout():
    st.session_state['user'] = None
    st.rerun()

# ================= 4. GIAO DIỆN CHÍNH =================

if 'user' not in st.session_state or st.session_state['user'] is None:
    login()
else:
    user = st.session_state['user']
    
    # Sidebar Navigation
    with st.sidebar:
        st.write(f"**Student:** {user['name']}")
        st.write(f"**Class:** {user['class']}")
        st.info(f"Level: {user['level']['level']}")
        st.markdown("---")
        menu = st.radio("Navigation", ["Speaking", "Reading", "Listening"])
        st.markdown("---")
        if st.button("Log Out"):
            logout()

    # --- MODULE 1: SPEAKING ---
    if menu == "Speaking":
        st.title("Speaking Assessment")
        st.write("Select a lesson and record your answer. The AI will evaluate based on your class level.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson = st.selectbox("Lesson", list(SPEAKING_DATA.keys()))
        with col2:
            q_list = SPEAKING_DATA.get(lesson, [])
            if q_list:
                question = st.selectbox("Question", q_list)
            else:
                st.info("Content coming soon.")
                question = None

        if question:
            st.markdown(f"**Topic:** {question}")
            audio = st.audio_input("Record Answer", key=f"rec_{question}")
            
            if audio:
                with st.spinner("Analyzing speech..."):
                    try:
                        audio_data = base64.b64encode(audio.read()).decode('utf-8')
                        
                        prompt = f"""
                        Role: IELTS Examiner.
                        Student Level: {user['level']['level']}.
                        Task: Evaluate response for "{question}".
                        Tone: Professional, constructive. Output in Vietnamese.
                        
                        Format:
                        **BAND SCORE:** [Range]
                        **FEEDBACK:**
                        - **Fluency:** [Comment]
                        - **Vocabulary:** [Good words used] vs [Words to improve]
                        - **Grammar:** [Mistakes fixed]
                        **IMPROVEMENT:**
                        Original: "[Quote]" -> Better: "[Correction]"
                        """
                        
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                        data = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_data}}]}]}
                        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
                        
                        if resp.status_code == 200:
                            st.success("Assessment Complete")
                            st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                        else:
                            st.error(f"Error {resp.status_code}. Please try again.")
                    except Exception as e:
                        st.error(f"System error: {e}")

    # --- MODULE 2: READING ---
    elif menu == "Reading":
        st.title("Academic Reading")
        lesson = st.selectbox("Select Passage", list(READING_DATA.keys()))
        data = READING_DATA[lesson]
        
        # Tabs phân chia rõ ràng
        tab1, tab2 = st.tabs(["Part 1: Comprehension", "Part 2: Vocabulary Matching"])
        
        # Part 1: Điền từ
        with tab1:
            with st.expander("📄 Show Reading Text", expanded=True):
                st.markdown(data['text']) # Thầy nhớ paste full text vào biến ở trên
            
            st.write("#### Questions 1-6: Fill in the blanks")
            with st.form("reading_fill"):
                answers = {}
                for q in data['questions_fill']:
                    answers[q['id']] = st.text_input(q['q'])
                
                if st.form_submit_button("Submit Answers"):
                    score = 0
                    for q in data['questions_fill']:
                        user_ans = answers[q['id']].strip().lower()
                        correct_ans = q['a'].strip().lower()
                        
                        if user_ans == correct_ans:
                            st.success(f"✅ Correct: {q['a']}")
                            score += 1
                        else:
                            st.error(f"❌ Question: {q['q']}")
                            st.markdown(f"**Correct:** `{q['a']}` | *Explanation: {q['exp']}*")
                    
                    st.info(f"**Total Score: {score}/{len(data['questions_fill'])}**")

        # Part 2: Nối từ (Vocabulary)
        with tab2:
            st.write("#### Match the word with its definition")
            st.write("*Select the correct definition (A-E) for each word.*")
            
            # Hiển thị danh sách định nghĩa
            col_def, col_quiz = st.columns(2)
            with col_def:
                st.write("**Definitions:**")
                for item in data['vocab_match']:
                    st.write(f"**{item['key']}.** {item['def']}")
            
            with col_quiz:
                with st.form("vocab_match_form"):
                    match_ans = {}
                    # Trộn thứ tự câu hỏi nếu cần, ở đây giữ nguyên
                    for item in data['vocab_match']:
                        match_ans[item['word']] = st.selectbox(f"Word: **{item['word']}**", ["Choose...", "A", "B", "C", "D", "E"], key=item['word'])
                    
                    if st.form_submit_button("Check Vocabulary"):
                        v_score = 0
                        for item in data['vocab_match']:
                            if match_ans[item['word']] == item['key']:
                                v_score += 1
                        
                        if v_score == len(data['vocab_match']):
                            st.success(f"Perfect! {v_score}/{len(data['vocab_match'])}")
                        else:
                            st.warning(f"You got {v_score}/{len(data['vocab_match'])}. Review the definitions on the left.")

    # --- MODULE 3: LISTENING ---
    elif menu == "Listening":
        st.title("Active Listening Station")
        
        tab_rec, tab_script = st.tabs(["Recommended Channels", "Script Analyzer"])
        
        # Phần 1: Đề xuất kênh (Dữ liệu tĩnh - Không lỗi)
        with tab_rec:
            st.write(f"Based on your level **{user['level']['level']}**, here are the recommended resources:")
            
            # Lấy danh sách gợi ý theo level
            recs = LISTENING_RECOMMENDATIONS.get(user['level']['level'], LISTENING_RECOMMENDATIONS["5.0 - 6.0"])
            
            for item in recs:
                with st.container(border=True):
                    st.markdown(f"**{item['name']}** ({item['type']})")
                    st.write(f"Is it suitable? - {item['why']}")
                    st.caption("👉 Search this name on Youtube/Google to start listening.")

        # Phần 2: Phân tích Script (Vẫn dùng AI nhưng có cảnh báo)
        with tab_script:
            st.write("Paste your listening script below. The AI will translate and highlight new words.")
            script_text = st.text_area("Paste script here", height=200)
            
            if st.button("Analyze Script"):
                if not script_text:
                    st.warning("Please enter text first.")
                else:
                    with st.spinner("Processing..."):
                        try:
                            prompt = f"""
                            Role: IELTS Teacher. Level: {user['level']['level']}.
                            Task: Analyze listening script.
                            1. Translate to Vietnamese (Parallel text if possible).
                            2. Highlight vocabulary (B2-C1 words) with definitions.
                            Script: {script_text[:3000]} 
                            """
                            # Giới hạn ký tự script để tránh quá tải token
                            
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                            data = {"contents": [{"parts": [{"text": prompt}]}]}
                            resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(data))
                            
                            if resp.status_code == 200:
                                st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                            elif resp.status_code == 429:
                                st.error("⚠️ Hệ thống đang quá tải (Error 429). Vui lòng thử lại sau 1-2 phút.")
                            else:
                                st.error(f"Lỗi: {resp.status_code}")
                        except Exception as e:
                            st.error("Connection Error.")