import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time

# --- 嘗試載入 AI 模組，失敗也不要讓網頁壞掉 ---
try:
    import google.generativeai as genai
    HAS_AI_MODULE = True
except ImportError:
    HAS_AI_MODULE = False

# ==========================================
# 🔑 請在這裡貼上你申請到的 API Key
GOOGLE_API_KEY = "這裡貼上你的金鑰" 
# ==========================================

# 初始化 AI 大腦
if HAS_AI_MODULE and GOOGLE_API_KEY != "這裡貼上你的金鑰":
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = None
else:
    model = None

# --- 1. 後端資料核心 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 介面樣式 ---
st.set_page_config(page_title="家族投資 AI 系統", layout="wide")
st.markdown("""
<style>
    :root { color-scheme: light; }
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3 { color: #1E3A8A !important; }
    input { color: #000000 !important; }
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
        if st.button("🚀 安全登入", use_container_width=True):
            db = lod()
            if uid and upw:
                ph=hsh(upw)
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid; st.session_state.db = db; st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.title(f"👋 你好, {u}")
m = st.sidebar.radio("功能選單", ["📈 即時資產看板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()

# --- 5. 即時資產看板 ---
if m == "📈 即時資產看板":
    st.title("💎 持股戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i['t'])
                df_h = tk.history(period="5d")
                if not df_h.empty:
                    curr = round(df_h["Close"].iloc[-1], 2)
                    is_us = ".TW" not in i['t'] and ".TWO" not in i['t']
                    rate = ex_rate if is_us else 1.0
                    mv = int(curr * rate * i['q'])
                    pf = int(mv - (i['p'] * rate * i['q']))
                    res.append({"股票": i['n'], "現價": f"{curr} {'USD' if is_us else 'TWD'}", "市值(TWD)": mv, "損益(TWD)": pf, "代碼": i['t']})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.metric("總市值 (台幣)", f"{df['市值(TWD)'].sum():,} 元", delta=int(df['損益(TWD)'].sum()))
            st.dataframe(df, use_container_width=True)

    with st.expander("📝 編輯持股"):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("名稱"); t = st.text_input("代碼 (例: 6982.TWO)")
            p = st.number_input("平均成本", 0.0); q = st.number_input("持有股數", 1.0)
            if st.button("💾 儲存"):
                db = lod(); db[u]["s"].append({"n":n,"t":t.upper().strip(),"p":p,"q":q})
                sav(db); st.session_state.db = db; st.rerun()
        with col2:
            st.write("🗑️ 快速刪除")
            for idx, item in enumerate(sk):
                if st.button(f"刪除 {item['n']}", key=f"d_{idx}"):
                    db = lod(); db[u]["s"].pop(idx); sav(db); st.session_state.db = db; st.rerun()

# --- 6. AI 投資助手 ---
elif m == "🤖 AI 投資助手":
    st.title("🤖 私人投資 AI 顧問")
    
    if not HAS_AI_MODULE:
        st.error("❌ 尚未安裝 AI 模組，請在終端機執行 `pip install -U google-generativeai` 後重啟程式。")
    elif not model:
        st.warning("⚠️ 尚未填入正確的 API Key。請在程式碼中貼上金鑰以啟用功能！")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "您好！我是您的投資助手。今天想分析哪支股票？"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).markdown(msg["content"])

        if prompt := st.chat_input("詢問 AI..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            
            with st.spinner("AI 思考中..."):
                sk = st.session_state.db[u].get("s", [])
                full_prompt = f"持股:{sk}\n問題:{prompt}"
                response = model.generate_content(full_prompt)
                st.chat_message("assistant").markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", 100.0); q1 = st.number_input("原股數", 1000.0)
    p2 = st.number_input("加碼價", 90.0); q2 = st.number_input("加碼數", 1000.0)
    st.metric("💡 均價結果", f"{round(((p1*q1)+(p2*q2))/(q1+q2), 2)} 元")
