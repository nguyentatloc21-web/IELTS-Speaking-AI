import streamlit as st
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Mr. Tat Loc | AI Platform", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Global Font & Aesthetics */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 30px 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .brand-header h1 {
        margin: 0; font-size: 38px; font-weight: 800;
        background: -webkit-linear-gradient(#FACC15, #F59E0B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-header p { margin: 10px 0 0 0; font-size: 16px; color: #94A3B8; }

    /* Metric Cards */
    .metric-container { display: flex; gap: 20px; margin-bottom: 25px; }
    .metric-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        flex: 1;
    }
    .metric-card h3 { margin: 0; font-size: 32px; font-weight: 800; color: #0F172A; }
    .metric-card p { margin: 5px 0 0 0; font-size: 14px; color: #64748B; font-weight: 600; text-transform: uppercase; }

    /* AI Report & Feedback Box */
    .ai-report-box {
        background-color: #F8FAFC; 
        border-left: 4px solid #3B82F6;
        padding: 20px; 
        border-radius: 8px; 
        margin-top: 10px;
        font-size: 15px; 
        line-height: 1.6; 
        color: #334155; 
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5) # Refresh every 5 seconds
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

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0F172A; font-weight: 800;'>MENU</h2>", unsafe_allow_html=True)
    st.caption("Welcome back, Mr. Tat Loc")
    st.divider()
    
    menu = st.radio("Choose a section:", [
        "🏆 Leaderboard", 
        "📊 Student Reports", 
        "🗣️ Speaking Practice"
    ])

st.markdown("""
<div class="brand-header">
    <h1>MR. TAT LOC IELTS</h1>
    <p>AI Learning Platform</p>
</div>
""", unsafe_allow_html=True)

df, error_msg = fetch_real_sheet_data()

if menu == "🏆 Leaderboard":
    st.title("🏆 Class Leaderboard")
    st.markdown("Check out the top students in our classes!")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        auto_refresh = st.checkbox("🔄 Auto Update")
        if auto_refresh:
            time.sleep(5)
            st.rerun()

    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty:
        total_students = df['Student'].nunique() if 'Student' in df.columns else 0
        total_tests = len(df)
        avg_band = df['Band_Score'].mean() if 'Band_Score' in df.columns else 0.0
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card"><h3>{total_students}</h3><p>Students</p></div>
            <div class="metric-card"><h3>{total_tests}</h3><p>Tests Taken</p></div>
            <div class="metric-card"><h3 style="color:#27AE60;">{avg_band:.1f}</h3><p>Average Score</p></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("🥇 Top Students")
        
        try:
            lb_df = df.groupby(['Student', 'Class']).agg(
                Tests=('Band_Score', 'count'),
                Average_Score=('Band_Score', 'mean'),
            ).reset_index()
            
            lb_df['Average_Score'] = lb_df['Average_Score'].round(1)
            lb_df = lb_df.sort_values(by='Average_Score', ascending=False).reset_index(drop=True)
            lb_df.index += 1
            
            # Simple column names for students
            lb_df.columns = ['Student', 'Class', 'Tests Taken', 'Average Score']
            st.dataframe(lb_df, use_container_width=True)
        except Exception as e:
            st.dataframe(df) # Fallback to raw data
            
    else:
        st.info("No data found. Please do some tests first!")

elif menu == "📊 Student Reports":
    st.title("📊 Student Reports")
    st.markdown("View your test history and AI feedback here.")
    
    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty and 'Student' in df.columns:
        student_list = df['Student'].dropna().unique().tolist()
        
        selected_student = st.selectbox("🔍 Select Student:", sorted(student_list))
        
        st.subheader(f"🎓 Profile: {selected_student}")
        
        student_data = df[df['Student'] == selected_student]
        if 'Timestamp' in student_data.columns:
            student_data = student_data.sort_values(by='Timestamp', ascending=False)
        
        if student_data.empty:
            st.warning("No records found for this student.")
        else:
            for index, row in student_data.iterrows():
                with st.container(border=True):
                    cols = st.columns([4, 1])
                    
                    date_str = str(row.get('Timestamp', 'N/A'))
                    lesson_str = str(row.get('Lesson', 'N/A'))
                    topic_str = str(row.get('Question', 'N/A'))
                    band_str = str(row.get('Band_Score', 'N/A'))
                    feedback_str = str(row.get('Feedback_Summary', 'No feedback available.'))
                    
                    with cols[0]:
                        st.markdown(f"**🕒 Date:** {date_str} &nbsp;|&nbsp; **Lesson:** {lesson_str}")
                        st.markdown(f"**📌 Topic:** *{topic_str}*")
                    with cols[1]:
                        st.markdown(f"<h2 style='text-align: right; color: #3B82F6; margin:0;'>Band {band_str}</h2>", unsafe_allow_html=True)
                    
                    with st.expander("View AI Feedback", expanded=True):
                        st.markdown(f"<div class='ai-report-box'>\n\n{feedback_str}\n\n</div>", unsafe_allow_html=True)
    else:
        st.info("No student data available. Please check your Google Sheet.")

elif menu == "🗣️ Speaking Practice":
    st.title("🗣️ Speaking Practice")
    st.markdown("Practice your IELTS Speaking with our AI and get instant feedback.")
    
    st.info("""
    **Topic (Part 1):**
    Let's talk about what you do. Do you work or are you a student?
    """)
    
    audio_data = st.audio_input("🎙️ Click to record your answer:")
    
    if audio_data:
        with st.spinner("🤖 AI is analyzing your speech..."):
            time.sleep(3) # Simulate loading time for demo
            
        st.success("✅ Analysis Complete!")
        st.balloons()
        
        st.markdown("""
        <div class="ai-report-box">
            <h4>🎯 OVERALL BAND: 7.0</h4>
            <hr>
            <h4>📝 DETAILED FEEDBACK:</h4>
            <ul>
                <li><b>Fluency & Coherence (7.0):</b> You speak clearly and answer the question directly. Good use of linking words like "currently" and "therefore".</li>
                <li><b>Lexical Resource (7.0):</b> Good vocabulary for work and study. You used nice phrases like <i>"fast-paced environment"</i>.</li>
                <li><b>Grammatical Range (6.5):</b> Most sentences are correct. Be careful with present perfect tense.</li>
                <li><b>Pronunciation (7.5):</b> Very easy to understand. Good natural rhythm.</li>
            </ul>
            <br>
            <h4>💡 HOW TO IMPROVE:</h4>
            <b>1. Grammar mistake</b><br>
            ❌ <i>You said:</i> "I have work there for 2 years."<br>
            ✅ <i>Better:</i> "I have <b>been working</b> there for 2 years."<br><br>
            
            <b>2. Better Vocabulary</b><br>
            ❌ <i>You said:</i> "My job is very busy."<br>
            ✅ <i>Better:</i> "My job is quite <b>demanding and hectic</b>."<br>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Try Again"):
            st.rerun()
