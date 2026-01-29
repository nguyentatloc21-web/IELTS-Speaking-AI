import streamlit as st
import google.generativeai as genai
import importlib.metadata

# ================= CẤU HÌNH =================
st.set_page_config(page_title="System Check", page_icon="🛠️")
st.title("🛠️ Công cụ Kiểm tra Hệ thống")

# 1. Kiểm tra API Key
try:
    # Ưu tiên lấy từ Secrets
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        source = "Secrets (Bảo mật)"
    else:
        # Nếu không có Secrets thì thử dùng key dán trực tiếp (chỉ để test)
        # Bạn có thể dán tạm key vào dòng dưới nếu cần test nhanh:
        api_key = "DÁN_KEY_CỦA_BẠN_VÀO_ĐÂY_NẾU_KHÔNG_DÙNG_SECRETS" 
        source = "Dán trực tiếp (Hard-code)"
    
    st.success(f"✅ Đã tìm thấy API Key từ: {source}")
    genai.configure(api_key=api_key)
    
except Exception as e:
    st.error(f"❌ Lỗi API Key: {e}")
    st.stop()

# 2. Kiểm tra Phiên bản Thư viện
try:
    version = importlib.metadata.version("google-generativeai")
    st.info(f"📦 Phiên bản thư viện 'google-generativeai' đang chạy: **{version}**")
    
    # Cảnh báo nếu phiên bản quá cũ
    if version < "0.7.0":
        st.error("⚠️ Phiên bản QUÁ CŨ! Cần cập nhật requirements.txt thành: google-generativeai>=0.7.0")
    else:
        st.success("✅ Phiên bản thư viện: ỔN")
except:
    st.warning("⚠️ Không kiểm tra được phiên bản thư viện.")

# 3. Quét danh sách Model khả dụng (QUAN TRỌNG NHẤT)
st.divider()
st.write("🔄 Đang hỏi Google xem Key này dùng được Model nào...")

if st.button("Bấm để Quét Model (Scan Models)"):
    try:
        available_models = []
        for m in genai.list_models():
            # Chỉ lấy những model có khả năng tạo nội dung (generateContent)
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if available_models:
            st.success(f"🎉 Tìm thấy {len(available_models)} model hoạt động được:")
            st.code("\n".join(available_models))
            st.caption("👉 Hãy copy một cái tên trong danh sách trên (ví dụ: models/gemini-1.5-flash) để dùng.")
        else:
            st.error("❌ Kết nối thành công nhưng KHÔNG tìm thấy model nào. Có thể Key này bị hạn chế quyền hoặc sai vùng.")
            
    except Exception as e:
        st.error("❌ Lỗi KẾT NỐI nghiêm trọng:")
        st.code(e)
        st.markdown("""
        **Gợi ý nguyên nhân:**
        1. API Key bị sai hoặc đã bị xóa/hủy.
        2. File `requirements.txt` chưa được máy chủ cập nhật (Hãy Reboot App & Clear Cache).
        """)