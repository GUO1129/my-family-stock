import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"

# 請確保已在 Streamlit Secrets 設定 GEMINI_KEY
if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    st.warning("🔑 請在 Streamlit Secrets 設定 GEMINI_KEY")
    STABLE_KEY = ""

def ask_gemini(prompt):
    """2026 修正版：確保 Payload 格式符合 Google 最新規範"""
    if not STABLE_KEY: return "❌ 未設定 API Key"
    
    # 嘗試 v1beta 與 v1 兩個路徑
    urls = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}"
    ]
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for url in urls:
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except: continue
    return "❌ AI 暫時無法連線，請確認 Secrets 中的 Key 是否有效。"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 漲跌計算邏輯 ---
def calc_limit(price, is_tw=True, direction="up"):
    """計算台股漲跌停價 (10%)"""
    if not is_tw: return round(price * (1.1 if direction=="up" else 0.9), 2)
    change = 1.1 if direction == "up" else 0.9
    raw = price * change
    # 簡單四捨五入邏輯，符合台股大致規律
    return round(raw, 2)

# --- 3. 頁面配置 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 4. 登入系統 ---
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

# --- 5. 導覽選單 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u = None; st.rerun()

# --- 6. AI 助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 投資顧問")
    st.subheader("💡 預估市場走勢與建議")
    p = st.chat_input("請輸入股票代碼或投資問題（例如：分析 2330.TW 的未來走勢）")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問正在讀取最新數據並預估漲跌..."):
            ans = ask_gemini(f"請以投資顧問身份，針對以下問題給予漲跌預估分析與建議：{p}")
            with st.chat_message("assistant"): st.write(ans)

# --- 7. 資產儀表板 (含漲跌分析表) ---
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
                    df_hist = tk.history(period="5d")
                    curr = df_hist["Close"].iloc[-1]
                    prev = df_hist["Close"].iloc[-2]
                    
                    is_tw = ".TW" in sym or ".TWO" in sym
                    up_limit = calc_limit(prev, is_tw, "up")
                    down_limit = calc_limit(prev, is_tw, "down")
                    
                    rate = ex_rate if not is_tw else 1.0
                    mv = round(curr * rate * i.get("q", 0))
                    pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                    
                    res.append({
                        "名稱": i.get("n", ""),
                        "代碼": sym,
                        "昨日收盤": round(prev, 2),
                        "今日現價": round(curr, 2),
                        "預估漲停": up_limit,
                        "預估跌停": down_limit,
                        "市值": mv,
                        "損益": pf
                    })
                except: continue
        
        if res:
            final_df = pd.DataFrame(res)
            st.metric("總市值 (TWD)", f"{final_df['市值'].sum():,} 元", delta=f"總損益: {final_df['損益'].sum():,}")
            
            st.subheader("🔥 漲跌停監控與持股分析")
            st.dataframe(final_df, use_container_width=True)
            
            if st.button("🔮 讓 AI 分析現有持股漲跌"):
                stock_list = ", ".join([f"{x['名稱']}({x['代碼']})" for x in res])
                with st.spinner("分析中..."):
                    analysis = ask_gemini(f"我的持股包含：{stock_list}。請根據目前市場狀況，簡短預估這些股票的短期漲跌趨勢。")
                    st.success("AI 預估報告：")
                    st.write(analysis)

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            ca, cb, cc, cd = st.columns(4)
            n, t, p, q = ca.text_input("名稱"), cb.text_input("代碼"), cc.number_input("成本"), cd.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                db = lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db); st.rerun()

# --- 8. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼股數", value=1000.0)
    if (q1 + q2) > 0:
        avg = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.metric("💡 攤平後均價", f"{round(avg, 2)} 元")
