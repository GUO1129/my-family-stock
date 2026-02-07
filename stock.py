import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 後端 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 設定 ---
st.set_page_config(page_title="家族投資", layout="wide")
st.markdown("<style>div[data-testid='metric-container']{background-color:rgba(28,131,225,0.1);border:1px solid rgba(28,131,225,0.3);padding:15px;border-radius:15px;}</style>", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入 ---
if not u:
    st.title("🛡️ 家族投資管理系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 選單 ---
m = st.sidebar.radio("功能選單", ["📊 資產管理", "📅 股利日曆", "🧮 攤平工具"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()

# --- 5. 資產管理 ---
if m == "📊 資產管理":
    st.title("📈 投資儀表板")
    with st.expander("➕ 新增持股"):
        with st.form("add_f"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱"); t = c1.text_input("代碼 (2330.TW)")
            p = c2.number_input("買入均價"); q = c2.number_input("股數", min_value=1.0)
            tg = c1.number_input("停利價"); sp = c2.number_input("停損價"); dv = c2.number_input("單股股利")
            if st.form_submit_button("儲存"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); h =
