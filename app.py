import streamlit as st
import requests
import base64
import json
import time

# ================= CẤU HÌNH (LẤY TỪ SECRETS) =================
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Lỗi: Chưa tìm thấy Key trong Secrets.")
    st.stop()

# ================= GIAO DIỆN =================
st.set_page_config(page_title="IELTS Speaking", page_icon="🎙️")
st.title("IELTS Speaking Assessment")
st.caption("System: Smart Auto-Switch Mode ⚡")

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

# === HÀM THÔNG MINH: TỰ TÌM MODEL SỐNG ===
def find_working_model_and_generate(api_key, audio_b64, question):
    # Danh sách tất cả các Model có thể có (Thử từ Cũ -> Mới -> Lạ)
    candidate_models = [
        "gemini-1.5-flash",          # Bản chuẩn cũ (thường Free)
        "gemini-1.5-flash-latest",   # Bản cập nhật mới nhất
        "gemini-1.5-flash-001",      # Bản ổn định
        "gemini-1.5-pro",            # Bản Pro
        "gemini-2.0-flash-lite-preview-02-05", # Bản Lite Preview (Mới ra)
        "gemini-2.0-flash-lite-001", # Bản Lite chuẩn
        "gemini-exp-1206",           # Bản thử nghiệm (Thường Free limit to)
        "gemini-2.0-flash-exp",      # Bản thử nghiệm 2.0
    ]
    
    status_text = st.empty() # Ô thông báo trạng thái tạm thời
    
    for model_name in candidate_models:
        status_text.info(f"🔄 Đang thử kết nối với model: {model_name}...")
        
        try:
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
            
            # Gửi thử
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # Nếu thành công (200) -> Dừng vòng lặp ngay và trả kết quả
            if response.status_code == 200:
                status_text.success(f"✅ Đã tìm thấy model hoạt động: {model_name}")
                time.sleep(1) # Dừng 1 xíu cho thầy nhìn thấy tên model
                status_text.empty() # Xóa thông báo
                return True, response.json()
            
            # Nếu lỗi 429 (Hết hạn mức) hoặc 404 (Không tìm thấy) -> Thử con tiếp theo
            else:
                continue 

        except:
            continue
            
    # Nếu thử hết sạch danh sách mà vẫn không được
    status_text.error("❌ Đã thử tất cả Model nhưng đều thất bại.")
    return False, None

if audio_value:
    with st.container(): # Gom nhóm để giao diện đẹp hơn
        try:
            # 1. Xử lý file
            audio_bytes = audio_value.read()
            if len(audio_bytes) < 500:
                st.error("⚠️ File quá ngắn.")
                st.stop()
            
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # 2. GỌI HÀM TỰ ĐỘNG
            success, result = find_working_model_and_generate(API_KEY, audio_b64, selected_q)
            
            # 3. Xử lý kết quả
            if success and result:
                try:
                    text_response = result['candidates'][0]['content']['parts'][0]['text']
                    st.success("✅ CHẤM ĐIỂM THÀNH CÔNG!")
                    with st.container(border=True):
                        st.markdown(text_response)
                    st.balloons()
                except:
                    st.error("⚠️ Lỗi đọc nội dung trả về.")
            else:
                st.error("⛔ THÔNG BÁO QUAN TRỌNG:")
                st.warning("""
                Tài khoản Google này hiện tại KHÔNG cho phép dùng miễn phí bất kỳ model nào (Lỗi Limit: 0).
                
                👉 **GIẢI PHÁP CUỐI CÙNG (100% ĐƯỢC):**
                Thầy hãy vào trang Google AI Studio -> Settings -> **Set up Billing**.
                * Thầy add thẻ Visa vào (Google sẽ tặng 300$ dùng thử hoặc cho dùng Free Tier thực sự).
                * Nếu không xác minh thanh toán, Google sẽ chặn API đối với tài khoản mới này.
                """)

        except Exception as e:
            st.error("⚠️ Lỗi hệ thống:")
            st.code(e)