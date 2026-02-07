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

# --- 2. 登入與風格設定 ---
st.set_page_config(page_title="家族投資", layout="wide")
# 移除原本黑黑的背景，改用邊框美化
st.markdown("""<style>
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.3);
        padding: 15px; border-radius: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
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
m = st.sidebar.radio("選單", ["資產管理", "股利日曆", "攤平計算"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()

# --- 4. 資產管理 ---
if m == "資產管理":
    st.title("📈 投資儀表板")
    with st.expander("📝 新增持股項目"):
        with st.form("f"):
            c1,c2=st.columns(2)
            n=c1.text_input("股票名稱"); t=c1.text_input("代碼(例:2330.TW)")
            p=c2.number_input("平均買價"); q=c2.number_input("持有股數",min_value=1.0)
            tg=c1.number_input("停利價"); sp=c2.number_input("停損價")
            dv=c1.number_input("單股預估年股利")
            if st.form_submit_button("儲存至清單"):
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
            # 美化後的總結欄位
            st.write("### 💰 財務總結")
            ca,cb,cc = st.columns(3)
            ca.metric("💎 總市值", f"{df['市值'].sum():,} 元")
            cb.metric("🧧 總股利", f"{df['年股利'].sum():,} 元")
            cc.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=f"{df['損益'].sum():,}")
            
            # Excel
            bio=BytesIO()
            with pd.ExcelWriter(bio,engine='xlsxwriter') as w: df.to_excel(w,index=False)
            st.download_button("📥 匯出Excel報表",bio.getvalue(),"list.xlsx")
            st.divider(); l,r=st.columns(2)
            l.plotly_chart(px.pie(df,values='市值',names='股票',title="資產佔比比例"),use_container_width=True)
            with r:
                sel=st.selectbox("查看歷史走勢",df["股票"].tolist())
                cod=df[df["股票"]==sel]["代碼"].values
