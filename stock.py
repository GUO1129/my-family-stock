import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO

# --- 1. 資料庫與安全 ---
DB_FILE = "users_stock_data.json"

def make_hash(p):
    return hashlib.sha256(str.encode(p)).hexdigest()

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 2. 登入系統 ---
st.set_page_config(page_title="家族投資究極系統", layout="wide")
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()

user = st.session_state.get('user', None)

if not user:
    st.title("🛡️ 家族投資管理系統")
    u_in = st.sidebar.text_input("帳號")
    p_in = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if u_in and p_in:
            h = make_hash(p_in)
            if u_in not in st.session_state.all_data:
                st.session_state.all_data[u_in] = {"password": h, "stocks": []}
                save_data(st.session_state.all_data)
            if st.session_state.all_data[u_in]["password"] == h:
                st.session_state.user = u_in
                st.rerun()
            else: st.sidebar.error("密碼錯誤")
    st.stop()

# --- 3. 側邊選單 ---
st.sidebar.title(f"👤 {user}")
menu = st.sidebar.radio("功能", ["📈 我的資產", "🧮 成本攤平", "📅 行事曆"])
if st.sidebar.button("登出"):
    del st.session_state.user
    st.rerun()

# --- 4. 我的資產 ---
if menu == "📈 我的資產":
    st.title("📈 投資儀表板")
    with st.expander("📝 新增持股"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("名稱")
            code = c2.text_input("代碼 (如 2330.TW)")
            b_p = c3.number_input("買入價", min_value=0.0)
            qty = c1.number_input("股數", min_value=1)
            tgt = c2.number_input("停利價", min_value=0.0)
            stp = c3.number_input("停損價", min_value=0.0)
            if st.form_submit_button("➕ 加入"):
                if name and code:
                    st.session_state.all_data[user]["stocks"].append({
                        "name": name, "code": code.upper(), "buy_price": b_p, 
                        "qty": qty, "target": tgt, "stop": stp
                    })
                    save_data(st.session_state.all_data)
                    st.rerun()

    stocks = st.session_state.all_data[user]["stocks"]
    if stocks:
        res, t_tw, t_us = [], 0.0, 0.0
        with st.spinner('更新股價中...'):
            for s in stocks:
                try:
                    curr = round(yf.Ticker(s["code"]).history(period="1d")['Close'].iloc[-1], 2)
