import streamlit as st
import requests
import json
import base64
import re
import time
import random
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# ================= 0. HÀM HỖ TRỢ (TIỆN ÍCH) =================
def get_current_time_str():
    """Trả về thời gian hiện tại định dạng dễ đọc: DD/MM/YYYY HH:MM:SS"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# --- TỪ ĐIỂN GỘP TÊN (MỚI THÊM) ---
# Quy tắc: "tên viết sai/không dấu/viết tắt viết thường": "Tên Chuẩn Xác Viết Hoa"
NAME_MAPPING = {
    "bui hoang minh nhat": "Bùi Hoàng Minh Nhật",
    "tâm huỳnh": "Huỳnh Ngọc Tài Tâm",
    "tam huynh": "Huỳnh Ngọc Tài Tâm",
    "khánh trần": "Trần Lê Gia Khánh",
    "khanh tran": "Trần Lê Gia Khánh",
    "fiona": "Fiona" # (Nếu Fiona là nickname của ai đó trong lớp, bạn có thể sửa chữ "Fiona" bên phải thành tên thật)
    # Bạn có thể tự thêm các bạn khác vào đây nếu phát hiện trùng lặp...
}

def normalize_name(name):
    """
    Chuẩn hóa tên học viên:
    - Xóa khoảng trắng thừa ở đầu/cuối và giữa các từ.
    - Gộp các tên gõ không dấu / tên viết tắt thành 1 tên chuẩn.
    - Viết hoa chữ cái đầu mỗi từ.
    """
    if not name: return ""
    # Tách các từ, bỏ khoảng trắng thừa, viết hoa chữ đầu, rồi ghép lại
    clean_name = " ".join(name.strip().split()).title()
    
    # Kiểm tra xem tên có nằm trong danh sách cần gộp không (chuyển về chữ thường để so sánh)
    lower_name = clean_name.lower()
    if lower_name in NAME_MAPPING:
        return NAME_MAPPING[lower_name]
        
    return clean_name

def extract_score(value):
    """
    Hàm an toàn để trích xuất điểm số.
    Xử lý trường hợp AI trả về list [7] hoặc [7.5] thay vì số 7 hoặc 7.5
    """
    if isinstance(value, list):
        return value[0] if len(value) > 0 else 0
    return value

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

def save_writing_log(student, class_code, lesson, topic, band_score, criteria_scores, feedback, mode="Practice"):
    """Lưu điểm Writing (Đã cập nhật thêm tham số mode)"""
    try:
        sheet = connect_gsheet()
        if sheet:
            try: 
                ws = sheet.worksheet("Writing_Logs")
            except:
                # Nếu chưa có sheet, tạo mới và thêm header có cột Mode
                ws = sheet.add_worksheet(title="Writing_Logs", rows="1000", cols="10")
                ws.append_row(["Timestamp", "Student", "Class", "Lesson", "Topic", "Overall_Band", "TR_CC_LR_GRA", "Feedback", "Mode"])
            
            # Lưu dữ liệu bao gồm cả Mode
            ws.append_row([str(datetime.now()), student, class_code, lesson, topic, band_score, str(criteria_scores), feedback, mode])
            st.toast("✅ Đã lưu bài Writing!", icon="💾")
    except Exception as e:
        print(f"Save Writing Error: {e}")
        st.error(f"Không thể lưu kết quả: {e}")

def get_leaderboard(class_code):
    try:
        sheet = connect_gsheet()
        if not sheet: return None, None, None

        def extract_float(val):
            try:
                found = re.search(r"(\d+\.?\d*)", str(val))
                return float(found.group(1)) if found else 0.0
            except: return 0.0

        # 1. Speaking (Trung bình 5 lần gần nhất)
        try:
            ws_s = sheet.worksheet("Speaking_Logs")
            data = ws_s.get_all_values()
            
            if len(data) > 1:
                headers = data[0]
                df_s = pd.DataFrame(data[1:], columns=headers)
                df_s.columns = [str(c).strip() for c in df_s.columns]
                
                if 'Class' in df_s.columns:
                    df_s = df_s[df_s['Class'] == class_code]
                    
                    if not df_s.empty:
                        if 'Student' in df_s.columns:
                            df_s['Student'] = df_s['Student'].astype(str).apply(normalize_name)

                        score_col = None
                        for col in ['Score_Num', 'Band_Score', 'Band_Short', 'Score']:
                            if col in df_s.columns:
                                score_col = col
                                break
                        
                        if score_col:
                            df_s['Final_Score'] = df_s[score_col].apply(extract_float)
                            df_s = df_s[df_s['Final_Score'] > 0]
                            
                            # LOGIC MỚI: Lấy 5 dòng cuối cùng (5 lần nộp gần nhất) của mỗi học sinh
                            last_5_s = df_s.groupby('Student').tail(5)
                            
                            # Tính điểm trung bình dựa trên 5 lần này
                            lb_s = last_5_s.groupby('Student')['Final_Score'].mean().reset_index()
                            lb_s.columns = ['Học Viên', 'Điểm Speaking (TB)']
                            lb_s = lb_s.sort_values(by='Điểm Speaking (TB)', ascending=False).head(10)
                        else: lb_s = None
                    else: lb_s = None
                else: lb_s = None
            else: lb_s = None
        except Exception as e: 
            print(f"Leaderboard Speaking Error: {e}")
            lb_s = None 

        # 2. Reading (Giữ nguyên Max cao nhất)
        try:
            ws_r = sheet.worksheet("Reading_Logs")
            data_r = ws_r.get_all_values()
            if len(data_r) > 1:
                df_r = pd.DataFrame(data_r[1:], columns=data_r[0])
                df_r.columns = [str(c).strip() for c in df_r.columns]

                if 'Class' in df_r.columns:
                    df_r = df_r[df_r['Class'] == class_code]
                    if not df_r.empty:
                        if 'Student' in df_r.columns:
                            df_r['Student'] = df_r['Student'].astype(str).apply(normalize_name)
                        
                        r_score_col = next((c for c in ['Score', 'Total_Score', 'Points', 'Percentage'] if c in df_r.columns), None)

                        if r_score_col:
                            df_r['Final_Score'] = df_r[r_score_col].apply(extract_float)
                            lb_r = df_r.groupby('Student')['Final_Score'].max().reset_index()
                            lb_r.columns = ['Học Viên', 'Điểm Reading (Max)']
                            lb_r = lb_r.sort_values(by='Điểm Reading (Max)', ascending=False).head(10)
                        else: lb_r = None
                    else: lb_r = None
                else: lb_r = None
            else: lb_r = None
        except: lb_r = None

        # 3. Writing (Trung bình 5 lần gần nhất)
        try:
            ws_w = sheet.worksheet("Writing_Logs")
            data_w = ws_w.get_all_values()
            
            if len(data_w) > 1:
                df_w = pd.DataFrame(data_w[1:], columns=data_w[0])
                df_w.columns = [str(c).strip() for c in df_w.columns]
                
                if 'Class' in df_w.columns:
                    df_w = df_w[df_w['Class'] == class_code]
                    
                    if not df_w.empty:
                        if 'Student' in df_w.columns:
                            df_w['Student'] = df_w['Student'].astype(str).apply(normalize_name)

                        w_score_col = next((c for c in ['Overall_Band', 'Overall Band', 'Band', 'Score', 'Band_Score', 'Overall'] if c in df_w.columns), None)
                        
                        if w_score_col:
                            df_w['Final_Score'] = df_w[w_score_col].apply(extract_float)
                            df_w = df_w[df_w['Final_Score'] > 0]
                            
                            # LOGIC MỚI: Lấy 5 dòng cuối cùng (5 lần nộp gần nhất) của mỗi học sinh
                            last_5_w = df_w.groupby('Student').tail(5)
                            
                            # Tính điểm trung bình dựa trên 5 lần này
                            lb_w = last_5_w.groupby('Student')['Final_Score'].mean().reset_index()
                            lb_w.columns = ['Học Viên', 'Điểm Writing (TB)']
                            lb_w = lb_w.sort_values(by='Điểm Writing (TB)', ascending=False).head(10)
                        else: lb_w = None
                    else: lb_w = None
                else: lb_w = None
            else: lb_w = None
        except Exception as e:
            print(f"Leaderboard Writing Error: {e}")
            lb_w = None

        return lb_s, lb_r, lb_w

    except Exception as e:
        print(f"Global Leaderboard Error: {e}")
        return None, None, None

# ================= 1. CẤU HÌNH & DỮ LIỆU (TEACHER INPUT) =================

CLASS_CONFIG = {
    "PLA1601": {"level": "3.0 - 4.0", "desc": "Lớp Platinum"},
    "DIA2702": {"level": "4.0 - 5.0", "desc": "Lớp Diamond"},
    "MAS0901": {"level": "5.0 - 6.0", "desc": "Lớp Master"},
    "ELITE1912": {"level": "6.5 - 7.0", "desc": "Lớp Elite"}
}

HOMEWORK_CONFIG = {
    "PLA": {
        "Speaking": ["Lesson 1: Work & Study", "Lesson 2: Habits & Lifestyle", "Lesson 3: Home & Transport", "Lesson 4: Describing People", "Lesson 5: Describing Objects", "Lesson 6: Describing Places", "Lesson 7: Describing Events"],
        "Reading":  ["Lesson 2: Marine Chronometer", "Lesson 3: Australian Agricultural Innovations", "Lesson 4: The lost giants of Australian fauna"],
        "Writing":  [] 
    },
    "ELITE": {
        "Speaking": [], 
        "Reading":  [], 
        "Writing":  [
            "Lesson 3: Education & Society",
            "Lesson 4: Salt Intake (Task 1)",
            "Lesson 5: News Media (Task 2)",
            "Lesson 6: Easternburg Map (Task 1)"
        ]
    },
    "DIA": {
        "Speaking": ["Lesson 1: Work & Study", "Lesson 2: Habits & Lifestyle", "Lesson 3: Home & Transport"], "Reading": [], "Writing": []
    },
    "MAS": {
        "Speaking": [], 
        "Reading": [], 
        "Writing": [
            "Lesson 5: Resource Depletion (Task 2)"
        ]
    }
}

# --- FORECAST DATA QUÝ 1 2026 ---
FORECAST_PART1 = {
    "Views": ["Do you like taking pictures of different views?", "Do you prefer views in urban areas or rural areas?", "Do you prefer views in your own country or in other countries?", "Have you seen an unforgettable and beautiful view or scenery?"],
    "Childhood activities": ["What are your favourite activities?", "What were your favourite activities when you were a child?", "Did you prefer to do activities alone or with a group of people when you were a child?", "Are there any differences between the activities you liked when you were a child and those you like now?"],
    "Life stages": ["Do you enjoy being the age you are now?", "What did you often do with your friends in your childhood?", "What do you think is the most important at the moment?", "Do you have any plans for the next five years?", "How do people remember each stage of their lives?", "At what age do you think people are the happiest?"],
    "Building": ["Are there tall buildings near your home?", "Do you take photos of buildings?", "Is there a building that you would like to visit?"],
    "Scenery": ["Do you look out the window at the scenery when travelling by bus or car?", "Do you prefer the mountains or the sea?", "Do you like to take scenery pictures?", "What are the most beautiful sights you have seen while travelling?"],
    "Reading": ["Do you like reading?", "Do you prefer to read on paper or on a screen?", "When do you need to read carefully, and when not?", "Do you prefer scanning or detailed reading?"],
    "Sports team": ["Have you ever been part of a sports team?", "Are team sports popular in your culture?", "Do you like watching team games? Why?", "What are the differences between team sports and individual sports?"],
    "Walking": ["Do you walk a lot?", "Did you often go outside to have a walk when you were a child?", "Why do people like to walk in parks?", "Where would you like to take a long walk if you had the chance?", "Where did you go for a walk lately?"],
    "Typing": ["Do you prefer typing or handwriting?", "Do you type on a desktop or laptop keyboard every day?", "When did you learn how to type on a keyboard?", "How do you improve your typing?"],
    "Food": ["What is your favourite food?", "What kind of food did you like when you were young?", "Has your favourite food changed since you were a child?", "Do you eat different foods at different times of the year?"],
    "Hobby": ["Do you have the same hobbies as your family members?", "Do you have a hobby that you’ve had since childhood?", "Did you have any hobbies when you were a child?", "Do you have any hobbies?"],
    "Gifts": ["What gift have you received recently?", "Have you ever sent handmade gifts to others?", "Have you ever received a great gift?", "What do you consider when choosing a gift?", "Do you think you are good at choosing gifts?"],
    "Day off": ["When was the last time you had a few days off?", "What do you usually do when you have days off?", "Do you usually spend your days off with your parents or with your friends", "What would you like to do if you had a day off tomorrow?"],
    "Keys": ["Do you always bring a lot of keys with you?", "Have you ever lost your keys?", "Do you often forget the keys and lock yourself out?", "Do you think it’s a good idea to leave your keys with a neighbour?"],
    "Morning time": ["Do you like getting up early in the morning?", "What do you usually do in the morning?", "What did you do in the morning when you were little? Why?", "Are there any differences between what you do in the morning now and what you did in the past?", "Do you spend your mornings doing the same things on both weekends and weekdays? Why?"],
    "Dreams": ["Can you remember the dreams you had?", "Do you share your dreams with others?", "Do you think dreams have special meanings?", "Do you want to make your dreams come true?"],
    "Pets and Animals": ["What’s your favourite animal? Why?", "Where do you prefer to keep your pet, indoors or outdoors?", "Have you ever had a pet before?", "What is the most popular animal in Vietnam?"],
    "Doing something well": ["Do you have an experience when you did something well?", "Do you have an experience when your teacher thought you did a good job?", "Do you often tell your friends when they do something well?"],
    "Rules": ["Are there any rules for students at your school?", "Do you think students would benefit more from more rules?", "Have you ever had a really dedicated teacher?", "Do you prefer to have more or fewer rules at school?"],
    "Public places": ["Have you ever talked with someone you don’t know in public places?", "Do you wear headphones in public places?", "Would you like to see more public places near where you live?", "Do you often go to public places with your friends?"],
    "Staying with old people": ["Have you ever worked with old people?", "Are you happy to work with people who are older than you?", "Do you enjoy spending time with old people?", "What are the benefits of being friends with or working with old people?"],
    "Growing vegetables/fruits": ["Are you interested in growing vegetables and fruits?", "Is growing vegetables popular in your country?", "Do many people grow vegetables in your city?", "Do you think it’s easy to grow vegetables?", "Should schools teach students how to grow vegetables?"],
    "Going out": ["Do you bring food or snacks with you when going out?", "Do you always take your mobile phone with you when going out?", "Do you often bring cash with you?", "How often do you use cash?"],
    "Advertisements": ["Do you often see advertisements when you are on your phone or computer?", "Is there an advertisement that made an impression on you when you were a child?", "Do you see a lot of advertising on trains or other transport?", "Do you like advertisements?", "What kind of advertising do you like?"],
    "Crowded place": ["Is the city where you live crowded?", "Is there a crowded place near where you live?", "Do you like crowded places?", "Do most people like crowded places?", "When was the last time you were in a crowded place?"],
    "Chatting": ["Do you like chatting with friends?", "What do you usually chat about with friends?", "Do you prefer to chat with a group of people or with only one friend?", "Do you prefer to communicate face-to-face or via social media?", "Do you argue with friends?"],
    "Friends": ["Is there a difference between where you meet friends now and where you used to meet them in the past?", "Why are some places suitable for meeting while others are not?", "Do you prefer to spend time with one friend or with a group of friends?", "Would you invite friends to your home?", "How important are friends to you?", "Do you often go out with your friends?", "Where do you often meet each other?", "What do you usually do with your friends?", "Do you have a friend you have known for a long time?"],
    "The city you live in": ["Would you recommend your city to others?", "What’s the weather like where you live?", "Are there people of different ages living in this city?", "Are the people friendly in the city?", "Is the city friendly to children and old people?", "Do you often see your neighbors?", "What city do you live in?", "Do you like this city? Why?", "How long have you lived in this city?", "Are there big changes in this city?", "Is this city your permanent residence?"],
    "Shoes": ["Do you like buying shoes? How often?", "Have you ever bought shoes online?", "How much money do you usually spend on shoes?", "Which do you prefer, fashionable shoes or comfortable shoes?"],
    "Museums": ["Do you think museums are important?", "Are there many museums in your hometown?", "Do you often visit museums?", "When was the last time you visited a museum?"],
    "Having a break": ["How often do you take a rest or a break?", "What do you usually do when you are resting?", "Do you take a nap when you are taking your rest?", "How do you feel after taking a nap?"],
    "Borrowing/lending things": ["Do you mind if others borrow money from you?", "How do you feel when people don’t return things they borrowed from you?", "Do you like to lend things to others?", "Have you ever borrowed money from others?", "Have you borrowed books from others?"],
    "Sharing things": ["Who is the first person you would like to share good news with?", "Do you prefer to share news with your friends or your parents?", "Do you have anything to share with others recently?", "What kind of things are not suitable for sharing?", "What kind of things do you like to share with others?", "Did your parents teach you to share when you were a child?"],
    "Plants": ["Do you keep plants at home?", "What plant did you grow when you were young?", "Do you know anything about growing a plant?", "Do Chinese people send plants as gifts?"],
    "Work or studies": ["What subjects are you studying?", "Do you like your subject?", "Why did you choose to study that subject?", "Do you think that your subject is popular in your country?", "Do you have any plans for your studies in the next five years?", "What are the benefits of being your age?", "Do you want to change your major?", "Do you prefer to study in the mornings or in the afternoons?", "How much time do you spend on your studies each week?", "Are you looking forward to working?", "What technology do you use when you study?", "What changes would you like to see in your school?", "What work do you do?", "Why did you choose to do that type of work (or that job)?", "Do you like your job?", "What requirements did you need to meet to get your current job?", "Do you have any plans for your work in the next five years?", "What do you think is the most important at the moment?", "Do you want to change to another job?", "Do you miss being a student?", "What technology do you use at work?", "Who helps you the most? And how?"],
    "Home & Accommodation": ["Who do you live with?", "Do you live in an apartment or a house?", "What part of your home do you like the most?", "What’s the difference between where you are living now and where you have lived in the past?", "What kind of house or apartment do you want to live in in the future?", "What room does your family spend most of the time in?", "What do you usually do in your apartment?", "What kinds of accommodation do you live in?", "Do you plan to live there for a long time?", "Can you describe the place where you live?", "Do you prefer living in a house or an apartment?", "Please describe the room you live in.", "What’s your favorite room in your apartment or house？", "What makes you feel pleasant in your home？", "How long have you lived there?", "Do you think it is important to live in a comfortable environment？"],
    "Hometown": ["Have you learned anything about the history of your hometown?", "Did you learn about the culture of your hometown in your childhood?", "Is that a big city or a small place?", "Do you like your hometown?", "What do you like (most) about your hometown?", "Is there anything you dislike about it?", "How long have you been living there?", "Do you like living there?", "Please describe your hometown a little.", "What’s your hometown famous for?", "Did you learn about the history of your hometown at school?", "Are there many young people in your hometown?", "Is your hometown a good place for young people to pursue their careers?"],
    "The area you live in": ["Do you live in a noisy or a quiet area?", "Are the people in your neighborhood nice and friendly?", "Do you like the area that you live in?", "Where do you like to go in that area?", "Do you know any famous people in your area?", "What are some changes in the area recently?", "Do you know any of your neighbours?"]
}

FORECAST_PART23 = {
    "Give advice": {
        "cue_card": "Describe a time when you gave advice to others.\nYou should say:\n- When it was\n- To whom you gave the advice\n- What the advice was\n- And explain why you gave the advice",
        "part3": ["Should people prepare before giving advice?", "Is it good to ask advice from strangers online?", "What are the personalities of people whose job is to give advice to others?", "What are the problems if you ask too many people for advice?", "Why do some people think it is better to ask for advice from friends than from parents?", "When would old people ask young people for advice?"]
    },
    "Person helps others": {
        "cue_card": "Describe a person who often helps others.\nYou should say:\n- Who this person is\n- How often he/she helps others\n- How/why he/she helps others\n- And how you feel about this person",
        "part3": ["Do you think schools should teach children to do household chores?", "Why are employees reluctant to ask their managers for help?", "What can children do to help their parents?", "Should children help their parents with household chores?", "What kind of help do people need when looking for a new job?", "Who should people ask for help, colleagues or family members?"]
    },
    "Bad music event": {
        "cue_card": "Describe an event you attended in which you didn’t enjoy the music played.\nYou should say:\n- What it was\n- Who you went with\n- Why you decided to go there\n- And explain why you didn’t enjoy it",
        "part3": ["What kind of music events do people like today?", "Do you think children should receive some musical education?", "What are the differences between old and young people’s music preferences?", "What kind of music events are there in your country?"]
    },
    "Learned without teacher": {
        "cue_card": "Describe one of your friends who learned something without a teacher.\nYou should say:\n- Who he/she is\n- What he/she learned\n- Why he/she learned this\n- And explain whether it would be easier to learn from a teacher",
        "part3": ["Is it necessary to keep learning after graduating from school?", "Should teachers make learning in their classes fun?", "Do you think there are too many subjects for students to learn?", "Is it better to focus on a few subjects or to learn many subjects?", "Do you think enterprises should provide training for their employees?", "Do you think it is good for older adults to continue learning?"]
    },
    "Technology (not phone)": {
        "cue_card": "Describe a piece of technology (not a phone) that you would like to own.\nYou should say:\n- What it is\n- How much it costs\n- How you knew it\n- And explain why you would like to own it",
        "part3": ["What are the differences between the technology of the past and that of today?", "What technology do young people like to use?", "What are the differences between online and face-to-face communication?", "Do you think technology has changed the way people communicate?", "What negative effects does technology have on people’s relationships?", "What are the differences between making friends in real life and online?"]
    },
    "Perfect job": {
        "cue_card": "Describe a perfect job you would like to have in the future.\nYou should say:\n- What it is\n- How you knew it\n- What you need to learn to get this job\n- And explain why you think it is a perfect job for you",
        "part3": ["What kind of job can be called a ‘dream job’?", "What jobs do children want to do when they grow up?", "Do people’s ideal jobs change as they grow up?", "What should people consider when choosing jobs?", "Is salary the main reason why people choose a certain job?", "What kind of jobs are the most popular in your country?"]
    },
    "Child drawing": {
        "cue_card": "Describe a child who loves drawing/painting.\nYou should say:\n- Who he/she is\n- How/when you knew him/her\n- How often he/she draws/paints\n- And explain why you think he/she loves drawing/painting",
        "part3": ["What is the right age for a child to learn drawing?", "Why do most children draw more often than adults do?", "Why do some people visit galleries or museums instead of viewing artworks online?", "Do you think galleries and museums should be free of charge?", "How do artworks inspire people?", "What are the differences between reading a book and visiting a museum?"]
    },
    "App or program": {
        "cue_card": "Describe a program or app on your computer or phone.\nYou should say:\n- What it is\n- How often you use it\n- When/how you use it\n- When/how you found it\n- And explain how you feel about it",
        "part3": ["What are the differences between old and young people when using apps?", "Why do some people not like using apps?", "What apps are popular in your country? Why?", "Should parents limit their children’s use of computer programs and computer games? Why and how?", "Do you think young people are more and more reliant on these programs?"]
    },
    "Person good at planning": {
        "cue_card": "Describe a person who makes plans a lot and is good at planning.\nYou should say:\n- Who he/she is\n- How you knew him/her\n- What plans he/she makes\n- And explain how you feel about this person",
        "part3": ["Do you think it’s important to plan ahead?", "Do you think children should plan their future careers?", "Is making study plans popular among young people?", "Do you think choosing a college major is closely related to a person’s future career?"]
    },
    "Famous person": {
        "cue_card": "Describe a famous person you would like to meet.\nYou should say:\n- Who he/she is\n- How you knew him/her\n- How/where you would like to meet him/her\n- And explain why you would like to meet him/ her",
        "part3": ["What are the advantages and disadvantages of being a famous child?", "What can today’s children do to become famous?", "What can children do with their fame?", "Do people become famous because of their talent?"]
    },
    "Disappointing movie": {
        "cue_card": "Describe a movie you watched recently that you felt disappointed about.\nYou should say:\n- When it was\n- Why you didn’t like it\n- Why you decided to watch it\n- And explain why you felt disappointed about it",
        "part3": ["Do you believe movie reviews?", "What are the different types of films in your country?", "Are historical films popular in your country? Why?", "Do you think films with famous actors or actresses are more likely to become successful films?", "Why are Japanese animated films so popular?", "Should the director pay a lot of money to famous actors?"]
    },
    "Relax place": {
        "cue_card": "Describe your favorite place in your house where you can relax.\nYou should say:\n- Where it is\n- What it is like\n- What you enjoy doing there\n- And explain why you feel relaxed at this place",
        "part3": ["Why is it difficult for some people to relax?", "What are the benefits of doing exercise?", "Do people in your country exercise after work?", "What is the place where people spend most of their time at home?", "Do you think there should be classes for training young people and children how to relax?", "Which is more important, mental relaxation or physical relaxation?"]
    },
    "Item (not phone/computer)": {
        "cue_card": "Describe something that you can’t live without (not a computer/phone).\nYou should say:\n- What it is\n- What you do with it\n- How it helps you in your life\n- And explain why you can’t live without it",
        "part3": ["Why do all children like toys?", "Do you think it is good for a child to always take his or her favourite toy with them all the time?", "Why are children attracted to new things (such as electronics)?", "Why do some grown-ups hate to throw out old things (such as clothes)?", "Is the way people buy things affected? How?", "What do you think influences people to buy new things?"]
    },
    "Proud of family": {
        "cue_card": "Describe a time when you felt proud of a family member.\nYou should say:\n- When it happened\n- Who the person is\n- What the person did\n- And explain why you felt proud of him/her",
        "part3": ["When would parents feel proud of their children?", "Should parents reward children? Why and how?", "Is it good to reward children too often? Why?", "On what occasions would adults be proud of themselves?"]
    },
    "Trip vehicle": {
        "cue_card": "Describe a bicycle/motorcycle/car trip you would like to go.\nYou should say:\n- Who you would like to go with\n- Where you would like to go\n- When you would like to go\n- And explain why you would like to go by bicycle/motorcycle/car",
        "part3": ["Which form of vehicle is more popular in your country, bikes, cars or motorcycles?", "Do you think air pollution comes mostly from mobile vehicles?", "Do you think people need to change the way of transportation drastically to protect the environment?", "Why do people prefer to travel by car?", "How are the transportation systems in urban areas and rural areas different?"]
    },
    "Smiling occasion": {
        "cue_card": "Describe an occasion when many people were smiling.\nYou should say:\n- When it happened\n- Who you were with\n- What happened\n- And explain why most people were smiling",
        "part3": ["Do people smile more when they are younger or older?", "Do you think people who like to smile are more friendly?", "Why do most people smile in photographs?", "Do women smile more than men? Why?"]
    },
    "No mobile phone": {
        "cue_card": "Describe an occasion when you were not allowed to use your mobile phone.\nYou should say:\n- When it was\n- Where it was\n- Why you were not allowed to use your mobile phone\n- And how you felt about it",
        "part3": ["How do young and old people use mobile phones differently?", "What positive and negative impact do mobile phones have on friendship?", "Is it a waste of time to take pictures with mobile phones?", "Do you think it is necessary to have laws on the use of mobile phones?"]
    },
    "Important family item": {
        "cue_card": "Describe something important that has been kept in your family for a long time.\nYou should say:\n- What it is\n- When your family had it\n- How your family got it\n- And explain why it is important to your family",
        "part3": ["What things do families keep for a long time?", "What’s the difference between things valued by people in the past and today?", "What kinds of things are kept in museums?", "What’s the influence of technology on museums?"]
    },
    "Useful book": {
        "cue_card": "Describe a book you read that you found useful.\nYou should say:\n- What it is\n- When you read it\n- Why you think it is useful\n- And explain how you felt about it",
        "part3": ["What are the types of books that young people like to read?", "What should the government do to make libraries better?", "Do you think old people spend more time reading than young people?", "Which one is better, paper books or e-books?", "Have libraries changed a lot with the development of the internet?", "What should we do to prevent modern libraries from closing down?"]
    },
    "Popular person": {
        "cue_card": "Describe a popular person.\nYou should say:\n- Who this person is\n- What kind of person he or she is\n- When you see him/her normally\n- And explain why you think this person is popular",
        "part3": ["Why are some students popular in school?", "Is it important for a teacher to be popular?", "Do you think good teachers are always popular among students?", "What are the qualities of being a good teacher?", "Is it easier to become popular nowadays?", "Why do people want to be popular?"]
    },
    "Creative person": {
        "cue_card": "Describe a creative person (e.g. an artist, a musician, an architect, etc.) you admire.\nYou should say:\n- Who he/she is\n- How you knew him/her\n- What his/her greatest achievement is\n- And explain why you think he/she is creative",
        "part3": ["Do you think children should learn to play musical instruments?", "How do artists acquire inspiration?", "Do you think pictures and videos in news reports are important?", "What can we do to help children stay creative?", "How does drawing help to enhance children’s creativity?", "What kind of jobs require creativity?"]
    },
    "Long journey": {
        "cue_card": "Describe a long journey you had and would like to take again.\nYou should say:\n- When/where you went\n- Who you had the journey with\n- Why you had the journey\n- And explain why you would like to have it again",
        "part3": ["Do you think it is a good choice to travel by plane?", "What are the differences between group travelling and travelling alone?", "What do we need to prepare for a long journey?", "Why do some people like making long journeys?", "Why do some people prefer to travel in their own country?", "Why do some people prefer to travel abroad?"]
    },
    "Family business worker": {
        "cue_card": "Describe a person you know who enjoys working for a family business (e.g. a shop, etc.).\nYou should say:\n- Who he/she is\n- What the business is\n- What his/her job is\n- And explain why he/she enjoys working there",
        "part3": ["Would you like to start a family business?", "Would you like to work for a family business?", "Why do some people choose to start their own company?", "What are the advantages and disadvantages of family businesses?", "What family businesses do you know in your local area?", "What makes a successful family business?"]
    },
    "Wild animal": {
        "cue_card": "Describe a wild animal that you want to learn more about.\nYou should say:\n- What it is\n- When/where you saw it\n- Why you want to learn more about it\n- And explain what you want to learn more about it",
        "part3": ["Why should we protect wild animals?", "Why are some people more willing to protect wild animals than others?", "Do you think it’s important to take children to the zoo to see animals?", "Why do some people attach more importance to protecting rare animals?", "Should people educate children to protect wild animals?", "Is it more important to protect wild animals or the environment?"]
    },
    "Broke something": {
        "cue_card": "Describe a time when you broke something.\nYou should say:\n- What it was\n- When/where that happened\n- How you broke it\n- And explain what you did after that",
        "part3": ["What kind of things are more likely to be broken by people at home?", "What kind of people like to fix things by themselves?", "Do you think clothes produced in the factory are of better quality than those made by hand?", "Do you think handmade clothes are more valuable?", "Is the older generation better at fixing things?", "Do you think elderly people should teach young people how to fix things?"]
    },
    "Good friend": {
        "cue_card": "Describe a good friend who is important to you.\nYou should say:\n- Who he/she is\n- How/where you got to know him/her\n- How long you have known each other\n- And explain why he/she is important to you",
        "part3": ["How do children make friends at school?", "How do children make friends when they are not at school?", "Do you think it is better for children to have a few close friends or many casual friends?", "Do you think a child’s relationship with friends can be replaced by that with other people, like parents or other family members?", "What are the differences between friends made inside and outside the workplace?", "Do you think it’s possible for bosses and their employees to become friends?"]
    },
    "Friend good at music": {
        "cue_card": "Describe a friend of yours who is good at music/singing.\nYou should say:\n- Who he/she is\n- When/where you listen to his/her music/singing\n- What kind of music/songs he/she is good at\n- And explain how you feel when listening to his music/singing",
        "part3": ["What kind of music is popular in your country?", "What kind of music do young people like?", "What are the differences between young people’s and old people’s preferences in music?", "What are the benefits of children learning a musical instrument?", "Do you know what kind of music children like today?", "Do you think the government should invest more money in concerts?"]
    },
    "Great dinner": {
        "cue_card": "Describe a great dinner you and your friends or family members enjoyed.\nYou should say:\n- What you had\n- Who you had the dinner with\n- What you talked about during the dinner\n- And explain why you enjoyed it",
        "part3": ["Do people prefer to eat out at restaurants or eat at home during the Spring Festival?", "What food do you eat on special occasions, like during the Spring Festival or the Mid-autumn Festival?", "Why do people like to have meals together during important festivals?", "Is it a hassle to prepare a meal at home?", "What do people often talk about during meals?", "People are spending less and less time having meals with their families these days. Is this good or bad?"]
    },
    "Important decision": {
        "cue_card": "Describe an important decision made with the help of other people.\nYou should say:\n- What the decision was\n- Why you made the decision\n- Who helped you make the decision\n- And how you felt about it",
        "part3": ["What kind of decisions do you think are meaningful?", "What important decisions should be made by teenagers themselves?", "Why are some people unwilling to make quick decisions?", "Do people like to ask for advice more for their personal life or their work?", "Why do some people like to ask others for advice?"]
    },
    "Electricity off": {
        "cue_card": "Describe a time when the electricity suddenly went off.\nYou should say:\n- When/where it happened\n- How long it lasted\n- What you did during that time\n- And explain how you felt about it",
        "part3": ["Which is better, electric bicycles or ordinary bicycles?", "Do you think electric bicycles will replace ordinary bicycles in the future?", "Which is better, electric cars or petrol cars?", "How did people manage to live without electricity in the ancient world?", "Is it difficult for the government to replace all the petrol cars with electric cars?", "Do people use more electricity now than before?"]
    },
    "Exciting activity": {
        "cue_card": "Describe an exciting activity you have tried for the first time.\nYou should say:\n- What it is\n- When/where you did it\n- Why you thought it was exciting\n- And explain how you felt about it",
        "part3": ["Why are some people unwilling to try new things?", "Do you think fear stops people from trying new things?", "Why are some people keen on doing dangerous activities?", "Do you think that children adapt to new things more easily than adults?", "What can people learn from doing dangerous activities?", "What are the benefits of trying new things?"]
    },
    "Traditional story": {
        "cue_card": "Describe an interesting traditional story.\nYou should say:\n- What the story is about\n- When/how you knew it\n- Who told you the story\n- And explain how you felt when you first heard it",
        "part3": ["What kind of stories do children like?", "What are the benefits of listening to stories before bed?", "Why do most children like listening to stories before bedtime?", "What can children learn from stories?", "Do all stories for children have happy endings?", "Is a good storyline important for a movie?"]
    },
    "Old person interesting life": {
        "cue_card": "Describe an old person who has an interesting life and you enjoy talking to him/her.\nYou should say:\n- Who this person is\n- Where he/she lives\n- What his/her life is like\n- What you like to talk about with him/her\n- And explain why you enjoy talking to him/her",
        "part3": ["Should companies employ older workers?", "What do you think older people can contribute at work?", "Why do governments make retirement policies?", "When do you think is the best time to retire?", "Do you think people should spend more time with their grandparents?", "Is it beneficial to live with elderly people?"]
    },
    "Sky object": {
        "cue_card": "Describe a time when you saw something in the sky (e.g. flying kites, birds, sunset, etc.).\nYou should say:\n- What you saw\n- Where/when you saw it/them\n- How long you saw it/them\n- And explain how you felt about the experience",
        "part3": ["Would people be willing to get up early to watch and enjoy the sunrise?", "When would people watch the sky?", "Do many people pay attention to the shapes of stars?", "What do people usually see in the sky in the daytime?", "What are the differences between things people see in the sky in the daytime and at night?", "Why do some people like to watch stars at night?"]
    },
    "Positive change": {
        "cue_card": "Describe a positive change that you have made recently in your daily routine.\nYou should say:\n- What the change is\n- How you have changed the routine\n- Why you think it is a positive change\n- And explain how you feel about the change",
        "part3": ["What do people normally plan in their daily lives?", "Is time management very important in our daily lives?", "What changes would people often make?", "Do you think it is good to change jobs frequently?", "Who do you think would make changes more often, young people or old people?", "Who should get more promotion opportunities in the workplace, young people or older people?"]
    },
    "Good service": {
        "cue_card": "Describe a time when you received good service in a shop/store.\nYou should say:\n- Where the shop is\n- When you went to the shop\n- What service you received from the staff\n- And explain how you felt about the service",
        "part3": ["Why are shopping malls so popular in Vietnam?", "What are the advantages and disadvantages of shopping in small shops?", "Why do some people not like shopping in small shops?", "What are the differences between online shopping and in-store shopping?", "What are the advantages and disadvantages of shopping online?", "Can consumption drive economic growth?"]
    },
    "Natural place": {
        "cue_card": "Describe a natural place (e.g. parks, mountains, etc.).\nYou should say:\n- Where this place is\n- How you knew this place\n- What it is like\n- And explain why you like to visit it",
        "part3": ["What kind of people like to visit natural places?", "What are the differences between a natural place and a city?", "Do you think that going to the park is the only way to get close to nature?", "What can people gain from going to natural places?", "Are there any wild animals in the city?", "Do you think it is a good idea to let animals stay in local parks for people to see?"]
    },
    "Successful sportsperson": {
        "cue_card": "Describe a successful sportsperson you admire.\nYou should say:\n- Who he/she is\n- What you know about him/her\n- What he/she is like in real life\n- What achievement he/she has made\n- And explain why you admire him/her",
        "part3": ["Should students have physical education and do sports at school?", "What qualities should an athlete have?", "Is talent important in sports?", "Is it easy to identify children’s talents?", "What is the most popular sport in your country?", "Why are there so few top athletes?"]
    },
    "Science subject": {
        "cue_card": "Describe an area/subject of science (biology, robotics, etc.) that you are interested in and would like to learn more about.\nYou should say:\n- Which area/subject it is\n- When and where you came to know this area/subject\n- How you get information about this area/subject\n- And explain why you are interested in this area/subject",
        "part3": ["Why do some children not like learning science at school?", "Is it important to study science at school?", "Which science subject is the most important for children to learn?", "Should people continue to study science after graduating from school?", "How do you get to know about scientific news?", "Should scientists explain the research process to the public?"]
    },
    "Unusual meal": {
        "cue_card": "Describe an unusual meal you had.\nYou should say:\n- When you had it\n- Where you had it\n- Whom you had it with\n- And explain why it was unusual",
        "part3": ["What are the advantages and disadvantages of eating in restaurants?", "What fast food are there in your country?", "Do people eat fast food at home?", "Why do some people choose to eat out instead of ordering takeout?", "Do people in your country socialize in restaurants? Why?", "Do people in your country value food culture?"]
    },
    "Good habit": {
        "cue_card": "Describe a good habit your friend has and you want to develop.\nYou should say:\n- Who your friend is\n- What habit he/she has\n- When you noticed this habit\n- And explain why you want to develop this habit",
        "part3": ["How do we develop bad habits?", "What can we do to get rid of bad habits?", "What habits should children have?", "What should parents do to teach their children good habits?", "What influences do children with bad habits have on other children?", "Why do some habits change when people get older?"]
    },
    "Waited for special": {
        "cue_card": "Describe a time when you waited for something special that would happen.\nYou should say:\n- What you waited for\n- Where you waited\n- Why it was special\n- And explain how you felt while you were waiting",
        "part3": ["Why are some people unwilling to wait?", "Where do children learn to be patient, at home or at school?", "On what occasions do people usually need to wait?", "Who behave better when waiting, children or adults?", "Compared to the past, are people less patient now？Why?", "What are the positive and negative effects of waiting on society？"]
    },
    "Interesting social media": {
        "cue_card": "Describe a time you saw something interesting on social media.\nYou should say:\n- When it was\n- Where you saw it\n- What you saw\n- And explain why you think it was interesting",
        "part3": ["Why do people like to use social media?", "What kinds of things are popular on social media?", "What are the advantages and disadvantages of using social media?", "What do you think of making friends on social network?", "Are there any people who shouldn’t use social media?", "Do you think people spend too much time on social media?"]
    },
    "Natural talent": {
        "cue_card": "Describe a natural talent (sports, music, etc.) you want to improve.\nYou should say:\n- What it is\n- When you discovered it\n- How you want to improve it\n- And how you feel about it",
        "part3": ["Do you think artists with talents should focus on their talents?", "Is it possible for us to know whether children who are 3 or 4 years old will become musicians and painters when they grow up?", "Why do people like to watch talent shows？", "Do you think it is more interesting to watch famous people’s or ordinary people’s shows?"]
    },
    "Childhood toy": {
        "cue_card": "Describe a toy you liked in your childhood.\nYou should say:\n- What kind of toy it is\n- When you received it\n- How you played it\n- And how you felt about it",
        "part3": ["What’s the difference between the toys boys play with and girls play with?", "What are the advantages and disadvantages of modern toys?", "How do advertisements influence children?", "Should advertising aimed at kids be prohibited?", "What’s the difference between the toys kids play now and those they played in the past?", "Do you think parents should buy more toys for their kids or spend more time with them?"]
    },
    "Talked foreign language": {
        "cue_card": "Describe the time when you first talked in a foreign language.\nYou should say:\n- Where you were\n- Who you were with\n- What you talked about\n- And explain how you felt about it",
        "part3": ["Does learning a foreign language help in finding a job?", "Which stage of life do you think is the best for learning a foreign language?", "At what age should children start learning a foreign language?", "Which skill is more important, speaking or writing ?", "Does a person still need to learn other languages, if he or she is good at English?", "Do you think minority languages will disappear?"]
    },
    "Lost way": {
        "cue_card": "Describe an occasion when you lost your way.\nYou should say:\n- Where you were\n- What happened\n- How you felt\n- And explain how you found your way",
        "part3": ["Is a paper map still necessary?", "How do people react when they get lost?", "Why do some people get lost more easily than others?", "Do you think it is important to be able to read a map?", "Do you think it is important to do some preparation before you travel to new places?", "How can people find their way when they are lost?"]
    },
    "Apology": {
        "cue_card": "Describe a time when someone apologized to you.\nYou should say:\n- When it was\n- Who this person is\n- Why he or she apologized to you\n- And how you felt about it",
        "part3": ["Do you think every “sorry” is from the bottom of the heart?", "Are women better than men at recognizing emotions?", "On what occasion do people usually apologize to others?", "Do people in your country like to say “sorry”?", "Do you think people should apologize for anything wrong they do?", "Why do some people refuse to say “sorry” to others?"]
    }
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
    ],    
    "Lesson 3: Home & Transport": [
        "1. Did you live in a house or an apartment when you were a child?",
        "2. What was your favorite room in your childhood home?",
        "3. Have you moved house many times?",
        "4. How did you go to school when you were younger?",
        "5. Did you enjoy traveling by bus/motorbike in the past?",
        "6. Have you ever been stuck in a terrible traffic jam?"
    ],
    "Lesson 4: Describing People": [
        "Describe a family member or a friend that you spend a lot of time with (Part 2)"
    ],
    "Lesson 5: Describing Objects": [
        "Describe a memorable gift you received (Part 2)"
    ],
    "Lesson 6: Describing Places": [
        "Describe a city or town you really liked visiting (Part 2)"
    ],
    "Lesson 7: Describing Events": [
        "Describe a time when you tried to do something you had never done before (Part 2)"
    ]
}

CLASS_CUE_CARDS = {
    "Describe a family member or a friend that you spend a lot of time with (Part 2)": "Describe a family member or a friend that you spend a lot of time with.\n\nYou should say:\n- Who this person is\n- What they look like\n- What their personality is\n- And explain why you like spending time with them."
}

# READING: Lesson 2 Full Passage & Questions
READING_CONTENT = {
    "Lesson 2: Marine Chronometer": {
        "status": "Active",
        "title": "Timekeeper: Invention of Marine Chronometer",
        "intro_text": "Thời chưa có vệ tinh, các thủy thủ rất sợ đi biển xa vì họ không biết mình đang ở đâu. Cách duy nhất để xác định vị trí là phải biết giờ chính xác. Nhưng khổ nỗi, đồng hồ quả lắc ngày xưa cứ mang lên tàu rung lắc là chạy sai hết. Bài này kể về hành trình chế tạo ra chiếc đồng hồ đi biển đầu tiên, thứ đã cứu mạng hàng ngàn thủy thủ.",
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
        "intro_text": "Làm nông nghiệp ở Úc khó hơn nhiều so với ở Anh hay châu Âu vì đất đai ở đây rất khô và thiếu dinh dưỡng. Vào cuối thế kỷ 19, những người nông dân Úc đứng trước nguy cơ phá sản vì các phương pháp canh tác cũ không còn hiệu quả.\nBài đọc này sẽ cho các bạn thấy họ đã xoay sở như thế nào bằng công nghệ. Từ việc chế tạo ra chiếc cày đặc biệt có thể tự 'nhảy' qua gốc cây, cho đến việc lai tạo giống lúa mì chịu hạn. Chính những sáng kiến này đã biến nước Úc từ một nơi chỉ nuôi cừu thành một cường quốc xuất khẩu lúa mì thế giới.",
        "text": """
