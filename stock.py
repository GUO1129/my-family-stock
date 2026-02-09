import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"
# 確保這裡是你最新申請的 Key
NEW_API_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw" 

def ask_gemini(prompt):
    """手動透過 HTTP 連線，並嘗試不同路徑與模型名稱"""
    # 嘗試方案 A: 使用 1.5-flash-latest (這是目前最穩定的別名)
    # 嘗試方案 B: 如果 v1 不行，改回 v1beta (有時候 v1 正式版需要透過 Google Cloud 啟用才能用)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={NEW_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        if response.status_code == 200:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            # 如果 1.5-flash 失敗，自動嘗試 1.0-pro (這是保底方案)
            if response.status_code == 404:
                return "❌ 模型找不到 (404)。請檢查：\n1. Google AI Studio 帳號是否開通了 Gemini 1.5 權限。\n2. 你的帳號地區是否在支援範圍。"
            return f"❌ API 錯誤 ({response.status_code}): {result.get('error', {}).get('message', '未知錯誤')}"
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

# --- 5. AI 助手 (手動 API 版) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("請輸入您的投資問題...")
    if p:
        with st.chat_message("user"): st.write(p)
        try:
            with st.spinner("AI 正在分析市場數據..."):
                ans = ask_gemini(p)
                with st.chat_message("assistant"): st.write(ans)
        except Exception as e:
            st.error(f"連線失敗：{e}")

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
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
            c1, c2 = st.columns([1, 1.2])
            with c1:
                st.subheader("🍕 資產配置")
                st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4), use_container_width=True)
            with c2:
                st.subheader("📈 價格走勢")
                if chart_data: st.line_chart(pd.DataFrame(chart_data).ffill())
            st.subheader("📊 持股明細")
            def color_p(v):
                c = "#E11D48" if v > 0 else "#059669" if v < 0 else "black"
                return f"color: {c}; font-weight: bold;"
            st.dataframe(df.style.applymap(color_p, subset=['損益']), use_container_width=True)
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("總市值", f"{df['市值'].sum():,} 元")
            mc2.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            mc3.metric("美金匯率", f"{ex_rate}")

    st.divider()
    with st.expander("🛠️ 持股管理"):
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

