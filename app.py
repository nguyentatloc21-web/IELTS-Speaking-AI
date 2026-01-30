import streamlit as st
import requests
import base64
import json
import time

# ================= CẤU HÌNH =================
# ⚠️ DÁN KEY MỚI CỦA THẦY VÀO ĐÂY (Key ...f0K0)
API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0" 

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("Mode: Auto-Detect Model | Account: Free Tier")

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

def try_generate(api_key, audio_b64, question):
    """Hàm thử lần lượt các Model khác nhau cho đến khi được thì thôi"""
    
    # Danh sách các tên Model có thể dùng được (Thử lần lượt)
    candidate_models = [
        "gemini-1.5-flash",          # Ưu tiên 1: Bản chuẩn
        "gemini-1.5-flash-latest",   # Ưu tiên 2: Bản mới nhất
        "gemini-1.5-flash-001",      # Ưu tiên 3: Bản ổn định cũ
        "gemini-pro"                 # Đường cùng: Bản Pro (chỉ text, nhưng thử vận may)
    ]
    
    last_error = ""

    for model_name in candidate_models:
        try:
            # Tạo URL với tên model hiện tại
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            
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
            
            # Gửi đi
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                # Nếu thành công -> Trả về kết quả ngay
                return True, response.json(), model_name
            else:
                # Nếu thất bại -> Lưu lỗi lại và thử con tiếp theo
                error_detail = response.text
                last_error = f"Model {model_name} lỗi: {error_detail}"
                continue 

        except Exception as e:
            last_error = str(e)
            continue
            
    # Nếu thử hết danh sách mà vẫn không được
    return False, last_error, None

if audio_value:
    with st.spinner("AI đang tìm model phù hợp và chấm điểm..."):
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. Gọi hàm tự động dò model
            success, result, used_model = try_generate(API_KEY, audio_b64, selected_q)
            
            # 3. Xử lý kết quả
            if success:
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.success(f"✅ THÀNH CÔNG! (Đã dùng model: {used_model})")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ Lỗi đọc nội dung trả về.")
            else:
                st.error("⚠️ TẤT CẢ MODEL ĐỀU THẤT BẠI.")
                st.code(result) # In lỗi cuối cùng ra xem

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)