import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib

# --- 1. 後端資料 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 乾淨明亮模式 CSS (修正重疊問題) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    /* 基礎背景 */
    .stApp { background-color: #FFFFFF; }
    
    /* 強制文字顏色：黑 */
    .main .block-container p, .main .block-container label, .main .block-container span {
        color: #000000 !important;
        font-weight: 500;
    }
    
    /* 標題顏色 */
    h1, h2, h3 { color: #1E3A8A !important; }

    /* Metric 數據卡片美化 */
    [data-testid="stMetric"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #2563EB !important; }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] { background-color: #F1F5F9 !important; }
    
    /* 修正展開面板後的間距，防止重疊 */
    .stExpander { margin-bottom: 2rem !important; border: 1px solid #E2E8F0 !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入 ---
if not u:
    st.markdown("<h1 style='text-align: center;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.2, 1])
    with c2:
        uid = st.text_input("👤 帳號")
        upw = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 登入系統", use_container_width=True):
            if uid and upw:
                ph=hsh(upw); db=st.session_state.db
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])

# --- 5. 功能：資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    # 這裡加入一個清晰的邊界
    with st.expander("📝 點擊此處：新增持股項目"):
        with st.form("my_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 2330.TW)")
            p = c2.number_input("平均成本", min_value=0.0, step=0.1)
            q = c2.number_input("持有股數", min_value=1.0, step=1.0)
            tg = c1.number_input("停利目標價", min_value=0.0)
            sp = c2.number_input("停損預警價", min_value=0.0)
            dv = c1.number_input("單股年股利", min_value=0.0)
            if st.form_submit_button("💾 儲存資料"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()

    # 加入一點垂直間距
    st.markdown("<br>", unsafe_allow_html=True)

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
            
            st.markdown("### 📊 財務總覽")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預計年股利", f"{df['年股利'].sum():,} 元")
            
            st.divider()
            l, r = st.columns([1, 1.5])
            with l:
                fig_pie = px.pie(df, values='市值', names='股票', hole=0.4, title="資產配比")
                st.plotly_chart(fig_pie, use_container_width=True)
            with r:
                sel = st.selectbox("分析趨勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    st.plotly_chart(px.line(h, y="Close", title=f"{sel} 趨勢"), use_container_width=True)
    else:
        st.info("目前清單為空，請點擊上方展開選單新增。")

# --- 6. 股利日曆 ---
elif m == "📅 股利日曆":
    st.title("📅 事件追蹤")
    if sk:
        ev = []
        for i in sk:
            try:
                c = yf.Ticker(i["t"]).calendar
                if c is not None and not c.empty:
                    ev.append({"股票": i["n"], "日期": c.iloc[0, 0].strftime('%Y-%m-%d')})
            except: continue
        if ev: st.table(pd.DataFrame(ev))
        else: st.info("近期無重大事件。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", value=100.0)
    q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0)
    q2 = st.number_input("加碼數", value=1000.0)
    avg = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
    st.metric("💡 均價結果", f"{avg} 元")
