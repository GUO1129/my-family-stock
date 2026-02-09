import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"
# 替換為全新金鑰
BACKEND_GEMINI_KEY = "AIzaSyD-new-key-2026-v2" 

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 介面樣式 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")
st.markdown("""
<style>
    :root { color-scheme: light; }
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3 { color: #1E3A8A !important; }
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
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
        if st.button("🚀 進入系統", use_container_width=True):
            db = lod()
            if uid and upw:
                ph=hsh(upw)
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid; st.session_state.db=db; st.rerun()
                else: st.error("密碼錯誤")
    st.stop()

# --- 4. 側邊選單 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()

# --- 5. AI 助手 (修復 404 問題) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("詢問投資建議...")
    if p:
        with st.chat_message("user"): st.write(p)
        # 嘗試不同的 API 版本路徑
        api_endpoints = [
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}",
            f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"
        ]
        
        success = False
        for url in api_endpoints:
            try:
                res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}, timeout=10)
                if res.status_code == 200:
                    ans = res.json()['candidates'][0]['content']['parts'][0]['text']
                    with st.chat_message("assistant"): st.write(ans)
                    success = True
                    break
            except: continue
        
        if not success:
            st.error("AI 連線失敗 (404/500)。這通常是金鑰額度用盡或失效。請聯繫開發者更換金鑰。")

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res, chart_data = [], {}
        with st.spinner('同步市場數據中...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym)
                    hist = tk.history(period="1mo")
                    if not hist.empty:
                        curr = round(hist["Close"].iloc[-1], 2)
                        is_us = ".TW" not in sym and ".TWO" not in sym
                        rate = ex_rate if is_us else 1.0
                        mv = round(curr * rate * i.get("q", 0))
                        pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                        res.append({"名稱": i.get("n", ""), "代碼": sym, "現價": curr, "市值": mv, "損益": pf})
                        chart_data[i.get("n", "")] = hist["Close"]
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            col1, col2 = st.columns([1, 1.2])
            with col1:
                st.subheader("🍕 資產比例")
                st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4), use_container_width=True)
            with col2:
                st.subheader("📈 趨勢圖")
                if chart_data: st.line_chart(pd.DataFrame(chart_data).ffill())

            st.subheader("📊 持股清單")
            def color_p(v):
                color = "#E11D48" if v > 0 else "#059669" if v < 0 else "black"
                return f"color: {color}; font-weight: bold;"
            st.dataframe(df.style.applymap(color_p, subset=['損益']), use_container_width=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("總市值", f"{df['市值'].sum():,} 元")
            c2.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            c3.metric("美金匯率", f"{ex_rate}")

    st.divider()
    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            ca, cb, cc, cd = st.columns(4)
            n, t, p, q = ca.text_input("名稱"), cb.text_input("代碼"), cc.number_input("成本"), cd.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db)
                    st.session_state.db=db; st.rerun()
        if sk:
            for idx, item in enumerate(sk):
                cola, colb = st.columns([5, 1])
                cola.write(f"🗑️ {item.get('n')} ({item.get('t')})")
                if colb.button("移除", key=f"del_{idx}"):
                    db = lod(); db[u]["s"].pop(idx); sav(db); st.rerun()

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", 100.0); q1 = st.number_input("原股", 1000.0)
    p2 = st.number_input("加碼價", 90.0); q2 = st.number_input("加碼數", 1000.0)
    if (q1 + q2) > 0:
        st.metric("💡 攤平後均價", f"{round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)} 元")
