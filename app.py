import streamlit as st
import requests
import json
import base64
import re
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ================= 1. KẾT NỐI GOOGLE SHEETS (DATABASE) =================
def connect_gsheet():
    """Kết nối Google Sheets an toàn"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif "private_key" in st.secrets:
            creds_dict = {k: v for k, v in st.secrets.items() if k in ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]}
        else:
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("IELTS_DB") 
        return sheet
        
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def save_speaking_log(student, class_code, lesson, question, full_feedback):
    """
    Hàm lưu điểm Speaking thông minh:
    Tự động lọc tìm con số Band Score trong bài văn feedback dài.
    """
    try:
        sheet = connect_gsheet()
        if sheet:
            try:
                ws = sheet.worksheet("Speaking_Logs")
            except:
                ws = sheet.add_worksheet(title="Speaking_Logs", rows="1000", cols="10")
                # Header chuẩn 8 cột
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Question", "Band_Short", "Score_Num", "Full_Feedback"])
            
            # --- LOGIC TRÍCH XUẤT ĐIỂM SỐ ---
            # Tìm dòng chứa "Band Score" hoặc "Kết quả"
            # Regex này tìm số dạng x.x (ví dụ 5.0, 6.5)
            score_num = 0.0
            band_short = "N/A"
            
            # Tìm các mẫu số phổ biến trong bài chấm IELTS
            match = re.search(r"(?:Band Score|KẾT QUẢ|BAND|Band).*?(\d+\.?\d*)", full_feedback, re.IGNORECASE)
            if match:
                try:
                    score_num = float(match.group(1))
                    band_short = str(score_num)
                except: pass
            
            # Nếu không tìm thấy, thử tìm số đầu tiên xuất hiện trong dòng đầu
            if score_num == 0.0:
                first_line = full_feedback.split('\n')[0]
                match_fallback = re.search(r"(\d+\.?\d*)", first_line)
                if match_fallback:
                    score_num = float(match_fallback.group(1))
                    band_short = str(score_num)

            # Lưu vào Sheet (Đảm bảo đủ 8 cột để không bị trật)
            ws.append_row([
                str(datetime.now()), 
                student, 
                class_code, 
                lesson, 
                question, 
                band_short,  # Cột 6: Text ngắn (VD: "5.5")
                score_num,   # Cột 7: Số thực (VD: 5.5) -> Dùng để tính toán
                full_feedback # Cột 8: Bài feedback đầy đủ
            ])
            st.toast("✅ Đã lưu điểm và feedback vào hệ thống!", icon="💾")
    except Exception as e:
        print(f"Save Error: {e}")

def save_reading_log(student, class_code, lesson, score, total):
    try:
        sheet = connect_gsheet()
        if sheet:
            try:
                ws = sheet.worksheet("Reading_Logs")
            except:
                ws = sheet.add_worksheet(title="Reading_Logs", rows="1000", cols="10")
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Score", "Total", "Percentage"])
            
            percentage = round((score / total) * 100, 1) if total > 0 else 0
            ws.append_row([str(datetime.now()), student, class_code, lesson, score, total, percentage])
            st.toast("✅ Đã lưu kết quả Reading!", icon="💾")
    except: pass

def get_leaderboard(class_code):
    try:
        sheet = connect_gsheet()
        if not sheet: return None, None

        # 1. Speaking Leaderboard
        try:
            ws_s = sheet.worksheet("Speaking_Logs")
            df_s = pd.DataFrame(ws_s.get_all_records())
            
            # Kiểm tra cột Score_Num (Cột số 7)
            if not df_s.empty and 'Class' in df_s.columns and 'Score_Num' in df_s.columns:
                df_s = df_s[df_s['Class'] == class_code]
                if not df_s.empty:
                    # Chuyển cột điểm sang số
                    df_s['Score_Num'] = pd.to_numeric(df_s['Score_Num'], errors='coerce').fillna(0)
                    
                    # Logic: Lấy điểm cao nhất của mỗi câu hỏi -> Tính trung bình các câu
                    best_s = df_s.groupby(['Student', 'Question'])['Score_Num'].max().reset_index()
                    lb_s = best_s.groupby('Student')['Score_Num'].mean().reset_index()
                    lb_s.columns = ['Học Viên', 'Điểm Speaking (TB)']
                    lb_s = lb_s.sort_values(by='Điểm Speaking (TB)', ascending=False)
                else: lb_s = None
            else: lb_s = None
        except: lb_s = None

        # 2. Reading Leaderboard
        try:
            ws_r = sheet.worksheet("Reading_Logs")
            df_r = pd.DataFrame(ws_r.get_all_records())
            if not df_r.empty and 'Class' in df_r.columns:
                df_r = df_r[df_r['Class'] == class_code]
                if not df_r.empty:
                    df_r['Score'] = pd.to_numeric(df_r['Score'], errors='coerce')
                    # Reading: Lấy điểm cao nhất từng đạt được
                    lb_r = df_r.groupby('Student')['Score'].max().reset_index()
                    lb_r.columns = ['Học Viên', 'Điểm Reading (Max)']
                    lb_r = lb_r.sort_values(by='Điểm Reading (Max)', ascending=False)
                else: lb_r = None
            else: lb_r = None
        except: lb_r = None

        return lb_s, lb_r
    except: return None, None

# ================= 1. CẤU HÌNH & DỮ LIỆU (TEACHER INPUT) =================

CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Platinum"},
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

# READING: Lesson 2 Full Passage & Questions
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
    .stButton button:hover {background-color: #002244;}
    .explanation-box {
        background-color: #e8f4fd; 
        padding: 15px; 
        border-radius: 8px;
        border-left: 5px solid #004080; 
        margin-top: 10px; 
        font-size: 0.95rem;
        color: #2c3e50;
    }
    .correct-ans {color: #27ae60; font-weight: bold;}
    .wrong-ans {color: #c0392b; font-weight: bold;}
    .stRadio label {font-size: 16px;}
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

    # --- MODULE 4: LEADERBOARD (Ưu tiên hiển thị đầu để dễ thấy) ---
    if menu == "🏆 Bảng Xếp Hạng":
        st.title(f"🏆 Bảng Xếp Hạng Lớp {user['class']}")
        st.info("Cập nhật theo thời gian thực (Top 10).")
        
        if st.button("🔄 Làm mới"): st.rerun()

        lb_s, lb_r = get_leaderboard(user['class'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎤 Speaking (Điểm TB)")
            if lb_s is not None and not lb_s.empty:
                lb_s.index = range(1, len(lb_s) + 1)
                st.dataframe(lb_s.style.format({"Điểm Speaking (TB)": "{:.2f}"}).background_gradient(cmap="Blues"), use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")
                
        with col2:
            st.subheader("📚 Reading (Điểm Max)")
            if lb_r is not None and not lb_r.empty:
                lb_r.index = range(1, len(lb_r) + 1)
                st.dataframe(lb_r.style.format({"Điểm Reading (Max)": "{:.1f}"}).background_gradient(cmap="Greens"), use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

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
                    with st.spinner("Đang chấm điểm..."):
                        try:
                            audio_bytes = audio.read()
                            if len(audio_bytes) < 1000:
                                st.warning("File âm thanh quá ngắn. Vui lòng thử lại.")
                            else:
                                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                                # TỰ ĐỘNG NHẬN DIỆN ĐỊNH DẠNG ÂM THANH (Fix lỗi Mobile)
                                mime_type = audio.type if audio.type else "audio/wav"
                                prompt = f"""
                                Role: Senior IELTS Speaking Examiner (Friendly & Constructive).
                                Student Level: {user['level']['level']}.
                                Task: Assess speaking response for "{question}".
                                Output in Vietnamese
                                Only assess if the answer is relevant. Otherwise, give him/her a second chance
                                CRITICAL INSTRUCTIONS:
                                1. **Scoring:** Be encouraging. If they communicate clearly, don't grade too harshly.
                                2. **Criteria:** You MUST evaluate based on 4 IELTS criteria:
                                   - Fluency & Coherence
                                   - Lexical Resource
                                   - Grammatical Range & Accuracy
                                   - **Pronunciation** (Estimate based on audio flow/intonation)
                                3. **Improvement:** Suggest a **NATURAL, SPOKEN** way to say it. Avoid "fancy" or "academic writing" words. Use phrasal verbs or common collocations suitable for speaking.
                                
                                OUTPUT FORMAT (Vietnamese Markdown):
                                
                                ### KẾT QUẢ: [Band Score]
                                
                                ### CHI TIẾT 4 TIÊU CHÍ:
                                1. **Fluency & Coherence:** [Nhận xét độ trôi chảy, ngập ngừng, mở rộng/đào sâu được câu trả lời ở mức nào?]
                                2. **Lexical Resource:** [Từ vựng tốt đã dùng vs Từ nên thay thế]
                                3. **Grammar:** [Lỗi ngữ pháp & Cách sửa]
                                4. **Pronunciation & Intonation:** [Nhận xét về ngữ điệu, trọng âm, hoặc các âm bị nuốt/sai, âm đuôi, số ít số nhiều]
                                
                                ### ĐỀ XUẤT CẢI THIỆN:
                                * **Câu của bạn:** "[Trích dẫn]"
                                * **Cách nói tự nhiên hơn:** "[Viết lại theo văn phong NÓI, tự nhiên, native]"
                                  *(Giải thích: Tại sao cách này tự nhiên hơn?)*
                                """
                        
                                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                                payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                        
                                resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                                
                                if resp.status_code == 200:
                                    text_result = resp.json()['candidates'][0]['content']['parts'][0]['text']
                                    st.markdown(text_result)
                                    st.session_state['speaking_attempts'][question] = attempts + 1
                                    
                                    # LƯU ĐIỂM
                                    save_speaking_log(user['name'], user['class'], lesson_choice, question, text_result[:50], text_result)
                                else:
                                    st.error(f"⚠️ Lỗi Google (Mã {resp.status_code}): {resp.text}")
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}")
            else:
                st.warning("⛔ Đã hết 5 lượt trả lời.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 2: READING ---
    elif menu == "📖 Reading":
        st.title("📖 Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        if "Marine Chronometer" in lesson_choice:
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["Bài Đọc & Điền Từ", "Bài Tập Từ Vựng"])
            
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
                            
                            # Hiển thị kết quả & Giải thích ngay bên dưới mỗi câu
                            status_icon = "✅" if is_correct else "❌"
                            status_text = f"<span class='correct-ans'>Đúng</span>" if is_correct else f"<span class='wrong-ans'>Sai (Đáp án: {q['a']})</span>"
                            
                            st.markdown(f"**{q['q']}**")
                            st.markdown(f"{status_icon} Kết quả: {status_text}", unsafe_allow_html=True)
                            st.markdown(f"<div class='explanation-box'><b>Giải thích chi tiết:</b><br>{q['exp']}</div>", unsafe_allow_html=True)
                            st.write("---")
                            
                        st.info(f"📊 **Tổng điểm: {score}/{len(data['questions_fill'])}**")

            # TAB 2: Bài tập AI tương tác (JSON Parsing)
            with tab2:
                st.info(f"Dành cho trình độ: **{user['level']['level']}**. AI sẽ tạo bài tập trắc nghiệm giúp bạn hiểu sâu từ vựng.")
                
                if st.button("✨ Tạo Bài Tập Mới"):
                    with st.spinner("AI đang soạn đề..."):
                        # Prompt tạo câu hỏi JSON CHẤT LƯỢNG CAO
                        prompt = f"""
                        Based on the text 'Invention of Marine Chronometer', create 10 Vocabulary Questions suitable for IELTS Band {user['level']['level']}.
                        
                        REQUIREMENTS:
                        
                        1. **Part 1 (Questions 1-5): Practical Meaning**
                           - Select 5 academic words from the text (e.g., longitude, reliance, fluctuate).
                           - Ask for their meaning **in Vietnamese**.
                           - **CRITICAL:** Do NOT reveal the meaning in the question.
                           - Good example: "Từ 'fluctuating' trong đoạn 4 có nghĩa là gì?"
                           - Options: 4 Vietnamese definitions.
                        
                        2. **Part 2 (Questions 6-10): Contextual Use**
                           - Select 5 other academic words.
                           - Create a **NEW English sentence** (unrelated to marine history) with a blank.
                           - Ask user to choose the correct word to fill in.
                           - Options: 4 English words from the text.
                        
                        Output STRICTLY JSON array format:
                        [
                            {{"question": "Question text?", "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"], "answer": "A. Option 1", "explanation": "Brief explanation in Vietnamese."}}
                        ]
                        """
                        json_str = call_gemini(prompt, expect_json=True)
                        if json_str:
                            try:
                                quiz_data = json.loads(json_str)
                                st.session_state['generated_quiz'] = quiz_data
                            except: st.error("Lỗi dữ liệu từ AI. Vui lòng thử lại.")
                        else: st.warning("⚠️ Máy chủ Google đang quá tải. Vui lòng thử lại sau giây lát.")

                # Hiển thị bài tập nếu đã có trong Session State
                if st.session_state['generated_quiz']:
                    st.divider()
                    st.subheader("✍️ Bài Tập Ôn Luyện")
                    
                    with st.form("ai_quiz_form"):
                        quiz = st.session_state['generated_quiz']
                        user_choices = {}
                        
                        for i, q in enumerate(quiz):
                            st.markdown(f"**Câu {i+1}: {q['question']}**")
                            # Dùng radio button cho tương tác
                            user_choices[i] = st.radio(f"Lựa chọn câu {i+1}", q['options'], key=f"ai_q_{i}", label_visibility="collapsed")
                            st.write("")
                        
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
        st.info("Chọn chủ đề -> Nhận gợi ý Kênh -> Tìm Script -> Dán vào để học.")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox("Chọn chủ đề:", LISTENING_TOPICS)
        with col2:
            duration = st.selectbox("Thời lượng:", ["Ngắn (3-5 phút)", "Trung bình (10-15 phút)", "Dài (> 30 phút)"])
            
        if st.button("🔍 Tìm Kênh Phù Hợp"):
            with st.spinner("Đang tìm kiếm..."):
                # Prompt
                prompt = f"""
                Suggest 3-4 specific Youtube Channels or Podcasts suitable for IELTS Student Level {user['level']['level']} regarding topic "{topic}".
                Output in Vietnamese.
                Format:
                1. **[Name of Channel/Podcast]**
                   - **Lý do phù hợp:** [Explain clearly why this fits level {user['level']['level']}]
                   - **Từ khóa tìm kiếm:** [Exact keyword to type in Youtube/Google]
                """
                result = call_gemini(prompt)
                if result:
                    st.markdown(result)
                else:
                    st.error("Hệ thống đang bận. Bạn vui lòng bấm nút lại lần nữa nhé!")

        st.divider()
        st.subheader("Phân tích Script")
        script_input = st.text_area("Dán Script vào đây:", height=200)
        
        if st.button("Dịch & Highlight"):
            if script_input:
                with st.spinner("Đang phân tích..."):
                    prompt = f"""
                    Translate the following script to Vietnamese (Sentence by sentence or Paragraph).
                    Then, highlight 5 vocabulary words suitable for IELTS Band {user['level']['level']}. Explain them in Vietnamese context.
                    Script: {script_input[:2500]}
                    """
                    result = call_gemini(prompt)
                    if result:
                        st.markdown(result)
                    else:
                        st.error("Script quá dài hoặc hệ thống bận.")
            else:
                st.warning("Vui lòng dán script.")