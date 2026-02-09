import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests

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
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    :root { color-scheme: light; }
    .stApp { background-color: #FFFFFF !important; }
    .main .block-container p, .main .block-container label, .main .block-container span, .main .block-container div { 
        color: #000000 !important; font-weight: 500; 
    }
    h1, h2, h3 { color: #1E3A8A !important; }
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
    .stChatMessage { background-color: #F0F2F6 !important; border-radius: 10px; padding: 10px; margin-bottom: 5px; }
    input { color: #000000 !important; background-color: #FFFFFF !important; border: 1px solid #ddd !important; }
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
            if uid and upw:
                ph=hsh(upw); db=st.session_state.db
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid; st.session_state.db=db; st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u=None; st.rerun()

# --- 5. AI 投資助手 (解決 404 專用版) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族私人 AI 顧問")
    api_key = st.sidebar.text_input("填入 Gemini API Key", type="password")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]): st.markdown(chat["content"])

    if prompt := st.chat_input("想問關於持股的問題嗎？"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        if not api_key:
            st.warning("⚠️ 請在側邊欄填入 API Key")
        else:
            with st.spinner("AI 正在分析..."):
                try:
                    sk = st.session_state.db[u].get("s", [])
                    # 修正網址：使用 v1 版本通常比 v1beta 更穩定，模型名稱使用最通用的 gemini-1.5-flash
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": f"你是專業投資顧問。我的持股：{json.dumps(sk)}。問題：{prompt}"}]
                        }]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        ans = response.json()['candidates'][0]['content']['parts'][0]['text']
                        with st.chat_message("assistant"): st.markdown(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    elif response.status_code == 404:
                        st.error("❌ 錯誤 404：模型路徑不正確。這通常是 Google 更新了網址。請聯繫開發者更新 API 端點。")
                    elif response.status_code == 400:
                        st.error("❌ 錯誤 400：請求格式錯誤。請確認您的 API Key 是否正確複製。")
                    else:
                        st.error(f"連線失敗 (代碼: {response.status_code})")
                except Exception as e:
                    st.error(f"連線異常: {str(e)}")

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增持股", expanded=False):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 6982.TWO)")
            p = c2.number_input("平均成本", 0.0)
            q = c2.number_input("持有股數", 1.0)
            if st.form_submit_button("💾 立即儲存"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n, "t":t.upper().strip(), "p":p, "q":q})
                    sav(db); st.session_state.db = db; st.success("✅ 已儲存"); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i['t'])
                df_h = tk.history(period="5d")
                if not df_h.empty:
                    curr = round(df_h["Close"].values[-1], 2)
                    is_us = ".TW" not in i['t'] and ".TWO" not in i['t']
                    rate = ex_rate if is_us else 1.0
                    mv = int(curr * rate * i['q'])
                    pf = int(mv - (i['p'] * rate * i['q']))
                    res.append({"股票": i['n'], "現價": f"{curr} {'USD' if is_us else 'TWD'}", "市值(TWD)": mv, "損益(TWD)": pf, "代碼": i['t']})
            except: continue
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.metric("總市值", f"{df['市值(TWD)'].sum():,} 元", delta=int(df['損益(TWD)'].sum()))
    else: st.info("尚無持股。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", 100.0); q1 = st.number_input("原股數", 1000.0)
    p2 = st.number_input("加碼價", 90.0); q2 = st.number_input("加碼數", 1000.0)
    st.metric("💡 均價結果", f"{round(((p1*q1)+(p2*q2))/(q1+q2), 2)} 元")
