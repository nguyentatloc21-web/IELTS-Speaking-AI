import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH (DÙNG KEY MỚI) =================
# ⚠️ DÁN KEY TỪ PROJECT MỚI VÀO ĐÂY
API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0"

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("Mode: Direct API (Bypass Library Errors)")

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
    with st.spinner("AI đang chấm điểm (Chế độ trực tiếp)..."):
        try:
            # 1. Chuyển file âm thanh sang mã Base64
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            # Mã hóa file
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. Soạn nội dung gửi đi (Thủ công)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"Role: IELTS Examiner. Assess speaking for: '{selected_q}'. Provide output in Vietnamese: Band Score, Pros/Cons, Fixes, Conclusion."},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": audio_b64
                            }
                        }
                    ]
                }]
            }

            # 3. Gửi đi bằng đường tắt (Requests)
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # 4. Xử lý kết quả trả về
            if response.status_code == 200:
                result = response.json()
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ Đã chấm xong!")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ AI trả về lỗi định dạng (Thử lại lần nữa).")
            else:
                # Nếu lỗi, in rõ lỗi gì từ Google
                st.error(f"⚠️ LỖI TỪ GOOGLE ({response.status_code}):")
                st.code(response.text)

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)