During this period, there was a widespread expansion of agriculture in Australia. The selection system was begun, whereby small sections of land were parceled out by lot. Particularly in New South Wales, this led to conflicts between small holders and the emerging squatter class, whose abuse of the system often allowed them to take vast tracts of fertile land.

There were also many positive advances in farming technology as the farmers adapted agricultural methods to the harsh Australian conditions. One of the most important was “dry farming”. This was the discovery that repeated ploughing of fallow, unproductive land could preserve nitrates and moisture, allowing the land to eventually be cultivated. This, along with the extension of the railways, allowed the development of what are now great inland wheat lands.

The inland areas of Australia are less fertile than most other wheat-producing countries and yields per acre are lower. This slowed their development, but also led to the development of several labour saving devices. In 1843 John Ridley, a South Australian farmer, invented “the stripper”, a basic harvesting machine. By the 1860s its use was widespread. H. V. McKay, then only nineteen, modified the machine so that it was a complete harvester: cutting, collecting and sorting. McKay developed this early innovation into a large harvester manufacturing industry centred near Melbourne and exporting worldwide. Robert Bowyer Smith invented the “stump jump plough”, which let a farmer plough land which still had tree stumps on it. It did this by replacing the traditional plough shear with a set of wheels that could go over stumps, if necessary.

