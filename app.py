import streamlit as st
import requests
import json
import base64
import re
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import streamlit.components.v1 as components
# QUAN TRỌNG: Phải import timedelta để tính giờ làm bài
from datetime import datetime, timedelta

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
    Hàm lưu điểm Speaking thông minh
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
            score_num = 0.0
            band_short = "N/A"
            
            # Tìm các mẫu số phổ biến trong bài chấm IELTS
            match = re.search(r"(?:Band Score|KẾT QUẢ|BAND|Band).*?(\d+\.?\d*)", full_feedback, re.IGNORECASE)
            if match:
                try:
                    score_num = float(match.group(1))
                    band_short = str(score_num)
                except: pass
            
            if score_num == 0.0:
                first_line = full_feedback.split('\n')[0]
                match_fallback = re.search(r"(\d+\.?\d*)", first_line)
                if match_fallback:
                    score_num = float(match_fallback.group(1))
                    band_short = str(score_num)

            # Lưu vào Sheet
            ws.append_row([
                str(datetime.now()), 
                student, 
                class_code, 
                lesson, 
                question, 
                band_short,  # Cột 6
                score_num,   # Cột 7
                full_feedback # Cột 8
            ])
            st.toast("✅ Đã lưu điểm và feedback vào hệ thống!", icon="💾")
    except Exception as e:
        print(f"Save Error: {e}")

# --- ĐÃ SỬA LẠI HÀM NÀY ĐỂ NHẬN THAM SỐ MODE ---
def save_reading_log(student, class_code, lesson, score, total, mode="Practice"):
    try:
        sheet = connect_gsheet()
        if sheet:
            try:
                ws = sheet.worksheet("Reading_Logs")
            except:
                ws = sheet.add_worksheet(title="Reading_Logs", rows="1000", cols="10")
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Score", "Total", "Percentage", "Mode"])
            
            percentage = round((score / total) * 100, 1) if total > 0 else 0
            ws.append_row([str(datetime.now()), student, class_code, lesson, score, total, percentage, mode])
            st.toast("✅ Đã lưu kết quả Reading!", icon="💾")
    except: pass

def save_writing_log(student, class_code, lesson, topic, band_score, criteria_scores, feedback):
    """Lưu điểm Writing"""
    try:
        sheet = connect_gsheet()
        if sheet:
            try: ws = sheet.worksheet("Writing_Logs")
            except:
                ws = sheet.add_worksheet(title="Writing_Logs", rows="1000", cols="10")
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Topic", "Overall_Band", "TR_CC_LR_GRA", "Feedback"])
            
            ws.append_row([str(datetime.now()), student, class_code, lesson, topic, band_score, str(criteria_scores), feedback])
            st.toast("✅ Đã lưu bài Writing!", icon="💾")
    except: pass

def get_leaderboard(class_code):
    try:
        sheet = connect_gsheet()
        if not sheet: return None, None, None # Thêm None cho Writing

        # 1. Speaking
        try:
            ws_s = sheet.worksheet("Speaking_Logs")
            df_s = pd.DataFrame(ws_s.get_all_records())
            if not df_s.empty and 'Class' in df_s.columns and 'Score_Num' in df_s.columns:
                df_s = df_s[df_s['Class'] == class_code]
                if not df_s.empty:
                    df_s['Score_Num'] = pd.to_numeric(df_s['Score_Num'], errors='coerce').fillna(0)
                    lb_s = df_s.groupby('Student')['Score_Num'].mean().reset_index()
                    lb_s.columns = ['Học Viên', 'Điểm Speaking (TB)']
                    lb_s = lb_s.sort_values(by='Điểm Speaking (TB)', ascending=False).head(10)
                else: lb_s = None
            else: lb_s = None
        except: lb_s = None

        # 2. Reading
        try:
            ws_r = sheet.worksheet("Reading_Logs")
            df_r = pd.DataFrame(ws_r.get_all_records())
            if not df_r.empty and 'Class' in df_r.columns:
                df_r = df_r[df_r['Class'] == class_code]
                if not df_r.empty:
                    df_r['Score'] = pd.to_numeric(df_r['Score'], errors='coerce')
                    lb_r = df_r.groupby('Student')['Score'].max().reset_index()
                    lb_r.columns = ['Học Viên', 'Điểm Reading (Max)']
                    lb_r = lb_r.sort_values(by='Điểm Reading (Max)', ascending=False).head(10)
                else: lb_r = None
            else: lb_r = None
        except: lb_r = None

        # 3. Writing (Mới)
        try:
            ws_w = sheet.worksheet("Writing_Logs")
            df_w = pd.DataFrame(ws_w.get_all_records())
            if not df_w.empty and 'Class' in df_w.columns:
                df_w = df_w[df_w['Class'] == class_code]
                if not df_w.empty:
                    df_w['Overall_Band'] = pd.to_numeric(df_w['Overall_Band'], errors='coerce')
                    lb_w = df_w.groupby('Student')['Overall_Band'].mean().reset_index() # TB điểm writing
                    lb_w.columns = ['Học Viên', 'Điểm Writing (TB)']
                    lb_w = lb_w.sort_values(by='Điểm Writing (TB)', ascending=False).head(10)
                else: lb_w = None
            else: lb_w = None
        except: lb_w = None

        return lb_s, lb_r, lb_w
    except: return None, None, None

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

