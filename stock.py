import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 資料處理 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if os.path.exists(F):
        try:
            with open(F, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 登入系統 ---
st.set_page_config(layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ 家族投資系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        if uid and upw:
            ph = hsh(upw)
            if uid not in st.session_state.db:
                st.session_state.db[uid] = {"p": ph, "s": []}
                sav(st.session_state.db)
            if st.session_state.db[uid]["p"] == ph:
                st.session_state.u = uid
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"使用者: {u}")
m = st.sidebar.radio("選單", ["資產", "工具"])
if st.sidebar.button("登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產頁面 ---
if m == "資產":
    st.title("📈 投資儀表板")
    with st.expander("➕ 新增持股"):
        with st.form("f", clear_on_submit=True):
            n = st.text_input("股票名稱")
            t = st.text_input("代碼 (例
