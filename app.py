import streamlit as st
import google.generativeai as genai

# ================= 1. CẤU HÌNH =================
# Lấy Key an toàn
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Dự phòng cho thầy test nhanh nếu lười chỉnh secrets
    GOOGLE_API_KEY = "DÁN_KEY_CỦA_THẦY_VÀO_ĐÂY" 

genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# --- CHIẾN THUẬT: THỬ LẦN LƯỢT CÁC MODEL CÓ TRONG LIST CỦA THẦY ---
# Danh sách này lấy từ ảnh thầy gửi (những con này chắc chắn Key thầy dùng được)
model_candidates = [
    "models/gemini-flash-latest",       # Ưu tiên 1: Bản Flash mới nhất
    "models/gemini-2.0-flash-exp",      # Ưu tiên 2: Bản 2.0 (Ngon nhưng experimental)
    "models/gemini-exp-1206",           # Ưu tiên 3: Bản thử nghiệm tháng 12
    "models/gemini-pro"                 # Đường cùng: Bản cũ siêu bền
]

active_model = None
last_error = None

# Vòng lặp thử từng con một
for m_name in model_candidates:
    try:
        test_model = genai.GenerativeModel(m_name)
        # Thử kết nối giả vờ một cái xem sống hay chết
        test_model.count_tokens("Hello")
        active_model = test_model
        print(f"✅ Đã kết nối thành công với: {m_name}")
        break # Nếu ngon rồi thì dừng thử, dùng luôn
    except Exception as e:
        print(f"❌ {m_name} bị lỗi, đang thử con tiếp theo...")
        last_error = e

# Nếu thử hết cả danh sách mà vẫn chết
if not active_model:
    st.error("⚠️ LỖI NGHIÊM TRỌNG: Không model nào hoạt động.")
    st.write("Chi tiết lỗi cuối cùng (Gửi ảnh này cho Admin):")
    st.code(last_error)
    st.stop()

# ================= 2. GIAO DIỆN HỌC VIÊN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")

st.markdown("""
    <style>
        .stApp {background-color: #f4f6f9;}
        .instruction-box {
            background-color: white; padding: 20px; border-radius: 10px;
            border-left: 5px solid #1e3a8a; margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("IELTS Speaking Assessment")
st.caption(f"System Online | Model: {active_model.model_name.split('/')[-1]}") # Hiện tên model đang chạy

st.markdown("""
<div class="instruction-box">
    <strong>Hướng dẫn:</strong> Chọn chủ đề, bấm Record và trả lời (20-40s).
</div>
""", unsafe_allow_html=True)

questions = [
    "Part 1: What is your daily routine like?",
    "Part 1: Are you a morning person or a night person?",
    "Part 1: Do you often eat breakfast at home or outside?",
    "Part 1: Do you have a healthy lifestyle?",
    "Part 1: What do you usually do in your free time?",
    "Part 1: Do you prefer spending time alone or with friends?",
    "Part 1: Is there any new hobby you want to try in the future?",
    "Part 1: How do you relax after a stressful day?"
]
selected_q = st.selectbox("Topic:", questions)

st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("Analyzing..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.warning("File ghi âm quá ngắn.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess: "{selected_q}".
            INSTRUCTIONS:
            1. Determine Band Score.
            2. Feedback in VIETNAMESE.
            3. Level-adaptive: Band <5 -> Simple suggestions. Band >6 -> Advanced.
            
            OUTPUT:
            **1. Band Score:** [Score]
            **2. Nhận xét:** [Pros/Cons]
            **3. Sửa lỗi:** [Fixes]
            **4. Tổng kết:** [Conclusion]
            """

            response = active_model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.success("✅ Done!")
            with st.container(border=True):
                st.markdown(response.text)
            
        except Exception as e:
            # Lần này hiện nguyên hình lỗi ra để bắt bệnh
            st.error("⚠️ CÓ LỖI XẢY RA:")
            st.code(e)