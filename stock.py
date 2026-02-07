import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 0. 標籤定義 (放在最前面防止邏輯截斷) ---
L_TITLE = "家族投資系統"
L_ID = "帳號"
L_PW = "密碼"
L_LOGIN = "登入"
L_OUT = "登出"
L_NAME = "股票名稱"
L_CODE = "代碼"
L_PRICE = "買價"
L_QTY = "股數"
L_SAVE = "存入"
L_DNL = "匯出Excel"
L_CLR = "清空資料"

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
    st.title(L_TITLE)
    uid = st.sidebar.text_input(L_ID)
    upw = st.sidebar.text_input(L_PW, type="password")
    if st.sidebar.button(L_LOGIN):
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
st.sidebar.write(f"User: {u}")
m = st.sidebar.radio("Menu", ["Stock", "Tool"])
if st.sidebar.button(L_OUT):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產頁面 ---
if m == "Stock":
    st.title("📈 Dashboard")
    with st.expander("Add"):
        with st.form("f", clear_on_submit=True):
            n = st.text_input(L_NAME)
            t = st.text_input(L_CODE)
            p = st.number_input(L_PRICE, min_value=0.0)
            q = st.number_input(L_QTY, min_value=1.0)
            if st.form_submit_button(L_SAVE):
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
                h = o.history(period="1d")
                c = round(h["Close"].iloc[-1], 2)
                v = round(c * i["q"])
                res.append({"Name":i["n"],"Price":c,"Value":v,"Code":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            # Excel
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w:
                df.to_excel(w, index=False)
            st.download_button(L_DNL, bio.getvalue(), "list.xlsx")

            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='Value', names='Name', title="Asset"), use_container_width=True)
            with r:
                sel = st.selectbox("Chart", df["Name"].tolist())
                cod = df[df["Name"]==sel]["Code"].values[0]
                hd = yf.Ticker(cod).history(period="6mo")
                if not hd.empty:
                    st.plotly_chart(px.line(hd, y="Close", title=sel), use_container_width=True)
            
            if st.sidebar.button(L_CLR):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db)
                st.rerun()
    else: st.info("Empty")

# --- 5. 工具頁面 ---
elif m == "Tool":
    st.title("🧮 Calculator")
    p1 = st.number_input("P1", value=100.0)
    q1 = st.number_input("Q1", value=1000.0)
    p2 = st.number_input("P2", value=90.0)
    q2 = st.number_input("Q2", value=1000.0)
    st.metric("Avg", round(((p1*q1)+(p2*q2))/(q1+q2), 2))
