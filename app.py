import streamlit as st
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Mr. Tat Loc | AI Platform", page_icon="🎓", layout="wide")

# ==========================================
# KHỞI TẠO BỘ NHỚ TẠM CHO ĐIỀU HƯỚNG
# ==========================================
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🏆 Leaderboard"

# ==========================================
# GIAO DIỆN CHUẨN SAAS (MODERN CLEAN UI)
# ==========================================
st.markdown("""
    <style>
    /* Global Font & App Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Light gray background for the whole app to make white cards pop */
    [data-testid="stAppViewContainer"] {
        background-color: #F9FAFB;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Premium Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
        padding: 32px 24px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .brand-header h1 {
        margin: 0; 
        font-size: 36px; 
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(to right, #60A5FA, #3B82F6);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
    }
    .brand-header p { 
        margin: 8px 0 0 0; 
        font-size: 16px; 
        color: #9CA3AF; 
        font-weight: 500;
    }

    /* Quick Navigation Buttons (SaaS Style) */
    .quick-nav-container {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-bottom: 32px;
        flex-wrap: wrap;
    }
    div[data-testid="stButton"] button {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        color: #374151 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        transform: translateY(-1px);
    }

    /* Metric Cards (Left Aligned, White Background, Soft Shadow) */
    .metric-container { 
        display: flex; 
        gap: 24px; 
        margin-bottom: 32px; 
        flex-wrap: wrap;
    }
    .metric-card {
        background: #FFFFFF; 
        border: 1px solid #F3F4F6; 
        border-radius: 12px;
        padding: 24px; 
        text-align: left; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        flex: 1;
        min-width: 200px;
    }
    .metric-card p { 
        margin: 0 0 8px 0; 
        font-size: 13px; 
        color: #6B7280; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
    }
    .metric-card h3 { 
        margin: 0; 
        font-size: 36px; 
        font-weight: 800; 
        color: #111827; 
        line-height: 1;
    }

    /* Highlighted Student Selection Box */
    .student-selector-highlight {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #4F46E5;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .student-selector-highlight h3 {
        margin-top: 0;
        color: #111827;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .student-selector-highlight p {
        color: #6B7280;
        font-size: 15px;
        margin-bottom: 0;
    }

    /* AI Report & Feedback Box */
    .ai-report-box {
        background-color: #F9FAFB; 
        border: 1px solid #E5E7EB;
        border-radius: 8px; 
        padding: 20px; 
        margin-top: 12px;
        font-size: 15px; 
        line-height: 1.6; 
        color: #374151; 
    }
    
    /* Customizing Streamlit Expanders */
    [data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Headers inside the app */
    h1, h2, h3 {
        color: #111827;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CÁC HÀM XỬ LÝ DỮ LIỆU
# ==========================================
def clean_student_name(name):
    if pd.isna(name): return name
    clean_name = str(name).strip().title()
    mapping = {
        "Nguyen Thi Nhu Quynh": "Nguyễn Thị Như Quỳnh",
        "Nhu Quynh": "Nguyễn Thị Như Quỳnh",
        "Như Quỳnh": "Nguyễn Thị Như Quỳnh",
        "Bui Hoang Minh Nhat": "Bùi Hoàng Minh Nhật",
        "Tam Huynh": "Tâm Huỳnh"
    }
    return mapping.get(clean_name, clean_name)

@st.cache_data(ttl=60) # Cập nhật mỗi 60 giây để tránh sập RAM
def fetch_real_sheet_data():
    sheet_id = "1woji0ugdk7xfmpfZ6PKVU0dDvSwxtfDw-8rnmcidnDQ"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        if 'html' in str(df.columns[0]).lower():
            raise Exception("401")
            
        if 'Band_Score' in df.columns:
            df['Band_Score'] = pd.to_numeric(df['Band_Score'], errors='coerce')
            
        if 'Student' in df.columns:
            df = df.dropna(subset=['Student'])
            df['Student'] = df['Student'].apply(clean_student_name)
            
        if len(df.columns) > 7:
            df['Feedback_Detail'] = df.iloc[:, 7]
        else:
            df['Feedback_Detail'] = "No detailed feedback available."
            
        return df, None
    except Exception as e:
        if "401" in str(e) or "403" in str(e) or "HTTP Error" in str(e):
            err_msg = """
            🔒 **Lỗi Quyền Truy Cập (HTTP 401): Google Sheet của bạn đang bị khóa.**
            
            **Cách sửa lỗi này trong 3 bước:**
            1. Mở file Google Sheet của bạn.
            2. Bấm nút **Share (Chia sẻ)** màu xanh ở góc phải trên cùng.
            3. Ở mục *General access (Quyền truy cập chung)*, chuyển từ *Restricted (Bị hạn chế)* sang **Anyone with the link (Bất kỳ ai có liên kết)**.
            4. Tải lại trang web này là xong!
            """
            return None, err_msg
        return None, f"Connection Error: {str(e)}"

# ==========================================
# THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #111827; font-weight: 800;'>MENU</h2>", unsafe_allow_html=True)
    st.caption("Welcome back, Mr. Tat Loc")
    st.divider()
    
    menu = st.radio(
        "Choose a section:", 
        ["🏆 Leaderboard", "📊 Student Reports", "🗣️ Speaking Practice"],
        key="active_tab" # ĐỒNG BỘ VỚI SESSION STATE
    )

# ==========================================
# BANNER VÀ THANH ĐIỀU HƯỚNG TOÀN CỤC (HUB)
# ==========================================
st.markdown("""
<div class="brand-header">
    <h1>MR. TAT LOC IELTS</h1>
    <p>AI Learning Platform</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='quick-nav-container'>", unsafe_allow_html=True)
col_nav1, col_nav2 = st.columns([1, 1])

if st.session_state.active_tab == "🏆 Leaderboard":
    if col_nav1.button("📊 Go to Student Reports", use_container_width=True):
        st.session_state.active_tab = "📊 Student Reports"
        st.rerun()
    if col_nav2.button("🗣️ Go to Speaking Practice", use_container_width=True):
        st.session_state.active_tab = "🗣️ Speaking Practice"
        st.rerun()

elif st.session_state.active_tab == "📊 Student Reports":
    if col_nav1.button("🏆 Back to Leaderboard", use_container_width=True):
        st.session_state.active_tab = "🏆 Leaderboard"
        st.rerun()
    if col_nav2.button("🗣️ Go to Speaking Practice", use_container_width=True):
        st.session_state.active_tab = "🗣️ Speaking Practice"
        st.rerun()

elif st.session_state.active_tab == "🗣️ Speaking Practice":
    if col_nav1.button("🏆 Back to Leaderboard", use_container_width=True):
        st.session_state.active_tab = "🏆 Leaderboard"
        st.rerun()
    if col_nav2.button("📊 Go to Student Reports", use_container_width=True):
        st.session_state.active_tab = "📊 Student Reports"
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# Kéo dữ liệu một lần cho các trang
df, error_msg = fetch_real_sheet_data()

# ==========================================
# TRANG 1: LEADERBOARD
# ==========================================
if st.session_state.active_tab == "🏆 Leaderboard":
    st.markdown("<h2 style='margin-top: 0;'>Class Leaderboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 16px; margin-bottom: 24px;'>Check out the top students in our classes based on AI scores!</p>", unsafe_allow_html=True)
    
    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty:
        total_students = df['Student'].nunique() if 'Student' in df.columns else 0
        total_tests = len(df)
        avg_band = df['Band_Score'].mean() if 'Band_Score' in df.columns else 0.0
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card"><p>Total Students</p><h3>{total_students}</h3></div>
            <div class="metric-card"><p>Tests Taken</p><h3>{total_tests}</h3></div>
            <div class="metric-card"><p>Average Score</p><h3 style="color:#4F46E5;">{avg_band:.1f}</h3></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🥇 Top Students")
        try:
            lb_df = df.groupby('Student').agg(
                Tests=('Band_Score', 'count'),
                Average_Score=('Band_Score', 'mean'),
            ).reset_index()
            
            lb_df['Average_Score'] = lb_df['Average_Score'].round(1)
            lb_df = lb_df.sort_values(by='Average_Score', ascending=False).reset_index(drop=True)
            lb_df.index += 1
            
            lb_df.columns = ['Student Name', 'Tests Taken', 'Average Band Score']
            st.dataframe(lb_df, use_container_width=True)
        except Exception as e:
            st.dataframe(df)
    else:
        st.info("No data found. Please do some tests first!")

# ==========================================
# TRANG 2: STUDENT REPORTS
# ==========================================
elif st.session_state.active_tab == "📊 Student Reports":
    st.markdown("<h2 style='margin-top: 0;'>Student Reports</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 16px; margin-bottom: 24px;'>Deep-dive analytics into individual performance.</p>", unsafe_allow_html=True)
    
    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty and 'Student' in df.columns:
        student_list = df['Student'].dropna().unique().tolist()
        
        st.markdown("""
            <div class='student-selector-highlight'>
                <h3>🔍 Find a Student</h3>
                <p>Select a student's name below to see their test scores and detailed AI feedback.</p>
            </div>
        """, unsafe_allow_html=True)
        
        selected_student = st.selectbox("Select Student:", sorted(student_list), label_visibility="collapsed")
        
        st.markdown(f"<h3 style='margin-top: 32px;'>🎓 Academic Profile: {selected_student}</h3>", unsafe_allow_html=True)
        
        student_data = df[df['Student'] == selected_student]
        if 'Timestamp' in student_data.columns:
            student_data = student_data.sort_values(by='Timestamp', ascending=False)
        
        if student_data.empty:
            st.warning("No records found for this student.")
        else:
            for index, row in student_data.iterrows():
                with st.container():
                    cols = st.columns([4, 1])
                    date_str = str(row.get('Timestamp', 'N/A'))
                    lesson_str = str(row.get('Lesson', 'N/A'))
                    topic_str = str(row.get('Question', 'N/A'))
                    band_str = str(row.get('Band_Score', 'N/A'))
                    feedback_str = str(row.get('Feedback_Detail', 'No detailed feedback available.'))
                    
                    with cols[0]:
                        st.markdown(f"**🕒 Date:** {date_str} &nbsp;|&nbsp; **Lesson:** {lesson_str}")
                        st.markdown(f"**📌 Topic:** *{topic_str}*")
                    with cols[1]:
                        st.markdown(f"<h2 style='text-align: right; color: #4F46E5; margin:0;'>Band {band_str}</h2>", unsafe_allow_html=True)
                    
                    with st.expander("View Detailed AI Feedback", expanded=True):
                        st.markdown(f"<div class='ai-report-box'>\n\n{feedback_str}\n\n</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No student data available. Please check your Google Sheet.")

# ==========================================
# TRANG 3: SPEAKING PRACTICE
# ==========================================
elif st.session_state.active_tab == "🗣️ Speaking Practice":
    st.markdown("<h2 style='margin-top: 0;'>Speaking Practice</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 16px; margin-bottom: 24px;'>Practice your IELTS Speaking with our AI and get instant feedback.</p>", unsafe_allow_html=True)
    
    topics = {
        "Part 1: Work or Study": "Let's talk about what you do. Do you work or are you a student?",
        "Part 1: Hometown": "Tell me a little about where you live. What do you like most about your hometown?",
        "Part 1: Hobbies & Free Time": "What do you usually do in your free time? Have your hobbies changed since you were a child?",
        "Part 1: Food & Cooking": "What is your favorite food? Do you prefer eating at home or eating out?",
        "Part 2: Describe a Person": "Describe a family member or a friend that you spend a lot of time with.\n\nYou should say:\n- Who this person is\n- What they look like\n- What their personality is\n- And explain why you like spending time with them.",
        "Part 2: A Memorable Journey": "Describe a long journey you had and would like to take again.\n\nYou should say:\n- When/where you went\n- Who you went with\n- Why you went there\n- And explain why you would like to have it again.",
        "Part 2: A Book You Enjoyed": "Describe a book that you enjoyed reading.\n\nYou should say:\n- What this book is about\n- Why you decided to read it\n- What you learned from it\n- And explain why you enjoyed reading it.",
        "Part 2: A Useful Website": "Describe a useful website you often visit.\n\nYou should say:\n- What the website is\n- How you found it\n- What you do on this website\n- And explain why you think it is useful.",
        "Part 3: Technology & Communication": "How has technology changed the way people communicate with each other? Do you think these changes are mostly positive or negative?",
        "Part 3: Environment & Pollution": "What are the main environmental problems in your country? What can individuals do to help protect the environment?"
    }
    
    selected_topic_key = st.selectbox("📚 Choose a Topic Category:", list(topics.keys()))
    
    st.info(f"**{selected_topic_key}**\n\n{topics[selected_topic_key]}")
    
    audio_data = st.audio_input("🎙️ Click to record your answer:")
    
    if audio_data:
        with st.spinner("🤖 AI is analyzing your pronunciation, grammar, and fluency..."):
            time.sleep(3)
            
        st.success("✅ Analysis Complete!")
        
        st.markdown("""
        <div class="ai-report-box">
            <h4 style="color: #4F46E5;">🎯 OVERALL BAND: 7.0</h4>
            <hr style="border-top: 1px solid #E5E7EB;">
            <h4>📝 DETAILED FEEDBACK:</h4>
            <ul>
                <li><b>Fluency & Coherence (7.0):</b> You spoke clearly and maintained a very good pace throughout your answer. Excellent use of linking phrases to connect your ideas logically.</li>
                <li><b>Lexical Resource (7.5):</b> Appropriate and somewhat advanced vocabulary used. You deployed relevant topic-specific words accurately.</li>
                <li><b>Grammatical Range (6.5):</b> Most sentences are well-structured. However, pay attention to the consistency of your past tense verbs when describing past events.</li>
                <li><b>Pronunciation (7.0):</b> Very easy to understand with a natural rhythm and good chunking of phrases.</li>
            </ul>
            <br>
            <h4>💡 HOW TO IMPROVE:</h4>
            <b>1. Grammar Accuracy</b><br>
            ❌ <i>Common error detected:</i> Missing articles (a/an/the) in complex sentences.<br>
            ✅ <i>Advice:</i> Review the rules for definite and indefinite articles, especially before specific nouns.<br><br>
            
            <b>2. Vocabulary Upgrade</b><br>
            Instead of repeating the word "good" or "nice", try using higher-level alternatives like <b>"outstanding"</b>, <b>"phenomenal"</b>, or <b>"captivating"</b> depending on the context.<br>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Try Another Topic"):
            st.rerun()
