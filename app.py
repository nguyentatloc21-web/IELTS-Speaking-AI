import streamlit as st
import requests
import json
import base64
import re
import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ================= 0. HÀM HỖ TRỢ (TIỆN ÍCH) =================
def get_current_time_str():
    """Trả về thời gian hiện tại định dạng dễ đọc: DD/MM/YYYY HH:MM:SS"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def normalize_name(name):
    """
    Chuẩn hóa tên học viên:
    - Xóa khoảng trắng thừa ở đầu/cuối và giữa các từ.
    - Viết hoa chữ cái đầu mỗi từ.
    VD: "  nguyễn   văn  a " -> "Nguyễn Văn A"
    """
    if not name: return ""
    # Tách các từ, bỏ khoảng trắng thừa, viết hoa chữ đầu, rồi ghép lại
    return " ".join(name.strip().split()).title()

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
    """Lưu điểm Speaking"""
    try:
        sheet = connect_gsheet()
        if sheet:
            try:
                ws = sheet.worksheet("Speaking_Logs")
            except:
                ws = sheet.add_worksheet(title="Speaking_Logs", rows="1000", cols="10")
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Question", "Band_Short", "Score_Num", "Full_Feedback"])
            
            score_num = 0.0
            band_short = "N/A"
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

            ws.append_row([str(datetime.now()), student, class_code, lesson, question, band_short, score_num, full_feedback])
            st.toast("✅ Đã lưu kết quả!", icon="💾")
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
        if not sheet: return None, None, None

        # 1. Speaking
        try:
            ws_s = sheet.worksheet("Speaking_Logs")
            data = ws_s.get_all_values()
            
            if len(data) > 1:
                headers = data[0]
                df_s = pd.DataFrame(data[1:], columns=headers)
                
                if 'Class' in df_s.columns:
                    df_s = df_s[df_s['Class'] == class_code]
                    
                    if not df_s.empty:
                        # --- FIX LỖI: Chuẩn hóa tên học viên trước khi Group ---
                        if 'Student' in df_s.columns:
                            df_s['Student'] = df_s['Student'].astype(str).apply(normalize_name)

                        score_col = None
                        for col in ['Score_Num', 'Band_Score', 'Band_Short', 'Score']:
                            if col in df_s.columns:
                                score_col = col
                                break
                        
                        if score_col:
                            def extract_float(val):
                                try:
                                    found = re.search(r"(\d+\.?\d*)", str(val))
                                    return float(found.group(1)) if found else 0.0
                                except: return 0.0

                            df_s['Final_Score'] = df_s[score_col].apply(extract_float)
                            df_s = df_s[df_s['Final_Score'] > 0]
                            
                            # Group by tên đã chuẩn hóa
                            lb_s = df_s.groupby('Student')['Final_Score'].mean().reset_index()
                            lb_s.columns = ['Học Viên', 'Điểm Speaking (TB)']
                            lb_s = lb_s.sort_values(by='Điểm Speaking (TB)', ascending=False).head(10)
                        else: lb_s = None
                    else: lb_s = None
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
                    # --- FIX LỖI: Chuẩn hóa tên ---
                    if 'Student' in df_r.columns:
                        df_r['Student'] = df_r['Student'].astype(str).apply(normalize_name)

                    df_r['Score'] = pd.to_numeric(df_r['Score'], errors='coerce')
                    lb_r = df_r.groupby('Student')['Score'].max().reset_index()
                    lb_r.columns = ['Học Viên', 'Điểm Reading (Max)']
                    lb_r = lb_r.sort_values(by='Điểm Reading (Max)', ascending=False).head(10)
                else: lb_r = None
            else: lb_r = None
        except: lb_r = None

        # 3. Writing
        try:
            ws_w = sheet.worksheet("Writing_Logs")
            df_w = pd.DataFrame(ws_w.get_all_records())
            if not df_w.empty and 'Class' in df_w.columns:
                df_w = df_w[df_w['Class'] == class_code]
                if not df_w.empty:
                    # --- FIX LỖI: Chuẩn hóa tên ---
                    if 'Student' in df_w.columns:
                        df_w['Student'] = df_w['Student'].astype(str).apply(normalize_name)

                    df_w['Overall_Band'] = pd.to_numeric(df_w['Overall_Band'], errors='coerce')
                    lb_w = df_w.groupby('Student')['Overall_Band'].mean().reset_index()
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
    },
    "Lesson 3: Australian Agricultural Innovations": {
        "status": "Active",
        "title": "Australian Agricultural Innovations: 1850 – 1900",
        "text": """
