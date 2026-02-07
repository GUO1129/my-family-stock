import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO
from datetime import datetime

# --- 1. 資料庫與安全邏輯 ---
DB_FILE = "users_stock_data.json"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_all_data(all_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --- 2. 網頁初始化 ---
st.set_page_config(page_title="家族投資究極系統 3.0", layout="wide")

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_all_data()

current_user = st.session_state.get('current_user', None)

if not current_user:
    st.title("🛡️ 家族投資管理系統 3.0")
    st.sidebar.title("🔐 系統登入")
    user_id_input = st.sidebar.text_input("使用者帳號", key="login_user_id")
    password_input = st.sidebar.text_input("密碼", type="password", key="login_password")

    if st.sidebar.button("登入 / 建立帳號"):
        if user_id_input and password_input:
            pw_hash = make_hash(password_input)
            if user_id_input not in st.session_state.all_data:
                st.session_state.all_data[user_id_input] = {"password": pw_hash, "stocks": []}
                save_all_data(st.session_state.all_data)
                st.session_state.current_user = user_id_input
                st.rerun()
            else:
                if st.session_state.all_data[user_id_input]["password"] == pw_hash:
                    st.session_state.current_user = user_id_input
                    st.rerun()
                else: st.sidebar.error("❌ 密碼錯誤")
    st.stop()

# --- 3. 側邊欄：功能選單 ---
st.sidebar.title(f"👤 {current_user}")
menu = st.sidebar.radio("功能選單", ["📈 我的資產", "🧮 成本攤平計算器", "📅 財經行事曆"])

if st.sidebar.button("登出系統"):
    del st.session_state.current_user
    st.rerun()

st.sidebar.divider()
fee_discount = st.sidebar.slider("手續費折數", 0.1, 1.0, 0.28, 0.01)

# --- 4. 主功能：我的資產 ---
if menu == "📈 我的資產":
    st.title(f"📈 {current_user} 的投資即時儀表板")
    
    with st.
