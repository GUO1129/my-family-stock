import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"

# 從 Streamlit Secrets 讀取金鑰
if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    st.warning("🔑 請在 Streamlit Secrets 設定 GEMINI_KEY")
    STABLE_KEY = ""

def ask_gemini(prompt):
    """2026 最終修復版：精準對齊模型路徑，解決 404 問題"""
    if not STABLE_KEY: return "❌ Secrets 中找不到 GEMINI_KEY"
    
    # 鎖定目前新帳號最穩定的 v1beta / gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}"
    
    # 強化 Prompt，確保 AI 會針對漲跌進行分析
    refined_prompt = f"你是一位專業的台美股投資顧問，請針對以下問題給予具體的短期漲跌分析與預估：\n{prompt}"
    
    payload = {"contents": [{"parts": [{"text": refined_prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        if response.status_code == 200:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            # 抓取詳細原因
            detail = result.get('error', {}).get('message', '未知錯誤')
            return f"❌ AI 目前無法回應 (HTTP {response.status_code}): {detail}"
    except Exception as e:
        return f"⚠️ 網路連線異常: {str(e)}"

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
    """計算台股 10% 漲跌停價"""
    if not is_tw: return round(price * (1.1 if direction=="up" else 0.9), 2)
    change = 1.1 if direction == "up" else 0.9
    raw = price * change
    # 簡單四捨五入（台股精確跳動規律較複雜，此處取近似值）
    return round(raw, 2)

# --- 3. 頁面配置 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 4. 登入系統 (密碼保護) ---
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
                # 自動註冊新帳號或驗證舊帳號
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

# --- 5. 導覽選單 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 6. AI 投資助手 (預估漲跌) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 投資顧問")
    st.subheader("🔮 漲跌預估與市場分析")
    p = st.chat_input("輸入股票代碼或問題，例如：預估 2330.TW 明天漲跌？")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問正在分析數據並預估走勢..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"): st.write(ans)

# --- 7. 資產儀表板 (含漲跌停分析) ---
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
            st.metric("總市值 (TWD)", f"{final_df['市值'].sum():,} 元", delta=f"總盈虧: {final_df['損益'].sum():,}")
            
            st.subheader("🔥 漲跌停監控與持股分析")
            st.dataframe(final_df, use_container_width=True)
            
            # --- AI 批量預估按鈕 ---
            if st.button("🔮 讓 AI 分析現有持股短期漲跌"):
                stock_names = ", ".join([f"{x['名稱']}({x['代碼']})" for x in res])
                with st.spinner("AI 顧問正在掃描所有持股走勢..."):
                    report = ask_gemini(f"我的持股名單為：{stock_names}。請分別針對這些股票給出短期的漲跌分析報告。")
                    st.success("AI 持股分析報告：")
                    st.write(report)

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            ca, cb, cc, cd = st.columns(4)
            n, t, p, q = ca.text_input("名稱"), cb.text_input("代碼"), cc.number_input("成本"), cd.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db); st.rerun()

# --- 8. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原價", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼股數", value=1000.0)
    if (q1 + q2) > 0:
        avg = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.metric("💡 攤平後均價", f"{round(avg, 2)} 元")
