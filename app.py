import streamlit as st
import requests
import base64
import json
import time

# ================= CẤU HÌNH (LẤY TỪ KÉT SẮT) =================
# Code tự động lấy Key trong Secrets để không bị Google khóa
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Nếu thầy chưa cài Secrets, nó sẽ hiện lỗi hướng dẫn
    st.error("⚠️ QUAN TRỌNG: Thầy chưa cất Key vào Két sắt (Secrets)!")
    st.info("👉 Cách sửa: Vào web Streamlit -> Settings -> Secrets -> Dán Key vào đó theo mẫu: GOOGLE_API_KEY = '...'")
    st.stop()

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("Model: Gemini Exp 1206 (Experimental Channel)")

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
    with st.spinner("AI đang chấm điểm (Thử nghiệm Exp 1206)..."):
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. GỌI CON MODEL "CỬA SAU": GEMINI EXP 1206
            # Con này thường được thả Free để test
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-exp-1206:generateContent?key={API_KEY}"
            
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
                
                # Nếu con này cũng chết thì bó tay với tài khoản này
                if "429" in str(response.status_code):
                    st.error("⛔ KẾT LUẬN: Tài khoản Google này đã bị khóa 'Hard Limit' (Cấm toàn bộ model).")
                    st.warning("👉 GIẢI PHÁP CUỐI CÙNG: Thầy bắt buộc phải tạo một GMAIL MỚI TINH (chưa từng dính dáng đến Google Cloud/Gemini) để lấy Key mới.")

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)