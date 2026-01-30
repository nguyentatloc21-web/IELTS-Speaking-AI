import streamlit as st
import requests
import json

# ================= CẤU HÌNH =================
# ⚠️ DÁN KEY ...f0K0 VÀO ĐÂY
API_KEY = "AIzaSyC3vMiv7f5eJXxLKiKWoh7F6tyOGeTf0K0"

st.set_page_config(page_title="System Scanner", page_icon="🔍")
st.title("🔍 MÁY QUÉT MODEL GOOGLE")

if st.button("BẤM ĐỂ QUÉT DANH SÁCH MODEL"):
    with st.spinner("Đang hỏi Google..."):
        try:
            # Lệnh hỏi danh sách Model
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                st.success("✅ KẾT NỐI THÀNH CÔNG! Dưới đây là danh sách Model thầy có thể dùng:")
                
                # Lọc ra những model dùng được (generateContent)
                usable_models = []
                if 'models' in data:
                    for m in data['models']:
                        if "generateContent" in m['supportedGenerationMethods']:
                            usable_models.append(m['name'])
                            st.code(m['name']) # In tên model ra màn hình
                
                if not usable_models:
                    st.error("❌ Tài khoản này kết nối được, nhưng KHÔNG CÓ model nào hỗ trợ tạo nội dung.")
                else:
                    st.info(f"💡 Thầy hãy copy một trong các tên ở trên (ví dụ: {usable_models[0]}) để dùng.")
            else:
                st.error(f"❌ Lỗi kết nối ({response.status_code}):")
                st.json(response.json())
                
        except Exception as e:
            st.error(f"Lỗi code: {e}")