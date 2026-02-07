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

# --- 2. 強化對比美化 CSS (針對清晰度優化) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    /* 1. 深藍背景 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    /* 2. 強制所有文字為高亮度白色 */
    html, body, [class*="st-"] {
        color: #FFFFFF !important;
        font-family: 'PingFang TC', 'Heiti TC', sans-serif;
    }
    /* 3. 側邊欄標籤強化 */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    /* 4. 輸入框標籤與內容 */
    label[data-testid="stWidgetLabel"] p {
        color: #E2E8F0 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    input {
        background-color: #000000 !important;
        color: #00FF00 !important; /* 輸入文字用亮綠色，最清楚 */
        border: 1px solid #60A5FA !important;
    }
    /* 5. 表格對比強化 */
    .stDataFrame td, .stDataFrame th {
        color: #FFFFFF !important;
        background-color: rgba(255,255,255,0.05) !important;
    }
    /* 6. Metric (數據卡片) 清晰化 */
    [data-testid="stMetricValue"] {
        color: #60A5FA !important;
        text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
    }
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    /* 7. 下拉選單顏色 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入畫面 ---
if not u:
    st.markdown("<h1 style='text-align: center; color: #60A5FA; text-shadow: 2px 2px 4px #000;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='background:rgba(255,255,255,0.1); padding:30px; border-radius:20px; border:1px solid #60A5FA;'>", unsafe_allow_html=True)
        uid = st.text_input("👤 使用者帳號")
        upw = st.text_input("🔑 登入密碼", type="password")
        if st.button("🚀 啟動戰情室"):
            if uid and upw:
                ph=hsh(upw); db=st.session_state.db
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 🚀 在線: {u}")
m = st.sidebar.radio("導覽菜單", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
st.sidebar.markdown("---")
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])

# --- 5. 功能：資產儀表板 ---
if m == "📈 資產儀表板":
    st.markdown("<h2 style='color: #60A5FA;'>💎 持股即時戰報</h2>", unsafe_allow_html=True)
    with st.expander("📝 展開/收合：新增持股項目"):
        c1, c2 = st.columns(2)
        n = c1.text_input("名稱"); t = c1.text_input("代碼(例:2330.TW)")
        p = c2.number_input("平均成本", 0.0); q = c2.number_input("持有股數", 1.0)
        tg = c1.number_input("停利目標", 0.0); sp = c2.number_input("停損預警", 0.0)
        dv = c2.number_input("年股利(單股)", 0.0)
        if st.button("💾 儲存至雲端"):
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
            
            st.markdown("### 📊 核心財務數據")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總損益", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預估年利", f"{df['年股利'].sum():,} 元")
            
            st.markdown("---")
            l, r = st.columns([1, 1.5])
            with l:
                fig_pie = px.pie(df, values='市值', names='股票', hole=0.5, title="資產比例")
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_pie, use_container_width=True)
            with r:
                sel = st.selectbox("分析歷史趨勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    fig_l = px.line(h, y="Close", title=f"{sel} 歷史趨勢")
                    fig_l.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
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
                        ev.append({"股票": i["n"], "日期": d_v.strftime('%Y-%m-%d'), "內容": "預計公告"})
            except: continue
        if ev: st.table(pd.DataFrame(ev))
        else: st.info("近期無重大事件。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    st.markdown("<div style='background:rgba(255,255,255,0.1); padding:20px; border-radius:15px; border:1px solid #60A5FA;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    p1 = c1.number_input("原始單價", value=100.0)
    q1 = c1.number_input("原始股數", value=1000.0)
    p2 = c2.number_input("加碼單價", value=90.0)
    q2 = c2.number_input("加碼股數", value=1000.0)
    avg = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
    st.divider()
    st.metric("💡 攤平後預估均價", f"{avg} 元")
    st.markdown("</div>", unsafe_allow_html=True)
