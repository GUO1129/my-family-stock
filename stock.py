import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time
import plotly.express as px
import google.generativeai as genai  # 使用官方驅動程式

# --- 1. 後端資料核心 ---
F = "data.json"
# 設定後端 AI 金鑰
API_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    .stMetric { background-color: #f8fafc; padding: 10px; border-radius: 10px; border: 1px solid #e2e8f0; }
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

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()

# --- 5. AI 助手 (官方驅動穩定版) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    p = st.chat_input("詢問市場趨勢...")
    if p:
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.spinner("AI 思考中..."):
            try:
                response = model.generate_content(p)
                ans = response.text
                with st.chat_message("assistant"): st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error(f"AI 啟動失敗：請確認 API Key 是否有效。錯誤訊息: {e}")

# --- 6. 資產儀表板 (保留你的圈圈與圖表) ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        chart_data = {}
        with st.spinner('同步市場數據...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym); hist = tk.history(period="1mo")
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
            c1, c2 = st.columns([1, 1.2])
            with c1: st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4), use_container_width=True)
            with c2: 
                if chart_data: st.line_chart(pd.DataFrame(chart_data).ffill())
            
            st.subheader("📊 持股清單")
            st.dataframe(df.style.applymap(lambda v: f'color: {"red" if v > 0 else "green" if v < 0 else "black"}; font-weight: bold;', subset=['損益']), use_container_width=True)
            
            mc1, mc2 = st.columns(2)
            mc1.metric("總市值", f"{df['市值'].sum():,} 元")
            mc2.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))

    st.divider()
    with st.expander("管理持股"):
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            n, t, p, q = c1.text_input("名稱"), c2.text_input("代碼"), c3.number_input("成本"), c4.number_input("股數")
            if st.form_submit_button("新增"):
                db=lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db); st.rerun()

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", 100.0); q1 = st.number_input("原股", 1000.0)
    p2 = st.number_input("加碼價", 90.0); q2 = st.number_input("加碼股", 1000.0)
    if (q1+q2)>0: st.metric("💡 均價", f"{round(((p1*q1)+(p2*q2))/(q1+q2), 2)} 元")