During this period, there was a widespread expansion of agriculture in Australia. The selection
system was begun, whereby small sections of land were parceled out by lot. Particularly in New
South Wales, this led to conflicts between small holders and the emerging squatter class, whose
abuse of the system often allowed them to take vast tracts of fertile land.
There were also many positive advances in farming technology as the farmers adapted agricultural
methods to the harsh Australian conditions. One of the most important was “dry farming”. This
was the discovery that repeated ploughing of fallow, unproductive land could preserve nitrates and
moisture, allowing the land to eventually be cultivated. This, along with the extension of the
railways, allowed the development of what are now great inland wheat lands.
The inland areas of Australia are less fertile than most other wheat-producing countries and yields
per acre are lower. This slowed their development, but also led to the development of several labour
saving devices. In 1843 John Ridley, a South Australian farmer, invented “the stripper”, a basic
harvesting machine. By the 1860s its use was widespread. H. V. McKay, then only nineteen,
modified the machine so that it was a complete harvester: cutting, collecting and sorting. McKay
developed this early innovation into a large harvester manufacturing industry centred near
Melbourne and exporting worldwide. Robert Bowyer Smith invented the “stump jump plough”,
which let a farmer plough land which still had tree stumps on it. It did this by replacing the
traditional plough shear with a set of wheels that could go over stumps, if necessary.
The developments in farm machinery were supported by scientific research. During the late 19th
century, South Australian wheat yields were declining. An agricultural scientist at the colony’s
agricultural college, John Custance, found that this was due to a lack of phosphates and advised the
use of soluble superphosphate fertilizer. The implementation of this scheme revitalised the industry.
From early days it had been obvious that English and European sheep breeds had to be adapted to
Australian conditions, but only near the end of the century was the same applied to crops. Prior to
this, English and South African strains had been use, with varying degrees of success. WilliamFarrer, from Cambridge University, was the first to develop new wheat varieties that were better
able to withstand dry Australian conditions. By 1914, Australia was no longer thought of as a land
suitable only for sheep, but as a wheat-growing nation.
        """,
        "questions_mc": [
            {"id": "q1", "q": "1. What is dry farming?", "options": ["A. Preserving nitrates and moisture.", "B. Ploughing the land again and again.", "C. Cultivating fallow land."], "a": "B. Ploughing the land again and again.", "exp": "Dẫn chứng (Đoạn 2): 'This was the discovery that repeated ploughing of fallow... could preserve nitrates...' -> Dry farming là phương pháp cày xới liên tục (repeated ploughing) để giữ ẩm."},
            {"id": "q2", "q": "2. What did H. V. McKay do?", "options": ["A. Export the stripper.", "B. Improve the stripper.", "C. Cut, collect, and sort wheat."], "a": "B. Improve the stripper.", "exp": "Dẫn chứng (Đoạn 3): 'H. V. McKay... modified the machine so that it was a complete harvester...' -> Modified the machine = Improve the stripper."},
            {"id": "q3", "q": "3. What did the 'stump jump plough’ innovation allow farmers to do?", "options": ["A. Cut through tree stumps.", "B. Change the wheels for a traditional plough.", "C. Allow farmers to cultivate land that hadn’t been fully cleared."], "a": "C. Allow farmers to cultivate land that hadn’t been fully cleared.", "exp": "Dẫn chứng (Đoạn 3): '...let a farmer plough land which still had tree stumps on it.' -> Cày trên đất vẫn còn gốc cây (chưa dọn sạch)."},
            {"id": "q4", "q": "4. What did John Custance recommend?", "options": ["A. Improving wheat yields.", "B. Revitalizing the industry.", "C. Fertilizing the soil."], "a": "C. Fertilizing the soil.", "exp": "Dẫn chứng (Đoạn 4): '...advised the use of soluble superphosphate fertilizer.' -> Khuyên dùng phân bón."},
            {"id": "q5", "q": "5. Why was William Farrer’s wheat better?", "options": ["A. It was drought-resistant.", "B. It wasn’t from England or South Africa.", "C. It was drier for Australian conditions."], "a": "A. It was drought-resistant.", "exp": "Dẫn chứng (Đoạn 5): '...better able to withstand dry Australian conditions.' -> Chịu hạn tốt (drought-resistant)."}
        ]
    }
}

    
# WRITING CONTENT (Chỉ lớp ELITE)
WRITING_CONTENT = {
    "Lesson 3: Education & Society": {
        "task_type": "Task 2",
        "time": 40,
        "question": """
### 📝 IELTS Writing Task 2

**Some people think that parents should teach children how to be good members of society. Others, however, believe that school is the place to learn this.**

**Instructions:**
* Discuss both these views and give your own opinion.
* Give reasons for your answer and include any relevant examples from your own knowledge or experience.

