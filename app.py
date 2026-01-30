import streamlit as st
import requests
import base64
import json

# ================= CẤU HÌNH =================
st.set_page_config(page_title="IELTS Speaking VIP", page_icon="💎")

# 1. Lấy Key từ Két sắt (Secrets)
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Chưa tìm thấy Key. Thầy hãy dán Key AIzaSy... vào Secrets nhé!")
    st.stop()

# ================= GIAO DIỆN =================
st.title("💎 IELTS Speaking Examiner (VIP Mode)")
st.caption("Powered by: Google Gemini 2.0 Flash (Paid/Billing Account)")

# Danh sách câu hỏi
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

# ================= XỬ LÝ =================
if audio_value:
    with st.spinner("AI đang chấm điểm bằng tài khoản VIP..."):
        try:
            # 1. Chuyển đổi file âm thanh sang mã Base64
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File ghi âm quá ngắn, thầy nói dài hơn xíu nhé.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. GỬI ĐẾN GOOGLE GEMINI 2.0 FLASH
            # (Model này xịn nhất, tài khoản thường bị khóa, nhưng tài khoản thầy đã Add thẻ nên dùng vô tư)
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

            # 3. Gửi request
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # 4. Đọc kết quả
            if response.status_code == 200:
                result = response.json()
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    st.success("✅ THÀNH CÔNG! (Billing Account Verified)")
                    st.divider()
                    
                    # Hiển thị kết quả đẹp
                    with st.container(border=True):
                        st.markdown(text_response)
                        
                    st.balloons() # Thả bóng bay chúc mừng thầy!
                except Exception as parse_err:
                    st.error("⚠️ Lỗi đọc nội dung trả về (JSON Error).")
                    st.code(result)
            else:
                # Nếu vẫn lỗi thì in chi tiết ra để xem
                st.error(f"⚠️ Lỗi kết nối ({response.status_code}):")
                st.code(response.text)
                
                if response.status_code == 403:
                    st.warning("👉 Gợi ý: Lỗi 403 thường do thầy chưa bật 'Generative Language API'. Thầy vào lại trang tạo Key, tìm API này và bấm ENABLE nhé.")

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)