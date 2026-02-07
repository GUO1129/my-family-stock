import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib

# --- 1. 後端與資料安全 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 科技感介面設定 ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""<style>
    [data-testid="stMetric"] {background:rgba(28,131,225,0.08); border:1px solid rgba(28,131,225,0.2); padding:18px; border-radius:12px;}
    .stDataFrame {border-radius: 10px; overflow: hidden;}
    h1, h2, h3 {color: #1c83e1;}
</style>""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入系統 ---
if not u:
    st.title("🛡️ 家族投資安全系統")
    uid = st.text_input("帳號")
    upw = st.text_input("密碼", type="password")
    if st.button("確認登入"):
        if uid and upw:
            ph=hsh(upw); db=st.session_state.db
            if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
            if db[uid]["p"]==ph: 
                st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 側邊導覽 ---
st.sidebar.title(f"👤 {u}")
m = st.sidebar.radio("導覽分頁", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
if st.sidebar.button("安全登出"): st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])

# --- 5. 功能：資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 投資座艙")
    with st.expander("➕ 新增持股"):
        c1, c2 = st.columns(2)
        n = c1.text_input("名稱"); t = c1.text_input("代碼 (例: 2330.TW)")
        p = c2.number_input("平均成本", 0.0); q = c2.number_input("持有股數", 1.0)
        tg = c1.number_input("停利目標", 0.0); sp = c2.number_input("停損預警", 0.0)
        dv = c1.number_input("預估年股利 (單股)", 0.0)
        if st.button("儲存紀錄"):
            if n and t:
                st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                sav(st.session_state.db); st.rerun()

    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
                curr = round(df_h["Close"].values[-1], 2)
                # 漲跌空間計算
                tg_p = i.get("tg", 0); sp_p = i.get("sp", 0)
                dist_tg = f"{round(((tg_p-curr)/curr)*100,1)}%" if tg_p > 0 else "-"
                dist_sp = f"{round(((sp_p-curr)/curr)*100,1)}%" if sp_p > 0 else "-"
                # 狀態標籤
                stt = "⚖️ 穩定"
                if tg_p > 0 and curr >= tg_p: stt = "🎯 停利"
                elif sp_p > 0 and curr <= sp_p: stt = "⚠️ 停損"
                
                mv = round(curr * i["q"]); pf = mv - (i["p"] * i["q"])
                res.append({"股票":i["n"],"現價":curr,"狀態":stt,"距停利":dist_tg,"距停損":dist_sp,"市值":mv,"損益":int(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res); st.dataframe(df, use_container_width=True)
            st.write("### 💰 財務總覽")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預估年利", f"{df['年股利'].sum():,} 元")
            st.divider()
            l, r = st.columns([1, 1.5])
            l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產比例", hole=0.4), use_container_width=True)
            with r:
                sel = st.selectbox("個股歷史走勢 (半年)", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                hist = yf.Ticker(cod).history(period="6mo")
                if not hist.empty: st.plotly_chart(px.line(hist, y="Close", title=f"{sel} 趨勢"), use_container_width=True)
    else: st.info("目前清單是空的，請先新增股票。")

# --- 6. 功能：股利日曆 (安全性加強版) ---
elif m == "📅 股利日曆":
    st.title("📅 重要財經日曆")
    if sk:
        ev = []
        for i in sk:
            try:
                c = yf.Ticker(i["t"]).calendar
                # 檢查 calendar 是否存在且有內容，防止 iloc 報錯
                if c is not None and hasattr(c, 'empty') and not c.empty:
                    date_val = c.iloc[0, 0]
                    # 判斷抓到的是否為日期格式
                    if hasattr(date_val, 'strftime'):
                        ev.append({"股票": i["n"], "日期": date_val.strftime('%Y-%m-%d'), "備註": "預計公告/配息"})
            except: continue
        if ev: st.table(pd.DataFrame(ev))
        else: st.info("近期清單內股票無重大公告事件。")
    else: st.warning("請先新增持股。")

# --- 7. 功能：攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平計算")
    c1, c2 = st.columns(2)
    p1 = c1.number_input("原買入價", value=100.0); q1 = c1.number_input("原持股量", value=1000.0)
    p2 = c2.number_input("新加碼價", value=90.0); q2 = c2.number_input("新加碼量", value=1000.0)
    total_c = (p1 * q1) + (p2 * q2); total_q = q1 + q2
    avg = round(total_c / total_q, 2)
    st.divider()
    st.metric("攤平後均價", f"{avg} 元")
    st.info(f"總成本: {int(total_c):,} 元 | 總持股: {int(total_q):,} 股")
