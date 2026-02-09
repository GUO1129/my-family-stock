import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"

# 從 Streamlit Secrets 讀取金鑰，確保安全性
if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    st.error("🔑 請在 Streamlit Secrets 中設定 GEMINI_KEY")
    st.stop()

def ask_gemini(prompt):
    """具備路徑容錯機制的 AI 調用函數"""
    # 2026 年最穩定的兩個路徑組合
    targets = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1", "gemini-pro")
    ]
    
    last_err = ""
    for api_ver, model_name in targets:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={STABLE_KEY}"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()
            if response.status_code == 200:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                last_err = result.get('error', {}).get('message', '未知錯誤')
        except Exception as e:
            last_err = str(e)
            continue
    return f"❌ AI 無法連線：{last_err}\n💡 提示：請確認您的 API Key 是否來自 Google AI Studio 的 'New Project'。"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 頁面配置 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入系統 (落實密碼保護) ---
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
                # 記憶功能：新用戶設定密碼，老用戶驗證密碼
                if uid not in db: 
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                if db[uid]["p"] == ph: 
                    st.session_state.u = uid
                    st.session_state.db = db
                    st.rerun()
                else: 
                    st.error("密碼錯誤，請重新輸入。")
    st.stop()

# --- 4. 側邊選單 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 5. AI 助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("請輸入您的投資問題...")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問思考中..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"): st.write(ans)

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except:
        ex_rate = 32.5
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('同步市場數據中...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym)
                    curr = tk.history(period="1d")["Close"].iloc[-1]
                    is_us = ".TW" not in sym and ".TWO" not in sym
                    rate = ex_rate if is_us else 1.0
                    mv = round(curr * rate * i.get("q", 0))
                    pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                    res.append({"名稱": i.get("n", ""), "代碼": sym, "現價": round(curr, 2), "市值": mv, "損益": pf})
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.metric("總市值 (TWD)", f"{df['市值'].sum():,} 元", delta=f"{df['損益'].sum():,} 元")
            st.dataframe(df, use_container_width=True)
            st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4), use_container_width=True)

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            n, t, p, q = c1.text_input("名稱"), c2.text_input("代碼"), c3.number_input("成本"), c4.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                if n and t:
                    db = lod()
                    db[u]["s"].append({"n": n, "t": t.upper(), "p": p, "q": q})
                    sav(db); st.session_state.db=db; st.rerun()

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", value=100.0); q1 = st.number_input("原股", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼數", value=1000.0)
    if (q1 + q2) > 0:
        avg = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.metric("💡 攤平後均價", f"{round(avg, 2)} 元")
