import streamlit as st
import requests
import json
import base64
import re
import time

# ================= 1. CẤU HÌNH & DỮ LIỆU =================

CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Nền tảng"},
    "DIA2024": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite"}
}

LISTENING_TOPICS = [
    "Công nghệ (Technology & AI)", "Sức khỏe (Health & Fitness)", 
    "Kinh doanh (Business & Startups)", "Du lịch (Travel & Culture)", 
    "Giáo dục (Education)", "Môi trường (Environment)"
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
Up to the middle of the 18th century, the navigators were still unable to exactly identify the position at sea... 
(Thầy giữ nguyên đoạn text dài ở đây nhé, em rút gọn để code đỡ dài dòng)
...safe and pragmatic way of navigation at sea over the next century and half.
        """,
        "questions_fill": [
            {"id": "q1", "q": "1. Sailors were able to use the position of the Sun to calculate [.........].", "a": "local time", "exp": "Dẫn chứng (Đoạn 4): 'A comparison with the local time...'"},
            {"id": "q2", "q": "2. An invention that could win the competition would lose no more than [.........] every day.", "a": "2.8 seconds", "exp": "Dẫn chứng (Đoạn 5): '...needed to be within 2.8 seconds a day...'"},
            {"id": "q3", "q": "3. John and James Harrison’s clock worked accurately without [.........].", "a": "lubrication", "exp": "Dẫn chứng (Đoạn 6): '...revolutionary because it required no lubrication.'"},
            {"id": "q4", "q": "4. Harrison’s main competitor’s invention was known as [.........].", "a": "sextant", "exp": "Dẫn chứng (Đoạn 7): '...John Hadley, who developed sextant.'"},
            {"id": "q5", "q": "5. Hadley’s instrument can use [.........] to make a calculation of location of ships or planes.", "a": "angles", "exp": "Dẫn chứng (Đoạn 7): 'The sextant is the tool that people adopt to measure angles...'"},
            {"id": "q6", "q": "6. The modern version of Harrison’s invention is called [.........].", "a": "marine chronometer", "exp": "Dẫn chứng (Đoạn 8): '...turns it into a genuine modem commercial product... marine chronometer...'"}
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
    h1 {color: #003366; font-size: 26px; font-weight: 700;}
    h2 {color: #004080; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 25px;}
    .stButton button {background-color: #004080; color: white; border-radius: 6px; font-weight: 600;}
    .explanation-box {background-color: #e8f4fd; padding: 15px; border-radius: 5px; border-left: 5px solid #004080; margin-top: 10px;}
    .correct-ans {color: #27ae60; font-weight: bold;}
    .wrong-ans {color: #c0392b; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa có API Key.")
    st.stop()

# --- HÀM GỌI API (DÙNG MODEL 1.5 FLASH CHO ỔN ĐỊNH) ---
def call_gemini(prompt, expect_json=False):
    # ĐỔI MODEL: gemini-1.5-flash (Ổn định hơn 2.0)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    final_prompt = prompt
    if expect_json:
        final_prompt += "\n\nIMPORTANT: Output STRICTLY JSON array without Markdown blocks."
    
    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            if expect_json:
                text = re.sub(r"```json|```", "", text).strip()
            return text
        else:
            return None
    except:
        return None

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

    # --- MODULE 1: SPEAKING (FIX LỖI) ---
    if menu == "🗣️ Speaking":
        st.title("🗣️ Luyện Tập Speaking")
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson_choice = st.selectbox("Chọn bài học:", SPEAKING_MENU)
        
        if lesson_choice in SPEAKING_CONTENT:
            with col2:
                q_list = SPEAKING_CONTENT[lesson_choice]
                question = st.selectbox("Chọn câu hỏi:", q_list)
            
            attempts = st.session_state['speaking_attempts'].get(question, 0)
            remaining = 5 - attempts
            
            st.markdown(f"**Topic:** {question}")
            
            if remaining > 0:
                st.info(f"⚡ Bạn còn **{remaining}** lượt trả lời.")
                audio = st.audio_input("Ghi âm câu trả lời:", key=f"rec_{question}")
                
                if audio:
                    with st.spinner("Đang xử lý âm thanh và chấm điểm..."):
                        try:
                            audio_bytes = audio.read()
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                            
                            # PROMPT CHI TIẾT
                            prompt = f"""
                            Role: IELTS Examiner.
                            Student Level: {user['level']['level']}.
                            Task: Evaluate response for "{question}".
                            Output: Vietnamese Markdown.
                            
                            ### 📊 KẾT QUẢ
                            * **Band Score:** [Range]
                            * **Nhận xét:** [General feedback]
                            
                            ### 🔍 PHÂN TÍCH
                            **1. Fluency:** [Details]
                            **2. Vocab:** [Good words vs Improvements]
                            **3. Grammar:** [Mistakes & Fixes]
                            
                            ### 💡 NÂNG CẤP (Paraphrase)
                            * **Original:** "[Quote]"
                            * **Better:** "[Correction]"
                            """
                            
                            # Gửi request (ĐỔI SANG GEMINI 1.5 FLASH)
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
                            payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                            
                            resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                            
                            # DEBUG: KIỂM TRA LỖI CỤ THỂ
                            if resp.status_code == 200:
                                st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                                st.session_state['speaking_attempts'][question] = attempts + 1
                            else:
                                st.error(f"⚠️ Lỗi từ Google (Mã {resp.status_code}):")
                                st.code(resp.text) # In lỗi ra để thầy xem
                                st.warning("Gợi ý: Nếu lỗi 400, có thể do file âm thanh lỗi. Nếu lỗi 429, là do quá tải.")
                        
                        except Exception as e:
                            st.error(f"⚠️ Lỗi hệ thống: {str(e)}")
            else:
                st.warning("⛔ Đã hết lượt trả lời cho câu này.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 2: READING ---
    elif menu == "📖 Reading":
        st.title("📖 Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        if "Marine Chronometer" in lesson_choice:
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["📝 Điền Từ (Full)", "🤖 Trắc Nghiệm AI"])
            
            with tab1:
                with st.expander("📄 ĐỌC VĂN BẢN (FULL TEXT)", expanded=True):
                    st.markdown(data['text'])
                
                st.subheader("Fill in the blanks")
                with st.form("read_fill"):
                    user_answers = {}
                    for q in data['questions_fill']:
                        user_answers[q['id']] = st.text_input(q['q'])
                    
                    if st.form_submit_button("Nộp bài & Xem Giải Thích"):
                        score = 0
                        for q in data['questions_fill']:
                            u_ans = user_answers[q['id']].strip().lower()
                            c_ans = q['a'].lower()
                            is_correct = u_ans == c_ans
                            if is_correct: score += 1
                            
                            status_icon = "✅" if is_correct else "❌"
                            ans_display = f"<span class='correct-ans'>Đúng</span>" if is_correct else f"<span class='wrong-ans'>Sai (Đáp án: {q['a']})</span>"
                            
                            st.markdown(f"**{q['q']}**")
                            st.markdown(f"{status_icon} Kết quả: {ans_display}", unsafe_allow_html=True)
                            st.markdown(f"<div class='explanation-box'>💡 <b>Giải thích:</b> {q['exp']}</div>", unsafe_allow_html=True)
                            st.write("---")
                        st.info(f"📊 Điểm: {score}/{len(data['questions_fill'])}")

            with tab2:
                st.info("AI sẽ tạo bài tập trắc nghiệm mới dựa trên bài đọc.")
                if st.button("✨ Tạo Bài Tập Mới"):
                    with st.spinner("AI đang soạn đề..."):
                        prompt = f"Create 3 multiple choice vocab questions from text based on IELTS Band {user['level']['level']}. Output JSON array."
                        json_str = call_gemini(prompt, expect_json=True)
                        if json_str:
                            try:
                                st.session_state['generated_quiz'] = json.loads(json_str)
                            except: st.error("Lỗi dữ liệu AI.")
                        else: st.warning("Máy chủ bận, vui lòng thử lại.")

                if st.session_state['generated_quiz']:
                    st.divider()
                    with st.form("ai_quiz"):
                        quiz = st.session_state['generated_quiz']
                        u_choices = {}
                        for i, q in enumerate(quiz):
                            st.markdown(f"**{i+1}. {q['question']}**")
                            u_choices[i] = st.radio(f"Opt {i}", q['options'], key=f"qz_{i}", label_visibility="collapsed")
                            st.write("")
                        
                        if st.form_submit_button("Chấm điểm"):
                            score = 0
                            for i, q in enumerate(quiz):
                                choice = u_choices.get(i)
                                if choice and (choice == q['answer'] or choice.startswith(q['answer'])):
                                    st.success(f"✅ Câu {i+1}: Đúng!")
                                    score += 1
                                else:
                                    st.error(f"❌ Câu {i+1}: Sai. Đáp án: {q['answer']}")
                                st.markdown(f"<div class='explanation-box'>💡 {q.get('explanation', '')}</div>", unsafe_allow_html=True)
                            st.info(f"Kết quả: {score}/{len(quiz)}")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 3: LISTENING ---
    elif menu == "🎧 Listening":
        st.title("🎧 Luyện Nghe Chủ Động")
        col1, col2 = st.columns(2)
        with col1: topic = st.selectbox("Chủ đề:", LISTENING_TOPICS)
        with col2: duration = st.selectbox("Thời lượng:", ["Ngắn (3-5p)", "Trung bình (10-15p)", "Dài (> 30p)"])
            
        if st.button("🔍 Tìm Kênh"):
            with st.spinner("Đang tìm kiếm..."):
                prompt = f"Suggest 2 Youtube Channels for IELTS Level {user['level']['level']} on '{topic}'. Vietnamese output."
                res = call_gemini(prompt)
                if res: st.markdown(res)
                else: st.warning("Máy chủ bận, vui lòng thử lại.")

        st.divider()
        script_in = st.text_area("Dán Script vào đây:", height=200)
        if st.button("Dịch & Highlight"):
            if script_in:
                with st.spinner("Đang phân tích..."):
                    prompt = f"Translate to Vietnamese. Highlight 5 vocab words for level {user['level']['level']}. Script: {script_in[:2000]}"
                    res = call_gemini(prompt)
                    if res: st.markdown(res)
                    else: st.warning("Máy chủ bận.")
            else: st.warning("Vui lòng dán script.")