The developments in farm machinery were supported by scientific research. During the late 19th century, South Australian wheat yields were declining. An agricultural scientist at the colony’s agricultural college, John Custance, found that this was due to a lack of phosphates and advised the use of soluble superphosphate fertilizer. The implementation of this scheme revitalised the industry.

From early days it had been obvious that English and European sheep breeds had to be adapted to Australian conditions, but only near the end of the century was the same applied to crops. Prior to this, English and South African strains had been use, with varying degrees of success. WilliamFarrer, from Cambridge University, was the first to develop new wheat varieties that were better able to withstand dry Australian conditions. By 1914, Australia was no longer thought of as a land suitable only for sheep, but as a wheat-growing nation.
        """,
        "questions_mc": [
            {"id": "q1", "q": "1. What is dry farming?", "options": ["A. Preserving nitrates and moisture.", "B. Ploughing the land again and again.", "C. Cultivating fallow land."], "a": "B. Ploughing the land again and again.", "exp": "Dẫn chứng (Đoạn 2): 'This was the discovery that repeated ploughing of fallow... could preserve nitrates...' -> Dry farming là phương pháp cày xới liên tục (repeated ploughing) để giữ ẩm."},
            {"id": "q2", "q": "2. What did H. V. McKay do?", "options": ["A. Export the stripper.", "B. Improve the stripper.", "C. Cut, collect, and sort wheat."], "a": "B. Improve the stripper.", "exp": "Dẫn chứng (Đoạn 3): 'H. V. McKay... modified the machine so that it was a complete harvester...' -> Modified the machine = Improve the stripper."},
            {"id": "q3", "q": "3. What did the 'stump jump plough’ innovation allow farmers to do?", "options": ["A. Cut through tree stumps.", "B. Change the wheels for a traditional plough.", "C. Allow farmers to cultivate land that hadn’t been fully cleared."], "a": "C. Allow farmers to cultivate land that hadn’t been fully cleared.", "exp": "Dẫn chứng (Đoạn 3): '...let a farmer plough land which still had tree stumps on it.' -> Cày trên đất vẫn còn gốc cây (chưa dọn sạch)."},
            {"id": "q4", "q": "4. What did John Custance recommend?", "options": ["A. Improving wheat yields.", "B. Revitalizing the industry.", "C. Fertilizing the soil."], "a": "C. Fertilizing the soil.", "exp": "Dẫn chứng (Đoạn 4): '...advised the use of soluble superphosphate fertilizer.' -> Khuyên dùng phân bón."},
            {"id": "q5", "q": "5. Why was William Farrer’s wheat better?", "options": ["A. It was drought-resistant.", "B. It wasn’t from England or South Africa.", "C. It was drier for Australian conditions."], "a": "A. It was drought-resistant.", "exp": "Dẫn chứng (Đoạn 5): '...better able to withstand dry Australian conditions.' -> Chịu hạn tốt (drought-resistant)."}
        ]
    },
    "Lesson 4: The lost giants of Australian fauna": {
        "status": "Active",
        "title": "The lost giants of Australian fauna",
        "intro_text": "Cùng khám phá thế giới động vật hoang dã độc đáo của Úc vào 1 triệu năm trước thời kỷ Pleistocene - kỷ nguyên của những loài thú có vú khổng lồ. Bài đọc sẽ đưa bạn tìm hiểu về sự biến mất bí ẩn của chúng và bài học về bảo vệ động vật ngày nay.",
        "text": """
