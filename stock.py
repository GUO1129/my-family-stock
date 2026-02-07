import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 0. 中文介面標籤預載 (確保不被截斷) ---
T_APP = "🛡️ 家族投資管理系統"
T_ID = "請輸入帳號"
T_PW = "請輸入密碼"
T_LOG = "登入 / 註冊"
T_OUT = "安全登出"
T_DB = "📈 我的投資儀表板"
T_ADD = "➕ 新增持股資料"
T_NAME = "股票名稱 (例：台積電)"
T_CODE = "代碼 (例：2330.TW)"
T_BP = "買入平均價格"
T_BQ = "持有股數"
T_SAV = "儲存至清單"
T_EXC = "📥 匯出 Excel 報表"
T_PIE = "資產佔比比例"
T_CHT = "查看歷史走勢"
T_CLR = "🗑️ 清空所有紀錄"
T_CAL = "🧮 成本攤平計算器"
T_EMPTY = "目前清單是空的，請先新增股票。"

# --- 1. 後端處理 ---
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
st.set_page_config(page_title=T_APP, layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title(T_APP)
    uid = st.sidebar.text_input(T_ID)
    upw = st.sidebar.text_input(T_PW, type="password")
    if st.sidebar.button(T_LOG):
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
st.sidebar.write(f"👤 使用者: {u}")
m = st.sidebar.radio("選單", ["📊 資產管理", "🧮 攤平工具"])
if st.sidebar.button(T_OUT):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產頁面 ---
if m == "📊 資產管理":
    st.title(T_DB)
    with st.expander(T_ADD):
        with st.form("add_form", clear_on_submit=True):
            n = st.text_input(T_NAME)
            t = st.text_input(T_CODE)
            p = st.number_input(T_BP, min_value=0.0)
            q = st.number_input(T_BQ, min_value=1.0)
            if st.form_submit_button(T_SAV):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q})
                    sav(st.session_state.db)
                    st.rerun()

    sk = st.session_state.db[u]["s"]
    if sk:
        res = []
        with st.spinner('讀取即時股價中...'):
            for i in sk:
                try:
                    o = yf.Ticker(i["t"])
                    h = o.history(period="1d")
                    c = round(h["Close"].iloc[-1], 2)
                    v = round(c * i["q"])
                    res.append({"股票":i["n"],"現價":c,"市值":v,"代碼":i["t"]})
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            # Excel 匯出
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w:
                df.to_excel(w, index=False)
            st.download_button(T_EXC, bio.getvalue(), "list.xlsx")

            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='市值', names='股票', title=T_PIE), use_container_width=True)
            with r:
                sel = st.selectbox(T_CHT, df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                hd = yf.Ticker(cod).history(period="6mo")
                if not hd.empty:
                    st.plotly_chart(px.line(hd, y="Close", title=f"{sel} 半年走勢"), use_container_width=True)
            
            if st.sidebar.button(T_CLR):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db)
                st.rerun()
    else: st.info(T_EMPTY)

# --- 5. 工具頁面 ---
elif m == "🧮 攤平工具":
    st.title(T_CAL)
    p1 = st.number_input("原始買入價格", value=100.0)
    q1 = st.number_input("原始持有股數", value=1000.0)
    p2 = st.number_input("加碼買入價格", value=90.0)
    q2 = st.number_input("加碼買入股數", value=1000.0)
    total_avg = ((p1*q1)+(p2*q2))/(q1+q2)
    st.metric("攤平後平均成本", round(total_avg, 2))
