import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# 1. 基礎設定 (只有金鑰)
BACKEND_GEMINI_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw"

st.set_page_config(page_title="家族投資系統", layout="wide")

# 初始化持股資料 (這個版本關閉網頁後資料會重置)
if 'stocks' not in st.session_state:
    st.session_state.stocks = []

# 2. 側邊選單
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手"])

# 3. 功能邏輯：資產儀表板
if m == "📈 資產儀表板":
    st.title("📈 家族持股清單")
    
    with st.form("add_stock"):
        col1, col2, col3, col4 = st.columns(4)
        n = col1.text_input("名稱")
        t = col2.text_input("代碼 (如 2330.TW)")
        p = col3.number_input("成本", 0.0)
        q = col4.number_input("股數", 0.0)
        if st.form_submit_button("新增持股"):
            st.session_state.stocks.append({"名稱": n, "代碼": t, "成本": p, "股數": q})
            st.rerun()

    if st.session_state.stocks:
        st.table(pd.DataFrame(st.session_state.stocks))
    else:
        st.info("目前還沒有輸入資料喔！")

# 4. 功能邏輯：AI 投資助手
elif m == "🤖 AI 投資助手":
    st.title("🤖 家族投資 AI 顧問")
    prompt = st.chat_input("想問什麼？例如：分析台積電現在可以買嗎？")
    
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        
        if res.status_code == 200:
            ans = res.json()['candidates'][0]['content']['parts'][0]['text']
            with st.chat_message("assistant"):
                st.write(ans)
