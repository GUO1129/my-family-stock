import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests

# ==========================================
# 🔑 後端金鑰設定區 (填好後，所有裝置登入皆免輸入)
# 請將下面引號內換成你的 AIza... 金鑰
BACKEND_GEMINI_KEY ="AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw" 
# ==========================================

# --- 1. 後端資料核心邏輯 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 介面樣式美化 (手機適配) ---
st.set_page_config(page_title="家族投資 AI 系統", layout="wide")
st.markdown("""
<style>
    :root { color-scheme: light; }
    .stApp { background-color: #FFFFFF !important; }
    .main .block-container p, label, span, div { color: #000000 !important; font-weight: 500; }
    h1, h2, h3 { color: #1E3A8A !important; }
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
    .stChatMessage { background-color: #F0F2F6 !important; border-radius: 12px; padding: 10px; margin-bottom: 8px; }
    input { color: #000000 !important; background-color: #FFFFFF !important; border: 1px solid #ddd !important; }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入系統 (含帳號自動建立與密碼保護) ---
if not u:
    st.markdown("<h1 style='text-align: center;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.2, 1])
    with c2:
        uid = st.text_input("👤 帳號")
        upw = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 安全登入", use_container_width=True):
            db = st.session_state.db
            if uid and upw:
                ph = hsh(upw)
                if uid not in db: 
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                if db[uid]["p"] == ph: 
                    st.session_state.u = uid
                    st.session_state.db = db
                    st.rerun()
                else:
                    st.error("密碼不正確")
    st.stop()

# --- 4. 側邊導覽選單 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])

with st.sidebar.expander("🔐 帳號安全"):
    old_p = st.text_input("舊密碼", type="password")
    new_p = st.text_input("新密碼", type="password")
    if st.button("確認修改密碼"):
        db = lod()
        if hsh(old_p) == db[u]["p"]:
            db[u]["p"] = hsh(new_p)
            sav(db)
            st.success("修改成功！請重新登入")
            st.session_state.u = None
            st.rerun()
        else: st.error("舊密碼錯誤")

if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u = None
    st.rerun()

# --- 5. 功能：AI 投資助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族私人 AI 顧問")
    st.caption("AI 助手已就緒，分析您的個人資產組合。")
    
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    
    # 顯示歷史訊息
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]): st.markdown(chat["content"])

    if prompt := st.chat_input("您可以問我：'分析我的大井表現' 或 '目前市場趨勢'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.spinner("AI 正在思考中..."):
            success = False
            # 嘗試不同 API 路徑以防止 404
            urls = [
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}",
                f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"
            ]
            
            sk = st.session_state.db[u].get("s", [])
            stock_context = json.dumps(sk, ensure_ascii=False)
            
            for url in urls:
                try:
                    payload = {
                        "contents": [{
                            "parts": [{"text": f"你是專業投資導師。使用者目前的持股資料：{stock_context}。請根據這些資料親切地回答問題：{prompt}"}]
                        }]
                    }
                    res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=12)
                    if res.status_code == 200:
                        ans = res.json()['candidates'][0]['content']['parts'][0]['text']
                        with st.chat_message("assistant"): st.markdown(ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                        success = True
                        break
                except: continue
            
            if not success:
                st.error("❌ AI 連線失敗。請確認第 14 行的 API Key 是否正確且有效。")

# --- 6. 功能：資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    # 即時匯率
    try: ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 管理持股項目", expanded=False):
        with st.form("add_stock_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("股票名稱 (如: 台積電)")
            sym = c1.text_input("代碼 (台股需加 .TW 或 .TWO)")
            price = c2.number_input("平均成本", 0.0)
            qty = c2.number_input("持有股數", 1.0)
            if st.form_submit_button("💾 儲存至雲端"):
                if name and sym:
                    db = lod()
                    db[u]["s"].append({"n": name, "t": sym.upper().strip(), "p": price, "q": qty})
                    sav(db); st.session_state.db = db
                    st.success("已儲存！"); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner("抓取最新行情中..."):
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
                        res.append({"股票": i['n'], "現價": curr, "市值(TWD)": mv, "損益(TWD)": pf, "代碼": i['t']})
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.markdown("---")
            c1, c2 = st.columns(2)
            total_mv = df["市值(TWD)"].sum()
            total_pf = df["損益(TWD)"].sum()
            c1.metric("總市值 (台幣)", f"{total_mv:,} 元")
            c2.metric("總損益 (台幣)", f"{total_pf:,} 元", delta=int(total_pf))

            with st.expander("🗑️ 刪除錯誤項目"):
                for idx, item in enumerate(sk):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"{item['n']} ({item['t']})")
                    if col_b.button("刪除", key=f"del_{idx}"):
                        db = lod(); db[u]["s"].pop(idx); sav(db)
                        st.session_state.db = db; st.rerun()
    else: st.info("目前尚無持股資料，請點擊上方展開表單新增。")

# --- 7. 功能：攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    st.write("計算加碼後的平均成本")
    col1, col2 = st.columns(2)
    p1 = col1.number_input("現有成本價", value=100.0)
    q1 = col1.number_input("現有股數", value=1000.0)
    p2 = col2.number_input("預計加碼價", value=90.0)
    q2 = col2.number_input("預計加碼股數", value=1000.0)
    
    if (q1 + q2) > 0:
        avg_res = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
        st.metric("💡 攤平後預估均價", f"{avg_res} 元")

