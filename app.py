import streamlit as st
import subprocess
import sys
import time

# ================= 0. CƯỠNG BỨC CẬP NHẬT THƯ VIỆN (CHÌA KHÓA SỬA LỖI 404) =================
# Đoạn code này sẽ chạy TRƯỚC khi Import AI để đảm bảo thư viện luôn mới nhất
try:
    import google.generativeai as genai
    import importlib.metadata
    
    # Kiểm tra xem phiên bản hiện tại là bao nhiêu
    current_version = importlib.metadata.version("google-generativeai")
    
    # Nếu phiên bản cũ hơn 0.7.2 (chưa có Flash 1.5), ép cài lại ngay lập tức
    if current_version < "0.7.2":
        placeholder = st.empty()
        placeholder.warning(f"⚠️ Phát hiện thư viện cũ ({current_version}). Đang cưỡng bức cập nhật...")
        
        # Lệnh ép cài đặt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "google-generativeai>=0.7.2"])
        
        placeholder.success("✅ Đã cập nhật xong! Đang khởi động lại...")
        time.sleep(1)
        st.rerun() # Tự reload lại trang
        
except Exception as e:
    # Nếu chưa có thư viện thì cài mới luôn
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.7.2"])
    st.rerun()

# ================= 1. CẤU HÌNH AI =================
import google.generativeai as genai # Import lại sau khi đã chắc chắn cập nhật

# ⚠️ DÁN KEY CỦA PROJECT MỚI VÀO ĐÂY
GOOGLE_API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0"

try:
    genai.configure(api_key=GOOGLE_API_KEY, transport="rest")
except Exception as e:
    st.error(f"Lỗi Key: {e}")
    st.stop()

# --- CHIẾN THUẬT TỰ ĐỘNG TÌM MODEL ---
# Thử Flash trước, nếu không được thì dùng Pro (chậm hơn xíu nhưng chắc chắn chạy)
active_model = None
model_status = ""

try:
    # Ưu tiên 1: Gemini 1.5 Flash (Nhanh, chuẩn)
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Test thử 1 phát xem có lỗi 404 không
    model.count_tokens("Test connection") 
    active_model = model
    model_status = "Gemini 1.5 Flash (High Speed)"
except:
    try:
        # Ưu tiên 2: Gemini 1.5 Pro (Nếu Flash bị lỗi 404 thì dùng con này)
        # Con Pro thường xuất hiện trong API sớm hơn Flash
        model = genai.GenerativeModel("gemini-1.5-pro")
        model.count_tokens("Test connection")
        active_model = model
        model_status = "Gemini 1.5 Pro (High Quality)"
    except:
        st.error("❌ Lỗi nghiêm trọng: Tài khoản Google này chưa kích hoạt Model nào.")
        st.info("Gợi ý: Thầy hãy chờ khoảng 5 phút để Google cập nhật Key mới rồi thử lại.")
        st.stop()

# ================= 2. GIAO DIỆN LỚP HỌC =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.markdown(f"**Instructor:** Mr. Tat Loc | **System:** {model_status}")

st.info("👋 Hướng dẫn: Chọn chủ đề -> Bấm Record -> Chờ AI chấm điểm.")

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
selected_q = st.selectbox("📌 Select a Topic:", questions)

st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

if audio_value:
    with st.spinner("AI đang chấm điểm (Mất khoảng 10-15s)..."):
        try:
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
                
            gemini_audio_input = {"mime_type": "audio/wav", "data": audio_bytes}
            
            prompt = f"""
            Role: IELTS Examiner. Assess speaking for: "{selected_q}".
            Feedback in VIETNAMESE.
            Output: Band Score, Pros/Cons, Fixes, Conclusion.
            """

            response = active_model.generate_content([prompt, gemini_audio_input], stream=False)
            
            st.success("✅ Đã chấm xong!")
            with st.container(border=True):
                st.markdown(response.text)
            st.balloons()
            
        except Exception as e:
            st.error("⚠️ LỖI KẾT NỐI:")
            st.code(e)