import streamlit as st
import requests
import base64
import json
import time

# ================= CẤU HÌNH =================
# ⚠️ DÙNG LẠI ĐÚNG CÁI KEY VỪA QUÉT RA DANH SÁCH KIA
API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0" 

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("Model: Gemini 2.0 Flash (Premium Tester Access)")

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
    with st.spinner("AI đang chấm điểm (Gemini 2.0 Flash)..."):
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. GỌI ĐÚNG TÊN MODEL TRONG DANH SÁCH CỦA THẦY
            # Em chọn con này vì nó ổn định nhất trong đám Tester
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
            
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
                    st.success("✅ THÀNH CÔNG!")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ Lỗi đọc kết quả.")
            else:
                st.error(f"⚠️ Lỗi Google ({response.status_code}):")
                st.code(response.text)
                
                # Nếu con 2.0 Flash này cũng bị khóa (429), ta sẽ thử con 2.5
                if response.status_code == 429:
                    st.warning("👉 Gợi ý: Nếu lỗi 429, thầy thử đổi dòng `url` trong code thành `models/gemini-2.5-flash` xem sao.")

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)