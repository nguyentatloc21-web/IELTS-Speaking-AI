import streamlit as st
import requests
import json
import base64
import re

# ================= 1. CẤU HÌNH & DỮ LIỆU (TEACHER INPUT) =================

CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Nền tảng"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite"}
}

LISTENING_TOPICS = [
    "Công nghệ (Technology & AI)", "Sức khỏe (Health & Fitness)", 
    "Kinh doanh (Business & Startups)", "Du lịch (Travel & Culture)", 
    "Tâm lý học (Psychology)", "Giáo dục (Education)", 
    "Môi trường (Environment)", "Thể thao (Sports)"
]

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
        """,
        "questions_fill": [
            {"id": "q1", "q": "1. Sailors were able to use the position of the Sun to calculate [.........].", "a": "local time", "exp": "Dẫn chứng: 'A comparison with the local time (easily identified by checking the position of the Sun)...'"},
            {"id": "q2", "q": "2. An invention that could win the competition would lose no more than [.........] every day.", "a": "2.8 seconds", "exp": "Dẫn chứng: '...needed to be within 2.8 seconds a day...'"},
            {"id": "q3", "q": "3. The British government offered an amount of [.........] for the solution.", "a": "£20,000", "exp": "Dẫn chứng: '...British government offered a tremendous amount of £20,000...'"}
        ]
    }
}

SPEAKING_MENU = list(SPEAKING_CONTENT.keys()) + [f"Lesson {i}: (Sắp ra mắt)" for i in range(3, 11)]
READING_MENU = [f"Lesson {i}" if i != 2 else "Lesson 2: Marine Chronometer" for i in range(1, 11)]

# ================= 2. HỆ THỐNG & API =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #ffffff; font-family: 'Segoe UI', sans-serif;}
    h1 {color: #003366; font-size: 24px; font-weight: 700;}
    h2 {color: #004080; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 20px;}
    .stButton button {background-color: #004080; color: white; border-radius: 4px;}
    .explanation-box {background-color: #f0f7ff; padding: 10px; border-left: 4px solid #004080; margin-top: 5px; font-size: 0.9rem;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa có API Key.")
    st.stop()

# --- HÀM GỌI API GEMINI (ĐÃ TỐI ƯU JSON) ---
def call_gemini(prompt, expect_json=False):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Nếu cần JSON, thêm chỉ dẫn rõ ràng vào prompt
    final_prompt = prompt
    if expect_json:
        final_prompt += "\n\nIMPORTANT: Output STRICTLY JSON without Markdown formatting (no ```json or ```)."
    
    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            if expect_json:
                # Làm sạch chuỗi nếu AI lỡ thêm markdown
                text = re.sub(r"```json|```", "", text).strip()
            return text
        else:
            return None
    except:
        return None

# --- QUẢN LÝ SESSION STATE ---
if 'speaking_attempts' not in st.session_state: st.session_state['speaking_attempts'] = {}
if 'generated_quiz' not in st.session_state: st.session_state['generated_quiz'] = None

# ================= 3. LOGIC ĐĂNG NHẬP =================
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

    # --- MODULE 1: SPEAKING (ĐÃ GIỚI HẠN 5 LẦN & FORMAT MỚI) ---
    if menu == "🗣️ Speaking":
        st.title("Luyện Tập Speaking")
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson_choice = st.selectbox("Chọn bài học:", SPEAKING_MENU)
        
        if lesson_choice in SPEAKING_CONTENT:
            with col2:
                q_list = SPEAKING_CONTENT[lesson_choice]
                question = st.selectbox("Câu hỏi:", q_list)
            
            # Kiểm tra số lần nộp
            attempts = st.session_state['speaking_attempts'].get(question, 0)
            remaining = 5 - attempts
            
            st.markdown(f"**Topic:** {question}")
            
            if remaining > 0:
                st.info(f"⚡ Bạn còn **{remaining}** lượt trả lời cho câu này.")
                audio = st.audio_input("Ghi âm câu trả lời:", key=f"rec_{question}")
                
                if audio:
                    with st.spinner("AI đang chấm điểm..."):
                        audio_b64 = base64.b64encode(audio.read()).decode('utf-8')
                        
                        # PROMPT THEO YÊU CẦU CỦA THẦY
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
                        payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                        
                        try:
                            resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                            if resp.status_code == 200:
                                st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                                # Trừ lượt sau khi thành công
                                st.session_state['speaking_attempts'][question] = attempts + 1
                            else:
                                st.error("Lỗi kết nối Google.")
                        except: st.error("Lỗi hệ thống.")
            else:
                st.warning("⛔ Bạn đã hết 5 lượt trả lời cho câu hỏi này. Vui lòng chuyển sang câu khác.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 2: READING (TƯƠNG TÁC AI XỊN HƠN) ---
    elif menu == "📖 Reading":
        st.title("Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        if "Marine Chronometer" in lesson_choice:
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["📝 Bài Đọc & Điền Từ", "🤖 Bài Tập Từ Vựng AI (Tương tác)"])
            
            # TAB 1: Bài điền từ cơ bản
            with tab1:
                with st.expander("📄 HIỂN THỊ BÀI ĐỌC (FULL TEXT)", expanded=True):
                    st.markdown(data['text'])
                
                st.subheader("Fill in the blanks")
                with st.form("read_fill"):
                    user_answers = {}
                    for q in data['questions_fill']:
                        user_answers[q['id']] = st.text_input(q['q'])
                    
                    if st.form_submit_button("Nộp bài"):
                        score = 0
                        for q in data['questions_fill']:
                            u_ans = user_answers[q['id']].strip().lower()
                            c_ans = q['a'].lower()
                            if u_ans == c_ans:
                                st.success(f"✅ Đúng: {q['a']}")
                                score += 1
                            else:
                                st.error(f"❌ Sai: Bạn điền '{user_answers[q['id']]}' -> Đáp án: '{q['a']}'")
                            st.markdown(f"<div class='explanation-box'>💡 {q['exp']}</div>", unsafe_allow_html=True)
                        st.info(f"Điểm: {score}/{len(data['questions_fill'])}")

            # TAB 2: Bài tập AI tương tác (JSON Parsing)
            with tab2:
                st.info("Bấm nút dưới để AI tạo 3 câu trắc nghiệm từ vựng mới.")
                
                if st.button("✨ Tạo Bài Tập Mới"):
                    with st.spinner("AI đang soạn đề trắc nghiệm..."):
                        # Prompt ép kiểu JSON
                        prompt = f"""
                        Create 3 multiple choice vocabulary questions based on this text:
                        {data['text'][:2000]}
                        
                        Output STRICTLY JSON array format like this:
                        [
                            {{"question": "What does X mean?", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Because..."}},
                            ...
                        ]
                        Do not use Markdown blocks.
                        """
                        json_str = call_gemini(prompt, expect_json=True)
                        if json_str:
                            try:
                                quiz_data = json.loads(json_str)
                                st.session_state['generated_quiz'] = quiz_data
                            except:
                                st.error("Lỗi định dạng dữ liệu từ AI. Vui lòng thử lại.")
                        else:
                            st.error("Hệ thống bận, không thể tạo bài tập lúc này.")

                # Hiển thị bài tập nếu đã có trong Session State
                if st.session_state['generated_quiz']:
                    st.divider()
                    st.subheader("✍️ Bài Tập Trắc Nghiệm")
                    
                    with st.form("ai_quiz_form"):
                        user_choices = {}
                        quiz = st.session_state['generated_quiz']
                        
                        for i, q in enumerate(quiz):
                            st.write(f"**Câu {i+1}:** {q['question']}")
                            # Dùng radio button cho tương tác
                            user_choices[i] = st.radio(f"Chọn đáp án câu {i+1}", q['options'], key=f"ai_q_{i}", index=None)
                            st.write("---")
                        
                        if st.form_submit_button("Chấm điểm"):
                            score = 0
                            for i, q in enumerate(quiz):
                                u_choice = user_choices.get(i)
                                if u_choice:
                                    # So sánh đáp án (AI thường trả về full text option hoặc ký tự A,B,C)
                                    # Ta so sánh chuỗi tương đối
                                    if u_choice == q['answer'] or u_choice.startswith(q['answer']):
                                        st.success(f"✅ Câu {i+1}: Chính xác!")
                                        score += 1
                                    else:
                                        st.error(f"❌ Câu {i+1}: Sai. Đáp án đúng là {q['answer']}")
                                    
                                    # Hiện giải thích
                                    if 'explanation' in q:
                                        st.markdown(f"<div class='explanation-box'>💡 {q['explanation']}</div>", unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ Câu {i+1}: Bạn chưa chọn đáp án.")
                            
                            st.info(f"Kết quả: {score}/{len(quiz)}")

        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 3: LISTENING (FIX LỖI & TỐI ƯU) ---
    elif menu == "🎧 Listening":
        st.title("Luyện Nghe Chủ Động")
        st.info("Chọn chủ đề -> AI gợi ý Kênh -> Dán Script -> AI Dịch.")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox("Chọn chủ đề:", LISTENING_TOPICS)
        with col2:
            duration = st.selectbox("Thời lượng:", ["Ngắn (3-5 phút)", "Trung bình (10-15 phút)", "Dài (> 30 phút)"])
            
        if st.button("🔍 Tìm Kênh Phù Hợp"):
            with st.spinner("Đang tìm kiếm..."):
                # Prompt ngắn gọn hơn để tránh lỗi 429/Busy
                prompt = f"""
                Suggest 2 Youtube Channels or Podcasts for IELTS level {user['level']['level']} about "{topic}".
                Format Vietnamese:
                - **[Tên]**: [Lý do ngắn gọn]
                """
                result = call_gemini(prompt)
                if result:
                    st.markdown(result)
                else:
                    st.error("Hệ thống đang bận. Bạn hãy thử chọn chủ đề khác xem sao nhé.")

        st.divider()
        st.subheader("Phân tích Script")
        script_input = st.text_area("Dán Script vào đây:", height=200)
        
        if st.button("Dịch & Highlight"):
            if script_input:
                with st.spinner("Đang phân tích..."):
                    prompt = f"""
                    Translate to Vietnamese. Highlight 5 hard vocabulary words for level {user['level']['level']}.
                    Script: {script_input[:2000]}
                    """
                    result = call_gemini(prompt)
                    if result:
                        st.markdown(result)
                    else:
                        st.error("Script quá dài hoặc hệ thống bận.")
            else:
                st.warning("Vui lòng dán script.")