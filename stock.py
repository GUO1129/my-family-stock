import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 後端與安全 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 風格設定 ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""<style>
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.3);
        padding: 15px; border-radius: 15px;
    }
</style>""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')
if not u:
    st.title("🛡️ 家族投資系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 使用者: **{u}**")
m = st.sidebar.radio("功能選單", ["資產管理", "股利日曆", "攤平工具"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()

# --- 4. 資產管理 ---
if m == "資產管理":
    st.title("📈 投資儀表板")
    with
