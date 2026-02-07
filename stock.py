import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 0. 中文標籤 (放在最前面，防止後方截斷報錯) ---
T1 = "🛡️ 家族投資系統"
T2 = "資產管理"
T3 = "股利日曆"
T4 = "攤平計算"
T5 = "📈 投資儀表板"
T6 = "歷史走勢 (半年)"

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

# --- 2. 登入 ---
st.set_page_config(page_title="家族投資", layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title(T1)
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: 
                st.session_state.u=uid
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 {u}")
m = st.sidebar.radio("選單", [T2, T3, T4])
if st.sidebar.button("登出"): 
    st.session_state.u=None
    st.rerun()

# --- 4. 資產管理 ---
if m == T2:
    st.title(T5)
    with st.expander("📝 新增"):
        with st.form("f"):
            n = st.text_input("股票名稱")
            t = st.text_input("代碼(例:2330.TW)")
            p = st.number_input("買價", value=0.0)
            q = st.number_input("股數", value=1.0)
            tg = st.number_input("停利價", value=0.0)
            sp = st.number_input("停損價", value=0.0)
            dv = st.number_input("單股股利", value=0.0)
            if st.form_submit_button("儲存"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()

    sk = st.session_state.db[u].get("s", [])
