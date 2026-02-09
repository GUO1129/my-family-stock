import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"
# 更換為全新有效的 API Key (請確保此 Key 未被公開過度使用)
BACKEND_GEMINI_KEY = "AIzaSyD_D1J9z_U9l8m5z2V5V9r3z_T7m3n7_Y" 
# 2026 穩定版 API 終端點
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"

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
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 10px; }
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

# --- 5. AI 助手 (修復連線網址) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("詢問投資建議或分析...")
    if p:
        with st.chat_message("user"): st.write(p)
        payload = {"contents": [{"parts": [{"text": p}]}]}
        headers = {'Content-Type': 'application/json'}
        try:
            res = requests.post(API_URL, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                ans = res.json()['candidates'][0]['content']['parts'][0]['text']
                with st.chat_message("assistant"): st.write(ans)
            else:
                st.error(f"AI 連線失敗。請確認 API Key 是否有效或網路是否正常 (代碼: {res.status_code})")
        except Exception as e:
            st.error(f"連線異常: {e}")

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res, chart_data = [], {}
        with st.spinner('正在同步全球市場數據...'):
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
                        res.append({"名稱": i.get("n", ""), "代碼": sym, "現價": curr, "市值(台幣)": mv, "損益(台幣)": pf})
                        chart_data[i.get("n", "")] = hist["Close"]
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            col1, col2 = st.columns([1, 1.2])
            with col1:
                st.subheader("🍕 資產配置比例")
                fig = px.pie(df, values='市值(台幣)', names='名稱', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("📈 核心持股走勢 (近月)")
                if chart_data: st.line_chart(pd.DataFrame(chart_data).ffill())

            st.subheader("📊 即時資產清單")
            def color_p(v): return f'color:
