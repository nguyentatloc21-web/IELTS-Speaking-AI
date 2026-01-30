import streamlit as st
import requests
import json
import base64
import re
import time

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

# READING: FULL TEXT KHÔNG CẮT BỚT
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
        "questions_fill": [
            {"id": "q1", "q": "1. Sailors were able to use the position of the Sun to calculate [.........].", "a": "local time", "exp": "Dẫn chứng (Đoạn 4): 'A comparison with the local time (easily identified by checking the position of the Sun)...' -> Mặt trời giúp xác định giờ địa phương."},
            {"id": "q2", "q": "2. An invention that could win the competition would lose no more than [.........] every day.", "a": "2.8 seconds", "exp": "Dẫn chứng (Đoạn 5): '...needed to be within 2.8 seconds a day...' -> Sai số cho phép là 2.8 giây/ngày."},
            {"id": "q3", "q": "3. John and James Harrison’s clock worked accurately without [.........].", "a": "lubrication", "exp": "Dẫn chứng (Đoạn 6): '...revolutionary because it required no lubrication.' -> Không cần dầu bôi trơn."},
            {"id": "q4", "q": "4. Harrison’s main competitor’s invention was known as [.........].", "a": "sextant", "exp": "Dẫn chứng (Đoạn 7): '...John Hadley, who developed sextant.' -> Đối thủ là John Hadley với kính lục phân."},
            {"id": "q5", "q": "5. Hadley’s instrument can use [.........] to make a calculation of location of ships or planes.", "a": "angles", "exp": "Dẫn chứng (Đoạn 7): 'The sextant is the tool that people adopt to measure angles...' -> Dùng để đo góc."},
            {"id": "q6", "q": "6. The modern version of Harrison’s invention is called [.........].", "a": "marine chronometer", "exp": "Dẫn chứng (Đoạn 8): '...turns it into a genuine modem commercial product... marine chronometer...' -> Đồng hồ hàng hải."}
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
    .stButton button {background-color: #004080; color: white; border-radius: 6px; font-weight: 600; padding: 0.5rem 1rem;}
    .explanation-box {
        background-color: #e8f4fd; 
        padding: 15px; 
        border-radius: 5px;
        border-left: 5px solid #004080; 
        margin-top: 10px; 
        font-size: 0.95rem;
        color: #333;
    }
    .correct-ans {color: #27ae60; font-weight: bold;}
    .wrong-ans {color: #c0392b; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa có API Key.")
    st.stop()

# --- HÀM GỌI API GEMINI 2.0 FLASH ---
def call_gemini(prompt, expect_json=False):
    # Dùng đúng model gemini-2.0-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    final_prompt = prompt
    if expect_json:
        final_prompt += "\n\nIMPORTANT: Output STRICTLY JSON array without Markdown blocks (no ```json). Just the raw JSON."
    
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

# --- SESSION STATE ---
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

    # --- MODULE 1: SPEAKING ---
    if menu == "🗣️ Speaking":
        st.title("🗣️ Luyện Tập Speaking")
        col1, col2 = st.columns([1, 2])
        with col1:
            lesson_choice = st.selectbox("Chọn bài học:", SPEAKING_MENU)
        
        if lesson_choice in SPEAKING_CONTENT:
            with col2:
                q_list = SPEAKING_CONTENT[lesson_choice]
                question = st.selectbox("Chọn câu hỏi:", q_list)
            
            # Quản lý lượt trả lời (Max 5)
            attempts = st.session_state['speaking_attempts'].get(question, 0)
            remaining = 5 - attempts
            
            st.markdown(f"**Topic:** {question}")
            
            if remaining > 0:
                st.info(f"⚡ Bạn còn **{remaining}** lượt trả lời cho câu này.")
                audio = st.audio_input("Ghi âm câu trả lời:", key=f"rec_{question}")
                
                if audio:
                    with st.spinner("Thầy Lộc AI đang chấm chi tiết..."):
                        try:
                            audio_bytes = audio.read()
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                            
                            # PROMPT CHI TIẾT THEO YÊU CẦU
                            prompt = f"""
                            Role: IELTS Examiner.
                            Student Level: {user['level']['level']} (Class {user['class']}).
                            Task: Evaluate response for "{question}".
                            Tone: Professional, constructive, detailed. Output in Vietnamese.
                            
                            Format strictly as below using Markdown:
                            
                            ### 📊 KẾT QUẢ ĐÁNH GIÁ
                            * **Band Score Ước lượng:** [Range, e.g., 5.0 - 5.5]
                            * **Nhận xét chung:** [Tổng quan về độ tự nhiên, phản xạ]
                            
                            ### 🔍 PHÂN TÍCH CHI TIẾT
                            **1. Fluency & Coherence (Độ trôi chảy):**
                            * [Nhận xét chi tiết về ngập ngừng, tốc độ, từ nối]
                            
                            **2. Lexical Resource (Từ vựng):**
                            * ✅ **Điểm cộng:** [Liệt kê các từ hay/đúng chủ đề đã dùng]
                            * ⚠️ **Cần cải thiện:** [Các từ dùng sai ngữ cảnh hoặc lặp lại]
                            
                            **3. Grammatical Range & Accuracy (Ngữ pháp):**
                            * [Chỉ ra lỗi sai thì, cấu trúc câu và cách sửa]
                            
                            ### 💡 NÂNG CẤP CÂU TRẢ LỜI (Paraphrase)
                            * **Original (Câu của bạn):** "[Trích dẫn]"
                            * **Better (Thầy Lộc gợi ý):** "[Viết lại câu đó hay hơn, chuẩn native hơn]"
                            """
                            
                            url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=){API_KEY}"
                            payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                            
                            resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                            
                            if resp.status_code == 200:
                                st.markdown(resp.json()['candidates'][0]['content']['parts'][0]['text'])
                                st.session_state['speaking_attempts'][question] = attempts + 1
                            else:
                                st.error(f"⚠️ Lỗi Google (Mã {resp.status_code}): {resp.text}")
                                if resp.status_code == 429:
                                    st.warning("👉 Bạn đang gửi yêu cầu quá nhanh. Vui lòng đợi 1 phút.")
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}")
            else:
                st.warning("⛔ Đã hết 5 lượt trả lời cho câu này. Hãy chuyển sang câu khác.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 2: READING ---
    elif menu == "📖 Reading":
        st.title("📖 Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        if "Marine Chronometer" in lesson_choice:
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["📝 Bài Đọc & Điền Từ (Cố định)", "🤖 Bài Tập Tương Tác (AI Generated)"])
            
            # TAB 1: Bài điền từ cơ bản
            with tab1:
                with st.expander("📄 ĐỌC VĂN BẢN (FULL TEXT)", expanded=True):
                    st.markdown(data['text'])
                
                st.subheader("Fill in the blanks (Điền từ vào chỗ trống)")
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
                            status_text = f"<span class='correct-ans'>Đúng</span>" if is_correct else f"<span class='wrong-ans'>Sai (Đáp án: {q['a']})</span>"
                            
                            st.markdown(f"**{q['q']}**")
                            st.markdown(f"{status_icon} Kết quả: {status_text}", unsafe_allow_html=True)
                            st.markdown(f"<div class='explanation-box'><b>Giải thích chi tiết:</b><br>{q['exp']}</div>", unsafe_allow_html=True)
                            st.write("---")
                            
                        st.info(f"📊 **Tổng điểm: {score}/{len(data['questions_fill'])}**")

            # TAB 2: Bài tập AI tương tác
            with tab2:
                st.info(f"Dành cho trình độ: **{user['level']['level']}**. AI sẽ tạo bài tập phù hợp để bạn ôn luyện.")
                
                if st.button("✨ Tạo Bài Tập Trắc Nghiệm Mới"):
                    with st.spinner("AI đang phân tích bài đọc và tạo câu hỏi..."):
                        prompt = f"""
                        Based on the text 'Invention of Marine Chronometer', create 3 Vocabulary Multiple Choice Questions suitable for IELTS Band {user['level']['level']}.
                        Output STRICTLY JSON array format:
                        [
                            {{"question": "Question text?", "options": ["A", "B", "C", "D"], "answer": "Option text", "explanation": "Why correct?"}}
                        ]
                        """
                        json_str = call_gemini(prompt, expect_json=True)
                        if json_str:
                            try:
                                quiz_data = json.loads(json_str)
                                st.session_state['generated_quiz'] = quiz_data
                            except: st.error("Lỗi dữ liệu từ AI. Vui lòng thử lại.")
                        else: st.warning("⚠️ Máy chủ Google đang quá tải. Vui lòng đợi 1 phút.")

                if st.session_state['generated_quiz']:
                    st.divider()
                    st.subheader("✍️ Bài Tập Ôn Luyện (AI)")
                    
                    with st.form("ai_quiz_form"):
                        quiz = st.session_state['generated_quiz']
                        user_choices = {}
                        
                        for i, q in enumerate(quiz):
                            st.markdown(f"**Câu {i+1}: {q['question']}**")
                            user_choices[i] = st.radio(f"Lựa chọn câu {i+1}", q['options'], key=f"ai_{i}", label_visibility="collapsed")
                            st.write("")
                        
                        if st.form_submit_button("Chấm điểm"):
                            score = 0
                            for i, q in enumerate(quiz):
                                u_choice = user_choices.get(i)
                                if u_choice and (u_choice == q['answer'] or u_choice.startswith(q['answer'])):
                                    st.success(f"✅ Câu {i+1}: Chính xác!")
                                    score += 1
                                else:
                                    st.error(f"❌ Câu {i+1}: Sai. Đáp án đúng là: **{q['answer']}**")
                                st.markdown(f"<div class='explanation-box'>💡 {q.get('explanation', 'Không có giải thích')}</div>", unsafe_allow_html=True)
                            st.info(f"Kết quả: {score}/{len(quiz)}")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 3: LISTENING ---
    elif menu == "🎧 Listening":
        st.title("🎧 Luyện Nghe Chủ Động")
        st.info("Chọn chủ đề -> Nhận gợi ý -> Tìm Script -> Dán vào để học từ vựng.")
        
        col1, col2 = st.columns(2)
        with col1: topic = st.selectbox("Chọn chủ đề:", LISTENING_TOPICS)
        with col2: duration = st.selectbox("Thời lượng:", ["Ngắn (3-5 phút)", "Trung bình (10-15 phút)", "Dài (> 30 phút)"])
            
        if st.button("🔍 Tìm Kênh/Podcast Phù Hợp"):
            with st.spinner("Đang tìm kiếm nguồn nghe chất lượng..."):
                prompt = f"""
                Suggest 2 specific Youtube Channels or Podcasts suitable for IELTS Student Level {user['level']['level']} regarding topic "{topic}".
                Output in Vietnamese.
                Format:
                1. **[Name of Channel/Podcast]**
                   - **Why fit:** [Explain clearly why this fits level {user['level']['level']}]
                   - **Search Keyword:** [Exact keyword to type in Youtube/Google]
                """
                result = call_gemini(prompt)
                if result: st.markdown(result)
                else: st.warning("⚠️ Máy chủ đang bận. Bạn vui lòng bấm nút lại lần nữa nhé!")

        st.divider()
        st.subheader("Phân tích Script & Dịch Song Ngữ")
        script_input = st.text_area("Dán Script vào đây:", height=200)
        
        if st.button("Dịch & Highlight"):
            if script_input:
                with st.spinner("AI đang phân tích..."):
                    prompt = f"""
                    Translate the following script to Vietnamese (Sentence by sentence or Paragraph).
                    Then, highlight 5 vocabulary words suitable for IELTS Band {user['level']['level']}.
                    Script: {script_input[:2000]}
                    """
                    result = call_gemini(prompt)
                    if result: st.markdown(result)
                    else: st.warning("⚠️ Máy chủ đang bận. Bạn vui lòng bấm nút lại lần nữa nhé!")
            else:
                st.warning("Vui lòng dán script vào trước.")