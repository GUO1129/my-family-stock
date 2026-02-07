import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

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

# --- 2. 介面樣式：強制明亮模式 (防止手機黑屏) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    /* 強制網頁背景與文字，無視手機系統深色模式 */
    :root { color-scheme: light; }
    
    .stApp { 
        background-color: #FFFFFF !important; 
    }
    
    /* 所有文字強制黑色 */
    .main .block-container p, 
    .main .block-container label, 
    .main .block-container span,
    .main .block-container div { 
        color: #000000 !important; 
    }
    
    /* 標題與 Metric 數值 */
    h1, h2, h3 { color: #1E3A8A !important; }
    [data-testid="stMetricValue"] { color: #2563EB !important; }
    [data-testid="stMetricLabel"] p { color: #64748B !important; }

    /* 側邊欄強制淺色 */
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; }

    /* 表格與輸入框文字修正 */
    .stDataFrame div, .stDataFrame span { color: #000000 !important; }
    input { color: #000000 !important; background-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入系統 ---
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
    
    with st.expander("📝 新增持股項目"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 2330.TW)")
            p = c2.number_input("平均成本", min_value=0.0)
            q = c2.number_input("持有股數", min_value=1.0)
            tg = c1.number_input("停利目標", min_value=0.0)
            sp = c2.number_input("停損預警", min_value=0.0)
            dv = c1.number_input("單股年股利", min_value=0.0)
            if st.form_submit_button("💾 儲存持股"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()

    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
                curr = round(df_h["Close"].values[-1], 2)
                tg_p, sp_p = i.get("tg", 0), i.get("sp", 0)
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
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label="📥 下載完整資產報表 (CSV)", data=csv, file_name=f'assets_{u}.csv', mime='text/csv')

            st.markdown("### 📊 財務總覽")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預計年股利", f"{df['年股利'].sum():,} 元")
            
            st.divider()
            
            with st.expander("🗑️ 管理/刪除持股"):
                for idx, item in enumerate(sk):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"**{item['n']}** ({item['t']})")
                    if col_b.button("刪除", key=f"del_{idx}"):
                        st.session_state.db[u]["s"].pop(idx)
                        sav(st.session_state.db); st.rerun()

            st.divider()
            l, r = st.columns([1, 1.5])
            with l:
                st.plotly_chart(px.pie(df, values='市值', names='股票', hole=0.4, title="資產配比"), use_container_width=True)
            with r:
                sel = st.selectbox("分析趨勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    st.plotly_chart(px.line(h, y="Close", title=f"{sel} 趨勢"), use_container_width=True)
    else:
        st.info("清單為空。")

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
