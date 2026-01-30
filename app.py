import streamlit as st
import requests
import base64
import json
import time

# ================= CẤU HÌNH (QUAN TRỌNG) =================
# ⚠️ DÁN CÁI KEY MỚI TẠO NGÀY 30/1 (ĐUÔI ...f0K0) VÀO ĐÂY:
API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0" 

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("Mode: Direct API | Model: Gemini 1.5 Flash (Auto-Retry)")

questions = [
    "Part 1: What is your daily routine like?",
    "Part 1: Are you a morning person or a night person?",
    "Part 1: Do you often eat breakfast at home or outside?",
    "Part 1: Do you have a healthy lifestyle?",
    "Part 1: What do you usually do in your free time?",
    "Part 1: Is there any new hobby you want to try in the future?",
    "Part 1: How do you relax after a stressful day?"
]
selected_q = st.selectbox("📌 Select a Topic:", questions)

st.write("🎙️ **Your Answer:**")
audio_value = st.audio_input("Record")

def send_to_google(api_key, audio_b64, question, retry_count=0):
    """Hàm gửi dữ liệu có khả năng tự thử lại khi bị Google chặn"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [
                {"text": f"Role: IELTS Examiner. Assess speaking for: '{question}'. Feedback in Vietnamese: Band Score, Pros/Cons, Fixes, Conclusion."},
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": audio_b64
                    }
                }
            ]
        }]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    # Nếu bị lỗi 429 (Quá tải), chờ 5s rồi thử lại (tối đa 3 lần)
    if response.status_code == 429 and retry_count < 3:
        st.toast(f"⏳ Hệ thống đang bận, đang thử lại lần {retry_count+1}...", icon="🔄")
        time.sleep(5)
        return send_to_google(api_key, audio_b64, question, retry_count + 1)
        
    return response

if audio_value:
    with st.spinner("AI đang chấm điểm (Vui lòng đợi)..."):
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File ghi âm quá ngắn (dưới 1 giây).")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. Gửi đi (Có cơ chế tự thử lại)
            response = send_to_google(API_KEY, audio_b64, selected_q)
            
            # 3. Xử lý kết quả
            if response.status_code == 200:
                result = response.json()
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ THÀNH CÔNG!")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ Lỗi đọc kết quả từ Google.")
            else:
                # Hiện lỗi chi tiết nếu thất bại hoàn toàn
                st.error(f"⚠️ Lỗi Google ({response.status_code}):")
                st.code(response.text)

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)