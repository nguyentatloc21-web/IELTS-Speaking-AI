import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH (LẤY TỪ SECRETS) =================
try:
    # Lấy Key từ "Két sắt" để Google không bao giờ khóa nữa
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Chưa cấu hình Secrets. Thầy hãy vào Settings -> Secrets trên Streamlit để dán Key vào nhé.")
    st.stop()

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("System: Clean Account | Model: Gemini 1.5 Flash")

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

if audio_value:
    with st.spinner("AI đang chấm điểm (Tài khoản mới)..."):
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. GỌI GEMINI 1.5 FLASH (Chuẩn nhất cho Gmail mới)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"Role: IELTS Examiner. Assess speaking for: '{selected_q}'. Feedback in Vietnamese: Band Score, Pros/Cons, Fixes, Conclusion."},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": audio_b64
                            }
                        }
                    ]
                }]
            }

            # 3. Gửi đi
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # 4. Xử lý kết quả
            if response.status_code == 200:
                result = response.json()
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ THÀNH CÔNG RỰC RỠ!")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ Lỗi đọc kết quả.")
            else:
                st.error(f"⚠️ Lỗi Google ({response.status_code}):")
                st.code(response.text)

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)