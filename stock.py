import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO

# --- 1. 資料庫與安全邏輯 ---
DB_FILE = "users_stock_data.json"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_all_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_all_data(all_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --- 2. 網頁初始化 ---
st.set_page_config(page_title="家族投資究極系統 4.1", layout="wide")

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_all_data()

current_user = st.session_state.get('current_user', None)

if not current_user:
    st.title("🛡️ 家族投資管理系統 4.1")
    st.sidebar.title("🔐 系統登入")
    u_input = st.sidebar.text_input("帳號", key="login_u")
    p_input = st.sidebar.text_input("密碼", type="password", key="login_p")

    if st.sidebar.button("登入 / 建立帳號"):
        if u_input and p_input:
            pw_hash = make_hash(p_input)
            if u_input not in st.session_state.all_data:
                st.session_state.all_data[u_input] = {"password": pw_hash, "stocks": []}
                save_all_data(st.session_state.all_data)
                st.session_state.current_user = u_input
                st.rerun()
            else:
                if st.session_state.all_data[u_input]["password"] == pw_hash:
                    st.session_state.current_user = u_input
                    st.rerun()
                else: st.sidebar.error("❌ 密碼錯誤")
    st.stop()

# --- 3. 側邊欄 ---
st.sidebar.title(f"👤 {current_user}")
menu = st.sidebar.radio("功能選單", ["📈 我的資產", "🧮 成本攤平計算器", "📅 財經行事曆"])

if st.sidebar.button("登出系統"):
    del st.session_state.current_user
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("⚙️ 費率設定")
fee_rate = st.sidebar.slider("台股手續費折數", 0.1, 1.0, 0.28, 0.01)

# --- 4. 主功能：我的資產 ---
if menu == "📈 我的資產":
    st.title(f"📈 {current_user} 的投資即時儀表板")
    
    with st.expander("📝 新增持股資料"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("股票名稱")
            code = c2.text_input("代碼 (.TW / AAPL)")
            buy_p = c3.number_input("買入均價", min_value=0.0)
            qty = c1.number_input("股數", min_value=1)
            tgt = c2.number_input("停利價", min_value=0.0)
            stp = c3.number_input("停損價", min_value=0.0)
            if st.form_submit_button("➕ 加入清單"):
                if name and code:
                    st.session_state.all_data[current_user]["stocks"].append({
                        "name": name, "code": code.upper(), "buy_price": buy_p, 
                        "qty": qty, "target": tgt, "stop": stp
                    })
                    save_all_data(st.session_state.all_data)
                    st.rerun()

    user_stocks = st.session_state.all_data[current_user]["stocks"]
    if user_stocks:
        results = []
        total_tw = 0
        total_us =
