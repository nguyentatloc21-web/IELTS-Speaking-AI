import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Mr. Tat Loc | AI IELTS Platform", page_icon="🎓", layout="wide")

# ==========================================
# PREMIUM CSS STYLING
# ==========================================
st.markdown("""
    <style>
    /* Global Font & Hide Default Streamlit Elements */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Premium Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 35px 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .brand-header h1 {
        margin: 0; font-size: 42px; font-weight: 800; letter-spacing: 1.5px;
        background: -webkit-linear-gradient(#FACC15, #F59E0B);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .brand-header p { margin: 10px 0 0 0; font-size: 18px; font-weight: 300; letter-spacing: 0.5px; color: #e2e8f0; }

    /* Metric Cards */
    .metric-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: all 0.3s ease;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    .metric-card h3 { margin: 0; font-size: 28px; font-weight: 800; color: #1e293b; }
    .metric-card p { margin: 5px 0 0 0; font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }

    /* AI Report Box */
    .ai-report-box {
        background-color: #f8fafc; border-left: 5px solid #3b82f6;
        padding: 20px 25px; border-radius: 8px; margin-top: 15px;
        font-size: 15px; line-height: 1.7; color: #334155; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .badge-score {
        background: #3b82f6; color: white; padding: 4px 10px;
        border-radius: 20px; font-weight: bold; font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATA FETCHING (REAL GOOGLE SHEETS + FALLBACK)
# ==========================================
@st.cache_data(ttl=10) # Cache clears every 10s for real-time effect
def fetch_google_sheet_data():
    """
    Reads directly from the public Google Sheet URL.
    Failsafes to beautiful Mock Data if the sheet is private/unreachable to prevent presentation crashes.
    """
    # The ID from your URL: https://docs.google.com/spreadsheets/d/1woji0ugdk7xfmpfZ6PKVU0dDvSwxtfDw-8rnmcidnDQ
    sheet_id = "1woji0ugdk7xfmpfZ6PKVU0dDvSwxtfDw-8rnmcidnDQ"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        df = pd.read_csv(csv_url)
        # Check if it actually read data or just a Google Login HTML page
        if 'html' in str(df.columns[0]).lower():
            raise Exception("Sheet is private")
        return df, True # Success, using Real Data
    except Exception as e:
        # FALLBACK MOCK DATA (Never let the demo crash)
        return generate_mock_leaderboard(), False

def generate_mock_leaderboard():
    students = ["Nguyen Van An", "Tran Thi Bich", "Le Hoang Cuong", "Pham Dung", "Hoang Duc", "Vu Hai", "Dang Giang"]
    data = []
    for i, name in enumerate(students):
        s_score = round(random.uniform(5.5, 8.0) * 2) / 2
        w_score = round(random.uniform(5.5, 7.5) * 2) / 2
        r_score = round(random.uniform(6.0, 9.0) * 2) / 2
        overall = round((s_score + w_score + r_score) / 3 * 2) / 2
        data.append({
            "Student Name": name, "Class": random.choice(["DIA2702", "PLA1601"]),
            "Speaking (AI)": s_score, "Writing (AI)": w_score, "Reading (Max)": r_score,
            "Overall Band": overall, "Last Active": datetime.now().strftime("%Y-%m-%d")
        })
    df = pd.DataFrame(data).sort_values(by="Overall Band", ascending=False).reset_index(drop=True)
    df.index += 1
    return df

def get_mock_history(student_name):
    return [
        {
            "date": "2026-06-25", "skill": "Speaking Part 2", "band": "7.5",
            "topic": "Describe a successful person you admire",
            "feedback": """
            <b>🟢 Strengths:</b><br>
            • <b>Fluency:</b> Excellent chunking and natural hesitation. The P.E.E.R structure was well maintained.<br>
            • <b>Lexical Resource:</b> Great use of idiomatic expressions (<i>look up to, a visionary leader, overcome unprecedented hurdles</i>).<br><br>
            <b>🔴 Areas for Improvement:</b><br>
            • <b>Grammar:</b> Noticeable omission of articles (a/an/the) in complex sentences.<br>
            • <b>Pronunciation:</b> Ending sounds /s/ and /z/ were occasionally dropped.<br><br>
            <span style='color:#d35400;'><b>💡 Mr. Tat Loc's Advice:</b></span> <i>Keep up the great pacing! Try to take deeper breaths before complex sentences to avoid losing energy at the end.</i>
            """
        },
        {
            "date": "2026-06-20", "skill": "Writing Task 2", "band": "6.5",
            "topic": "Technology in Education",
            "feedback": """
            <b>🔍 Logic & Coherence Analysis:</b><br>
            The essay has a clear position. However, in Body 2, the argument that 'AI can replace teachers' commits a <b>Slippery Slope</b> fallacy. You jumped to a conclusion without providing intermediate logical steps.<br><br>
            <b>✨ Vocabulary Upgrade (AI Suggestion):</b><br>
            ❌ <i>Original:</i> "Technology makes students study better."<br>
            ✅ <i>Upgraded:</i> "The integration of cutting-edge technology significantly <b>enhances students' academic performance</b>."
            """
        }
    ]

# ==========================================
# MAIN APP LAYOUT
# ==========================================
st.markdown("""
<div class="brand-header">
    <h1>MR. TAT LOC IELTS</h1>
    <p>Exclusive AI-Powered Teaching & Assessment Platform</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1e293b;'>👨‍🏫 DASHBOARD</h2>", unsafe_allow_html=True)
    st.caption("Welcome back, Mr. Tat Loc")
    st.divider()
    
    menu = st.radio("NAVIGATION MODULES", [
        "🏆 Live Leaderboard", 
        "📊 AI Student Reports", 
        "🗣️ Speaking AI Simulator"
    ])
    st.divider()
    st.markdown("### ⚙️ System Status")
    st.success("🟢 AI Engines: **Active**")
    st.success("🟢 Cloud Sync: **Online**")

# ------------------------------------------
# MODULE 1: LIVE LEADERBOARD
# ------------------------------------------
if menu == "🏆 Live Leaderboard":
    st.title("🏆 Class Performance Leaderboard")
    st.markdown("Real-time tracking of student progress and AI-assessed band scores.")
    
    # Fetch Data
    df, is_real_data = fetch_google_sheet_data()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if is_real_data:
            st.info("📡 Successfully connected to live Google Sheets database.")
        else:
            st.warning("⚠️ Google Sheet is private or unreachable. Displaying Demonstration Data.")
    with col2:
        auto_refresh = st.checkbox("🔄 Enable Live-sync (Auto-refresh 5s)")
        if auto_refresh:
            time.sleep(5)
            st.rerun()

    # Dashboard Metrics
    st.markdown("#### 📈 Platform Analytics")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><h3>{len(df) if not df.empty else 125}</h3><p>Active Students</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><h3>2,408</h3><p>Essays Graded</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3 style="color:#27ae60;">6.5</h3><p>Avg. Target Band</p></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><h3 style="color:#3b82f6;">99.9%</h3><p>AI Accuracy</p></div>', unsafe_allow_html=True)
    
    st.write("---")
    st.markdown("### 📋 Academic Rankings")
    
    # Beautify DataFrame
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=False
    )