---
*Write at least 250 words.*
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
    /* =============================================
       1. GLOBAL STYLES (Kế thừa từ bộ Visual Hierarchy)
       ============================================= */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, sans-serif;
        color: #333333;
    }

    h1 { color: #003366; font-size: 32px !important; font-weight: 800; margin-bottom: 20px; }
    h2 { color: #004080; font-size: 24px !important; font-weight: 700; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-top: 30px; }
    h3 { color: #0059b3; font-size: 20px !important; font-weight: 600; margin-top: 20px; }
    
    /* Button chuẩn */
    .stButton button {
        background-color: #004080; color: white; border-radius: 8px; font-weight: 600; 
        padding: 0.6rem 1.2rem; border: none; transition: all 0.3s ease;
    }
    .stButton button:hover { background-color: #002244; transform: translateY(-2px); }

    /* =============================================
       2. READING & EXAM MODE STYLES (Phần bạn mới thêm)
       ============================================= */
    
    /* Khung cuộn bài đọc */
    .scroll-container {
        height: 600px;
        overflow-y: auto;
        padding: 25px; /* Tăng padding chút cho thoáng */
        border: 1px solid #d1d9e6; /* Viền xanh xám nhẹ hợp tông hơn */
        border-radius: 12px; /* Bo tròn mềm mại hơn */
        background-color: #f8f9fa; /* Màu nền xám trắng hiện đại */
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); /* Hiệu ứng chìm nhẹ */
    }
    
    /* Nội dung bài đọc */
    .reading-text {
        font-size: 17px; /* Tăng lên 17px chuẩn sách giáo khoa */
        line-height: 1.8; /* Dãn dòng rộng để mắt không mỏi */
        color: #2c3e50; /* Màu chữ xanh đen đậm, dịu mắt hơn đen tuyền */
        text-align: justify;
        padding-right: 15px;
    }
    
    /* Câu hỏi */
    .question-text {
        font-size: 17px; /* Set 17px để phân biệt rõ với văn bản thường */
        
        color: #2c3e50; /* Dùng màu thương hiệu cho câu hỏi */
        margin-bottom: 12px;
        margin-top: 15px;
        line-height: 1.5;
    }
    
    /* Highlight (Vàng) */
    .highlighted {
        background-color: #fffacd; /* Vàng kem (LemonChiffon) dịu hơn vàng gắt */
        border-bottom: 2px solid #ffd700;
        color: #000;
        cursor: pointer;
        padding: 2px 0;
    }
    
    /* Hộp giải thích */
    .explanation-box {
        background-color: #eef6fc; /* Xanh rất nhạt */
        padding: 20px; 
        border-radius: 8px;
        border-left: 5px solid #004080; /* Đường kẻ trái màu xanh đậm chủ đạo */
        margin-top: 15px; 
        font-size: 16px;
        color: #2c3e50;
    }

    /* Trạng thái đúng/sai */
    .correct-ans { color: #27ae60; font-weight: bold; background-color: #e8f8f5; padding: 2px 6px; border-radius: 4px; }
    .wrong-ans { color: #c0392b; font-weight: bold; background-color: #fdedec; padding: 2px 6px; border-radius: 4px; }
    
    /* Tùy chỉnh thanh cuộn cho đẹp (Webkit) */
    .scroll-container::-webkit-scrollbar { width: 8px; }
    .scroll-container::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
    .scroll-container::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
    .scroll-container::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }
    </style>
    
    <script>
    // TÍNH NĂNG HIGHLIGHT BẰNG CÁCH BÔI ĐEN (Updated)
    document.addEventListener('mouseup', function() {
        var selection = window.getSelection();
        var selectedText = selection.toString();
        
        // Chỉ xử lý nếu có text được bôi đen
        if (selectedText.length > 0) {
            // Hàm kiểm tra xem node có nằm trong vùng bài đọc (.reading-text) không
            function hasReadingClass(node) {
                if (!node) return false;
                if (node.nodeType === 3) node = node.parentNode; // Nếu là Text Node thì lấy cha
                return node.closest('.reading-text') !== null;
            }

            var anchor = selection.anchorNode;
            var focus = selection.focusNode;

            if (hasReadingClass(anchor) && hasReadingClass(focus)) {
                var range = selection.getRangeAt(0);
                var span = document.createElement("span");
                span.className = "highlighted";
                span.title = "Click để xóa highlight";
                
                // Sự kiện click để xóa highlight
                span.onclick = function(e) {
                    e.stopPropagation(); // Ngăn sự kiện nổi bọt
                    var text = document.createTextNode(this.innerText);
                    this.parentNode.replaceChild(text, this);
                    // Gộp các text node lại để tránh lỗi chọn sau này
                    if (text.parentNode) text.parentNode.normalize(); 
                };

                try {
                    range.surroundContents(span);
                    selection.removeAllRanges(); // Bỏ bôi đen sau khi highlight xong
                } catch (e) { 
                    console.log("Không thể highlight qua nhiều đoạn văn (block elements)."); 
                }
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

# --- HÀM GỌI API GEMINI (ĐÃ TỐI ƯU JSON VÀ FIX LỖI 429) ---
# --- ĐỊNH NGHĨA QUAN TRỌNG: Cần có tham số audio_data ---
def call_gemini(prompt, expect_json=False, audio_data=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Nếu cần JSON, thêm chỉ dẫn rõ ràng vào prompt
    final_prompt = prompt
    if expect_json:
        final_prompt += "\n\nIMPORTANT: Output STRICTLY JSON without Markdown formatting (no ```json or ```)."
    
    # Cấu trúc message parts
    parts = [{"text": final_prompt}]
    if audio_data:
        parts.append({"inline_data": {"mime_type": "audio/wav", "data": audio_data}})

    data = {"contents": [{"parts": parts}]}
    
    # Cơ chế Retry khi gặp lỗi 429
    for attempt in range(4): # Thử lại tối đa 4 lần
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(data))
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                if expect_json:
                    # Làm sạch chuỗi nếu AI lỡ thêm markdown
                    text = re.sub(r"```json|```", "", text).strip()
                return text
            elif resp.status_code == 429: # Resource Exhausted
                time.sleep(2 ** attempt) # Đợi 1s, 2s, 4s...
                continue
            else:
                return None
        except:
            time.sleep(1)
            continue
            
    return None

# --- QUẢN LÝ SESSION STATE ---
if 'speaking_attempts' not in st.session_state: st.session_state['speaking_attempts'] = {}
if 'generated_quiz' not in st.session_state: st.session_state['generated_quiz'] = None
if 'reading_session' not in st.session_state: st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
if 'reading_highlight' not in st.session_state: st.session_state['reading_highlight'] = ""
if 'writing_step' not in st.session_state: st.session_state['writing_step'] = 'outline' 
if 'writing_outline_score' not in st.session_state: st.session_state['writing_outline_score'] = 0
# ================= 3. LOGIC ĐĂNG NHẬP (ĐÃ CHUẨN HÓA TÊN) =================
def login():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            name = st.text_input("Họ tên học viên:")
            class_code = st.selectbox("Chọn Mã Lớp:", ["-- Chọn lớp --"] + list(CLASS_CONFIG.keys()))
            if st.form_submit_button("Vào Lớp Học"):
                if name and class_code != "-- Chọn lớp --":
                    # CHUẨN HÓA TÊN: "  nguyễn văn a  " -> "Nguyễn Văn A"
                    clean_name = normalize_name(name)
                    st.session_state['user'] = {"name": clean_name, "class": class_code, "level": CLASS_CONFIG[class_code]}
                    st.rerun()
                else: st.warning("Vui lòng điền đủ thông tin.")

def logout(): st.session_state['user'] = None; st.rerun()

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
            if lb_s is not None and not lb_s.empty: 
                # Đã xóa .background_gradient để fix lỗi
                st.dataframe(lb_s.style.format({"Điểm Speaking (TB)": "{:.2f}"}), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")
        with c2:
            st.subheader("📚 Reading (Max)")
            if lb_r is not None and not lb_r.empty: 
                # Đã xóa .background_gradient để fix lỗi
                st.dataframe(lb_r.style.format({"Điểm Reading (Max)": "{:.1f}"}), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")
        with c3:
            st.subheader("✍️ Writing (TB)")
            if lb_w is not None and not lb_w.empty: 
                # Đã xóa .background_gradient để fix lỗi
                st.dataframe(lb_w.style.format({"Điểm Writing (TB)": "{:.2f}"}), use_container_width=True)
            else: st.info("Chưa có dữ liệu.")

    # --- MODULE 5: WRITING (NEW & POLISHED) ---
    elif menu == "✍️ Writing":
        st.title("✍️ Luyện Tập Writing (Task 2)")
        
        lesson_w = st.selectbox("Chọn bài viết:", WRITING_MENU)
        
        # Chỉ lớp ELITE mới thấy bài này (ví dụ)
        if "Lesson 3" in lesson_w:
            data_w = WRITING_CONTENT["Lesson 3: Education & Society"]
            st.info(f"### TOPIC: {data_w['question']}")
            
# --- PHẦN 1: CHECKLIST & OUTLINE ---
            
            # --- PHẦN 1: CHECKLIST & OUTLINE ---
            
            # Cập nhật nội dung Expander bằng Markdown thuần (Full nội dung, ít icon)
            with st.expander("📚 **CÁC LỖI TƯ DUY & CẤU TRÚC LOGIC (Đọc kỹ trước khi viết)**", expanded=False):
                st.markdown("""
                ### 1. CÁC LỖI TƯ DUY LOGIC CẦN TRÁNH 
                Đây là các lỗi lập luận phổ biến do ảnh hưởng của tư duy dịch từ tiếng Việt hoặc văn hóa giao tiếp hàng ngày, cần loại bỏ trong văn viết học thuật:

                **⚠️ Hasty Generalization (Khái quát hóa vội vã)**
                * **Bản chất:** Sử dụng các từ chỉ sự tuyệt đối (*All, Always, Everyone, Nobody*) dựa trên định kiến hoặc quan sát hẹp, thiếu tính khách quan.
                * **Ví dụ sai:** "Graduates **always** find it hard to get a job." (Sinh viên tốt nghiệp luôn khó tìm việc -> Sai sự thật).
                * **Khắc phục (Hedging):** Sử dụng ngôn ngữ rào đón để đảm bảo tính chính xác.
                * **Sửa:** "It can be challenging for **many** fresh graduates to secure employment."

                **⚠️ Slippery Slope (Trượt dốc phi logic)**
                * **Bản chất:** Suy diễn một chuỗi hậu quả cực đoan từ một nguyên nhân ban đầu mà thiếu các mắt xích logic trung gian. Lỗi này thường gặp khi người viết muốn nhấn mạnh hậu quả nhưng lại cường điệu hóa quá mức.
                * **Ví dụ sai:** "Playing video games leads to dropping out of school, which results in becoming a criminal." (Chơi game -> Bỏ học -> Tội phạm).
                * **Khắc phục:** Chỉ đề cập đến hệ quả trực tiếp và có tính khả thi cao nhất.
                * **Sửa:** "Excessive gaming may **negatively impact academic performance** due to a lack of focus."

                **⚠️ Circular Reasoning (Lập luận luẩn quẩn)**
                * **Bản chất:** Giải thích một vấn đề bằng cách lặp lại vấn đề đó với từ ngữ khác, không cung cấp thêm thông tin hay lý do sâu sắc (Why/How).
                * **Ví dụ sai:** "Air pollution is harmful because it has bad effects on humans." (*Harmful* và *Bad effects* là tương đương -> Không giải thích được gì).
                * **Khắc phục:** Triển khai ý bằng nguyên nhân cụ thể hoặc cơ chế tác động.
                * **Sửa:** "Air pollution is detrimental as it **directly contributes to respiratory diseases** such as asthma."

                ---

                ### 2. TIÊU CHUẨN CẤU TRÚC ĐOẠN VĂN (MÔ HÌNH P.E.E.R)
                Mỗi đoạn văn (Body Paragraph) cần tuân thủ cấu trúc chặt chẽ để đảm bảo tính mạch lạc:
                

                * **P - Point (Topic Sentence):** Câu chủ đề nêu luận điểm chính trực tiếp, ngắn gọn. Tránh lối viết "mở bài gián tiếp" vòng vo.
                * **E - Explanation (Elaboration):** Giải thích lý do tại sao luận điểm đó đúng. Đây là phần quan trọng nhất thể hiện tư duy (Critical Thinking).
                * **E - Example (Evidence):** Đưa ra ví dụ cụ thể, điển hình (không lấy ví dụ cá nhân chủ quan).
                * **R - Result/Link:** Câu chốt, khẳng định lại ý nghĩa của luận điểm đối với câu hỏi đề bài.

                ---

                ### 3. TÍNH MẠCH LẠC & PHÁT TRIỂN Ý (COHERENCE & PROGRESSION)
                
                **Depth over Breadth (Chiều sâu hơn Chiều rộng):**
                * **Lỗi thường gặp:** Liệt kê quá nhiều ý ("Firstly, Secondly, Thirdly...") nhưng mỗi ý chỉ viết sơ sài. Điều này khiến bài viết trở thành một bản danh sách (list) hơn là một bài luận (essay).
                * **Giải pháp:** Trong một đoạn văn, chỉ nên chọn 1 đến 2 ý tưởng đắt giá nhất và phát triển chúng trọn vẹn theo mô hình P.E.E.R.

                **Linear Thinking (Tư duy tuyến tính):**
                * Đảm bảo dòng chảy thông tin đi theo đường thẳng: **A dẫn đến B, B dẫn đến C**.
                * Tránh tư duy đường vòng hoặc nhảy cóc (nhắc đến kết quả D mà không giải thích quá trình B và C).
                """)

            st.subheader("📝 STEP 1: OUTLINE")
        
            
            with st.form("outline_form"):
                intro = st.text_area("Introduction:", height=80, placeholder="Paraphrase topic + Thesis statement (Quan điểm của bạn)")
                body1 = st.text_area("Body 1 (PEER Structure):", height=150, placeholder="Point (Luận điểm 1) --> Explanation (Tại sao?) --> Example --> Result")
                body2 = st.text_area("Body 2 (PEER Structure):", height=150, placeholder="Point (Luận điểm 2) --> Explanation (Tại sao?) --> Example --> Result")
                conc = st.text_area("Conclusion:", height=80, placeholder="Restate opinion + Summary (Tóm tắt)")
                
                check_outline = st.form_submit_button("🔍 Kiểm Tra Logic Outline")
            
            # Xử lý Check Outline
            if check_outline:
                if intro and body1 and body2 and conc:
                    with st.spinner("Đang phân tích..."):
                        
                        # Prompt giữ nguyên sự nghiêm khắc để khớp với checklist
                        prompt = f"""
                        ## ROLE:
                        You are a strict, high-level IELTS Writing Examiner and Logic Instructor. Your goal is to critique student outlines with a focus on **Critical Thinking** and **Academic Rigor**.

                        ## INPUT DATA:
                        - **Topic:** {data_w['question']}
                        - **Intro:** {intro}
                        - **Body 1:** {body1}
                        - **Body 2:** {body2}
                        - **Conclusion:** {conc}

                        ## EVALUATION CRITERIA (MATCHING THE STUDENT CHECKLIST):
                        Evaluate based on these specific academic standards:

                        1.  **LOGICAL FALLACIES (LỖI TƯ DUY):**
                            -   *Hasty Generalization:* Using absolute terms (All, Always) vs Hedging.
                            -   *Slippery Slope:* Extreme consequences without intermediate steps.
                            -   *Circular Reasoning:* Explaining X by repeating X.
                            -   *Non-Linear Thinking:* Jumping ideas (A->D).

                        2.  **STRUCTURE (PEER MODEL):**
                            -   *P-E-E-R:* Point -> Explanation (Why/How) -> Example -> Result.
                            -   *Depth over Breadth:* Is the explanation deep enough or just listing ideas?

                        ## REQUIREMENTS:
                        1.  **NO SCORE:** Qualitative feedback only.
                        2.  **LANGUAGE:** Vietnamese (Tiếng Việt).
                        3.  **TONE:** Constructive but SHARP.
                        4.  **OUTPUT FORMAT (Markdown):**
                            
                            ### 1. NHẬN XÉT TỔNG QUAN
                            (Summary of logical flow).

                            ### 2. PHÂN TÍCH CHI TIẾT LỖI
                            (Analyze strict logic. If error found, use format):
                            
                            **[Vị trí: Mở bài / Thân bài...]**
                            -   **Lỗi (Error Name):** [e.g., Circular Reasoning]
                            -   **Tại sao sai:** [Explain specifically]
                            -   **Cách sửa:** [Suggest academic fix]

                            ### 3. GỢI Ý NÂNG CẤP
                            (Vocab or flow adjustments. Suggest 5-10 academic collocations based on ideas from outline).
                        """
                        
                        res = call_gemini(prompt)
                        
                        if res:
                            st.session_state['writing_feedback_data'] = res
                            st.rerun()
                else:
                    st.warning("⚠️ Vui lòng điền đầy đủ cả 4 phần.")

            # Hiển thị Feedback
            if st.session_state.get('writing_feedback_data'):
                st.divider()
                st.markdown("### KẾT QUẢ PHÂN TÍCH DÀN Ý")
                with st.container(border=True):
                    st.markdown(st.session_state['writing_feedback_data'])

            # --- PHẦN 2: VIẾT BÀI (LUÔN HIỂN THỊ) ---
    # Chọn chế độ làm bài
            mode_w = st.radio("Chọn chế độ:", ["-- Chọn chế độ --", "Luyện Tập (Không giới hạn)", "Thi Thử (40 Phút)"], horizontal=True, key="w_mode_select")
            
            if mode_w != "-- Chọn chế độ --":
                # Hiển thị khu vực viết bài
                

                # Đồng hồ (Chỉ hiện khi chọn Thi Thử)
                if "Thi Thử" in mode_w:
                     timer_html = f"""
                    <div style="font-size: 24px; font-weight: bold; color: #d35400; font-family: 'Segoe UI', sans-serif; margin-bottom: 10px;">
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
                else:
                     st.success("Chế độ Luyện Tập")

                essay = st.text_area("Bài làm (Min 250 words):", height=400, key="essay_input")
                
                if st.button("Nộp Bài Chấm Điểm"):
                    if len(essay.split()) < 50: st.warning("Bài viết quá ngắn.")
                    else:
                        with st.spinner("Đang chấm điểm theo Band Descriptors (4-9)..."):
                            # PROMPT CHẤM BÀI
                            prompt = f"""
                            ## ROLE:
                            You are a strict, Senior IELTS Writing Examiner (IDP/BC certified).
                        
                            ## TASK:
                            Assess the following Task 2 Essay based on the official IELTS Writing Band Descriptors.
                        
                            **INPUT DATA:**
                            - **Topic:** {data_w['question']}
                            - **Student Essay:** {essay}

                            ## 🛡️ GRADING RUBRIC (STRICT DIFFERENTIATORS):
                            You must evaluate based on these specific distinctions between bands:

                            **1. Task Response (TR):**
                            - **Band 4:** Response is irrelevant or minimal; main ideas are difficult to identify or repetitive.
                            - **Band 5:** Addresses the task but usually only partially; ideas are limited/undeveloped; no clear conclusions.
                            - **Band 6:** Addresses all parts; main ideas are relevant but may be insufficiently developed or unclear.
                            - **Band 7:** Addresses all parts; presents a clear position throughout; extends and supports main ideas.
                            - **Band 8+:** Sufficiently addresses all parts; well-developed response with relevant, extended, and supported ideas.

                            **2. Coherence & Cohesion (CC):**
                            - **Band 4:** No clear progression; basic or repetitive cohesive devices.
                            - **Band 5:** Some organization but lacks overall progression; cohesive devices are inadequate, inaccurate, or overused.
                            - **Band 6:** Arranges information coherently; uses cohesive devices effectively but they may sound **mechanical/faulty**.
                            - **Band 7:** Logically organizes information; uses a range of cohesive devices appropriately (**natural flow**).
                            - **Band 8+:** Sequences information and ideas logically; manages all aspects of cohesion well.

                            **3. Lexical Resource (LR):**
                            - **Band 4:** Basic vocabulary; used repetitively; inappropriate choices.
                            - **Band 5:** Limited range; minimally adequate for the task; noticeable errors in spelling/formation that **may cause difficulty for the reader**.
                            - **Band 6:** Adequate range; attempts less common items but with some inaccuracy; errors do not impede communication.
                            - **Band 7:** Sufficient range to allow flexibility; uses **less common lexical items** with awareness of style/collocation.
                            - **Band 8+:** Wide range; fluent and flexible; skilful use of uncommon items.

                            **4. Grammatical Range & Accuracy (GRA) - *CRITICAL*:**
                            - **Band 4:** Very limited range of structures; rare use of subordinate clauses; errors are frequent and cause strain.
                            - **Band 5:** Attempts complex sentences but these tend to be faulty; grammatical errors are frequent and **may cause some difficulty for the reader**.
                            - **Band 6:** Mix of simple and complex forms; errors occur but **rarely impede communication**.
                            - **Band 7:** Uses a variety of complex structures; produces **frequent error-free sentences**.
                            - **Band 8+:** Wide range of structures; the majority of sentences are error-free.

                            ## 📝 OUTPUT REQUIREMENTS:
                            1.  **SCORING:** Component scores (TR, CC, LR, GRA) must be INTEGERS (e.g., 4, 5, 6). Overall can be .5.
                            2.  **FEEDBACK FORMAT:** Return a valid JSON object strictly following this structure (Language: Vietnamese):

                            {{
                                "TR": [int], "CC": [int], "LR": [int], "GRA": [int],
                                "Overall": [float],
                                "Feedback": "### 🎯 KẾT QUẢ: Band [Overall]\\n\\n### 📊 CHI TIẾT ĐIỂM SỐ:\\n- **Task Response ([TR]):** [Brief explanation why based on rubric]\\n- **Coherence ([CC]):** [Brief explanation]\\n- **Lexical ([LR]):** [Brief explanation]\\n- **Grammar ([GRA]):** [Brief explanation]\\n\\n### 🛠️ SỬA LỖI CHI TIẾT (QUAN TRỌNG):\\n\\n**1. Cải thiện Từ vựng & Ngữ pháp:**\\n* ❌ **Lỗi:** [Quote exact mistake]\\n* ✅ **Sửa:** [Rewrite accurately]\\n* 💡 **Giải thích:** [Explain the error type]\\n\\n**2. Cải thiện Mạch lạc & Logic:**\\n* ❌ **Vấn đề:** [Point out logic gap or mechanical linking]\\n* 💡 **Gợi ý:** [Suggestion for better flow]\\n\\n### 💬 LỜI KHUYÊN CỦA GIÁM KHẢO:\\n[Constructive advice for next steps]"
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

            # --- GIAI ĐOẠN 3: KẾT QUẢ (HIỂN THỊ SAU KHI NỘP) ---
            if st.session_state.get('writing_step') == 'finished' and st.session_state.get('writing_result'):
                res = st.session_state['writing_result']
                st.balloons()
                st.success(f"OVERALL BAND: {res['Overall']}")
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
                    st.session_state['writing_result'] = None # Clear kết quả cũ
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
                    # --- LOGIC MỚI: Xử lý Retry thông minh ---
                    # 1. Đọc dữ liệu audio
                    audio.seek(0)
                    audio_bytes = audio.read()
                    # Hash để nhận diện file audio mới (để tránh chấm lại file cũ)
                    audio_sig = hash(audio_bytes)
                    
                    # 2. Khởi tạo State quản lý cho câu hỏi này
                    state_key = f"proc_{question}"
                    if state_key not in st.session_state:
                        st.session_state[state_key] = {"sig": None, "result": None, "error": False}
                    
                    proc = st.session_state[state_key]
                    should_call_api = False
                    
                    # A. Nếu đây là file audio mới -> Tự động chấm luôn
                    if proc["sig"] != audio_sig:
                        proc["sig"] = audio_sig
                        proc["result"] = None
                        proc["error"] = False
                        should_call_api = True
                    
                    # B. Nếu đang ở trạng thái lỗi -> Hiện nút Retry
                    if proc["error"]:
                        st.warning("⚠️ Hệ thống đang quá tải (Lỗi 429). Bản thu của bạn vẫn còn.")
                        if st.button("🔄 Bấm để thử chấm lại ngay", key=f"retry_{question}"):
                            should_call_api = True
            
                    # 3. Thực hiện gọi API (Nếu cần)
                    if should_call_api:
                        if len(audio_bytes) < 1000:
                            st.warning("File âm thanh quá ngắn.")
                            proc["error"] = False
                        else:
                            with st.spinner("Đang chấm điểm..."):
                                try:
                                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                                    # === PROMPT RUBRIC CHUẨN XÁC ===
                                    prompt = f"""
                                Role: Senior IELTS Speaking Examiner.
                        
                                Task: Assess speaking response for "{question}" based strictly on the rubric.
                                **🚨 CRITICAL INSTRUCTION FOR TRANSCRIPT (QUAN TRỌNG NHẤT):**
                                1. **VERBATIM TRANSCRIPTION:** You must write EXACTLY what you hear, sound-by-sound.
                                2. **NO AUTO-CORRECT:** Do NOT fix grammar or pronunciation errors. 
                                   - If the user says "I go school" (missing 'to'), WRITE "I go school".
                                   - If the user mispronounces "think" as "sink", WRITE "sink" (or "tink").
                                   - If the user misses final sounds (e.g., "five" -> "fi"), WRITE "fi".
                                3. The transcript MUST reflect the raw performance so the user can see their mistakes.

                                ## GRADING RUBRIC (TIÊU CHÍ PHÂN LOẠI CỐT LÕI):

                                * **BAND 9 (Native-like):**
                                * **Fluency:** Trôi chảy tự nhiên, không hề vấp váp.
                                * **Vocab:** Chính xác tuyệt đối, tinh tế.
                                * **Pronunciation:** Hoàn hảo. Transcript sạch bóng, không có bất kỳ từ nào sai ngữ cảnh hay vô nghĩa.

                                * **BAND 8 (Rất tốt):**
                                * **Fluency:** Mạch lạc, hiếm khi lặp lại.
                                * **Vocab:** Dùng điêu luyện Idioms/từ hiếm.
                                * **Pronunciation:** Dễ hiểu xuyên suốt. Ngữ điệu tốt. Transcript chính xác 99%.

                                * **BAND 7 (Tốt - Target):**
                                * **Fluency:** Nói dài dễ dàng. Từ nối linh hoạt.
                                * **Vocab:** Dùng được Collocation tự nhiên.
                                * **Grammar:** Thường xuyên có câu phức không lỗi.
                                * **Pronunciation:** Dễ hiểu. *(Lưu ý: Chấp nhận một vài lỗi nhỏ, nhưng nếu Transcript xuất hiện từ lạ/sai ngữ cảnh, hãy trừ điểm nhẹ).*

                                * **BAND 6 (Khá):**
                                * **Fluency:** Đôi khi mất mạch, từ nối máy móc.
                                * **Vocab:** Đủ để bàn luận, biết Paraphrase.
                                * **Grammar:** Có dùng câu phức nhưng thường xuyên sai.
                                * **Pronunciation:** Rõ ràng phần lớn thời gian. *(Lưu ý: Nếu thấy từ vựng bị biến đổi thành từ khác nghe na ná - Sound-alike words - hoặc 1-2 đoạn vô nghĩa, hãy đánh dấu là Lỗi Phát Âm).*

                                * **BAND 5 (Trung bình):**
                                * **Fluency:** Ngắt quãng nhiều, lặp từ.
                                * **Grammar:** Chỉ đúng khi dùng câu đơn.
                                * **Pronunciation:** *(Dấu hiệu nhận biết: Transcript thường xuyên xuất hiện các từ vô nghĩa hoặc sai hoàn toàn ngữ cảnh do máy không nhận diện được âm).*

                                * **BAND 4 (Hạn chế):**
                                * **Fluency:** Câu cụt, ngắt quãng dài.
                                * **Pronunciation:** Khó hiểu. Transcript gãy vụn, chứa nhiều từ không liên quan đến chủ đề.

                                ## OUTPUT FORMAT (Vietnamese Markdown):
                                Trả về kết quả chi tiết:

                                ### TRANSCRIPT:
                                "[Ghi lại chính xác từng âm thanh nghe được. Nếu học viên nói sai ngữ pháp hoặc phát âm sai từ nào, HÃY GHI LẠI Y NGUYÊN LỖI ĐÓ. Ví dụ: nói 'sink' thay vì 'think', hãy ghi 'sink'. TUYỆT ĐỐI KHÔNG TỰ ĐỘNG SỬA THÀNH CÂU ĐÚNG]"

                                ### KẾT QUẢ: [Score - format 5.0, 5.5]

                                ### PHÂN TÍCH CHI TIẾT:
                                1. **Fluency & Coherence:** [Nhận xét độ trôi chảy, xử lý các chỗ ngắt ngứ, từ nối và cách phát triển ý logic, trọng tâm câu trả lời]
                                2. **Lexical Resource:** [Nhận xét vốn từ, các idiomatic language dùng được liên quan đến topic câu hỏi]
                                3. **Grammar:** [Nhận xét cấu trúc câu, ngữ pháp]
                                4. **Pronunciation:** [Nhận xét phát âm, trọng âm, chunking, âm đuôi dựa trên file ghi âm]

                                ### CẢI THIỆN (NÂNG BAND):
                                *(Chỉ chọn ra tối đa 3-5 lỗi sai lớn nhất hoặc câu diễn đạt vụng về/Việt-lish nhất để sửa cho tự nhiên hơn. **TUYỆT ĐỐI KHÔNG** sửa những câu đã đúng/ổn).*

                                **Lỗi 1 (Grammar/Word Choice):**
                                * **Gốc:** "[Trích văn bản gốc]"
                                * **Sửa:** "[Viết lại tự nhiên hơn - Natural Speaking]"
                                * **Lý do:** [Giải thích ngắn gọn, nghĩa tiếng Việt]

                                **Lỗi 2 (Unnatural Phrasing):**
                                * **Gốc:** "..."
                                * **Sửa:** "..."
                                * **Lý do:** ...
                                """
                                    # Gọi API
                                    text_result = call_gemini(prompt, audio_data=audio_b64)
                                    
                                    if text_result:
                                        proc["result"] = text_result
                                        proc["error"] = False
                                        st.session_state['speaking_attempts'][question] = attempts + 1
                                        save_speaking_log(user['name'], user['class'], lesson_choice, question, text_result)
                                        st.rerun() # Rerun để ẩn nút Retry và hiện kết quả
                                    else:
                                        proc["error"] = True # Đánh dấu lỗi
                                        st.rerun() # Rerun để hiện nút Retry
                                except Exception as e:
                                    st.error(f"Lỗi không xác định: {e}")
                    
                    # 4. Hiển thị kết quả (Nếu đã có)
                    if proc["result"]:
                        st.markdown(proc["result"])
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

        if lesson_choice in READING_CONTENT:
            data = READING_CONTENT[lesson_choice]
            
            tab1, tab2 = st.tabs(["Làm Bài Đọc Hiểu", "Bài Tập Từ Vựng AI"])
            
            # TAB 1: BÀI ĐỌC CHÍNH (Split View)
            with tab1:
                # --- TRẠNG THÁI 1: GIỚI THIỆU & CHỌN CHẾ ĐỘ ---
                if st.session_state['reading_session']['status'] == 'intro':
                    st.info(f"### {data['title']}")
                    
                    # LOGIC INTRO MỚI
                    if 'reading_intro_text' not in st.session_state:
                         # 1. Lesson 2 cho lớp PLA
                        if "Lesson 2" in lesson_choice and user['class'].startswith("PLA"):
                             st.session_state['reading_intro_text'] = "Thời chưa có vệ tinh, các thủy thủ rất sợ đi biển xa vì họ không biết mình đang ở đâu. Cách duy nhất để xác định vị trí là phải biết giờ chính xác. Nhưng khổ nỗi, đồng hồ quả lắc ngày xưa cứ mang lên tàu rung lắc là chạy sai hết. Bài này kể về hành trình chế tạo ra chiếc đồng hồ đi biển đầu tiên, thứ đã cứu mạng hàng ngàn thủy thủ."
                        # 2. Lesson 3
                        elif "Lesson 3" in lesson_choice:
                             st.session_state['reading_intro_text'] = "Làm nông nghiệp ở Úc khó hơn nhiều so với ở Anh hay châu Âu vì đất đai ở đây rất khô và thiếu dinh dưỡng. Vào cuối thế kỷ 19, những người nông dân Úc đứng trước nguy cơ phá sản vì các phương pháp canh tác cũ không còn hiệu quả.\nBài đọc này sẽ cho các bạn thấy họ đã xoay sở như thế nào bằng công nghệ. Từ việc chế tạo ra chiếc cày đặc biệt có thể tự 'nhảy' qua gốc cây, cho đến việc lai tạo giống lúa mì chịu hạn. Chính những sáng kiến này đã biến nước Úc từ một nơi chỉ nuôi cừu thành một cường quốc xuất khẩu lúa mì thế giới."
                        
                        # Đã xóa phần tự động tạo Intro bằng AI
                    
                    if st.session_state.get('reading_intro_text'):
                        st.markdown(f"**Giới thiệu về bài đọc:**\n\n{st.session_state['reading_intro_text']}")
                    
                    
                    st.write("**Thông tin bài thi:**")
                    col_info1, col_info2 = st.columns(2)
                    if "questions_fill" in data:
                        col_info1.write("- **Dạng bài:** Fill in the blanks")
                        col_info2.write(f"- **Số lượng:** {len(data['questions_fill'])} câu hỏi")
                    elif "questions_mc" in data:
                        col_info1.write("- **Dạng bài:** Multiple Choice")
                        col_info2.write(f"- **Số lượng:** {len(data['questions_mc'])} câu hỏi")
                        
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    if c1.button("Luyện Tập (Không giới hạn thời gian)"):
                        st.session_state['reading_session']['status'] = 'doing'; st.session_state['reading_session']['mode'] = 'practice'; st.rerun()
                    if c2.button("Luyện Thi (20 Phút)"):
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
                        st.subheader("Bài đọc")
                        # --- Cập nhật UI: Hướng dẫn bôi đen highlight ---
                        st.caption("💡 **Mẹo:** Bôi đen văn bản để highlight nhanh. (Lưu ý: Highlight sẽ mất khi nộp bài).")

                        display_text = data['text']
                        # Xóa title cũ trong text nếu có để tránh lặp
                        if "###" in display_text:
                             display_text = re.sub(r"###.*?\n", "", display_text)
                        
                        # Hiển thị bài đọc
                        html_content = f"<h2>{data['title']}</h2>" + display_text.replace("\n", "<br>")
                        st.markdown(f"<div class='scroll-container'><div class='reading-text'>{html_content}</div></div>", unsafe_allow_html=True)

                    with c_quiz:
                        st.subheader("Câu Hỏi")
                        with st.container(height=600):
                            with st.form("read_exam_form"):
                                ans = {}
                                # DẠNG 1: ĐIỀN TỪ
                                if "questions_fill" in data:
                                    st.markdown("**Questions: Fill in the blanks (NO MORE THAN TWO WORDS)**")
                                    for q in data['questions_fill']:
                                        st.markdown(f"<div class='question-text'>{q['q']}</div>", unsafe_allow_html=True)
                                        ans[q['id']] = st.text_input(f"Answer {q['id']}", label_visibility="collapsed")
                                        st.write("")
                                # DẠNG 2: TRẮC NGHIỆM (MULTIPLE CHOICE)
                                elif "questions_mc" in data:
                                    st.markdown("**Questions: Choose the correct letter, A, B or C.**")
                                    for q in data['questions_mc']:
                                        st.markdown(f"**{q['q']}**")
                                        ans[q['id']] = st.radio(f"Select answer for {q['id']}", q['options'], key=q['id'], label_visibility="collapsed")
                                        st.write("")
                                
                                if st.form_submit_button("NỘP BÀI"):
                                    st.session_state['reading_session']['status'] = 'result'
                                    st.session_state['reading_session']['user_answers'] = ans
                                    st.rerun()

                # --- TRẠNG THÁI 3: KẾT QUẢ & GIẢI THÍCH ---
                elif st.session_state['reading_session']['status'] == 'result':
                    st.subheader("Kết Quả Bài Làm")
                    user_answers = st.session_state['reading_session']['user_answers']
                    score = 0
                    
                    col_res_L, col_res_R = st.columns([1, 1])
                    
                    # Hiển thị lại bài đọc để đối chiếu
                    with col_res_L:
                        with st.expander("Xem lại bài đọc", expanded=False):
                            st.markdown(data['text'])
                    
                    with col_res_R:
                        # Xác định danh sách câu hỏi đang làm
                        q_list = data.get('questions_fill') or data.get('questions_mc')
                        
                        for q in q_list:
                            # Lấy đáp án người dùng (xử lý chữ hoa thường nếu là điền từ)
                            u_ans_raw = user_answers.get(q['id'], "")
                            
                            # Logic chấm điểm
                            if "questions_fill" in data:
                                u_ans = str(u_ans_raw).strip().lower()
                                c_ans = q['a'].lower()
                                is_correct = u_ans == c_ans
                            else: # Trắc nghiệm
                                # Đáp án trắc nghiệm lưu dạng "A. Text...", ta so sánh ký tự đầu
                                u_ans = str(u_ans_raw)
                                c_ans = q['a']
                                is_correct = u_ans == c_ans
                            
                            if is_correct: score += 1
                            
                            if is_correct:
                                st.success(f"✅ {q['q']}")
                            else:
                                st.error(f"❌ {q['q']}")
                                st.markdown(f"**Bạn chọn:** {u_ans_raw} | **Đáp án đúng:** {q['a']}")
                            
                            # Luôn hiện giải thích
                            st.markdown(f"<div class='explanation-box'>💡 <b>Giải thích:</b> {q['exp']}</div>", unsafe_allow_html=True)
                            st.write("---")

                        st.success(f"Tổng điểm: {score}/{len(q_list)}")
                        
                        # Lưu điểm
                        save_reading_log(user['name'], user['class'], lesson_choice, score, len(q_list), st.session_state['reading_session']['mode'])
                        
                        if st.button("Làm lại bài này"):
                            st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
                            st.rerun()


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