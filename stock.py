import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 0. 中文標籤預載 (確保穩定) ---
T_APP = "🛡️ 家族投資管理系統"
T_ID = "帳號"; T_PW = "密碼"; T_LOG = "登入 / 註冊"
T_DB = "📈 我的投資即時儀表板"
T_ADD = "📝 新增持股"
T_NAME = "股票名稱"; T_CODE = "代碼 (例: 2330.TW)"
T_BP = "買入均價"; T_BQ = "股數"
T_TGT = "停利目標價"; T_STP = "停損預警價"
T_SAV = "儲存持股"; T_EXC = "📥 匯出 Excel"
T_CHT = "查看歷史走勢"; T_CLR = "🗑️ 清空紀錄"

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
st.set_page_config(page_title=T_APP, layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title(T_APP)
    uid = st.sidebar.text_input(T_ID)
    upw = st.sidebar.text_input(T_PW, type="password")
    if st.sidebar.button(T_LOG):
        if uid and upw:
            ph = hsh(upw); db = st.session_state.db
            if uid not in db:
                db[uid] = {"p": ph, "s": []}
                sav(db)
            if db[uid]["p"] == ph:
                st.session_state.u = uid
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 使用者: {u}")
m = st.sidebar.radio("選單", ["📊 資產管理", "🧮 攤平工具"])
if st.sidebar.button("登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產頁面 ---
if m == "📊 資產管理":
    st.title(T_DB)
    with st.expander(T_ADD):
        with st.form("f", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input(T_NAME)
            t = c1.text_input(T_CODE)
            p = c2.number_input(T_BP, min_value=0.0)
            q = c2.number_input(T_BQ, min_value=1.0)
            tgt = c1.number_input(T_TGT, min_value=0.0)
            stp = c2.number_input(T_STP, min_value=0.0)
            if st.form_submit_button(T_SAV):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tgt,"sp":stp})
                    sav(st.session_state.db); st.rerun()

    sk = st.session_state.db[u]["s"]
    if sk:
        res = []
        with st.spinner('更新即時數據...'):
            for i in sk:
                try:
                    o = yf.Ticker(i["t"]); h = o.history(period="1d")
                    c = round(h["Close"].iloc[-1], 2)
                    # 漲跌預估邏輯
                    stat = "⚖️ 穩定"
                    if i.get("tg", 0) > 0 and c >= i["tg"]: stat = "🎯 達標(停利)"
                    elif i.get("sp", 0) > 0 and c <= i["sp"]: stat = "⚠️ 破底(停損)"
                    
                    v = round(c * i["q"])
                    prof = v - (i["p"] * i["q"])
                    res.append({"股票":i["n"],"現價":c,"狀態":stat,"市值":v,"損益":round(prof),"代碼":i["t"]})
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w: df.to_excel(w, index=False)
            st.download_button(T_EXC, bio.getvalue(), "stock_list.xlsx")

            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產分配"), use_container_width=True)
            with r:
                sel = st.selectbox(T_CHT, df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                hd = yf.Ticker(cod).history(period="6mo")
                if not hd.empty: st.plotly_chart(px.line(hd,
