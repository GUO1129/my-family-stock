import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time, requests
import plotly.express as px  # 用來畫圓餅圖

# --- 1. 後端資料核心 ---
F = "data.json"
BACKEND_GEMINI_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw"

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

# --- 5. AI 助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("詢問市場趨勢...")
    if p:
        with st.chat_message("user"): st.write(p)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]})
        if res.status_code == 200:
            ans = res.json()['candidates'][0]['content']['parts'][0]['text']
            with st.chat_message("assistant"): st.write(ans)

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    
    # 匯率與資料抓取
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    sk = st.session_state.db[u].get("s", [])
    
    if sk:
        res = []
        chart_data = {}
        with st.spinner('同步最新市場數據中...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym)
                    hist = tk.history(period="1mo") # 抓一個月資料畫圖
                    if not hist.empty:
                        curr = round(hist["Close"].iloc[-1], 2)
                        is_us = ".TW" not in sym and ".TWO" not in sym
                        rate = ex_rate if is_us else 1.0
                        mv = round(curr * rate * i.get("q", 0))
                        pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                        res.append({"名稱": i.get("n", ""), "代碼": sym, "現價": curr, "市值(台幣)": mv, "損益(台幣)": pf})
                        chart_data[i.get("n", "")] = hist["Close"] # 存股價歷史
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            
            # --- 圖表區 ---
            col_chart1, col_chart2 = st.columns([1, 1.2])
            
            with col_chart1:
                st.subheader("🍕 資產比例圈圈")
                fig = px.pie(df, values='市值(台幣)', names='名稱', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
            
            with col_chart2:
                st.subheader("📈 近一個月漲跌圖")
                if chart_data:
                    # 規格化數據後畫圖
                    trend_df = pd.DataFrame(chart_data).ffill()
                    st.line_chart(trend_df)

            # --- 數據表格 ---
            st.subheader("📊 詳細持股清單")
            def color_p(v): return f'color: {"red" if v > 0 else "green" if v < 0 else "black"}; font-weight: bold;'
            st.dataframe(df.style.applymap(color_p, subset=['損益(台幣)']), use_container_width=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("總市值", f"{df['市值(台幣)'].sum():,} 元")
            c2.metric("總盈虧", f"{df['損益(台幣)'].sum():,} 元", delta=int(df['損益(台幣)'].sum()))
            c3.metric("美金匯率", f"{ex_rate}")

    # 新增與刪除放在最下面
    st.divider()
    with st.expander("🛠️ 管理持股 (新增/刪除)"):
        with st.form("add_form"):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("名稱")
            t = c2.text_input("代碼")
            p = c3.number_input("成本", 0.0)
            q = c4.number_input("股數", 1.0)
            if st.form_submit_button("➕ 新增項目"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db)
                    st.session_state.db=db; st.rerun()
        
        if sk:
            for idx, item in enumerate(sk):
                col_a, col_b = st.columns([5, 1])
                col_a.write(f"🗑️ {item.get('n')} ({item.get('t')})")
                if col_b.button("點我刪除", key=f"del_{idx}"):
                    db = lod(); db[u]["s"].pop(idx); sav(db)
                    st.session_state.db=db; st.rerun()

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", 100.0); q1 = st.number_input("原股數", 1000.0)
    p2 = st.number_input("加碼價", 90.0); q2 = st.number_input("加碼數", 1000.0)
    if (q1 + q2) > 0:
        avg = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
        st.metric("💡 攤平後均價", f"{avg} 元")
