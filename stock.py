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

# --- 2. 介面樣式 (強制明亮模式，優化手機讀取) ---
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

# --- 5. AI 投資助手 (免套件版) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族私人 AI 顧問")
    
    # 手機版可在此處輸入 API Key
    api_key = st.sidebar.text_input("填入 Gemini API Key", type="password", help="請從 Google AI Studio 獲取")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 顯示對話
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    if prompt := st.chat_input("想問關於持股的問題嗎？"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not api_key:
            st.warning("⚠️ 請在左側選單填入 API Key 才能連動 AI。")
        else:
            with st.spinner("AI 正在思考中..."):
                try:
                    # 獲取持股資料
                    sk = st.session_state.db[u].get("s", [])
                    stock_ctx = json.dumps(sk, ensure_ascii=False)
                    
                    # 建立請求
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": f"你是專業投資分析師。我的持股為：{stock_ctx}。請以此回答我的問題：{prompt}"}]
                        }]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        ans = response.json()['candidates'][0]['content']['parts'][0]['text']
                        with st.chat_message("assistant"):
                            st.markdown(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                    elif response.status_code == 403:
                        st.error("❌ 錯誤 403：API Key 無效或權限未開啟。請檢查是否已在 Google AI Studio 建立 Key。")
                    else:
                        st.error(f"連線失敗 (錯誤代碼: {response.status_code})")
                except Exception as e:
                    st.error(f"連線異常: {str(e)}")

# --- 6. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增持股項目", expanded=False):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 6982.TWO)")
            p = c2.number_input("平均成本", 0.0)
            q = c2.number_input("持有股數", 1.0)
            if st.form_submit_button("💾 立即儲存"):
                if n and t:
                    db = lod()
                    db[u]["s"].append({"n":n, "t":t.upper().strip(), "p":p, "q":q})
                    sav(db); st.session_state.db = db
                    st.success("✅ 已儲存"); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('同步行情中...'):
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
            
            st.markdown("### 📊 財務總覽")
            c1, c2 = st.columns(2)
            c1.metric("總市值", f"{df['市值(TWD)'].sum():,} 元")
            total_pf = df['損益(TWD)'].sum()
            c2.metric("總盈虧", f"{total_pf:,} 元", delta=int(total_pf))

            with st.expander("🗑️ 管理/刪除持股"):
                for idx, item in enumerate(sk):
                    ca, cb = st.columns([4, 1])
                    ca.write(f"**{item['n']}** ({item['t']})")
                    if cb.button("刪除", key=f"d_{idx}"):
                        db = lod(); db[u]["s"].pop(idx); sav(db)
                        st.session_state.db = db; st.rerun()
    else:
        st.info("目前尚無持股資料。")

# --- 7. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼數", value=1000.0)
    if (q1 + q2) > 0:
        avg = round(((p1*q1)+(p2*q2))/(q1+q2), 2)
        st.metric("💡 攤平後均價", f"{avg} 元")
