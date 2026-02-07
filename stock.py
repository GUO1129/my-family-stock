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

# --- 2. 登入系統 (維持原樣) ---
st.set_page_config(page_title="家族投資管理系統", layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ 家族投資管理系統")
    uid = st.sidebar.text_input("請輸入帳號")
    upw = st.sidebar.text_input("請輸入密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if uid and upw:
            ph = hsh(upw); db = st.session_state.db
            if uid not in db:
                db[uid] = {"p": ph, "s": []}
                sav(db)
            if db[uid]["p"] == ph:
                st.session_state.u = uid
                st.rerun()
    st.stop()

# --- 3. 側邊選單 ---
st.sidebar.write(f"👤 使用者: {u}")
m = st.sidebar.radio("功能選單", ["📊 資產管理", "🧮 攤平工具"])
if st.sidebar.button("安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產管理 (完整功能回歸) ---
if m == "📊 資產管理":
    st.title("📈 我的投資即時儀表板")
    with st.expander("📝 新增持股資料"):
        with st.form("add_f"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱 (例：台積電)")
            t = c1.text_input("代碼 (例：2330.TW)")
            p = c2.number_input("買入平均價格", min_value=0.0)
            q = c2.number_input("持有股數", min_value=1.0)
            tg = c1.number_input("停利目標價", min_value=0.0)
            sp = c2.number_input("停損預警價", min_value=0.0)
            if st.form_submit_button("儲存至清單"):
                if n and t:
                    st.session_state.db[u]["s"].append(
                        {"n":n,"t":t.