# WRITING CONTENT (Chỉ lớp ELITE)
WRITING_CONTENT = {
    "Lesson 3: Education & Society": {
        "task_type": "Task 2",
        "time": 40,
        "question": """
        **Some people think that parents should teach children how to be good members of society. Others, however, believe that school is the place to learn this.**
        
        Discuss both views and give your opinion.
        Give reasons for your answer and include any relevant examples from your own knowledge or experience.
        Write at least 250 words.
        """
    }
}
SPEAKING_MENU = list(SPEAKING_CONTENT.keys()) + [f"Lesson {i}: (Sắp ra mắt)" for i in range(3, 11)]
READING_MENU = [f"Lesson {i}" if i != 2 else "Lesson 2: Marine Chronometer" for i in range(1, 11)]
WRITING_MENU = ["Lesson 3: Education & Society"]
# ================= 2. HỆ THỐNG & API =================
st.set_page_config(page_title="Mr. Tat Loc IELTS Portal", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .main {background-color: #ffffff; font-family: 'Segoe UI', sans-serif;}
    h1 {color: #003366; font-size: 26px; font-weight: 700;}
    h2 {color: #004080; font-size: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 25px;}
    .stButton button {background-color: #004080; color: white; border-radius: 6px; font-weight: 600; padding: 0.5rem 1rem;}
    .stButton button:hover {background-color: #002244;}
    
    /* SCROLL CONTAINER (Khung cuộn độc lập) */
    .scroll-container {
        height: 600px;
        overflow-y: auto;
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #fcfcfc;
    }
    
    /* READING TEXT AREA */
    .reading-text {
        font-size: 16px; /* Tăng nhẹ size bài đọc cho dễ nhìn */
        line-height: 1.8;
        color: #2c3e50;
        text-align: justify;
        padding-right: 10px;
    }
    
    /* CÂU HỎI - ĐÃ TĂNG SIZE TO HƠN */
    .question-text {
        font-size: 16px; /* Tăng size chữ câu hỏi lên 20px */
        font-weight: 600;
        color: #000000; /* Màu đen đậm cho dễ đọc */
        margin-bottom: 8px;
        line-height: 1.5;
    }
    
    /* HIGHLIGHT STYLE (Vàng đậm) */
    .highlighted {
        background-color: #ffff00;
        color: #000;
        font-weight: 500;
        cursor: pointer;
    }
    
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
    </style>
    
    <!-- SCRIPT ĐỂ HIGHLIGHT KHI BÔI ĐEN -->
    <script>
    document.addEventListener('mouseup', function() {
        var selection = window.getSelection();
        var selectedText = selection.toString();
        
        if (selectedText.length > 0) {
            var range = selection.getRangeAt(0);
            var span = document.createElement("span");
            span.className = "highlighted";
            span.title = "Click để xóa highlight";
            span.onclick = function() {
                var text = document.createTextNode(this.innerText);
                this.parentNode.replaceChild(text, this);
            };
            try {
                range.surroundContents(span);
                selection.removeAllRanges();
            } catch (e) {
                console.log("Không thể highlight qua nhiều block");
            }
        }
    });
    </script>
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
if 'reading_session' not in st.session_state: st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
if 'reading_highlight' not in st.session_state: st.session_state['reading_highlight'] = ""
if 'writing_step' not in st.session_state: st.session_state['writing_step'] = 'outline' 
if 'writing_outline_score' not in st.session_state: st.session_state['writing_outline_score'] = 0
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
        menu = st.radio("CHỌN KỸ NĂNG:", ["🏆 Bảng Xếp Hạng", "🗣️ Speaking", "📖 Reading", "🎧 Listening", "✍️ Writing"])
        st.divider()
        if st.button("Đăng xuất"): logout()

    # --- MODULE 4: LEADERBOARD ---
    if menu == "🏆 Bảng Xếp Hạng":
        st.title(f"🏆 Bảng Xếp Hạng Lớp {user['class']}")
        if st.button("🔄 Làm mới"): st.rerun()
        lb_s, lb_r, lb_w = get_leaderboard(user['class'])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🎤 Speaking (TB)")
            if lb_s is not None and not lb_s.empty: st.dataframe(lb_s.style.format({"Điểm Speaking (TB)": "{:.2f}"}).background_gradient(cmap="Blues"), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")
        with c2:
            st.subheader("📚 Reading (Max)")
            if lb_r is not None and not lb_r.empty: st.dataframe(lb_r.style.format({"Điểm Reading (Max)": "{:.1f}"}).background_gradient(cmap="Greens"), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")
        with c3:
            st.subheader("✍️ Writing (TB)")
            if lb_w is not None and not lb_w.empty: st.dataframe(lb_w.style.format({"Điểm Writing (TB)": "{:.2f}"}).background_gradient(cmap="Oranges"), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")

    # --- MODULE 5: WRITING (NEW & POLISHED) ---
    elif menu == "✍️ Writing":
        st.title("✍️ Luyện Tập Writing (Task 2)")
        
        lesson_w = st.selectbox("Chọn bài viết:", WRITING_MENU)
        
        # Chỉ lớp ELITE mới thấy bài này (ví dụ)
        if "Lesson 3" in lesson_w:
            data_w = WRITING_CONTENT["Lesson 3: Education & Society"]
            st.info(f"### TOPIC: {data_w['question']}")
            
            # --- GIAI ĐOẠN 1: OUTLINE CHECK ---
            if st.session_state['writing_step'] == 'outline':
                st.subheader("BƯỚC 1: Lập Dàn Ý (Outline Logic Check)")
                st.markdown("Hệ thống sẽ kiểm tra **Logic, Mạch lạc** và **Task Response**.")
                
                with st.form("outline_form"):
                    intro = st.text_area("Introduction:", height=80, placeholder="Paraphrase topic + Thesis statement")
                    body1 = st.text_area("Body 1 (PEER / What-Why-How):", height=150, placeholder="Main Idea 1...")
                    body2 = st.text_area("Body 2 (PEER / What-Why-How):", height=150, placeholder="Main Idea 2...")
                    conc = st.text_area("Conclusion:", height=80, placeholder="Restate opinion + Summary")
                    
                    if st.form_submit_button("🔍 Kiểm Tra Outline"):
                        if intro and body1 and body2 and conc:
                            with st.spinner("AI đang soi lỗi logic (Fallacies Check)..."):
                                prompt = f"""
                                Role: Strict IELTS Writing Logic Coach.
                                Task: Evaluate this Task 2 Outline. Output in Vietnamese .
                                Topic: {data_w['question']}
                                Input: Intro: {intro} | B1: {body1} | B2: {body2} | Conc: {conc}
                                
                                CHECKLIST (Common Errors):
                                1. Logical Fallacies (False Cause, Overgeneralization, Slippery Slope, Either/Or, Equivocation).
                                2. Coherence (Unclear arguments, Listing ideas without explanation, Topic Sentence mismatch).
                                3. Task Response (Partial address, Irrelevant ideas).
                                4. Structure: Check for PEER (Point-Explanation-Example-Result) or What-Why-How flow.
                                
                                OUTPUT FORMAT (Vietnamese JSON):
                                {{
                                    "score": [Integer 0-10],
                                    "feedback": "[Specific feedback on logic & structure. Be sharp & direct.]",
                                    "collocations": "[List 5-7 academic collocations relevant to this specific outline to help writing]"
                                }}
                                """
                                res = call_gemini(prompt, expect_json=True)
                                if res:
                                    try:
                                        eval_data = json.loads(res)
                                        st.session_state['writing_outline_score'] = eval_data['score']
                                        st.session_state['writing_feedback'] = eval_data['feedback']
                                        st.session_state['writing_collocations'] = eval_data['collocations']
                                        
                                        if eval_data['score'] >= 8:
                                            st.success(f"✅ Outline Đạt: {eval_data['score']}/10")
                                            st.session_state['writing_step'] = 'writing'
                                            st.rerun()
                                        else:
                                            st.error(f"⛔ Outline Chưa Đạt: {eval_data['score']}/10")
                                            st.markdown(eval_data['feedback'])
                                            st.warning("Hãy sửa lại Outline để đảm bảo logic trước khi viết bài!")
                                    except: st.error("Lỗi AI. Vui lòng thử lại.")
                        else: st.warning("Vui lòng điền đủ 4 phần.")

            # --- GIAI ĐOẠN 2: VIẾT BÀI ---
            elif st.session_state['writing_step'] == 'writing':
                st.subheader("BƯỚC 2: Viết Bài (Essay Writing)")
                
                with st.expander("Gợi ý từ vựng (Từ Outline)", expanded=True):
                    st.info(st.session_state.get('writing_collocations', ''))
                
                # Timer JS
                timer_html = f"""
                <div style="font-size: 20px; font-weight: bold; color: #d35400;">
                    ⏳ Thời gian: <span id="timer_w">40:00</span>
                </div>
                <script>
                var time = {data_w['time']} * 60;
                setInterval(function() {{
                    var m = Math.floor(time / 60);
                    var s = time % 60;
                    document.getElementById("timer_w").innerHTML = m + ":" + (s < 10 ? "0" : "") + s;
                    time--;
                }}, 1000);
                </script>
                """
                components.html(timer_html, height=50)
                
                essay = st.text_area("Bài làm (Min 250 words):", height=400)
                
                if st.button("📤 Nộp Bài"):
                    if len(essay.split()) < 200:
                        st.warning("Bài viết còn ngắn. Hãy cố gắng viết đủ 250 từ.")
                    else:
                        with st.spinner("Đang chấm điểm theo Band Descriptors (4-9)..."):
                            prompt = f"""
                            Role: Professional IELTS Examiner, Output in Vietnamese.
                            Task: Grade Task 2 Essay.
                            Topic: {data_w['question']}
                            Essay: {essay}
                            
                            RUBRIC (Strict Adherence):
                            - **Band 4 (Limited):** Ideas irrelevant/repetitive. No clear progression. Vocab basic/repetitive. Grammar limited/frequent errors.
                            - **Band 5 (Modest):** Addresses task but limited detail. Mechanical cohesion. Simple vocab accurate but limited range. Frequent grammar errors.
                            - **Band 6 (Competent):** Relevant overview. Coherent but mechanical cohesive devices. Vocab adequate but some inaccuracy. Mix of simple/complex sentences.
                            - **Band 7 (Good):** Clear position throughout. Logically organised. Flexible vocab/collocations. Frequent error-free sentences.
                            - **Band 8 (Very Good):** Sufficiently developed ideas. Skilful paragraphing. Precise vocab (uncommon items). Flexible/accurate grammar.
                            - **Band 9 (Expert):** Fully satisfied. Effortless cohesion. Sophisticated lexical control. Grammatically accurate.
                            
                            CONSTRAINT: Component scores (TR, CC, LR, GRA) MUST be INTEGERS (e.g. 6, 7, 8). Overall can be .5.
                            
                            OUTPUT JSON:
                            {{
                                "TR": [int], "CC": [int], "LR": [int], "GRA": [int],
                                "Overall": [float],
                                "Feedback": "[Detailed critique in VIETNAMESE. Start with Strengths, then Weaknesses. Suggest specific improvements.]"
                            }}
                            """
                            res = call_gemini(prompt, expect_json=True)
                            if res:
                                try:
                                    grade = json.loads(res)
                                    st.session_state['writing_result'] = grade
                                    st.session_state['writing_step'] = 'finished'
                                    
                                    crit = json.dumps({"TR": grade['TR'], "CC": grade['CC'], "LR": grade['LR'], "GRA": grade['GRA']})
                                    save_writing_log(user['name'], user['class'], lesson_w, "Education", grade['Overall'], crit, grade['Feedback'])
                                    st.rerun()
                                except: st.error("Lỗi chấm bài.")

            # --- GIAI ĐOẠN 3: KẾT QUẢ ---
            elif st.session_state['writing_step'] == 'finished':
                res = st.session_state['writing_result']
                st.balloons()
                st.success(f"🏆 OVERALL BAND: {res['Overall']}")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Task Response", res['TR'])
                c2.metric("Coherence", res['CC'])
                c3.metric("Lexical", res['LR'])
                c4.metric("Grammar", res['GRA'])
                
                with st.container(border=True):
                    st.markdown("### 📝 Nhận xét chi tiết")
                    st.markdown(res['Feedback'])
                
                if st.button("Viết lại (Resubmit)"):
                    st.session_state['writing_step'] = 'outline'
                    st.rerun()
        else: st.warning("Bài này chưa mở.")
    
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
                                Role: Senior IELTS Speaking Examiner (Friendly but Strict on Rubric).
                                Task: Assess speaking response for "{question}".
                                **CẤM:** Không được dùng các câu dẫn nhập như "Đây là ...". Hãy vào thẳng nội dung luôn.
                            
                                
                                **RUBRIC CHẤM ĐIỂM (BẮT BUỘC TUÂN THỦ):**
                                - **Band 7-8-9:** Nói trôi chảy, ít ngắt quãng. Sử dụng từ nối, từ vựng phong phú (idioms, collocations) chính xác. Cấu trúc ngữ pháp phức tạp (câu điều kiện, mệnh đề quan hệ) thành thạo. Phát âm chuẩn, có ngữ điệu.
                                - **Band 6:** Nói mạch lạc nhưng đôi khi mất kết nối. Có dùng từ nối. Vốn từ đủ dùng, bắt đầu paraphrase. Có sử dụng câu phức nhưng vẫn còn lỗi. Phát âm rõ ràng.
                                - **Band 5:** Duy trì được mạch nói nhưng hay lặp lại/tự sửa sai. Vốn từ hạn chế ở các chủ đề quen thuộc. Dùng câu đơn đúng, câu phức thường sai.
                                - **Band 4:** Hay ngập ngừng, nói câu cụt. Vốn từ nghèo nàn, lặp lại. Ngữ pháp rất cơ bản, mắc lỗi thường xuyên.
                                
                                **Input Audio Context:** This is a student from class level {user['level']['level']}. However, GRADE BASED ON PERFORMANCE, not just level. E.g., if they use high-level idioms like "bilingual MC", "on the side" correctly, they deserve Band 6.0+ regardless of their class.
                                
                                OUTPUT FORMAT (Vietnamese Markdown):
                                
                                ### KẾT QUẢ: [Band Score] (Chấm công tâm theo rubric)
                                
                                ### PHÂN TÍCH CHI TIẾT (Dựa trên 4 tiêu chí):
                                1. **Fluency & Coherence:** [Nhận xét độ trôi chảy, các từ nối đã dùng]
                                2. **Lexical Resource:** [Đánh giá vốn từ, collocations, idioms (nếu có)]
                                3. **Grammatical Range & Accuracy:** [Nhận xét cấu trúc câu đơn/phức, thì sử dụng]
                                4. **Pronunciation:** [Nhận xét về âm đuôi, ngữ điệu, trọng âm]
                                
                                ### ĐỀ XUẤT CẢI THIỆN:
                                * **Original:** "[Trích dẫn toàn bộ bài nói của học viên]"
                                * **Better:** "[Phiên bản nâng cấp tự nhiên hơn/Native speaker style]"
                                * **Giải thích chi tiết:** [Giải thích từng thay đổi nhỏ: tại sao dùng từ này thay từ kia, cấu trúc này hay hơn chỗ nào...]
                                """
                        
                                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
                                payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}}]}]}
                        
                                resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                                
                                if resp.status_code == 200:
                                    text_result = resp.json()['candidates'][0]['content']['parts'][0]['text']
                                    st.markdown(text_result)
                                    st.session_state['speaking_attempts'][question] = attempts + 1
                                    
                                    # LƯU ĐIỂM (Đã sửa lỗi tham số thừa)
                                    save_speaking_log(user['name'], user['class'], lesson_choice, question, text_result)
                                else:
                                    st.error(f"⚠️ Lỗi Google (Mã {resp.status_code}): {resp.text}")
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}")
            else:
                st.warning("⛔ Đã hết 5 lượt trả lời.")
        else:
            st.info("Bài học này chưa cập nhật.")

    # --- MODULE 2: READING (SPLIT VIEW & REALTIME TIMER) ---
    elif menu == "📖 Reading":
        st.title("📖 Luyện Reading & Từ Vựng")
        lesson_choice = st.selectbox("Chọn bài đọc:", READING_MENU)
        
        # Reset session khi đổi bài
        if 'current_reading_lesson' not in st.session_state or st.session_state['current_reading_lesson'] != lesson_choice:
            st.session_state['current_reading_lesson'] = lesson_choice
            st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
            st.session_state['reading_highlight'] = ""
            if 'reading_intro_text' in st.session_state: del st.session_state['reading_intro_text']

        if "Marine Chronometer" in lesson_choice:
            data = READING_CONTENT["Lesson 2: Marine Chronometer"]
            
            tab1, tab2 = st.tabs(["Làm Bài Đọc Hiểu", "Bài Tập Từ Vựng AI"])
            
            # TAB 1: BÀI ĐỌC CHÍNH (Split View)
            with tab1:
                # --- TRẠNG THÁI 1: GIỚI THIỆU & CHỌN CHẾ ĐỘ ---
                if st.session_state['reading_session']['status'] == 'intro':
                    st.info(f"### {data['title']}")
                    
                    if 'reading_intro_text' not in st.session_state:
                        with st.spinner("AI đang tạo giới thiệu..."):
                            intro_prompt = f"""
                            Bạn là một giáo viên IELTS. Hãy giới thiệu 3 điều thú vị nhất về chủ đề "{data['title']}" dựa trên nội dung bài đọc, và khuyến khích học viên làm bài đọc để hiểu thêm.
                            
                            YÊU CẦU:
                            1. **Văn phong:** Đời thường, đơn giản hóa, dễ hiểu, không dùng thuật ngữ phức tạp, không dùng từ trong dấu ngoặc kép.
                            2. **Hình thức:** Trả về trực tiếp 3 gạch đầu dòng (bullet points) không dùng icon.
                            3. **CẤM:** Không được dùng các câu dẫn nhập như "Dựa trên bài đọc...", "Đây là tóm tắt...", "Chào bạn...". Hãy vào thẳng nội dung kiến thức luôn.
                            
                            Nội dung bài đọc (trích đoạn): {data['text'][:1000]}...
                            """
                            st.session_state['reading_intro_text'] = call_gemini(intro_prompt)
                    
                    if st.session_state.get('reading_intro_text'):
                        st.markdown(f"**Giới thiệu về bài đọc:**\n\n{st.session_state['reading_intro_text']}")
                    
                    
                    st.write("**Thông tin bài thi:**")
                    col_info1, col_info2 = st.columns(2)
                    col_info1.write("- **Dạng bài:** Fill in the blanks")
                    col_info2.write("- **Số lượng:** 6 câu hỏi")
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    if c1.button("🟢 Luyện Tập (Không giới hạn thời gian)"):
                        st.session_state['reading_session']['status'] = 'doing'; st.session_state['reading_session']['mode'] = 'practice'; st.rerun()
                    if c2.button("🔴 Luyện Thi (20 Phút)"):
                        st.session_state['reading_session']['status'] = 'doing'; st.session_state['reading_session']['mode'] = 'exam'
                        st.session_state['reading_session']['end_time'] = datetime.now() + timedelta(minutes=20); st.rerun()

                # --- TRẠNG THÁI 2: DOING ---
                # --- TRẠNG THÁI 2: DOING ---
                elif st.session_state['reading_session']['status'] == 'doing':
                    # Xử lý Timer (Javascript Realtime Countdown)
                    timer_html = ""
                    if st.session_state['reading_session']['mode'] == 'exam':
                        end_time = st.session_state['reading_session']['end_time']
                        remaining_seconds = (end_time - datetime.now()).total_seconds()
                        
                        if remaining_seconds > 0:
                            # Javascript để đếm ngược mượt mà không cần reload trang
                            timer_html = f"""
                            <div style="font-size: 20px; font-weight: bold; color: #d35400; margin-bottom: 10px; font-family: 'Segoe UI', sans-serif;">
                                ⏳ Thời gian còn lại: <span id="timer"></span>
                            </div>
                            <script>
                            var timeLeft = {int(remaining_seconds)};
                            var timerElement = document.getElementById("timer");
                            
                            var countdown = setInterval(function() {{
                                var minutes = Math.floor(timeLeft / 60);
                                var seconds = timeLeft % 60;
                                timerElement.innerHTML = minutes + "m " + (seconds < 10 ? "0" : "") + seconds + "s";
                                
                                timeLeft -= 1;
                                if (timeLeft < 0) {{
                                    clearInterval(countdown);
                                    timerElement.innerHTML = "HẾT GIỜ!";
                                    alert("Đã hết giờ làm bài! Vui lòng nộp bài.");
                                }}
                            }}, 1000);
                            </script>
                            """
                            st.components.v1.html(timer_html, height=50)
                        else:
                            st.error("🛑 ĐÃ HẾT GIỜ! Vui lòng nộp bài ngay.")
                    else:
                        st.success("🟢 Chế độ Luyện Tập (Thoải mái thời gian)")

                    c_text, c_quiz = st.columns([1, 1], gap="medium")
                    
                    with c_text:
                        st.subheader("📄 Bài Đọc")
                        with st.expander("🖍️ Highlight (Nhập từ)", expanded=True):
                            hl = st.text_input("Nhập từ cần tô màu:", key="hl")
                            c_h1, c_h2 = st.columns(2)
                            if c_h1.button("Tô màu"): st.session_state['reading_highlight'] = hl
                            if c_h2.button("Xóa"): st.session_state['reading_highlight'] = ""

                        display_text = data['text']
                        if "### Timekeeper" in display_text:
                             display_text = display_text.replace("### Timekeeper: Invention of Marine Chronometer", "")
                        
                        html_content = f"<h2>{data['title']}</h2>" + display_text.replace("\n", "<br>")
                        if st.session_state['reading_highlight']:
                            ptn = re.compile(re.escape(st.session_state['reading_highlight']), re.IGNORECASE)
                            html_content = ptn.sub(lambda m: f"<span class='highlighted'>{m.group(0)}</span>", html_content)
                        st.markdown(f"<div class='scroll-container'><div class='reading-text'>{html_content}</div></div>", unsafe_allow_html=True)

                    with c_quiz:
                        st.subheader("📝 Câu Hỏi")
                        with st.container(height=600):
                            st.markdown("**Questions 1-6: Fill in the blanks (NO MORE THAN TWO WORDS)**")
                            with st.form("read_exam_form"):
                                ans = {}
                                for q in data['questions_fill']:
                                    # --- SỬA Ở ĐÂY: DÙNG CLASS question-text ---
                                    st.markdown(f"<div class='question-text'>{q['q']}</div>", unsafe_allow_html=True)
                                    ans[q['id']] = st.text_input(f"Answer {q['id']}", label_visibility="collapsed")
                                    st.write("")
                                
                                if st.form_submit_button("NỘP BÀI"):
                                    st.session_state['reading_session']['status'] = 'result'
                                    st.session_state['reading_session']['user_answers'] = ans
                                    st.rerun()

                # --- TRẠNG THÁI 3: KẾT QUẢ & GIẢI THÍCH ---
                elif st.session_state['reading_session']['status'] == 'result':
                    st.subheader("📊 Kết Quả Bài Làm")
                    user_answers = st.session_state['reading_session']['user_answers']
                    score = 0
                    
                    col_res_L, col_res_R = st.columns([1, 1])
                    
                    # Hiển thị lại bài đọc để đối chiếu
                    with col_res_L:
                        with st.expander("Xem lại bài đọc", expanded=False):
                            st.markdown(data['text'])
                    
                    with col_res_R:
                        for q in data['questions_fill']:
                            u_ans = user_answers.get(q['id'], "").strip().lower()
                            c_ans = q['a'].lower()
                            
                            is_correct = u_ans == c_ans
                            if is_correct: score += 1
                            
                            if is_correct:
                                st.success(f"✅ {q['q']} -> Bạn trả lời: {u_ans}")
                            else:
                                st.error(f"❌ {q['q']}")
                                st.markdown(f"**Bạn trả lời:** {u_ans} | **Đáp án:** {q['a']}")
                            
                            # Luôn hiện giải thích
                            st.markdown(f"<div class='explanation-box'>💡 <b>Giải thích:</b> {q['exp']}</div>", unsafe_allow_html=True)
                            st.write("---")

                        st.success(f"🏆 Tổng điểm: {score}/{len(data['questions_fill'])}")
                        
                        # Lưu điểm
                        save_reading_log(user['name'], user['class'], lesson_choice, score, len(data['questions_fill']), st.session_state['reading_session']['mode'])
                        
                        if st.button("Làm lại bài này"):
                            st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
                            st.rerun()

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