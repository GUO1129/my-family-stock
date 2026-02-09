import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, time
import google.generativeai as genai  # 請記得先執行 pip install -U google-generativeai

# ==========================================
# 🔑 請在這裡貼上你申請到的 API Key
GOOGLE_API_KEY = "AIzaSyCjOOyjc_5Ts_KtQV_po0OnW0nW3X2AWj8" 
# ==========================================

# 設定 AI 
if GOOGLE_API_KEY != "AIzaSyCjOOyjc_5Ts_KtQV_po0OnW0nW3X2AWj8":
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- 後端資料核心 (維持穩定版本) ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 介面樣式 ---
st.set_page_config(page_title="家族投資 AI 系統", layout="wide")
st.markdown("<style>:root { color-scheme: light; } .stApp { background-color: #FFFFFF !important; } </style>", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 登入系統 ---
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
                if db[uid]["p"]==ph: st.session_state.u=uid; st.session_state.db=db; st.rerun()
    st.stop()

# --- 側邊欄 ---
st.sidebar.title(f"👋 你好, {u}")
m = st.sidebar.radio("功能選單", ["🤖 AI 投資助手", "📈 即時資產看板", "🧮 攤平計算機"])

# --- AI 投資助手 (威力加強版) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 私人投資 AI 顧問")
    
    if not model:
        st.warning("⚠️ 尚未偵測到有效的 API Key。請在程式碼中填入金鑰以啟用 AI 大腦！")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "您好！我是您的專屬 AI 投資顧問。我能分析您的持股狀況，並給予產業建議。今天想聊聊哪支股票？"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).markdown(msg["content"])

        if prompt := st.chat_input("詢問 AI 投資意見..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)

            with st.spinner("AI 正在分析數據與市場趨勢..."):
                try:
                    # 獲取持股背景
                    sk = st.session_state.db[u].get("s", [])
                    stock_info = "\n".join([f"名稱:{s['n']}, 代碼:{s['t']}, 成本:{s['p']}, 股數:{s['q']}" for s in sk])
                    
                    full_prompt = f"""
                    你是一位專業的台灣股市分析師。
                    使用者目前的持股如下：
                    {stock_info}
                    
                    請根據以上持股背景，回答使用者的問題：{prompt}
                    請用繁體中文回答，口吻要專業但親切。
                    """
                    
                    response = model.generate_content(full_prompt)
                    reply = response.text
                    
                    st.chat_message("assistant").markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"AI 思考時發生錯誤: {e}")

# --- 即時看板與其餘功能 (維持原本穩定代碼) ---
elif m == "📈 即時資產看板":
    st.title("💎 持股戰情室")
    # ... (此處保留上一版的看板代碼即可)