(A) Australia's wildlife is unique. The vast majority of the animals that live there are not found anywhere else – and things were no different 1 million years ago during the Pleistocene: the age of the super-sized mammal. Before humanity became Earth's undisputed superpower, giant beasts of all shapes and sizes dominated every continent, but the Pleistocene mammals of Australia were different. Some of them could grow to the size of small cars, or possessed teeth longer than knife blades.

(B) None of these animals survive today – although exactly why that's the case is a mystery. Humans, with their advanced hunting techniques and use of fire to modify the landscape, may have played a central role in the megafauna's disappearance, but this idea is still a matter of heated debate.

(C) Even if we cannot be sure that the arrival of Australian Aboriginals on the continent had catastrophic effects on its native animals, it seems that the animals had a rather spiritual effect on the humans. The Aboriginal mythological "Dreamtime" includes a cast of monstrous creatures, many of which bear a close resemblance to some of the real-life monsters that once stalked Australia's plains. Are the myths based on fact? Perhaps: after all, these creatures are far stranger than anything dreamed up by humans.

(D) For instance, the two-tonne weighting Diprotodon comfortably holds the title of largest marsupial ever. In size and appearance, it looked superficially like a modern rhinoceros, but the Diprotodon seems to have had a social lifestyle more like that of an elephant, another mammal with which it shares anatomical similarities. What the Diprotodon most resembles, however, is exactly what it is: an enormous wombat.

(E) Another record breaker, this time a world champion; Varanus priscus, commonly known by its antiquated genus name Megalania – was the largest terrestrial lizard the world has ever known. Megalania was a goanna lizard, a relative of today's infamous Komodo dragon, and conservative estimates have predicted that it was at least 5.5m long.

(F) These monster marsupials were not the only giants. Their numbers were swelled by half tonne birds and dinosaur-like tortoises. Although this biological assemblage was truly nightmarish for humans, it greatly enriched Australia's fauna and contributed to the world’s biological diversity. Unfortunately, all of these species are extinct nowadays. This fact shows us that even strong, monstrous creatures can easily die out. So we need to care about the animals that surround us today and don’t let them disappear as it happened to their distant ancestors.
        """,
        "questions_mc": [
            {
                "id": "q1", 
                "q": "Paragraph A", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "iv. Incredible creatures of Pleistocene Australia", 
                "exp": "Sau khi đọc đoạn này, ta có thể thấy rõ ý chính là mô tả động vật hoang dã ở Úc thời Pleistocene. Ý này được viết ngắn gọn ở câu đầu tiên: 'Australia's wildlife is unique.' Mặc dù thú có vú khổng lồ có được nhắc đến, nhưng trọng tâm chính của đoạn văn này là những sinh vật phi thường ở Úc thời Pleistocene. Vì vậy, đáp án đúng là iv."
            },
            {
                "id": "q2", 
                "q": "Paragraph B", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "viii. Mystery the giants' disappearance", 
                "exp": "Đoạn văn này nói rằng chúng ta không biết tại sao những sinh vật này lại biến mất. Và một lần nữa, câu đầu tiên của đoạn văn đã tóm tắt ý chính của nó: 'None of these animals survive today – although exactly why that's the case is a mystery.' (Không một loài nào sống sót đến nay - mặc dù lý do chính xác vẫn là một bí ẩn). Do đó, đáp án đúng là viii."
            },
            {
                "id": "q3", 
                "q": "Paragraph C", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "iii. Myths and reality", 
                "exp": "Những câu sau chứa ý chính của đoạn văn: '...Are the myths based on fact? Perhaps...' (Những huyền thoại có dựa trên sự thật không? Có lẽ...). Đoạn văn nói về sự liên hệ giữa thần thoại (myths) và thực tế (reality), do đó tiêu đề đúng là iii. Lưu ý rằng sự xuất hiện của thổ dân Úc (Aboriginals) cũng được nhắc đến nhưng không đóng vai trò then chốt."
            },
            {
                "id": "q4", 
                "q": "Paragraph D", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "ii. The largest mammal", 
                "exp": "Đoạn văn này miêu tả rõ ràng về loài động vật có vú khổng lồ Diprotodon: 'The two-tonne weighting Diprotodon comfortably holds the title of largest marsupial ever.' (Loài Diprotodon nặng hai tấn thoải mái giữ danh hiệu loài thú có túi lớn nhất từng tồn tại). Vì vậy, ý chính của đoạn D là ii. The largest mammal."
            },
            {
                "id": "q5", 
                "q": "Paragraph E", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "vi. Giant lizards", 
                "exp": "Toàn bộ đoạn văn được dành riêng để nói về loài thằn lằn khổng lồ Megalania: '... Megalania – was the largest terrestrial lizard ...' (...Megalania – là loài thằn lằn trên cạn lớn nhất...). Do đó, 'vi. Giant lizards' là lựa chọn tiêu đề chính xác."
            },
            {
                "id": "q6", 
                "q": "Paragraph F", 
                "options": ["i. Extinction of monstrous creatures", "ii. The largest mammal", "iii. Myths and reality", "iv. Incredible creatures of Pleistocene Australia", "v. Importance of animal protection", "vi. Giant lizards", "vii. Arrival of Australian Aboriginals", "viii. Mystery the giants' disappearance"], 
                "a": "v. Importance of animal protection", 
                "exp": "Đoạn F kể thêm một chút về các loài tuyệt chủng khác và kết thúc bằng một kết luận: 'Unfortunately, all of these species are extinct nowadays. This fact shows us that even strong, monstrous creatures can easily die out. So we need to care about animals that surround us today and don't let them disappear...' (Thật không may, tất cả các loài này nay đã tuyệt chủng... Vì vậy chúng ta cần quan tâm đến các loài động vật xung quanh ta ngày nay và đừng để chúng biến mất...). Kết luận này là ý chính của đoạn văn - chúng ta cần bảo vệ động vật. Do đó tiêu đề đúng là v."
            }
        ]
    }
}

# WRITING CONTENT (Chỉ lớp ELITE)
# WRITING CONTENT
# WRITING CONTENT
WRITING_CONTENT = {
    "Lesson 3: Education & Society": {
        "type": "Task 2",
        "time": 40,
        "question": """### 📝 IELTS Writing Task 2
**Some people think that parents should teach children how to be good members of society. Others, however, believe that school is the place to learn this.**
Discuss both these views and give your own opinion."""
    },
    "Lesson 4: Salt Intake (Task 1)": {
        "type": "Task 1",
        "time": 20,
        "image_url": "https://drive.google.com/thumbnail?id=1du4nIQMhHe5uoqyiy9-MNItYpQTaKUht&sz=w1000",
        "question": """### 📝 IELTS Writing Task 1
**The chart shows information about salt intake in the US in 2000.**
Summarise the information by selecting and reporting the main features, and make comparisons where relevant."""
    },
    "Lesson 5: News Media (Task 2)": {
        "type": "Task 2",
        "time": 40,
        "question": """### 📝 IELTS Writing Task 2
**Some people think that the news media has become much more influential in people's lives today and it is a negative development.**
Do you agree or disagree?"""
    },
    "Lesson 6: Easternburg Map (Task 1)": {
        "type": "Task 1",
        "time": 20,
        "image_url": "https://drive.google.com/thumbnail?id=1MqxQbcUxFPUWNmdcpqv5u6GVBse3Jxgg&sz=w1000",
        "question": """### 📝 IELTS Writing Task 1
**The diagrams below show the town of Easternburg in 1995 and the present day.**
Summarise the information by selecting and reporting the main features, and make comparisons where relevant."""
    },
    "Lesson 5: Resource Depletion (Task 2)": {
        "type": "Task 2",
        "time": 40,
        "question": """### 📝 IELTS Writing Task 2
**Some people believe that the depletion of natural resources is an unavoidable consequence of economic development.**
To what extent do you agree or disagree?"""
    }
}

# --- HÀM TẠO MENU TỰ ĐỘNG (Auto-generate Menu with "Sắp ra mắt" status) ---
def create_default_menu(content_dict, total_lessons=10):
    menu = []
    for i in range(1, total_lessons + 1):
        # Tìm bài học tương ứng trong dict (Lesson X: ...)
        lesson_key = next((k for k in content_dict.keys() if k.startswith(f"Lesson {i}:")), None)
        if lesson_key:
            menu.append(lesson_key)
        else:
            menu.append(f"Lesson {i}: (Sắp ra mắt)")
    return menu

SPEAKING_MENU = create_default_menu(SPEAKING_CONTENT)
READING_MENU = create_default_menu(READING_CONTENT)
WRITING_MENU = create_default_menu(WRITING_CONTENT)
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
    // TÍNH NĂNG HIGHLIGHT BẰNG CÁCH BÔI ĐEN (Robust Version)
    document.addEventListener('mouseup', function() {
        var selection = window.getSelection();
        var selectedText = selection.toString();
        
        // Chỉ xử lý nếu có text được bôi đen và không rỗng
        if (selectedText.length > 0 && selection.rangeCount > 0) {
            // Hàm kiểm tra xem node có nằm trong vùng bài đọc (.reading-text) không
            function hasReadingClass(node) {
                if (!node) return false;
                if (node.nodeType === 3) node = node.parentNode; // Nếu là Text Node thì lấy cha
                return node.closest('.reading-text') !== null;
            }

            var range = selection.getRangeAt(0);
            var commonAncestor = range.commonAncestorContainer;

            // Kiểm tra vùng chọn có nằm trọn vẹn trong bài đọc không
            if (hasReadingClass(commonAncestor)) {
                try {
                    var span = document.createElement("span");
                    span.className = "highlighted";
                    span.title = "Click để xóa highlight";
                    
                    // Sự kiện click để xóa highlight
                    span.onclick = function(e) {
                        e.stopPropagation(); // Ngăn sự kiện nổi bọt
                        var text = document.createTextNode(this.innerText);
                        this.parentNode.replaceChild(text, this);
                        // Gộp các text node lại
                        if (text.parentNode) text.parentNode.normalize(); 
                    };

                    range.surroundContents(span);
                    selection.removeAllRanges(); // Bỏ bôi đen sau khi highlight xong
                } catch (e) { 
                    console.log("Highlight phức tạp: Vui lòng chọn từng đoạn văn bản nhỏ hơn."); 
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

def call_gemini(prompt, expect_json=False, audio_data=None, image_data=None):
    """
    Hàm gọi Gemini API hỗ trợ:
    - Text Prompt
    - Audio (Speaking)
    - Image (Writing Task 1)
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    final_prompt = prompt
    if expect_json:
        final_prompt += "\n\nIMPORTANT: Output STRICTLY JSON without Markdown formatting (no ```json or ```)."
    
    # Tạo nội dung text
    parts = [{"text": final_prompt}]
    
    # Nếu có Audio (Speaking)
    if audio_data:
        parts.append({"inline_data": {"mime_type": "audio/wav", "data": audio_data}})
        
    # Nếu có Image (Writing Task 1) - Input là Base64 string của ảnh
    if image_data:
        parts.append({"inline_data": {"mime_type": "image/png", "data": image_data}})

    data = {"contents": [{"parts": parts}]}
    
    for attempt in range(4): 
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(data))
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                if expect_json: 
                    text = re.sub(r"```json|```", "", text).strip()
                return text
            elif resp.status_code == 429: 
                time.sleep(2 ** attempt)
                continue
            else: 
                print(f"Error {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(1)
            continue
            
    return None

# --- HÀM HỖ TRỢ LẤY ẢNH TỪ URL THÀNH BASE64 ---
def get_image_base64_from_url(url):
    try:
        # Thêm User-Agent giả lập trình duyệt để tránh bị chặn bởi Google Drive
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Lỗi tải ảnh: {e}")
        return None
    return None

# --- QUẢN LÝ SESSION STATE ---
if 'speaking_attempts' not in st.session_state: st.session_state['speaking_attempts'] = {}
if 'generated_quiz' not in st.session_state: st.session_state['generated_quiz'] = None
if 'reading_session' not in st.session_state: st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}
if 'reading_highlight' not in st.session_state: st.session_state['reading_highlight'] = ""
if 'writing_step' not in st.session_state: st.session_state['writing_step'] = 'outline' 
if 'writing_outline_score' not in st.session_state: st.session_state['writing_outline_score'] = 0