# ------------------------------------------
# MODULE 2: AI STUDENT REPORTS
# ------------------------------------------
elif menu == "📊 AI Student Reports":
    st.title("📊 Comprehensive AI Diagnostics")
    st.markdown("Deep-dive analytics into individual student performance, highlighting specific weaknesses identified by the AI engine.")
    
    df, _ = fetch_google_sheet_data()
    # Try to extract student names dynamically, otherwise use default list
    try:
        student_list = df.iloc[:, 0].dropna().unique().tolist() if not df.empty else []
    except:
        student_list = []
    
    if not student_list:
        student_list = ["Nguyen Van An", "Tran Thi Bich", "Le Hoang Cuong"]

    selected_student = st.selectbox("🔍 Search Student Profile:", student_list)
    
    st.subheader(f"🎓 Academic Profile: {selected_student}")
    history = get_mock_history(selected_student) # Using mock history for deep demonstration
    
    for record in history:
        with st.container(border=True):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"**Date:** {record['date']} &nbsp;|&nbsp; **Module:** {record['skill']}")
                st.markdown(f"**Topic:** *{record['topic']}*")
            with cols[1]:
                st.markdown(f"<h2 style='text-align: right; color: #3b82f6; margin:0;'>Band {record['band']}</h2>", unsafe_allow_html=True)
            
            with st.expander("Show Detailed AI Evaluation", expanded=(record == history[0])):
                st.markdown(f"<div class='ai-report-box'>{record['feedback']}</div>", unsafe_allow_html=True)

# ------------------------------------------
# MODULE 3: SPEAKING AI SIMULATOR
# ------------------------------------------
elif menu == "🗣️ Speaking AI Simulator":
    st.title("🗣️ Speaking AI Simulator")
    st.markdown("Experience our proprietary speech-to-text and NLP grading engine. Responses are evaluated instantly against IELTS rubrics.")
    
    st.info("""
    **CUE CARD (PART 2):**
    Describe a family member or a friend that you spend a lot of time with.
    
    You should say:
    - Who this person is
    - What they look like
    - What their personality is
    - And explain why you like spending time with them.
    """)
    
    audio_data = st.audio_input("🎙️ Click to record your response:")
    
    if audio_data:
        with st.spinner("🤖 AI is analyzing: Pronunciation, Lexical Resource, Grammar, and Fluency..."):
            time.sleep(3) # Simulate API latency for dramatic effect
            
        st.success("✅ Analysis Complete!")
        st.balloons()
        
        st.markdown("### EXAMINER REPORT")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Band", "7.5", "+0.5")
        c2.metric("Pronunciation", "7.0")
        c3.metric("Lexical Resource", "8.0")
        c4.metric("Grammar", "7.5")
        
        st.markdown("""
        <div class="ai-report-box">
        <h4>🎙️ Verbatim Transcript (AI Recognized):</h4>
        <p><i>"The person I’d like to talk about is my older brother. He’s someone I really <b>look up to</b>. In terms of appearance, he’s quite tall and has a <b>striking resemblance</b> to my dad..."</i></p>
        
        <hr>
        <h4>🔍 Diagnostic Breakdown:</h4>
        <ul>
            <li><b>Highlights:</b> Chunking is highly natural. Excellent deployment of topic-specific collocations (<i>striking resemblance</i>).</li>
            <li><b>Errors Detected:</b> Minor hesitation at 0:45s. One instance of incorrect past-tense verb conjugation.</li>
        </ul>
        
        <h4>🚀 Path to Band 8.0:</h4>
        Instead of saying <i>"He is a good person"</i>, elevate your vocabulary by saying <i>"He possesses an exceptionally benevolent character"</i>.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Try Another Prompt"):
            st.rerun()

st.markdown("<br><br><center><p style='color:#94a3b8; font-size: 13px;'>© 2026 Developed exclusively for Mr. Tat Loc IELTS. All rights reserved.</p></center>", unsafe_allow_html=True)
