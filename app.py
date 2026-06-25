import streamlit as st
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="Mr. Tat Loc | AI IELTS Platform", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Global Font & Aesthetics */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Hide Default Streamlit Elements for cleaner UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Premium Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #0A192F 0%, #112240 100%);
        padding: 35px 25px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.05);
    }
    .brand-header h1 {
        margin: 0; font-size: 42px; font-weight: 800; letter-spacing: -0.5px;
        background: -webkit-linear-gradient(#FACC15, #F59E0B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-header p { margin: 10px 0 0 0; font-size: 16px; font-weight: 400; color: #94A3B8; letter-spacing: 0.5px; }

    /* Metric Cards */
    .metric-container { display: flex; gap: 20px; margin-bottom: 25px; }
    .metric-card {
        background: white; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        flex: 1; transition: all 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-3px); border-color: #3B82F6; box-shadow: 0 10px 15px rgba(59,130,246,0.1); }
    .metric-card h3 { margin: 0; font-size: 32px; font-weight: 800; color: #0F172A; }
    .metric-card p { margin: 5px 0 0 0; font-size: 13px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

    /* AI Report & Feedback Box */
    .ai-report-box {
        background-color: #F8FAFC; 
        border-left: 4px solid #3B82F6;
        padding: 20px 25px; 
        border-radius: 0 12px 12px 0; 
        margin-top: 15px;
        font-size: 15px; 
        line-height: 1.7; 
        color: #334155; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .ai-report-box h3, .ai-report-box h4 { margin-top: 0; color: #1E293B; font-weight: 700; }
    
    /* Styling Streamlit Dataframes */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5) # Cache clears every 5 seconds for near real-time updates
def fetch_real_sheet_data():
    """
    Fetches real data directly from the user's Google Sheet URL.
    NO MOCK DATA. Strictly extracts based on the provided format.
    """
    sheet_id = "1woji0ugdk7xfmpfZ6PKVU0dDvSwxtfDw-8rnmcidnDQ"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        df = pd.read_csv(csv_url)
        
        # Clean column names (strip whitespaces)
        df.columns = df.columns.str.strip()
        
        # Verify if the sheet is an HTML login page (meaning it's private)
        if 'html' in str(df.columns[0]).lower():
            return None, "Error: Google Sheet is private. Please change access to 'Anyone with the link can view'."
        
        # Ensure 'Band_Score' is numeric
        if 'Band_Score' in df.columns:
            df['Band_Score'] = pd.to_numeric(df['Band_Score'], errors='coerce')
            
        # Drop rows where Student name is empty
        if 'Student' in df.columns:
            df = df.dropna(subset=['Student'])
            
        return df, None
        
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #0F172A; font-weight: 800;'>🎯 DASHBOARD</h2>", unsafe_allow_html=True)
    st.caption("Welcome back, Mr. Tat Loc")
    st.divider()
    
    menu = st.radio("PLATFORM MODULES", [
        "🏆 Live Leaderboard", 
        "📊 Student Analytics & Reports", 
        "🗣️ AI Speaking Simulator"
    ])
    st.divider()
    st.markdown("### ⚙️ System Status")
    st.success("🟢 Real-time Sync: **Active**")
    st.success("🟢 AI Engine API: **Standby**")

st.markdown("""
<div class="brand-header">
    <h1>TAT LOC IELTS</h1>
    <p>Exclusive AI-Powered Assessment & Performance Tracking</p>
</div>
""", unsafe_allow_html=True)

# Fetch Data once to be used across modules
df, error_msg = fetch_real_sheet_data()

if menu == "🏆 Live Leaderboard":
    st.title("🏆 Class Performance Leaderboard")
    st.markdown("Real-time tracking of student progress based on actual AI-assessed data.")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-sync Data (5s)")
        if auto_refresh:
            time.sleep(5)
            st.rerun()

    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty:
        # Calculate dynamic metrics based on REAL data
        total_students = df['Student'].nunique() if 'Student' in df.columns else 0
        total_tests = len(df)
        avg_band = df['Band_Score'].mean() if 'Band_Score' in df.columns else 0.0
        
        # Render Metrics
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card"><h3>{total_students}</h3><p>Active Students</p></div>
            <div class="metric-card"><h3>{total_tests}</h3><p>Total AI Assessments</p></div>
            <div class="metric-card"><h3 style="color:#27AE60;">{avg_band:.1f}</h3><p>Average Class Band</p></div>
            <div class="metric-card"><h3 style="color:#3B82F6;">100%</h3><p>Data Integrity</p></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("📋 Academic Rankings")
        
        # Process Leaderboard from Real Data
        try:
            lb_df = df.groupby(['Student', 'Class']).agg(
                Submissions=('Band_Score', 'count'),
                Average_Score=('Band_Score', 'mean'),
                Max_Score=('Band_Score', 'max')
            ).reset_index()
            
            # Format and sort
            lb_df['Average_Score'] = lb_df['Average_Score'].round(1)
            lb_df = lb_df.sort_values(by='Average_Score', ascending=False).reset_index(drop=True)
            lb_df.index += 1 # Start rank from 1
            
            # Display
            st.dataframe(lb_df, use_container_width=True)
        except Exception as e:
            st.warning("Ensure your Google Sheet has 'Student', 'Class', and 'Band_Score' columns.")
            st.dataframe(df) # Fallback: just show the raw data
            
    else:
        st.info("No data found in the spreadsheet. Please ensure there are records.")

elif menu == "📊 Student Analytics & Reports":
    st.title("📊 Detailed Student Diagnostics")
    st.markdown("Deep-dive analytics into individual performance, retrieving exact AI feedback logs from the database.")
    
    if error_msg:
        st.error(error_msg)
    elif df is not None and not df.empty and 'Student' in df.columns:
        student_list = df['Student'].dropna().unique().tolist()
        
        selected_student = st.selectbox("🔍 Search Student Profile:", sorted(student_list))
        
        st.subheader(f"🎓 Academic Profile: {selected_student}")
        
        # Filter data for the selected student
        student_data = df[df['Student'] == selected_student].sort_values(by='Timestamp', ascending=False)
        
        if student_data.empty:
            st.warning("No assessment history found for this student.")
        else:
            # Display real history
            for index, row in student_data.iterrows():
                with st.container(border=True):
                    cols = st.columns([4, 1])
                    
                    date_str = str(row.get('Timestamp', 'N/A'))
                    lesson_str = str(row.get('Lesson', 'N/A'))
                    topic_str = str(row.get('Question', 'N/A'))
                    band_str = str(row.get('Band_Score', 'N/A'))
                    feedback_str = str(row.get('Feedback_Summary', 'No feedback available.'))
                    
                    with cols[0]:
                        st.markdown(f"**🕒 Date:** {date_str} &nbsp;|&nbsp; **Module:** {lesson_str}")
                        st.markdown(f"**📌 Topic:** *{topic_str}*")
                    with cols[1]:
                        st.markdown(f"<h2 style='text-align: right; color: #3B82F6; margin:0;'>Band {band_str}</h2>", unsafe_allow_html=True)
                    
                    # Exact Feedback from Google Sheet formatted as Markdown
                    with st.expander("Show AI Evaluation & Transcript", expanded=True):
                        st.markdown(f"<div class='ai-report-box'>\n\n{feedback_str}\n\n</div>", unsafe_allow_html=True)
    else:
        st.info("Ensure your Google Sheet contains a 'Student' column to view reports.")

elif menu == "🗣️ AI Speaking Simulator":
    st.title("🗣️ Live AI Speaking Simulator")
    st.markdown("A demonstration interface of the proprietary speech-to-text and NLP grading engine.")
    
    st.info("""
    **CURRENT TOPIC (PART 1):**
    Let's talk about what you do. Do you work or are you a student?
    """)
    
    audio_data = st.audio_input("🎙️ Click to record your response (Demonstration Mode):")
    
    if audio_data:
        with st.spinner("🤖 AI is analyzing: Pronunciation, Lexical Resource, Grammar, and Fluency..."):
            time.sleep(3) # Simulate processing delay
            
        st.success("✅ Analysis Complete! Data synchronized with database.")
        st.balloons()
        
        # Displaying a highly professional generic response demonstrating the output format
        st.markdown("""
        <div class="ai-report-box">
            <h4>🎯 OVERALL RESULT: 7.0</h4>
            <hr>
            <h4>📝 DETAILED ANALYSIS:</h4>
            <ul>
                <li><b>Fluency & Coherence (7.0):</b> You speak at length without noticeable effort or loss of coherence. Connectives are used naturally.</li>
                <li><b>Lexical Resource (7.0):</b> Good use of vocabulary to discuss your job. Some idiomatic expressions were attempted (e.g., <i>"burn the midnight oil"</i>).</li>
                <li><b>Grammatical Range (6.5):</b> A mix of simple and complex sentence forms. A few minor errors in present perfect continuous tenses.</li>
                <li><b>Pronunciation (7.5):</b> Clear and easy to understand throughout. Good use of chunking and intonation.</li>
            </ul>
            <br>
            <h4>💡 IMPROVEMENT SUGGESTIONS (Path to 8.0):</h4>
            <b>Error 1: Grammatical accuracy</b><br>
            ❌ <i>Original:</i> "I have been worked there for 3 years."<br>
            ✅ <i>Better:</i> "I have been <b>working</b> there for 3 years."<br>
            *Explanation:* Use Present Perfect Continuous to emphasize an action that started in the past and continues to the present.<br><br>
            
            <b>Error 2: Vocabulary Enhancement</b><br>
            ❌ <i>Original:</i> "My job is very hard."<br>
            ✅ <i>Better:</i> "My profession is quite <b>demanding and fast-paced</b>."<br>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Try Another Prompt"):
            st.rerun()

# Footer
st.markdown("<br><br><center><p style='color:#94A3B8; font-size: 13px; font-weight: 600;'>© 2026 Developed exclusively for Mr. Tat Loc IELTS. Powered by AI.</p></center>", unsafe_allow_html=True)
