import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"

# 從 Streamlit Secrets 讀取金鑰，確保安全
if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    st.warning("🔑 請先在 Streamlit Cloud 的 Secrets 設定 GEMINI_KEY")
    STABLE_KEY = ""

def ask_gemini(prompt):
    """2026 年連線修正版：優先使用 v1beta 的 flash 模型"""
    if not STABLE_KEY: return "❌ 尚未設定 API Key"
    
    # 這是目前新帳號 100% 成功的路徑組合
    targets = [
        ("v1beta", "gemini-1.5-flash"), 
        ("v1", "gemini-1.5-flash")
    ]
    
    for api_ver, model_name in targets:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={STABLE_KEY}"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except: continue
    return "❌ AI 顧問目前忙線中，請稍後再試。"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 漲停計算邏輯 ---
def calc_limit(price, is_tw=True):
    """計算台股 10% 漲停價 (含五檔跳動規律)"""
    if not is_tw: return round(price * 1.1, 2)
    raw = price * 1.1
    if raw < 10: return floor_to_tick(raw, 0.01)
    elif raw < 50: return floor_to_tick(raw, 0.05)
    elif raw < 100: return floor_to_tick(raw, 0.1)
    elif raw < 500: return floor_to_tick(raw, 0.5)
    elif raw < 1000: return floor_to_tick(raw, 1.0)
    else: return floor_to_tick(raw, 5.0)

def floor_to_tick(val, tick):
    return round((val // tick) * tick, 2)

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
    st.title("🤖 家族 AI 顧問")
    p = st.chat_input("請輸入您的投資問題...")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問分析中..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"): st.write(ans)

# --- 7. 資產儀表板 (含漲停分析表) ---
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
                    df_hist = tk.history(period="2d")
                    curr = df_hist["Close"].iloc[-1]
                    prev = df_hist["Close"].iloc[-2]
                    
                    is_tw = ".TW" in sym or ".TWO" in sym
                    limit_price = calc_limit(prev, is_tw)
                    
                    rate = ex_rate if not is_tw else 1.0
                    mv = round(curr * rate * i.get("q", 0))
                    pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                    
                    res.append({
                        "名稱": i.get("n", ""),
                        "代碼": sym,
                        "昨日收盤": round(prev, 2),
                        "今日現價": round(curr, 2),
                        "預估漲停": limit_price,
                        "距漲停差": f"{round(limit_price - curr, 2)} ({round(((limit_price/curr)-1)*100, 1)}%)",
                        "市值": mv,
                        "損益": pf
                    })
                except: continue
        
        if res:
            final_df = pd.DataFrame(res)
            
            # 指標卡
            c1, c2, c3 = st.columns(3)
            c1.metric("總市值", f"{final_df['市值'].sum():,} 元")
            c2.metric("總盈虧", f"{final_df['損益'].sum():,} 元", delta=int(final_df['損益'].sum()))
            c3.metric("美金匯率", f"{ex_rate}")
            
            # 漲停監控表
            st.subheader("🔥 漲停監控與持股分析")
            st.dataframe(final_df, use_container_width=True)
            
            st.plotly_chart(px.pie(final_df, values='市值', names='名稱', hole=0.4), use_container_width=True)

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
