import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 後端資料核心 ---
F = "data.json"

if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    STABLE_KEY = ""

def ask_gemini(prompt):
    if not STABLE_KEY: return "❌ 未設定 API Key"
    targets = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}"
    ]
    payload = {"contents": [{"parts": [{"text": f"你是專業投資顧問，請分析：{prompt}"}]}]}
    headers = {'Content-Type': 'application/json'}
    for url in targets:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except: continue
    return "❌ AI 顧問連線失敗，請檢查金鑰權限。"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

def calc_limit(price, direction="up"):
    change = 1.1 if direction == "up" else 0.9
    return round(price * change, 2)

# --- 2. 介面設定 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #d1d5db; }
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
                ph = hsh(upw)
                if uid not in db: 
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                if db[uid]["p"] == ph: 
                    st.session_state.u = uid; st.session_state.db = db; st.rerun()
                else: st.error("密碼錯誤")
    st.stop()

# --- 4. 側邊導覽 ---
st.sidebar.markdown(f"### 👤 使用者: **{u}**")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u = None; st.rerun()

# --- 5. 功能頁面 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("輸入股票代碼或投資問題...")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("分析中..."):
            st.chat_message("assistant").write(ask_gemini(p))

elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('同步市場數據中...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym)
                    df_h = tk.history(period="5d")
                    curr, prev = df_h["Close"].iloc[-1], df_h["Close"].iloc[-2]
                    is_tw = ".TW" in sym or ".TWO" in sym
                    rate = ex_rate if not is_tw else 1.0
                    mv = round(curr * rate * i.get("q", 0))
                    cost = round(i.get("p", 0) * rate * i.get("q", 0))
                    pf = int(mv - cost)
                    res.append({
                        "名稱": i.get("n", ""), "代碼": sym, "今日價": round(curr, 2),
                        "昨日收": round(prev, 2), "預估漲停": calc_limit(prev, "up"),
                        "市值": mv, "損益": pf, "報酬%": round((pf/cost*100), 2) if cost>0 else 0
                    })
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 總市值", f"{df['市值'].sum():,} 元")
            c2.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=f"{df['損益'].sum():,}")
            c3.metric("💵 匯率", f"{ex_rate}")
            
            st.dataframe(df.style.applymap(lambda x: 'color: #4ade80' if x >= 0 else 'color: #f87171', subset=['損益', '報酬%']), use_container_width=True)

            # --- 新增：歷史走勢圖區塊 ---
            st.markdown("---")
            st.subheader("📊 個股歷史走勢線")
            sel_stock = st.selectbox("選擇要查看走勢的股票", options=df['名稱'].tolist())
            sel_sym = df[df['名稱'] == sel_stock]['代碼'].values[0]
            
            period = st.select_slider("選擇時間範圍", options=["1mo", "3mo", "6mo", "1y", "max"], value="3mo")
            hist_data = yf.Ticker(sel_sym).history(period=period)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], mode='lines', name='收盤價', line=dict(color='#1e3a8a', width=2)))
            fig.update_layout(title=f"{sel_stock} ({sel_sym}) 歷史走勢", xaxis_title="日期", yaxis_title="價格", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            # ---------------------------

            col_l, col_r = st.columns(2)
            with col_l: st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4, title="資產配置"), use_container_width=True)
            with col_r: 
                if st.button("🔮 讓 AI 診斷目前持股", use_container_width=True):
                    st.write(ask_gemini(f"我的持股：{', '.join(df['名稱'])}。請簡短預估漲跌。"))

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            n, t, p, q = c1.text_input("名稱"), c2.text_input("代碼"), c3.number_input("成本"), c4.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                db = lod(); db[u]["s"].append({"n":n, "t":t.upper(), "p":p, "q":q}); sav(db); st.rerun()

elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平精算")
    p1 = st.number_input("原成本", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼股數", value=1000.0)
    if (q1 + q2) > 0:
        total = (p1*q1)+(p2*q2)
        st.metric("💡 攤平後均價", f"{round(total/(q1+q2), 2)} 元")
        st.info(f"總投入資金：{int(total):,} 元")
