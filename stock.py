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
    if os.path.exists(F):
        try:
            with open(F, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 登入 ---
st.set_page_config(layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ 家族投資系統")
    id = st.sidebar.text_input("帳號")
    pw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        if id and pw:
            ph = hsh(pw)
            if id not in st.session_state.db:
                st.session_state.db[id] = {"p": ph, "s": []}
                sav(st.session_state.db)
            if st.session_state.db[id]["p"] == ph:
                st.session_state.u = id
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 {u}")
m = st.sidebar.radio("選單", ["資產", "工具"])
if st.sidebar.button("登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產 ---
if m == "資產":
    st.title("📈 儀表板")
    with st.expander("➕ 新增"):
        with st.form("f", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            n = c1.text_input("名稱")
            t = c2.text_input("代碼")
            p = c3.number_input("買價", min_value=0.0)
            q = c1.number_input("股數", min_value=1)
            if st.form_submit_button("存入"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q})
                    sav(st.session_state.db)
                    st.rerun()

    sk = st.session_state.db[u]["s"]
    if sk:
        res = []
        for i in sk:
            try:
                o = yf.Ticker(i["t"])
                c = round(o.history(period="1d")["Close"].iloc[-1], 2)
                v = round(c * i["q"])
                res.append({"股票":i["n"],"現價":c,"市值":v,"代碼":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            # Excel
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w:
                df.to_excel(w, index=False)
            st.download_button("📥 匯出