# State mới cho module Dịch câu
if 'trans_current_sentence' not in st.session_state: st.session_state['trans_current_sentence'] = ""
if 'trans_feedback' not in st.session_state: st.session_state['trans_feedback'] = ""

# --- SỬA LẠI: HÀM LẤY BÀI TẬP VỚI CỜ BÁO TRẠNG THÁI ---
def get_assignments_status(user_class_code):
    """
    Trả về (config, found)
    - config: Dict bài tập hoặc dict rỗng
    - found: True nếu lớp có trong danh sách cấu hình, False nếu không tìm thấy (lớp lạ)
    """
    for prefix, config in HOMEWORK_CONFIG.items():
        if user_class_code.startswith(prefix):
            return config, True
    return {"Speaking": [], "Reading": [], "Writing": []}, False

def login():
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1>MR. TAT LOC IELTS CLASS</h1></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            name = st.text_input("Họ tên học viên:")
            class_code = st.selectbox("Chọn Mã Lớp:", ["-- Chọn lớp --"] + list(CLASS_CONFIG.keys()))
            if st.form_submit_button("Vào Lớp Học"):
                if name and class_code != "-- Chọn lớp --":
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
    
    # --- LOGIC PHÂN QUYỀN MỚI (STRICT MODE) ---
    assigned_homework, is_class_configured = get_assignments_status(user['class'])
    
    # Hàm hỗ trợ lấy menu chuẩn xác
    def get_menu_for_skill(skill_key, default_menu):
        if is_class_configured:
            # Nếu lớp ĐÃ ĐƯỢC CẤU HÌNH trong hệ thống:
            # - Trả về list bài tập (nếu có)
            # - Nếu list rỗng, trả về list chứa thông báo "Chưa có bài"
            # - TUYỆT ĐỐI KHÔNG trả về default_menu (tránh hiện bài của lớp khác)
            if assigned_homework.get(skill_key):
                return assigned_homework[skill_key]
            else:
                return ["(Chưa có bài tập)"] 
        else:
            # Nếu lớp LẠ (Admin/Test): Hiện full menu mặc định
            return default_menu

    current_speaking_menu = get_menu_for_skill("Speaking", SPEAKING_MENU)
    current_reading_menu = get_menu_for_skill("Reading", READING_MENU)
    current_writing_menu = get_menu_for_skill("Writing", WRITING_MENU)

    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.caption(f"Lớp: {user['class']} | Level: {user['level']['level']}")
        st.divider()
        # Đã cập nhật Menu thêm chức năng Dịch Câu
        menu = st.radio("CHỌN KỸ NĂNG:", ["🏆 Bảng Xếp Hạng", "🗣️ Speaking", "📖 Reading", "🎧 Listening", "✍️ Writing", "🔄 Dịch Câu"])
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


    # --- MODULE 6: DỊCH CÂU (TRANSLATION PRACTICE) ---
    elif menu == "🔄 Dịch Câu":
        st.title("🔄 Luyện Dịch Câu IELTS")
        st.markdown("Cải thiện khả năng tư duy song ngữ và mở rộng vốn từ vựng với các câu hỏi chuẩn văn phong IELTS.")

        # DANH SÁCH CÁC CHỦ ĐỀ IELTS NGẮN GỌN VÀ HIỂN THỊ LÊN GIAO DIỆN
        TOPICS_LIST = [
            "Ngẫu nhiên (Random)", 
            "Giáo dục (Education)", 
            "Môi trường (Environment)", 
            "Công nghệ (Technology)", 
            "Sức khỏe (Health)", 
            "Xã hội (Society)", 
            "Kinh doanh & Việc làm (Work & Business)", 
            "Nghệ thuật & Văn hóa (Art & Culture)", 
            "Du lịch (Travel)",
            "Truyền thông (Media)"
        ]

        LEVEL_DESCRIPTIONS = {
            "A1": "Beginner (IELTS 2.0-3.0): Very short, simple sentences (5-8 words). Basic vocabulary for everyday needs. Simple tenses only.",
            "A2": "Elementary (IELTS 3.5-4.5): Simple compound sentences (8-12 words). Familiar daily topics. Basic grammatical structures.",
            "B1": "Intermediate (IELTS 5.0-5.5): Mixed simple and complex sentences (12-18 words). Good everyday vocabulary. Can express opinions.",
            "B2": "Upper-Intermediate (IELTS 6.0-6.5): Clear, detailed, complex sentences (15-22 words). Good control of grammar. Wide range of vocabulary, some academic words.",
            "C1": "Advanced (IELTS 7.0-8.0): Highly complex and well-structured sentences (20-30 words). Rich, academic, and idiomatic vocabulary. Nuanced meanings.",
            "C2": "Proficient (IELTS 8.5-9.0): Expert level. Sophisticated, precise, and highly natural language (long, academic sentences). Mastery of complex grammar and rare vocabulary."
        }

        col1, col2, col3 = st.columns(3)
        with col1:
            trans_direction = st.selectbox("Chọn chiều dịch:", ["Anh -> Việt", "Việt -> Anh"])
        with col2:
            trans_level = st.selectbox("Chọn cấp độ:", ["A1", "A2", "B1", "B2", "C1", "C2"])
        with col3:
            trans_topic_selection = st.selectbox("Chọn chủ đề:", TOPICS_LIST)
        
        # Nút tạo câu mới (chủ động gọi hàm)
        if st.button("🎲 Tạo câu mới"):
            with st.spinner("Đang tạo câu hỏi..."):
                # Xử lý chủ đề cho prompt
                if "Ngẫu nhiên" in trans_topic_selection:
                    english_topics = [t.split("(")[1].strip(")") for t in TOPICS_LIST[1:]]
                    chosen_topic = random.choice(english_topics)
                else:
                    chosen_topic = trans_topic_selection.split("(")[1].strip(")")

                prompt_gen = f"""
                Role: IELTS Teacher.
                Task: Generate exactly ONE single sentence for translation practice.
                Level Target: {LEVEL_DESCRIPTIONS[trans_level]}
                Condition: The sentence must be in {'English' if trans_direction == 'Anh -> Việt' else 'Vietnamese'}.
                Specific Topic: {chosen_topic}.
                Style: Academic or semi-academic (IELTS Style).
                Constraint: Strictly adhere to the grammar and vocabulary complexity expected for the Level Target. 
                OUTPUT EXACTLY AND ONLY THE SENTENCE. NO EXTRA TEXT, NO QUOTATION MARKS.
                """
                new_sentence = call_gemini(prompt_gen)
                if new_sentence:
                    # FIX: Thêm .strip() để xóa khoảng trắng và dòng trống ở đầu/cuối chuỗi
                    st.session_state['trans_current_sentence'] = new_sentence.strip()
                    st.session_state['trans_feedback'] = ""
                    st.rerun()

        st.divider()

        # Nếu đã có câu hỏi được tạo ra
        if st.session_state['trans_current_sentence']:
            st.markdown(f"### 📝 Dịch câu sau sang tiếng {'Việt' if trans_direction == 'Anh -> Việt' else 'Anh'}:")
            # FIX: Gọi lại .strip() 1 lần nữa cho an toàn khi in ra định dạng Markdown
            st.info(f"**{st.session_state['trans_current_sentence'].strip()}**")
            
            user_translation = st.text_area("Nhập bản dịch của bạn:", height=100)
            
            if st.button("✅ Kiểm tra đáp án"):
                if not user_translation.strip():
                    st.warning("Vui lòng nhập bản dịch của bạn trước khi kiểm tra.")
                else:
                    with st.spinner("Đang kiểm tra bản dịch..."):
                        prompt_check = f"""
                        Role: Expert IELTS Bilingual Tutor.
                        Task: Evaluate the student's translation.
                        Direction: {trans_direction}
                        Original Sentence: {st.session_state['trans_current_sentence']}
                        Student's Translation: {user_translation}
                        Level Expected: {LEVEL_DESCRIPTIONS[trans_level]}

                        Rules for Evaluation:
                        1. Ignore minor typos (e.g., missing a comma, slight misspellings) if the core meaning is fully intact.
                        2. Accept synonymous phrasing. If it's English to Vietnamese, accept different natural Vietnamese expressions as long as the semantic meaning and tone match. If Vietnamese to English, accept valid paraphrasing.
                        3. Be encouraging. Focus on major grammatical issues or wrong word choices that alter the meaning or are unnatural for the level.

                        Output format (Vietnamese Markdown):
                        ### Đánh giá chung
                        [Đúng/Sai cơ bản? Khen ngợi nếu làm tốt, chỉ ra lỗi sai lớn nếu có]

                        ### Lỗi cần lưu ý
                        [Chỉ ra các điểm dịch sai nghĩa, hoặc sai ngữ pháp nghiêm trọng. Nếu không có lỗi, ghi "Bản dịch rất tốt, không có lỗi nghiêm trọng!"]

                        ### Đáp án tham khảo 
                        [Cung cấp 1-2 cách dịch chuẩn, tự nhiên và học thuật nhất]

                        ### Từ vựng / Cấu trúc hay
                        [Liệt kê 2-3 từ/cụm từ đắt giá từ câu gốc kèm nghĩa và ví dụ ngắn]
                        """
                        feedback = call_gemini(prompt_check)
                        if feedback:
                            st.session_state['trans_feedback'] = feedback
                            st.rerun()

        # Hiển thị feedback và nhắc nhở
        if st.session_state['trans_feedback']:
            st.markdown(st.session_state['trans_feedback'])
            
            st.divider()
            st.warning("Nhớ note lại từ vựng rồi mới chuyển câu khác nha tình iu 💖")
            
            if st.button("✅ Đã note xong! Chuyển sang câu tiếp theo"):
                with st.spinner("Đang chuẩn bị câu tiếp theo..."):
                    # Tự động generate câu mới với logic chủ đề tương tự
                    if "Ngẫu nhiên" in trans_topic_selection:
                        english_topics = [t.split("(")[1].strip(")") for t in TOPICS_LIST[1:]]
                        chosen_topic = random.choice(english_topics)
                    else:
                        chosen_topic = trans_topic_selection.split("(")[1].strip(")")

                    prompt_gen = f"""
                    Role: IELTS Teacher.
                    Task: Generate exactly ONE single sentence for translation practice.
                    Level Target: {LEVEL_DESCRIPTIONS[trans_level]}
                    Condition: The sentence must be in {'English' if trans_direction == 'Anh -> Việt' else 'Vietnamese'}.
                    Specific Topic: {chosen_topic}.
                    Style: Academic or semi-academic (IELTS Style).
                    Constraint: Strictly adhere to the grammar and vocabulary complexity expected for the Level Target. 
                    OUTPUT EXACTLY AND ONLY THE SENTENCE. NO EXTRA TEXT, NO QUOTATION MARKS.
                    """
                    new_sentence = call_gemini(prompt_gen)
                    if new_sentence:
                        # FIX: Thêm .strip() khi gán biến để làm sạch câu sinh ra
                        st.session_state['trans_current_sentence'] = new_sentence.strip()
                        st.session_state['trans_feedback'] = ""
                        st.rerun()

    # --- MODULE 5: WRITING ---
    elif menu == "✍️ Writing":
        st.title("✍️ Luyện Tập Writing")
        
        lesson_w = st.selectbox("Chọn bài viết:", current_writing_menu)
        
        if "(Chưa có bài tập)" in lesson_w:
            st.info("Bài này chưa được giao.")
        elif lesson_w in WRITING_CONTENT:
            data_w = WRITING_CONTENT[lesson_w]
            task_type = data_w.get("type", "Task 2")
            
            st.info(f"### TOPIC ({task_type}):\n{data_w['question']}")

            image_b64 = None
            if task_type == "Task 1" and "image_url" in data_w:
                st.write("**📊 Chart/Diagram:**")
                st.image(data_w["image_url"], caption="Graphic:", use_container_width=True)
                # Tải ảnh ngầm để chấm
                with st.spinner("Đang tải dữ liệu biểu đồ..."):
                    image_b64 = get_image_base64_from_url(data_w["image_url"])

            # === PHÂN LUỒNG TASK 1 VS TASK 2 ===
            
            # --- LUỒNG TASK 1: TRỰC TIẾP LÀM BÀI ---
            if task_type == "Task 1":
                # Chọn chế độ
                mode_w = st.radio("Chọn chế độ:", ["-- Chọn chế độ --", "Luyện Tập (Không giới hạn)", "Thi Thử (20 Phút)"], horizontal=True, key="w_task1_mode")
                
                if mode_w != "-- Chọn chế độ --":
                    # Hiển thị đồng hồ nếu Thi Thử
                    if "Thi Thử" in mode_w:
                        timer_html = f"""
                        <div style="font-size: 24px; font-weight: bold; color: #d35400; font-family: 'Segoe UI', sans-serif; margin-bottom: 10px;">
                            ⏳ Thời gian Task 1: <span id="timer_w1">20:00</span>
                        </div>
                        <script>
                        var time = 20 * 60;
                        setInterval(function() {{
                            var m = Math.floor(time / 60);
                            var s = time % 60;
                            document.getElementById("timer_w1").innerHTML = m + ":" + (s < 10 ? "0" : "") + s;
                            time--;
                        }}, 1000);
                        </script>
                        """
                        components.html(timer_html, height=50)

                    essay_t1 = st.text_area("Bài làm Task 1 (Min 150 words):", height=300, key="essay_t1")
                    
                    if st.button("Nộp Bài Task 1"):
                        if len(essay_t1.split()) < 30: st.warning("Bài viết quá ngắn.")
                        else:
                            with st.spinner("Đang chấm Task 1..."):
                                prompt_t1 = f"""
                                ## ROLE: Senior IELTS Writing Examiner (Strict but Natural).
                                ## TASK: Assess IELTS Writing Task 1 Essay and provide deep, insightful feedback in a natural, conversational tone like a real teacher.
                                ## CRITICAL RULE 1: The ENTIRE "Feedback" string MUST be written in 100% Vietnamese (Tiếng Việt). DO NOT mix English and Vietnamese in your explanation. Only use English when quoting the student's text.
                                ## CRITICAL RULE 2 (INDEPENDENT & WHOLE NUMBER SCORING): DO NOT give flat, identical scores across all 4 criteria. You MUST evaluate EACH criterion completely independently. MOREOVER, individual criteria (TA, CC, LR, GRA) MUST be WHOLE NUMBERS ONLY (e.g., 5.0, 6.0, 7.0, 8.0). DO NOT give half bands (like 6.5 or 5.5) for individual criteria. ONLY the Overall score can be a half band (e.g., 6.5) calculated by averaging the 4 criteria. Reflect a realistic spiky profile.
                                ## CRITICAL RULE 3 (JSON SAFE): YOU MUST NOT use unescaped double quotes (\") inside the Feedback text. ALWAYS use single quotes (') for quoting words or sentences to avoid breaking the JSON format.
                                ## INPUT:
                                - Question: {data_w['question']}
                                - Essay: {essay_t1}

                                ## 🛡️ RUBRIC (TASK 1 - STRICT):
                                * **BAND 4 (Limited):**
                                    * **Task Achievement:** Lạc đề hoặc bỏ sót thông tin quan trọng.
                                    * **Coherence & Cohesion:** Lộn xộn, không chia đoạn.
                                    * **Lexical Resource:** Lặp từ, từ cơ bản.
                                    * **Grammar:** Lỗi sai dày đặc.
                                    
                                * **BAND 5 (Modest):**
                                    * **Task Achievement:** Kể lể chi tiết máy móc, KHÔNG CÓ Overview rõ ràng. Số liệu có thể sai.
                                    * **Coherence & Cohesion:** Thiếu mạch lạc, lạm dụng/thiếu từ nối.
                                    * **Lexical Resource:** Hạn chế, sai chính tả gây khó hiểu.
                                    * **Grammar:** Chỉ dùng được câu đơn, cố dùng câu phức là sai.

                                * **BAND 6 (Competent):**
                                    * **Task Achievement:** Có Overview nhưng thông tin chưa chọn lọc kỹ. Chi tiết đôi khi không liên quan.
                                    * **Coherence & Cohesion:** Có liên kết nhưng máy móc hoặc lỗi kết nối.
                                    * **Lexical Resource:** Đủ dùng, cố dùng từ khó nhưng hay sai ngữ cảnh.
                                    * **Grammar:** Kết hợp đơn/phức, lỗi ngữ pháp xuất hiện thường xuyên.
                                    
                                * **BAND 7 (Good):**
                                    * **Task Achievement:** Overview rõ ràng. Xu hướng chính được trình bày nhưng có thể chưa phát triển đầy đủ.
                                    * **Coherence & Cohesion:** Có tổ chức logic, dùng từ nối tốt dù đôi khi máy móc.
                                    * **Lexical Resource:** Dùng tốt từ vựng chủ đề/Collocations, sai sót nhỏ.
                                    * **Grammar:** Thường xuyên viết được câu phức không lỗi.

                                * **BAND 8 (Very Good):**
                                    * **Task Achievement:** Overview rõ ràng, làm nổi bật đặc điểm chính. Số liệu dẫn chứng đầy đủ, logic.
                                    * **Coherence & Cohesion:** Sắp xếp logic, chia đoạn hợp lý.
                                    * **Lexical Resource:** Vốn từ rộng, chính xác, rất ít lỗi.
                                    * **Grammar:** Đa số câu không lỗi, dùng linh hoạt câu phức.
                                    
                                * **BAND 9 (Expert):**
                                    * **Task Achievement:** Đáp ứng trọn vẹn yêu cầu, Overview sắc sảo, dữ liệu chọn lọc tinh tế.
                                    * **Coherence & Cohesion:** Mạch lạc hoàn hảo, tính liên kết không tì vết.
                                    * **Lexical Resource:** Từ vựng tự nhiên như người bản xứ, chính xác tuyệt đối.
                                    * **Grammar:** Cấu trúc đa dạng, hoàn toàn chính xác.

                                ## OUTPUT: JSON STRICTLY.
                                {{
                                    "TA": int, "CC": int, "LR": int, "GRA": int,
                                    "Overall": float,
                                    "Feedback": "Nhận xét chi tiết bằng Tiếng Việt (Markdown). Cấu trúc linh hoạt nhưng cần đi qua từng tiêu chí (Task Response, Coherence & Cohesion, Lexical Resource, Grammar). Ở mỗi tiêu chí, hãy chỉ ra các điểm cần cải thiện dựa trên rubric và đưa ra cách sửa cụ thể (ví dụ: trích dẫn câu gốc của học viên và viết lại câu mới tốt hơn)."
                                }}
                                """
                                res = call_gemini(prompt_t1, expect_json=True, image_data=image_b64)
                                if res:
                                    try:
                                        grade = json.loads(res)
                                        st.session_state['writing_result_t1'] = grade
                                        
                                        # Use .get() defensively in case AI forgets keys
                                        crit = json.dumps({
                                            "TA": grade.get('TA', grade.get('TR', 0)), 
                                            "CC": grade.get('CC', 0), 
                                            "LR": grade.get('LR', 0), 
                                            "GRA": grade.get('GRA', 0)
                                        })
                                        save_writing_log(user['name'], user['class'], lesson_w, "Task 1", grade.get('Overall', 0), crit, grade.get('Feedback', ''), mode=mode_w)
                                    except Exception as e:
                                        st.error(f"Lỗi chấm bài: {e}")
                                    else:
                                        st.rerun()

                # Hiện kết quả Task 1
                if 'writing_result_t1' in st.session_state:
                    res = st.session_state['writing_result_t1']
                    st.balloons()
                    st.success(f"OVERALL BAND: {res.get('Overall', 0)}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Task Achievement", extract_score(res.get('TA', res.get('TR', 0))))
                    c2.metric("Coherence", extract_score(res.get('CC', 0)))
                    c3.metric("Lexical", extract_score(res.get('LR', 0)))
                    c4.metric("Grammar", extract_score(res.get('GRA', 0)))
                    with st.container(border=True):
                        st.markdown(res.get('Feedback', ''))
                    if st.button("Làm lại Task 1"):
                        del st.session_state['writing_result_t1']
                        st.rerun()

            # --- LUỒNG TASK 2: 2 BƯỚC (OUTLINE -> WRITE) ---
            else:
                # --- PHẦN LÝ THUYẾT (EXPANDER) ---
                with st.expander("**CÁC LỖI TƯ DUY & CẤU TRÚC LOGIC (Đọc kỹ trước khi viết)**", expanded=False):
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

                # --- STEP 1: OUTLINE ---
                with st.expander("STEP 1: LẬP DÀN Ý & KIỂM TRA LOGIC", expanded=True):
                    st.markdown("### 📝 OUTLINE")
                    with st.form("outline_form"):
                        intro = st.text_area("Introduction:", height=80, placeholder="Paraphrase topic + Thesis statement")
                        body1 = st.text_area("Body 1 (PEER):", height=150, placeholder="Point -> Explanation -> Example -> Result")
                        body2 = st.text_area("Body 2 (PEER):", height=150, placeholder="Point -> Explanation -> Example -> Result")
                        conc = st.text_area("Conclusion:", height=80, placeholder="Restate opinion + Summary")
                        check_outline = st.form_submit_button("🔍 Kiểm Tra Logic Outline")
                    
                    if check_outline:
                        if intro and body1 and body2 and conc:
                            with st.spinner("Đang phân tích logic..."):
                                prompt = f"""
                                Role: IELTS Writing Examiner. Check Logic & Coherence for Task 2 Outline.
                                Topic: {data_w['question']}
                                Input Outline:
                                - Intro: {intro}
                                - Body 1: {body1}
                                - Body 2: {body2}
                                - Conclusion: {conc}

                                Task:
                                1. Analyze Logical Flow & Coherence.
                                2. Detect Logical Fallacies explicitly:
                                   - Hasty Generalization (Khái quát hóa vội vã)
                                   - Slippery Slope (Trượt dốc phi logic)
                                   - Circular Reasoning (Lập luận luẩn quẩn)
                                   - Other logical gaps.
                                3. Suggest at least 5 Academic Collocations based on the user's ideas to upgrade their vocabulary.

                                Output: Vietnamese Markdown. Focus on Logical Fallacies & Structure & Vocabulary Enhancement.
                                """
                                res = call_gemini(prompt)
                                if res:
                                    st.session_state['writing_feedback_data'] = res
                                    st.rerun()
                        else: st.warning("Điền đủ 4 phần.")

                    if st.session_state.get('writing_feedback_data'):
                        st.info("### Feedback Outline")
                        st.markdown(st.session_state['writing_feedback_data'])

                st.divider()
                
                # --- STEP 2: VIẾT BÀI ---
                st.subheader("STEP 2: VIẾT BÀI HOÀN CHỈNH")
                mode_w = st.radio("Chọn chế độ:", ["-- Chọn chế độ --", "Luyện Tập (Không giới hạn)", "Thi Thử (40 Phút)"], horizontal=True, key="w_task2_mode")

                if mode_w != "-- Chọn chế độ --":
                    if "Thi Thử" in mode_w:
                        timer_html = f"""
                        <div style="font-size: 24px; font-weight: bold; color: #d35400; font-family: 'Segoe UI', sans-serif; margin-bottom: 10px;">
                            ⏳ Thời gian Task 2: <span id="timer_w2">40:00</span>
                        </div>
                        <script>
                        var time = 40 * 60;
                        setInterval(function() {{
                            var m = Math.floor(time / 60);
                            var s = time % 60;
                            document.getElementById("timer_w2").innerHTML = m + ":" + (s < 10 ? "0" : "") + s;
                            time--;
                        }}, 1000);
                        </script>
                        """
                        components.html(timer_html, height=50)

                    essay = st.text_area("Bài làm Task 2 (Min 250 words):", height=400, key="essay_t2")
                    
                    if st.button("Nộp Bài Task 2"):
                        if len(essay.split()) < 50: st.warning("Bài viết quá ngắn.")
                        else:
                            with st.spinner("Đang chấm điểm Task 2..."):
                                prompt_t2 = f"""
                                ## ROLE: Senior IELTS Examiner (Strict but Natural).
                                ## TASK: Assess IELTS Writing Task 2 and provide deep, insightful, strict feedback in a natural, conversational tone like a real teacher.
                                ## CRITICAL RULE 1: The ENTIRE "Feedback" string MUST be written in 100% Vietnamese (Tiếng Việt). DO NOT mix English and Vietnamese in your explanation. Only use English when quoting the student's text.
                                ## CRITICAL RULE 2 (INDEPENDENT & WHOLE NUMBER SCORING): DO NOT give flat, identical scores across all 4 criteria. You MUST evaluate EACH criterion completely independently. MOREOVER, individual criteria (TR, CC, LR, GRA) MUST be WHOLE NUMBERS ONLY (e.g., 5.0, 6.0, 7.0, 8.0). DO NOT give half bands (like 6.5 or 5.5) for individual criteria. ONLY the Overall score can be a half band (e.g., 6.5) calculated by averaging the 4 criteria. Reflect a realistic spiky profile.
                                ## CRITICAL RULE 3 (JSON SAFE): YOU MUST NOT use unescaped double quotes (\") inside the Feedback text. ALWAYS use single quotes (') for quoting words or sentences to avoid breaking the JSON format.
                                ## TOPIC: {data_w['question']}
                                ## ESSAY: {essay}
                                ## RUBRIC (TASK 2):
                                * **BAND 4 (Limited):**
                                    * **Task Response:** Lạc đề hoặc quan điểm không rõ ràng.
                                    * **Coherence & Cohesion:** Sắp xếp lộn xộn, không chia đoạn.
                                    * **Lexical Resource:** Vốn từ nghèo nàn, lặp từ nhiều.
                                    * **Grammar:** Lỗi sai dày đặc, khó hiểu.

                                * **BAND 5 (Modest):**
                                    * **Task Response:** Trả lời một phần yêu cầu, lập luận chưa đầy đủ.
                                    * **Coherence & Cohesion:** Có chia đoạn nhưng thiếu mạch lạc, từ nối máy móc.
                                    * **Lexical Resource:** Vốn từ hạn chế, lỗi chính tả gây khó đọc.
                                    * **Grammar:** Cố dùng câu phức nhưng sai nhiều.

                                * **BAND 6 (Competent):**
                                    * **Task Response:** Trả lời đầy đủ các phần, quan điểm rõ ràng nhưng phát triển ý chưa sâu.
                                    * **Coherence & Cohesion:** Mạch lạc, có sự phát triển ý, nhưng liên kết câu đôi khi bị lỗi.
                                    * **Lexical Resource:** Đủ dùng, cố gắng dùng từ ít phổ biến nhưng đôi khi sai ngữ cảnh.
                                    * **Grammar:** Kết hợp câu đơn và câu phức, vẫn còn lỗi sai nhưng không gây hiểu lầm.

                                * **BAND 7 (Good):**
                                    * **Task Response:** Giải quyết trọn vẹn yêu cầu, quan điểm xuyên suốt, ý chính được mở rộng.
                                    * **Coherence & Cohesion:** Tổ chức logic, sử dụng từ nối linh hoạt.
                                    * **Lexical Resource:** Sử dụng từ vựng linh hoạt, có ý thức về phong cách và Collocation.
                                    * **Grammar:** Nhiều câu không có lỗi, kiểm soát tốt ngữ pháp và dấu câu.

                                * **BAND 8 (Very Good):**
                                    * **Task Response:** Câu trả lời phát triển đầy đủ, ý tưởng sâu sắc.
                                    * **Coherence & Cohesion:** Sắp xếp thông tin và ý tưởng một cách logic, mạch lạc tự nhiên.
                                    * **Lexical Resource:** Vốn từ phong phú, sử dụng chính xác và tự nhiên.
                                    * **Grammar:** Đa dạng cấu trúc, hầu như không có lỗi.

                                * **BAND 9 (Expert):**
                                    * **Task Response:** Đáp ứng trọn vẹn yêu cầu, lập luận sắc bén, thuyết phục hoàn toàn.
                                    * **Coherence & Cohesion:** Mạch lạc hoàn hảo, tính liên kết không tì vết.
                                    * **Lexical Resource:** Từ vựng tinh tế, tự nhiên như người bản xứ.
                                    * **Grammar:** Hoàn toàn chính xác, cấu trúc đa dạng và phức tạp.
                                ## OUTPUT: JSON STRICTLY.
                                {{
                                    "TA": int, "CC": int, "LR": int, "GRA": int,
                                    "Overall": float,
                                    "Feedback": "### 🎯 Nhận xét tổng quan\\n[Viết 1 đoạn văn tự nhiên (khoảng 2-3 câu) tóm tắt điểm mạnh và điểm yếu cốt lõi trong lập luận và ngôn ngữ của bài.]\\n\\n### 📝 Phân tích chi tiết\\n\\n**1. Task Response:**\\n[Viết đoạn văn phân tích độ sâu của lập luận. Hãy khen điểm tốt, sau đó chỉ ra cụ thể chỗ nào thiếu logic, ví dụ chưa thuyết phục. Bắt buộc trích dẫn lại ý của học viên và hướng dẫn cách đào sâu hơn theo mô hình PEER.]\\n\\n**2. Coherence & Cohesion:**\\n[Viết đoạn văn nhận xét sự mạch lạc. Chỉ ra đoạn nào dùng sai từ nối hoặc nhảy ý. Trích câu gốc và lồng ghép cách viết lại uyển chuyển hơn vào trong đoạn văn.]\\n\\n**3. Lexical Resource:**\\n[Viết đoạn văn đánh giá vốn từ. Để nâng band cho học viên, BẮT BUỘC chọn ra ít nhất 3 từ/cụm từ kém tự nhiên trong bài, trích dẫn lại và lồng ghép đề xuất nâng cấp (Band 7/8+) kèm giải thích ngắn gọn ngay trong đoạn văn nhận xét (không dùng bullet point cứng nhắc).]\\n\\n**4. Grammatical Range & Accuracy:**\\n[Viết đoạn văn đánh giá ngữ pháp. BẮT BUỘC trích dẫn ít nhất 3 câu sai hoặc quá đơn điệu từ bài làm, sau đó hướng dẫn học viên cách sửa hoặc gộp thành câu phức tinh tế hơn bằng văn phong của một giáo viên đang chữa bài.]"
                                }}
                                """
                                res = call_gemini(prompt_t2, expect_json=True)
                                if res:
                                    try:
                                        grade = json.loads(res)
                                        st.session_state['writing_result_t2'] = grade
                                        
                                        # Use .get() defensively in case AI forgets keys
                                        crit = json.dumps({
                                            "TR": grade.get('TR', grade.get('TA', 0)), 
                                            "CC": grade.get('CC', 0), 
                                            "LR": grade.get('LR', 0), 
                                            "GRA": grade.get('GRA', 0)
                                        })
                                        save_writing_log(user['name'], user['class'], lesson_w, "Task 2", grade.get('Overall', 0), crit, grade.get('Feedback', ''), mode=mode_w)
                                    except Exception as e:
                                        st.error(f"Lỗi chấm bài: {e}")
                                    else:
                                        st.rerun()

                # Hiện kết quả Task 2
                if 'writing_result_t2' in st.session_state:
                    res = st.session_state['writing_result_t2']
                    st.balloons()
                    st.success(f"OVERALL BAND: {res.get('Overall', 0)}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Task Response", extract_score(res.get('TR', res.get('TA', 0))))
                    c2.metric("Coherence", extract_score(res.get('CC', 0)))
                    c3.metric("Lexical", extract_score(res.get('LR', 0)))
                    c4.metric("Grammar", extract_score(res.get('GRA', 0)))
                    with st.container(border=True):
                        st.markdown(res.get('Feedback', ''))
                    if st.button("Làm lại Task 2"):
                        del st.session_state['writing_result_t2']
                        st.rerun()

        else: st.warning("Bài này chưa mở.")
    
    # --- MODULE 1: SPEAKING ---
    elif menu == "🗣️ Speaking":
        st.title("Luyện Tập Speaking")
        tab_class, tab_forecast = st.tabs(["Bài Tập Trên Lớp", "Luyện Đề Forecast Q1/2026"])
        
        with tab_class:
            col1, col2 = st.columns([1, 2])
            with col1:
                lesson_choice = st.selectbox("Chọn bài học:", current_speaking_menu, key="class_lesson")
            
            if "(Chưa có bài tập)" in lesson_choice:
                st.info("Bài này chưa được giao.")
            elif lesson_choice in SPEAKING_CONTENT:
                with col2:
                    q_list = SPEAKING_CONTENT[lesson_choice]
                    question = st.selectbox("Câu hỏi:", q_list, key="class_q")
                
                attempts = st.session_state['speaking_attempts'].get(question, 0)
                remaining = 5 - attempts
                
                st.markdown(f"**Topic:** {question}")
                
                # Cấu trúc lưu trữ trạng thái cho từng câu hỏi
                state_key = f"proc_class_{question}"
                if state_key not in st.session_state: 
                    st.session_state[state_key] = {"sig": None, "result": None, "audio_bytes": None, "audio_b64": None}
                proc = st.session_state[state_key]

                # --- LƯU TRỮ PROMPT GỐC ĐỂ DÙNG CHUNG CHO LẦN ĐẦU & RETRY ---
                prompt_class = f"""
                                Role: Senior IELTS Speaking Examiner.
                        
                                Task: Assess speaking response for "{question}" based strictly on the rubric with encouraging tone.
                                **🚨 CRITICAL INSTRUCTION FOR TRANSCRIPT (QUAN TRỌNG NHẤT):**
                                1. **VERBATIM TRANSCRIPTION:** You must write EXACTLY what you hear, sound-by-sound.
                                2. **NO AUTO-CORRECT:** Do NOT fix grammar or pronunciation errors. 
                                   - If the user says "I go school" (missing 'to'), WRITE "I go school".
                                   - If the user mispronounces "think" as "sink", WRITE "sink" (or "tink").
                                   - If the user misses final sounds (e.g., "five" -> "fi"), WRITE "fi".
                                3. The transcript MUST reflect the raw performance so the user can see their mistakes.

                                ## GRADING RUBRIC (TIÊU CHÍ PHÂN LOẠI CỐT LÕI):

                                * **BAND 4 (Hạn chế):**
                                * **Fluency:** Câu cụt, ngắt quãng dài, nói còn dang dở.
                                * **Vocab:** Vốn từ rất hạn chế, lặp lại thường xuyên, chỉ dùng từ đơn lẻ.
                                * **Grammar:** Không biết chia thì quá khứ, sai lỗi hòa hợp chủ ngữ - động từ nghiêm trọng.
                                * **Pronunciation:** Khó hiểu. Transcript gãy vụn, chứa nhiều từ không liên quan đến chủ đề.

                                * **BAND 5 (Trung bình):**
                                * **Fluency:** Nói khá ngắn, Ngắt quãng nhiều, lặp từ.
                                * **Vocab:** Vốn từ đủ dùng cho chủ đề quen thuộc nhưng hạn chế, khó diễn đạt ý phức tạp.
                                * **Grammar:** Hầu như chỉ dùng câu đơn. Thường xuyên quên chia thì quá khứ và sai hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Có nhiều từ vô nghĩa, không hợp ngữ cảnh *(Dấu hiệu nhận biết: Transcript thường xuyên xuất hiện các từ vô nghĩa hoặc sai hoàn toàn ngữ cảnh do máy không nhận diện được âm, và trừ điểm).*

                                * **BAND 6 (Khá):**
                                * **Fluency:** Nói dài, Khá trôi chảy, nhưng đôi khi mất mạch lạc, từ nối máy móc.
                                * **Vocab:** Đủ để bàn luận, biết Paraphrase.
                                * **Grammar:** Có dùng câu phức nhưng thường xuyên sai. Chia thì quá khứ chưa đều, còn lỗi hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Rõ ràng phần lớn thời gian. *(Lưu ý: Nếu thấy từ vựng bị biến đổi thành từ khác nghe na ná - Sound-alike words - hoặc 1-2 đoạn vô nghĩa, hãy đánh dấu là Lỗi Phát Âm và trừ điểm).*

                                * **BAND 7 (Tốt):**
                                * **Fluency:** Nói dài dễ dàng, khai thác sâu. Từ nối linh hoạt.
                                * **Vocab:** Dùng được Collocation tự nhiên.
                                * **Grammar:** Thường xuyên có câu phức không lỗi. Kiểm soát tốt thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu. *(Lưu ý: Chấp nhận một vài lỗi nhỏ, nhưng nếu Transcript xuất hiện từ lạ/sai ngữ cảnh, hãy trừ điểm).*

                                * **BAND 8 (Rất tốt):**
                                * **Fluency:** Mạch lạc, hiếm khi lặp lại.
                                * **Vocab:** Dùng điêu luyện Idioms/từ hiếm.
                                * **Grammar:** Hoàn toàn chính xác về thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu xuyên suốt. Ngữ điệu tốt. Transcript chính xác 99%.

                                * **BAND 9 (Native-like):**
                                * **Fluency:** Trôi chảy tự nhiên, không hề vấp váp.
                                * **Vocab:** Chính xác tuyệt đối, tinh tế.
                                * **Grammar:** Ngữ pháp và thì hoàn hảo tuyệt đối.
                                * **Pronunciation:** Hoàn hảo. Transcript sạch bóng, không có bất kỳ từ nào sai ngữ cảnh hay vô nghĩa.

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
                if remaining > 0:
                    st.info(f"⚡ Bạn còn **{remaining}** lượt trả lời cho câu này.")
                    audio = st.audio_input("Ghi âm câu trả lời:", key=f"rec_class_{question}")
                    
                    if audio:
                        audio_bytes = audio.read()
                        audio_sig = hash(audio_bytes)
                        
                        # Khi phát hiện người dùng thu âm FILE MỚI
                        if proc["sig"] != audio_sig:
                            if len(audio_bytes) < 1000: 
                                st.warning("File quá ngắn.")
                            else:
                                proc["sig"] = audio_sig
                                proc["audio_bytes"] = audio_bytes
                                proc["audio_b64"] = base64.b64encode(audio_bytes).decode('utf-8')
                                proc["result"] = None # Reset kết quả cũ
                                
                                with st.spinner("Đang chấm điểm..."):
                                    text_result = call_gemini(prompt_class, audio_data=proc["audio_b64"])
                                    if text_result:
                                        proc["result"] = text_result
                                        st.session_state['speaking_attempts'][question] = attempts + 1
                                        save_speaking_log(user['name'], user['class'], lesson_choice, question, text_result)
                                        st.rerun()

                    # NẾU ĐÃ CÓ AUDIO TRONG BỘ NHỚ -> HIỂN THỊ NÚT CHẤM LẠI
                    if proc["audio_bytes"]:
                        col_retry, _ = st.columns([1, 3])
                        with col_retry:
                            if st.button("🔄 Chấm lại (Không trừ lượt)", key=f"retry_class_{question}"):
                                with st.spinner("Đang chấm lại..."):
                                    text_result = call_gemini(prompt_class, audio_data=proc["audio_b64"])
                                    if text_result:
                                        proc["result"] = text_result
                                        save_speaking_log(user['name'], user['class'], lesson_choice, question, text_result)
                                        st.rerun()
                                    else:
                                        st.error("Lỗi API hoặc mạng. Vui lòng thử lại lần nữa.")

                    # HIỂN THỊ KẾT QUẢ
                    if proc["result"]: 
                        st.markdown(proc["result"])
                    elif proc["audio_bytes"] and not proc["result"]:
                        st.error("Chưa có kết quả hoặc hệ thống trả về lỗi rỗng. Vui lòng nhấn nút **🔄 Chấm lại** ở trên.")

                else: 
                    st.warning("Hết lượt trả lời cho câu này.")
            else: 
                st.info("Chưa có bài.")

        # === TAB 2: FORECAST & LUYỆN TẬP (MỚI) ===
        with tab_forecast:
            # Chọn Phần thi: Part 1, Part 2, Part 3
            part_mode = st.radio("Chọn phần thi:", ["Part 1", "Part 2", "Part 3"], horizontal=True)
            
            # --- LOGIC PART 1 ---
            if part_mode == "Part 1":
                topic_p1 = st.selectbox("Chọn chủ đề (Part 1):", list(FORECAST_PART1.keys()))
                q_p1 = st.selectbox("Câu hỏi:", FORECAST_PART1[topic_p1])
                st.write(f"**Question:** {q_p1}")
                
                audio_fc = st.audio_input("Trả lời:", key=f"rec_fc_p1_{q_p1}")
                if audio_fc:
                    # Tái sử dụng logic chấm điểm
                    audio_fc.seek(0)
                    audio_bytes_fc = audio_fc.read()
                    if len(audio_bytes_fc) < 1000: st.warning("File quá ngắn.")
                    else:
                        with st.spinner("Đang chấm điểm"):
                            audio_b64_fc = base64.b64encode(audio_bytes_fc).decode('utf-8')
                                
                            prompt_full= f"""Role: Examiner. Assess IELTS Speaking Part 1 about "{q_p1}". Transcript EXACTLY what user said (no auto-correct). Give Band Score & Feedback, encouraging tone.
                                ## GRADING RUBRIC (TIÊU CHÍ PHÂN LOẠI CỐT LÕI):

                                * **BAND 4 (Hạn chế):**
                                * **Fluency:** Câu cụt, ngắt quãng dài, nói còn dang dở.
                                * **Vocab:** Vốn từ rất hạn chế, lặp lại thường xuyên, chỉ dùng từ đơn lẻ.
                                * **Grammar:** Không biết chia thì quá khứ, sai lỗi hòa hợp chủ ngữ - động từ nghiêm trọng.
                                * **Pronunciation:** Khó hiểu. Transcript gãy vụn, chứa nhiều từ không liên quan đến chủ đề.

                                * **BAND 5 (Trung bình):**
                                * **Fluency:** Nói khá ngắn, Ngắt quãng nhiều, lặp từ.
                                * **Vocab:** Vốn từ đủ dùng cho chủ đề quen thuộc nhưng hạn chế, khó diễn đạt ý phức tạp.
                                * **Grammar:** Hầu như chỉ dùng câu đơn. Thường xuyên quên chia thì quá khứ và sai hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Có nhiều từ vô nghĩa, không hợp ngữ cảnh *(Dấu hiệu nhận biết: Transcript thường xuyên xuất hiện các từ vô nghĩa hoặc sai hoàn toàn ngữ cảnh do máy không nhận diện được âm, và trừ điểm).*

                                * **BAND 6 (Khá):**
                                * **Fluency:** Nói dài, Khá trôi chảy, nhưng đôi khi mất mạch lạc, từ nối máy móc.
                                * **Vocab:** Đủ để bàn luận, biết Paraphrase.
                                * **Grammar:** Có dùng câu phức nhưng thường xuyên sai. Chia thì quá khứ chưa đều, còn lỗi hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Rõ ràng phần lớn thời gian. *(Lưu ý: Nếu thấy từ vựng bị biến đổi thành từ khác nghe na ná - Sound-alike words - hoặc 1-2 đoạn vô nghĩa, hãy đánh dấu là Lỗi Phát Âm và trừ điểm).*

                                * **BAND 7 (Tốt):**
                                * **Fluency:** Nói dài dễ dàng, khai thác sâu. Từ nối linh hoạt.
                                * **Vocab:** Dùng được Collocation tự nhiên.
                                * **Grammar:** Thường xuyên có câu phức không lỗi. Kiểm soát tốt thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu. *(Lưu ý: Chấp nhận một vài lỗi nhỏ, nhưng nếu Transcript xuất hiện từ lạ/sai ngữ cảnh, hãy trừ điểm).*

                                * **BAND 8 (Rất tốt):**
                                * **Fluency:** Mạch lạc, hiếm khi lặp lại.
                                * **Vocab:** Dùng điêu luyện Idioms/từ hiếm.
                                * **Grammar:** Hoàn toàn chính xác về thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu xuyên suốt. Ngữ điệu tốt. Transcript chính xác 99%.

                                * **BAND 9 (Native-like):**
                                * **Fluency:** Trôi chảy tự nhiên, không hề vấp váp.
                                * **Vocab:** Chính xác tuyệt đối, tinh tế.
                                * **Grammar:** Ngữ pháp và thì hoàn hảo tuyệt đối.
                                * **Pronunciation:** Hoàn hảo. Transcript sạch bóng, không có bất kỳ từ nào sai ngữ cảnh hay vô nghĩa.
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
                            res = call_gemini(prompt_full, audio_data=audio_b64_fc)
                            if res: st.markdown(res)

            # --- LOGIC PART 2 ---
            elif part_mode == "Part 2":
                # Lấy danh sách Topic từ FORECAST_PART23 keys
                topic_p2 = st.selectbox("Chọn đề bài (Describe a/an...):", list(FORECAST_PART23.keys()))
                data_p2 = FORECAST_PART23[topic_p2]
                
                st.info(f"**Cue Card:**\n\n{data_p2['cue_card']}")
                st.write("⏱️ Bạn có 1 phút chuẩn bị và 2 phút nói.")
                
                if st.button("Bắt đầu 1 phút chuẩn bị", key="timer_p2"):
                    with st.empty():
                        for i in range(60, 0, -1):
                            st.write(f"⏳ Thời gian chuẩn bị: {i}s")
                            time.sleep(1)
                        st.write("⌛ Hết giờ chuẩn bị! Hãy ghi âm ngay.")

                audio_fc_p2 = st.audio_input("Trả lời Part 2:", key=f"rec_fc_p2_{topic_p2}")
                if audio_fc_p2:
                    audio_fc_p2.seek(0)
                    audio_bytes_p2 = audio_fc_p2.read()
                    if len(audio_bytes_p2) < 1000: st.warning("File quá ngắn.")
                    else:
                        with st.spinner("Đang chấm điểm"):
                            audio_b64_p2 = base64.b64encode(audio_bytes_p2).decode('utf-8')
                            
                            # PROMPT FULL COPY
                            prompt_full_p2 = f"""Role: Examiner. Assess IELTS Speaking response for Part 2 "{data_p2['cue_card']}". Transcript EXACTLY what user said (no auto-correct). Give Band Score & Feedback, encouraging tone.
                                ## GRADING RUBRIC (TIÊU CHÍ PHÂN LOẠI CỐT LÕI):

                                * **BAND 4 (Hạn chế):**
                                * **Fluency:** Câu cụt, ngắt quãng dài, nói còn dang dở.
                                * **Vocab:** Vốn từ rất hạn chế, lặp lại thường xuyên, chỉ dùng từ đơn lẻ.
                                * **Grammar:** Không biết chia thì quá khứ, sai lỗi hòa hợp chủ ngữ - động từ nghiêm trọng.
                                * **Pronunciation:** Khó hiểu. Transcript gãy vụn, chứa nhiều từ không liên quan đến chủ đề.

                                * **BAND 5 (Trung bình):**
                                * **Fluency:** Nói khá ngắn, Ngắt quãng nhiều, lặp từ.
                                * **Vocab:** Vốn từ đủ dùng cho chủ đề quen thuộc nhưng hạn chế, khó diễn đạt ý phức tạp.
                                * **Grammar:** Hầu như chỉ dùng câu đơn. Thường xuyên quên chia thì quá khứ và sai hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Có nhiều từ vô nghĩa, không hợp ngữ cảnh *(Dấu hiệu nhận biết: Transcript thường xuyên xuất hiện các từ vô nghĩa hoặc sai hoàn toàn ngữ cảnh do máy không nhận diện được âm, và trừ điểm).*

                                * **BAND 6 (Khá):**
                                * **Fluency:** Nói dài, Khá trôi chảy, nhưng đôi khi mất mạch lạc, từ nối máy móc.
                                * **Vocab:** Đủ để bàn luận, biết Paraphrase.
                                * **Grammar:** Có dùng câu phức nhưng thường xuyên sai. Chia thì quá khứ chưa đều, còn lỗi hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Rõ ràng phần lớn thời gian. *(Lưu ý: Nếu thấy từ vựng bị biến đổi thành từ khác nghe na ná - Sound-alike words - hoặc 1-2 đoạn vô nghĩa, hãy đánh dấu là Lỗi Phát Âm và trừ điểm).*

                                * **BAND 7 (Tốt):**
                                * **Fluency:** Nói dài dễ dàng, khai thác sâu. Từ nối linh hoạt.
                                * **Vocab:** Dùng được Collocation tự nhiên.
                                * **Grammar:** Thường xuyên có câu phức không lỗi. Kiểm soát tốt thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu. *(Lưu ý: Chấp nhận một vài lỗi nhỏ, nhưng nếu Transcript xuất hiện từ lạ/sai ngữ cảnh, hãy trừ điểm).*

                                * **BAND 8 (Rất tốt):**
                                * **Fluency:** Mạch lạc, hiếm khi lặp lại.
                                * **Vocab:** Dùng điêu luyện Idioms/từ hiếm.
                                * **Grammar:** Hoàn toàn chính xác về thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu xuyên suốt. Ngữ điệu tốt. Transcript chính xác 99%.

                                * **BAND 9 (Native-like):**
                                * **Fluency:** Trôi chảy tự nhiên, không hề vấp váp.
                                * **Vocab:** Chính xác tuyệt đối, tinh tế.
                                * **Grammar:** Ngữ pháp và thì hoàn hảo tuyệt đối.
                                * **Pronunciation:** Hoàn hảo. Transcript sạch bóng, không có bất kỳ từ nào sai ngữ cảnh hay vô nghĩa.
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
                            res = call_gemini(prompt_full_p2, audio_data=audio_b64_p2)
                            if res: st.markdown(res)
            # --- LOGIC PART 3 ---
            else:
                topic_p3 = st.selectbox("Chọn chủ đề (Part 3):", list(FORECAST_PART23.keys()))
                data_p3 = FORECAST_PART23[topic_p3]
                
                # Đã thêm phần chọn câu hỏi cho Part 3
                q_p3 = st.selectbox("Chọn câu hỏi:", data_p3['part3'])
                st.write(f"**Question:** {q_p3}")
                
                audio_fc_p3 = st.audio_input("Trả lời:", key=f"rec_fc_p3_{topic_p3}_{q_p3}")
                if audio_fc_p3:
                    audio_fc_p3.seek(0)
                    audio_bytes_p3 = audio_fc_p3.read()
                    if len(audio_bytes_p3) < 1000: st.warning("File quá ngắn.")
                    else:
                        with st.spinner("Đang chấm điểm"):
                            audio_b64_p3 = base64.b64encode(audio_bytes_p3).decode('utf-8')
                            
                            # PROMPT FULL COPY
                            prompt_full_p3 = f"""Role: Examiner. Assess IELTS Speaking response for Part 3 "{data_p3['part3']}". Transcript EXACTLY what user said (no auto-correct). Give Band Score & Feedback, encouraging tone.
                                ## GRADING RUBRIC (TIÊU CHÍ PHÂN LOẠI CỐT LÕI):

                                * **BAND 4 (Hạn chế):**
                                * **Fluency:** Câu cụt, ngắt quãng dài, nói còn dang dở.
                                * **Vocab:** Vốn từ rất hạn chế, lặp lại thường xuyên, chỉ dùng từ đơn lẻ.
                                * **Grammar:** Không biết chia thì quá khứ, sai lỗi hòa hợp chủ ngữ - động từ nghiêm trọng.
                                * **Pronunciation:** Khó hiểu. Transcript gãy vụn, chứa nhiều từ không liên quan đến chủ đề.

                                * **BAND 5 (Trung bình):**
                                * **Fluency:** Nói khá ngắn, Ngắt quãng nhiều, lặp từ.
                                * **Vocab:** Vốn từ đủ dùng cho chủ đề quen thuộc nhưng hạn chế, khó diễn đạt ý phức tạp.
                                * **Grammar:** Hầu như chỉ dùng câu đơn. Thường xuyên quên chia thì quá khứ và sai hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Có nhiều từ vô nghĩa, không hợp ngữ cảnh *(Dấu hiệu nhận biết: Transcript thường xuyên xuất hiện các từ vô nghĩa hoặc sai hoàn toàn ngữ cảnh do máy không nhận diện được âm, và trừ điểm).*

                                * **BAND 6 (Khá):**
                                * **Fluency:** Nói dài, Khá trôi chảy, nhưng đôi khi mất mạch lạc, từ nối máy móc.
                                * **Vocab:** Đủ để bàn luận, biết Paraphrase.
                                * **Grammar:** Có dùng câu phức nhưng thường xuyên sai. Chia thì quá khứ chưa đều, còn lỗi hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Rõ ràng phần lớn thời gian. *(Lưu ý: Nếu thấy từ vựng bị biến đổi thành từ khác nghe na ná - Sound-alike words - hoặc 1-2 đoạn vô nghĩa, hãy đánh dấu là Lỗi Phát Âm và trừ điểm).*

                                * **BAND 7 (Tốt):**
                                * **Fluency:** Nói dài dễ dàng, khai thác sâu. Từ nối linh hoạt.
                                * **Vocab:** Dùng được Collocation tự nhiên.
                                * **Grammar:** Thường xuyên có câu phức không lỗi. Kiểm soát tốt thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu. *(Lưu ý: Chấp nhận một vài lỗi nhỏ, nhưng nếu Transcript xuất hiện từ lạ/sai ngữ cảnh, hãy trừ điểm).*

                                * **BAND 8 (Rất tốt):**
                                * **Fluency:** Mạch lạc, hiếm khi lặp lại.
                                * **Vocab:** Dùng điêu luyện Idioms/từ hiếm.
                                * **Grammar:** Hoàn toàn chính xác về thì quá khứ và hòa hợp chủ ngữ - động từ.
                                * **Pronunciation:** Dễ hiểu xuyên suốt. Ngữ điệu tốt. Transcript chính xác 99%.

                                * **BAND 9 (Native-like):**
                                * **Fluency:** Trôi chảy tự nhiên, không hề vấp váp.
                                * **Vocab:** Chính xác tuyệt đối, tinh tế.
                                * **Grammar:** Ngữ pháp và thì hoàn hảo tuyệt đối.
                                * **Pronunciation:** Hoàn hảo. Transcript sạch bóng, không có bất kỳ từ nào sai ngữ cảnh hay vô nghĩa.
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
                            res = call_gemini(prompt_full_p3, audio_data=audio_b64_p3)
                            if res: st.markdown(res)

    # --- MODULE 2: READING ---
    elif menu == "📖 Reading":
        st.title("📖 Luyện Reading")
        
        # --- MENU READING CHUẨN XÁC ---
        lesson_choice = st.selectbox("Chọn bài đọc:", current_reading_menu)
        
        # Xử lý khi chọn vào mục "Chưa có bài tập"
        if "(Chưa có bài tập)" in lesson_choice:
            st.info("Bài này chưa được giao.")
            st.stop() # Dừng xử lý bên dưới
        
        # Reset session khi đổi bài
        if 'current_reading_lesson' not in st.session_state or st.session_state['current_reading_lesson'] != lesson_choice:
            st.session_state['current_reading_lesson'] = lesson_choice
            st.session_state['reading_session'] = {'status': 'intro', 'mode': None, 'end_time': None}

        if lesson_choice in READING_CONTENT:
            data = READING_CONTENT[lesson_choice]
            
            tab1, tab2 = st.tabs(["Làm Bài Đọc Hiểu", "Bài Tập Từ Vựng AI"])
            
            # TAB 1: BÀI ĐỌC CHÍNH (Split View)
            with tab1:
                # --- TRẠNG THÁI 1: GIỚI THIỆU & CHỌN CHẾ ĐỘ ---
                if st.session_state['reading_session']['status'] == 'intro':
                    st.info(f"### {data['title']}")
                    
                    # LOGIC INTRO CỐ ĐỊNH
                    intro_text = ""
                    # 1. Lesson 2 
                    if "Lesson 2" in lesson_choice and user['class'].startswith("PLA"):
                         intro_text = "Thời chưa có vệ tinh, các thủy thủ rất sợ đi biển xa vì họ không biết mình đang ở đâu. Cách duy nhất để xác định vị trí là phải biết giờ chính xác. Nhưng khổ nỗi, đồng hồ quả lắc ngày xưa cứ mang lên tàu rung lắc là chạy sai hết. Bài này kể về hành trình chế tạo ra chiếc đồng hồ đi biển đầu tiên, thứ đã cứu mạng hàng ngàn thủy thủ."
                    # 2. Lesson 3
                    if "Lesson 3" in lesson_choice:
                         intro_text = "Làm nông nghiệp ở Úc khó hơn nhiều so với ở Anh hay châu Âu vì đất đai ở đây rất khô và thiếu dinh dưỡng. Vào cuối thế kỷ 19, những người nông dân Úc đứng trước nguy cơ phá sản vì các phương pháp canh tác cũ không còn hiệu quả.\nBài đọc này sẽ cho các bạn thấy họ đã xoay sở như thế nào bằng công nghệ. Từ việc chế tạo ra chiếc cày đặc biệt có thể tự 'nhảy' qua gốc cây, cho đến việc lai tạo giống lúa mì chịu hạn. Chính những sáng kiến này đã biến nước Úc từ một nơi chỉ nuôi cừu thành một cường quốc xuất khẩu lúa mì thế giới."
                    elif "Lesson 4" in lesson_choice:
                        intro_text = "Cùng khám phá thế giới động vật hoang dã độc đáo của Úc vào 1 triệu năm trước thời kỷ Pleistocene - kỷ nguyên của những loài thú có vú khổng lồ. Bài đọc sẽ đưa bạn tìm hiểu về sự biến mất bí ẩn của chúng và bài học về bảo vệ động vật ngày nay."
                    if intro_text:
                        st.markdown(f"**Giới thiệu về bài đọc:**\n\n{intro_text}")
                    
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
                elif st.session_state['reading_session']['status'] == 'doing':
                    # Xử lý Timer
                    timer_html = ""
                    if st.session_state['reading_session']['mode'] == 'exam':
                        end_time = st.session_state['reading_session']['end_time']
                        remaining_seconds = (end_time - datetime.now()).total_seconds()
                        
                        if remaining_seconds > 0:
                            # Javascript
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
                        # Hướng dẫn bôi đen highlight
                        st.caption("💡 **Mẹo:** Bôi đen văn bản để highlight nhanh. (Lưu ý: Highlight sẽ mất khi nộp bài).")

                        display_text = data['text']
                        # Xóa title
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
                                if "questions_fill" in data:
                                    st.markdown("**Questions: Fill in the blanks (NO MORE THAN TWO WORDS)**")
                                    for q in data['questions_fill']:
                                        st.markdown(f"<div class='question-text'>{q['q']}</div>", unsafe_allow_html=True)
                                        ans[q['id']] = st.text_input(f"Answer {q['id']}", label_visibility="collapsed")
                                        st.write("")
                                elif "questions_mc" in data:
                                    st.markdown("**Questions: Choose the correct option.**")
                                    for q in data['questions_mc']:
                                        st.markdown(f"<div class='question-text'><strong>{q['q']}</strong></div>", unsafe_allow_html=True)
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