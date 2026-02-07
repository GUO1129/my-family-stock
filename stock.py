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
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)
# --- 2. 登入與設定 ---
st.set_page_config(page_title="家族投資", layout="wide")
st.markdown("<style>.stMetric{background-color:#1e2130;padding:10px;border-radius:10px;}</style>",unsafe_allow_html=True)
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
st.sidebar.write(f"👤 {u}")
m = st.sidebar.radio("選單", ["資產管理", "股利日曆", "攤平計算"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()
# --- 4. 資產管理 ---
if m == "資產管理":
    st.title("📈 投資儀表板")
    with st.expander("📝 新增持股"):
        with st.form("f"):
            c1,c2=st.columns(2)
            n=c1.text_input("名稱"); t=c1.text_input("代碼(例:2330.TW)")
            p=c2.number_input("買價"); q=c2.number_input("股數",min_value=1.0)
            tg=c1.number_input("停利價"); sp=c2.number_input("停損價")
            dv=c1.number_input("年股利(單股)")
            if st.form_submit_button("儲存"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk=yf.Ticker(i["t"]); h=tk.history(period="1d"); curr=round(h["Close"].iloc[-1],2)
                stt="⚖️ 穩定"
                if i.get("tg") and curr>=i["tg"]: stt="🎯 停利"
                if i.get("sp") and curr<=i["sp"]: stt="⚠️ 停損"
                mv=round(curr*i["q"]); pf=mv-(i["p"]*i["q"]); yv=round(i.get("dv",0)*i["q"])
                res.append({"股票":i["n"],"現價":curr,"狀態":stt,"市值":mv,"損益":round(pf),"年股利":yv,"代碼":i["t"]})
            except: continue
        if res:
            df=pd.DataFrame(res); st.dataframe(df,use_container_width=True)
            ca,cb=st.columns(2); ca.metric("總市值",f"{df['市值'].sum():,}"); cb.metric("總股利",f"{df['年股利'].sum():,}")
            # Excel
            bio=BytesIO()
            with pd.ExcelWriter(bio,engine='xlsxwriter') as w: df.to_excel(w,index=False)
            st.download_button("📥 匯出Excel",bio.getvalue(),"list.xlsx")
            st.divider(); l,r=st.columns(2)
            l.plotly_chart(px.pie(df,values='市值',names='股票',title="比例"),use_container_width=True)
            with r:
                sel=st.selectbox("走勢圖",df["股票"].tolist())
                cod=df[df["股票"]==sel]["代碼"].values[0]
                hd=yf.Ticker(cod).history(period="6mo")
                if not hd.empty: st.plotly_chart(px.line(hd,y="Close",title=sel),use_container_width=True)
            if st.sidebar.button("🗑️ 清空紀錄"): st.session_state.db[u]["s"]=[]; sav(st.session_state.db); st.rerun()
    else: st.info("空清單")
# --- 5. 日曆 ---
elif m == "股利日曆":
    st.title("📅 財經日曆")
    sk=st.session_state.db[u].get("s",[])
    ev=[]
    for i in sk:
        try:
            cl=yf.Ticker(i["t"]).calendar
            if cl is not None and not cl.empty: ev.append({"股票":i["n"],"日期":cl.iloc[0,0].strftime('%Y-%m-%d')})
        except: continue
    if ev: st.table(pd.DataFrame(ev))
    else: st.info("無事件")
# --- 6. 攤平 ---
elif m == "攤平計算":
    st.title("🧮 攤平工具")
    p1=st.number_input("原價",value=100.0); q1=st.number_input("原量",value=1000.0)
    p2=st.number_input("新價",value=90.0); q2=st.number_input("新量",value=1000.0)
    st.metric("新成本",round(((p1*q1)+(p2*q2))/(q1+q2),2))
