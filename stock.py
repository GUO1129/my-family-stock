import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib

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

# --- 2. 經典明亮模式 CSS (白底黑字) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    /* 全域背景設為淺亮灰色，讓白色卡片更突出 */
    .stApp {
        background-color: #f4f7f6;
    }
    /* 強制所有文字為深黑色，確保清晰度 */
    html, body, [class*="st-"], p, label {
        color: #1a202c !important;
        font-family: 'PingFang TC', 'Heiti TC', sans-serif;
        font-weight: 500 !important;
    }
    /* 側邊欄改為淺灰色背景，深黑字 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #1a202c !important;
    }
    /* 卡片設計 (Metrics)：白底深黑字，藍色邊框 */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 2px solid #3182ce !important;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 15px;
    }
    [data-testid="stMetricLabel"] { color: #4a5568 !important; }
    [data-testid="stMetricValue"] { color: #2b6cb0 !important; font-weight: 800 !important; }

    /* 表格強化：白底黑字，分界明顯 */
    .stDataFrame td, .stDataFrame th {
        color: #1a202c !important;
        background-color: #ffffff !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    /* 輸入框美化 */
    input {
        background-color: #ffffff !important;
        color: #1a202c !important;
        border: 1px solid #cbd5e0 !important;
    }
    /* 標題漸層藍 */
    h1, h2, h3 {
        color: #2c5282 !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入畫面 ---
if not u:
    st.markdown("<h1 style='text-align: center;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='background:#ffffff; padding:30px; border-radius:20px; border:1px solid #e2e8f0; box-shadow: 0 10px 15px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        uid = st.text_input("👤 帳號")
        upw = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 進入系統"):
            if uid and upw:
                ph=hsh(upw); db=st.session_state.db
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 當前用戶: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
st.sidebar.markdown("---")
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])

# --- 5. 功能：資產儀表板 ---
if m == "📈 資產儀表板":
    st.markdown("## 💎 持股即時戰報")
    with st.expander("📝 點擊此處：新增持股"):
        c1, c2 = st.columns(2)
        n = c1.text_input("股票名稱"); t = c1.text_input("代碼 (例: 2330.TW)")
        p = c2.number_input("平均成本", 0.0); q = c2.number_input("持有股數", 1.0)
        tg = c1.number_input("停利目標價", 0.0); sp = c2.number_input("停損預警價", 0.0)
        dv = c2.number_input("單股年股利", 0.0)
        if st.button("💾 儲存資料"):
            if n and t:
                st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                sav(st.session_state.db); st.rerun()

    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
                curr = round(df_h["Close"].values[-1], 2)
                tg_p = i.get("tg", 0); sp_p = i.get("sp", 0)
                dt = f"{round(((tg_p-curr)/curr)*100,1)}%" if tg_p > 0 else "-"
                ds = f"{round(((sp_p-curr)/curr)*100,1)}%" if sp_p > 0 else "-"
                stt = "⚖️ 穩定"
                if tg_p > 0 and curr >= tg_p: stt = "🎯 停利"
                elif sp_p > 0 and curr <= sp_p: stt = "⚠️ 停損"
                mv = round(curr * i["q"]); pf = mv - (i["p"] * i["q"])
                res.append({"股票":i["n"],"現價":curr,"狀態":stt,"距停利":dt,"距停損":ds,"市值":mv,"損益":int(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            st.markdown("### 📊 核心財務指標")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預估年股利", f"{df['年股利'].sum():,} 元")
            
            st.divider()
            l, r = st.columns([1, 1.5])
            with l:
                fig_pie = px.pie(df, values='市值', names='股票', hole=0.4, title="資產配比圖")
                fig_pie.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color="black")
                st.plotly_chart(fig_pie, use_container_width=True)
            with r:
                sel = st.selectbox("分析歷史趨勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    fig_l = px.line(h, y="Close", title=f"{sel} 6個月趨勢")
                    fig_l.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color="black")
                    st.plotly_chart(fig_l, use_container_width=True)
    else: st.info("目前清單為空。")

# --- 6. 股利日曆 ---
elif m == "📅 股利日曆":
    st.title("📅 事件追蹤")
    if sk:
        ev = []
        for i in sk:
            try:
                c = yf.Ticker(i["t"]).calendar
                if c is not None and not c.empty:
                    d_v = c.iloc[0, 0]
                    if hasattr(d_v, 'strftime'):
                        ev.append({"股票": i["n"], "日期": d_v.strftime('%Y-%m-%d'), "內容": "財務/配息公告"})
            except: continue
        if ev: st.table(pd.DataFrame(ev))
        else: st.info("無近期事件。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平計算")
    st.markdown("<div style='background:#ffffff; padding:20px; border-radius:15px; border:1px solid #3182ce;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    p1 = c1.number_input("原始單價", value=100.0)
    q1 = c1.number_input("原始股數", value=1000.0)
    p2 = c2.number_input("加碼單價", value=90.0)
    q2 = c2.number_input("加碼股數", value=1000.0)
    avg = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
    st.divider()
    st.metric("均價試算結果", f"{avg} 元")
    st.markdown("</div>", unsafe_allow_html=True)
