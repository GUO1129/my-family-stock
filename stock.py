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
    with open(F, "r", encoding="utf-8") as f: return json.load(f)
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 設定 ---
st.set_page_config(page_title="家族投資", layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入 ---
if not u:
    st.title("🛡️ 家族投資系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: 
                st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 選單 ---
m = st.sidebar.radio("選單", ["📊 資產管理", "📅 股利日曆", "🧮 攤平工具"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()

# --- 5. 資產管理 ---
if m == "📊 資產管理":
    st.title("📈 投資儀表板")
    with st.expander("➕ 新增持股"):
        with st.form("add_f"):
            n = st.text_input("名稱"); t = st.text_input("代碼(如:2330.TW)")
            p = st.number_input("買價", min_value=0.0); q = st.number_input("股數", min_value=1.0)
            tg = st.number_input("停利價"); sp = st.number_input("停損價")
            dv = st.number_input("年股利")
            if st.form_submit_button("儲存"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); h = tk.history(period="1d")
                curr = round(h["Close"].iloc[-1], 2)
                stt = "⚖️ 穩定"
                if i.get("tg",0)>0 and curr>=i["tg"]: stt="🎯 停利"
                if i.get("sp",0)>0 and curr<=i["sp"]: stt="⚠️ 停損"
                mv = round(curr * i["q"]); pf = mv - (i["p"] * i["q"])
                res.append({"股票":i["n"],"現價":curr,"狀態":stt,"市值":mv,"損益":round(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
            except: continue
        if res:
            df = pd.DataFrame(res); st.dataframe
