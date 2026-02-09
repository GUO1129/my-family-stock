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

# --- 2. 介面樣式 (確保手機白底黑字清晰) ---
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
    input { color: #000000 !important; background-color: #FFFFFF !important; }
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
                    st.session_state.u=uid
                    st.session_state.db = db
                    st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])

with st.sidebar.expander("🔐 帳號安全"):
    old_p = st.text_input("舊密碼", type="password")
    new_p = st.text_input("新密碼", type="password")
    if st.button("確認修改"):
        db = st.session_state.db
        if hsh(old_p) == db[u]["p"]:
            db[u]["p"] = hsh(new_p); sav(db)
            st.success("成功！請重新登入"); st.session_state.u = None; st.rerun()
        else: st.error("舊密碼錯誤")

if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u=None; st.rerun()

# --- 5. AI 投資助手 (純 Web 請求版，不需裝 google 庫) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族私人 AI 顧問")
    
    # 手機版建議將 API Key 存在側邊欄或程式碼中
    api_key = st.sidebar.text_input("填入 Gemini API Key", type="password")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 顯示對話
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.write(chat["content"])

    if prompt := st.chat_input("想問關於持股的問題嗎？"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if not api_key:
            st.error("請在左側選單填入 API Key 才能連動 AI。")
        else:
            with st.spinner("AI 正在分析市場數據..."):
                try:
                    # 抓取目前的持股背景
                    my_stocks = st.session_state.db[u].get("s", [])
                    context = f"我目前的持股資料是：{my_stocks}。請以此為基礎回答我的問題：{prompt}"
                    
                    # 使用極簡的 Requests 方式呼叫 Gemini
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    payload = {"contents": [{"parts": [{"text": context}]}]}
                    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
                    
                    if response.status_code == 200:
                        ans = response.json()['candidates'][0]['content']['parts'][0]['text']
                        with st.chat_message("assistant"):
                            st.write(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    else:
                        st.error(f"連線失敗 (錯誤碼: {response.status_code})")
                except Exception as e:
                    st.error(f"發生預期外錯誤: {e}")

# --- 6. 資產儀表板 (維持你最穩定的版本) ---
elif m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增持股項目", expanded=False):
        with st.form("simple_add_form"):
            c1, c2 = st.columns(2)
            new_n = c1.text_input("股票名稱")
            new_t = c1.text_input("代碼 (例: 6982.TWO)")
            new_p = c2.number_input("平均成本", 0.0)
            new_q = c2.number_input("持有股數", 1.0)
            if st.form_submit_button("💾 立即儲存"):
                if new_n and new_t:
                    current_db = lod()
                    current_db[u]["s"].append({"n":new_n, "t":new_t.upper().strip(), "p":new_p, "q":new_q})
                    sav(current_db); st.session_state.db = current_db
                    st.success("✅ 已儲存"); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i['t'])
                df_h = tk.history(period="5d") # 抓 5 天確保開盤/休盤都能讀到
                if not df_h.empty:
                    curr = round(df_h["Close"].values[-1], 2)
                    is_us = ".TW" not in i['t'] and ".TWO" not in i['t']
                    rate = ex_rate if is_us else 1.0
                    mv = int(curr * rate * i['q'])
                    pf = int(mv - (i['p'] * rate * i['q']))
                    res.append({"股票": i['n'], "現價": f"{curr} {'USD' if is_us else 'TWD'}", "市值(台幣)": mv, "損益(台幣)": pf, "代碼": i['t']})
                else:
                    res.append({"股票": i['n'], "現價": "讀取失敗", "市值(台幣)": 0, "損益(台幣)": 0, "代碼": i['t']})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.markdown("### 📊 財務總覽")
            c1, c2 = st.columns(2)
            c1.metric("總市值", f"{df['市值(台幣)'].sum():,} 元")
            c2.metric("總盈虧", f"{df['損益(台幣)'].sum():,} 元", delta=int(df['損益(台幣)'].sum()))

            with st.expander("🗑️ 管理/刪除持股"):
                for idx, item in enumerate(sk):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"**{item.get('n')}** ({item.get('t')})")
                    if col_b.button("刪除", key=f"del_{idx}"):
                        current_db = lod(); current_db[u]["s"].pop(idx); sav(current_db)
                        st.session_state.db = current_db; st.rerun()
    else:
        st.info("目前還沒有持股資料。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼數", value=1000.0)
    st.metric("💡 均價結果", f"{round(((p1*q1)+(p2*q2))/(q1+q2), 2)} 元")
