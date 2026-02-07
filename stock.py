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

# --- 2. 風格 ---
st.set_page_config(page_title="家族投資", layout="wide")
st.markdown("<style>div[data-testid='metric-container']{background-color:rgba(28,131,225,0.1);border:1px solid rgba(28,131,225,0.3);padding:15px;border-radius:15px;}</style>", unsafe_allow_html=True)

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
                st.session_state.u=uid
                st.rerun()
    st.stop()

# --- 4. 選單 ---
m = st.sidebar.radio("功能", ["📊 資產管理", "📅 股利日曆", "🧮 攤平工具"])
if st.sidebar.button("登出"):
    st.session_state.u=None
    st.rerun()

# --- 5. 資產管理 (徹底拆解短行) ---
if m == "📊 資產管理":
    st.title("📈 投資儀表板")
    with st.expander("➕ 新增持股"):
        with st.form("add_f"):
            n = st.text_input("名稱")
            t = st.text_input("代碼(例:2330.TW)")
            p = st.number_input("買價", min_value=0.0)
            q = st.number_input("股數", min_value=1.0)
            tg = st.number_input("停利價", min_value=0.0)
            sp = st.number_input("停損價", min_value=0.0)
            dv = st.number_input("年股利", min_value=0.0)
            if st.form_submit_button("儲存"):
                if n and t:
                    d = {"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv}
                    st.session_state.db[u]["s"].append(d)
                    sav(st.session_state.db); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"])
                h = tk.history(period="1d")
                # 解決第 71 行報錯：徹底拆開 iloc
                px_list = h["Close"].tolist()
                curr = round(px_list[-1], 2)
                
                stt = "⚖️ 穩定"
                if i.get("tg",0)>0 and curr>=i["tg"]: stt="🎯 停利"
                if i.get("sp",0)>0 and curr<=i["sp"]: stt="⚠️ 停損"
                
                mv = round(curr * i["q"])
                pf = mv - (i["p"] * i["q"])
                yv = round(i.get("dv",0) * i["q"])
                
                row = {"股票":i["n"],"現價":curr,"狀態":stt,"市值":mv,"損益":round(pf),"年股利":yv,"代碼":i["t"]}
                res.append(row)
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.write("### 💰 財務總結")
            ca, cb, cc = st.columns(3)
            ca.metric("💎 總市值", f"{df['市值'].sum():,} 元")
            cb.metric("🧧 總股利", f"{df['年股利'].sum():,} 元")
            cc.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            
            st.divider()
            l, r = st.columns([1, 1.2]) 
            l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產佔比"), use_container_width=True)
            with r:
                sel = st.selectbox("切換股票查看走勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                hist = yf.Ticker(cod).history(period="6mo")
                if not hist.empty:
                    fig = px.line(hist, y="Close", title=f"{sel} 半年走勢")
                    st.plotly_chart(fig, use_container_width=True)
            
            st.download_button("📥 匯出 Excel", df.to_csv(index=False).encode('utf-8-sig'), "list.csv")
    else: st.info("目前清單是空的")

elif m == "📅 股利日曆":
    st.title("📅 重要財經日曆")
    sk=st.session_state.db[u].get("s",[]); ev=[]
    for i in sk:
        try:
            cl=yf.Ticker(i["t"]).calendar
            if cl is not None and not cl.empty:
                ev.append({"股票":i["n"],"日期":cl.iloc[0,0].strftime('%Y-%m-%d')})
        except: continue
    if ev: st.table(pd.DataFrame(ev))
