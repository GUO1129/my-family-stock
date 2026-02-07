import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 後端資料處理 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 頁面設定與美化 ---
st.set_page_config(page_title="家族投資管理系統", layout="wide")
st.markdown("""<style>
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.3);
        padding: 15px; border-radius: 15px;
    }
</style>""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入系統 ---
if not u:
    st.title("🛡️ 家族投資管理系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: 
                st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 側邊選單 ---
m = st.sidebar.radio("功能選單", ["📊 資產管理", "📅 股利日曆", "🧮 攤平工具"])
if st.sidebar.button("安全登出"): st.session_state.u=None; st.rerun()

# --- 5. 資產管理 ---
if m == "📊 資產管理":
    st.title("📈 我的投資即時儀表板")
    with st.expander("➕ 新增持股資料"):
        with st.form("add_f"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 2330.TW)")
            p = c2.number_input("買入均價", min_value=0.0)
            q = c2.number_input("持有股數", min_value=1.0)
            tg = c1.number_input("停利目標價")
            sp = c2.number_input("停損預警價")
            dv = c2.number_input("年股利 (單股)")
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
                px_l = h["Close"].tolist()
                curr = round(px_l[-1], 2)
                stt = "⚖️ 穩定"
                if i.get("tg",0)>0 and curr>=i["tg"]: stt="🎯 停利"
                if i.get("sp",0)>0 and curr<=i["sp"]: stt="⚠️ 停損"
                mv = round(curr * i["q"]); pf = mv - (i["p"] * i["q"])
                res.append({"股票":i["n"],"現價":curr,"狀態":stt,"市值":mv,"損益":round(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
            except: continue
        if res:
            df = pd.DataFrame(res); st.dataframe(df, use_container_width=True)
            ca, cb, cc = st.columns(3)
            ca.metric("💎 總市值", f"{df['市值'].sum():,} 元")
            cb.metric("🧧 總股利", f"{df['年股利'].sum():,} 元")
            cc.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            st.divider(); l, r = st.columns([1, 1.2])
            l.plotly_chart
