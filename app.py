import streamlit as st
import google.generativeai as genai

# ================= 1. NHẬP KEY (KIỂM TRA KỸ) =================
# Thầy hãy dán Key vào giữa 2 dấu ngoặc kép.
# ⚠️ LƯU Ý: Kiểm tra kỹ xem có dư DẤU CÁCH ở đầu hoặc cuối không nhé!
GOOGLE_API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0"

# Cấu hình
genai.configure(api_key=GOOGLE_API_KEY, transport="rest")

# ================= 2. GIAO DIỆN KIỂM TRA =================
st.set_page_config(page_title="System Check", page_icon="🔧")
st.title("🔧 Kiểm tra Kết nối Google AI")

st.info("Đang thử kết nối với Gemini 1.5 Flash...")

# Nút bấm để test
if st.button("BẤM ĐỂ TEST KẾT NỐI"):
    try:
        # Gọi thử một câu đơn giản nhất
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say Hello")
        
        # Nếu chạy xuống được đây là NGON LÀNH
        st.success("✅ KẾT NỐI THÀNH CÔNG! (Key hoạt động tốt)")
        st.write("AI trả lời:", response.text)
        st.balloons()
        
    except Exception as e:
        # Nếu lỗi, in nguyên văn lỗi ra để bắt bệnh
        st.error("❌ KẾT NỐI THẤT BẠI. Nguyên nhân chi tiết:")
        st.code(str(e)) # Hiện nguyên hình con lỗi
        
        # Phân tích lỗi giúp thầy
        err_msg = str(e)
        if "INVALID_ARGUMENT" in err_msg or "API_KEY_INVALID" in err_msg:
            st.warning("👉 Lỗi Key sai: Có thể thầy copy thiếu chữ hoặc thừa dấu cách.")
        elif "PERMISSION_DENIED" in err_msg:
            st.warning("👉 Lỗi Quyền: Key này chưa được bật 'Generative Language API'.")
        elif "404" in err_msg:
            st.warning("👉 Lỗi 404: Máy chủ Streamlit vẫn chưa cập nhật xong thư viện.")