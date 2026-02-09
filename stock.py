import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"
# 已更新為你提供的新金鑰
NEW_API_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw" 

def ask_gemini(prompt):
    """手動透過 HTTP 連線 Google API (採用 2026 最穩定的 v1beta 門路)"""
    # 這是目前新產生的 Key 最容易成功的路徑
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={NEW_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        if response.status_code == 200:
            # 成功取得 AI 回覆
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            err_msg = result.get('error', {}).get('message', '未知錯誤')
            # 處理權限生效延遲
            if "403" in str(response.status_code) or "404" in str(response.status_code):
                return f"❌ 權限尚未生效或被擋：{err_msg}\n💡 提示：剛產生的 Key 可能需要 1-3 分鐘同步，請稍後再試。"
            return f"❌ API 錯誤 ({response.status_code}): {err_msg}"
            
    except Exception as e:
        return f"⚠️ 連線異常: {str(e)}"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 介面與登入系統 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

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
                # 根據您的要求：為每個帳號設定密碼保護
                if uid not in db: 
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                if db[uid]["p"] == ph: 
                    st.session_state.u = uid
                    st.session_state.db = db
                    st.rerun()
                else: 
                    st.error("密碼錯誤")
    st.stop()

# --- 3. 主導覽介面 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 功能邏輯：AI 助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    st.info("目前的顧問大腦：Gemini 1.5 Flash (2026 最新版)")
    
    p = st.chat_input("請輸入您的投資問題（例如：分析當前美股趨勢）...")
    if p:
        with st.chat_message("user"):
            st.write(p)
        with st.spinner("AI 正在分析大數據中..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"):
                st.write(ans)

# --- 5. 功能邏輯：資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except:
        ex_rate = 32.5
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res, chart_data = [], {}
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
            st.plotly_chart(px.pie(df, values='市值', names='名稱', title='資產分佈'), use_container_width=True)

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("名稱")
            t = c2.text_input("代碼 (如: 2330.TW)")
            p = c3.number_input("成本價格")
            q = c4.number_input("持有股數")
            if st.form_submit_button("新增持股"):
                db = lod()
                db[u]["s"].append({"n":n, "t":t, "p":p, "q":q})
                sav(db); st.rerun()

# --- 6. 功能邏輯：攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", value=100.0)
    q1 = st.number_input("原股", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0)
    q2 = st.number_input("加碼數", value=1000.0)
    if (q1 + q2) > 0:
        avg = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.metric("💡 攤平後均價", f"{round(avg, 2)} 元")
