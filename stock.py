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
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
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
    if st.sidebar.button("登入/註冊"):
        if id and pw:
            p_h = hsh(pw)
            if id not in st.session_state.db:
                st.session_state.db[id] = {"p": p_h, "s": []}
                sav(st.session_state.db)
            if st.session_state.db[id]["p"] == p_h:
                st.session_state.u = id
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 {u}")
m = st.sidebar.radio("選單", ["資產", "計算", "日曆"])
if st.sidebar.button("登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產頁面 ---
if m == "資產":
    st.title("📈 投資儀表板")
    with st.expander("➕ 新增"):
        with st.form("a", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
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
                # 這裡最關鍵，拆開寫防止截斷
                obj = yf.Ticker(i["t"])
                d = obj.history(period="1d")
                c = round(d["Close"].iloc[-1], 2)
                v = round(c * i["q"])
                res.append({"股票":i["n"], "現價":c, "市值":v, "代碼":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='市值', names='股票', title="比例"), use_container_width=True)
            
            with r:
                sel = st.selectbox("查看走勢", df["股票"].tolist())
                cod = df[df["股票"] == sel]["代碼"].values[0]
                h_d = yf.Ticker(cod).history(period="6mo")
                if not h_d.empty:
                    st.plotly_chart(px.line(h_d, y="Close", title=f"{sel} 半年走勢"), use_container_width=True)

            if st.button("🗑️ 清空所有持股"):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db)
                st.rerun()
    else: st.info("尚無資料")

# --- 5. 計算器 ---
elif m == "計算":
    st.title("🧮 成本攤平")
    p1 = st.number_input("原價", value=100.0)
    q1 = st.number_input("原量", value=1000)
    p2 = st.number_input("加碼", value=90.0)
    q2 = st.number_input("加量", value=1000)
    res = ((p1*q1)+(p2*q2))/(q1+q2)
    st.metric("新均價", f"{round(res, 2)}")

# --- 6. 日曆 ---
elif m == "日曆":
    st.title("📅 財經日曆")
    for i in st.session_state.db[u]["s"]:
        try:
            cl = yf.Ticker(i["t"]).calendar
            if not cl.empty: st.write(f"{i['n']}: {cl.iloc[0,0]}")
        except: continue
