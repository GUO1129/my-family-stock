import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests

# ==========================================
# 🔑 基礎設定與 AI 金鑰
# ==========================================
BACKEND_GEMINI_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw"
F = "data.json"

# --- 1. 資料庫管理工具 ---
def hsh(p): 
    return hashlib.sha256(p.encode()).hexdigest()

def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 系統介面初始化 ---
st.set_page_config(page_title="家族投資系統", layout="wide")

if 'db' not in st.session_state: 
    st.session_state.db = lod()
if 'u' not in st.session_state: 
    st.session_state.u = None

# --- 3. 登入保護系統 ---
if not st.session_state.u:
    st.markdown("<h1 style='text-align: center;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        uid = st.text_input("👤 帳號名稱")
        upw = st.text_input("🔑 登入密碼", type="password")
        if st.button("🚀 登入 / 註冊帳號", use_container_width=True):
            if uid and upw:
                db = st.session_state.db
                ph = hsh(upw)
                if uid not in db:
                    # 註冊新帳號
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                
                if db[uid]["p"] == ph:
                    st.session_state.u = uid
                    st.success("登入成功！")
                    st.rerun()
                else:
                    st.error("密碼錯誤，請重新輸入。")
            else:
                st.warning("請輸入帳號與密碼。")
    st.stop()

# --- 4. 側邊選單與登出 ---
u = st.session_state.u
st.sidebar.markdown(f"### 👤 目前使用者: {u}")
m = st.sidebar.radio("功能選單", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])

if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 5. 功能邏輯：AI 投資助手 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族私人 AI 顧問")
    st.info("您可以詢問關於市場趨勢、個股分析或資產配置的建議。")
    
    prompt = st.chat_input("輸入您的問題...")
    if prompt:
        with st.chat_message("user"): st.write(prompt)
        with st.spinner("AI 正在分析中..."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={BACKEND_GEMINI_KEY}"
            try:
                # 附帶用戶持股資訊給 AI 參考
                stocks = st.session_state.db[u].get("s", [])
                context = f"你是專業投資顧問。用戶目前持股：{json.dumps(stocks)}。問題：{prompt}"
                
                res = requests.post(url, json={"contents": [{"parts": [{"text": context}]}]}, timeout=15)
                if res.status_code == 200:
                    ans = res.json()['candidates'][0]['content']['parts'][0]['text']
                    with st.chat_message("assistant"): st.write(ans)
                else:
                    st.error("AI 連線失敗，請檢查金鑰或網路。")
            except Exception as e:
                st.error(f"連線錯誤: {e}")

# --- 6. 功能邏輯：資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("📈 持股清單管理")
    
    with st.expander("➕ 新增投資項目"):
        with st.form("add_stock_form"):
            col_a, col_b = st.columns(2)
            name = col_a.text_input("股票/標的名稱")
            ticker = col_b.text_input("代碼 (例: 2330.TW)")
            price = col_a.number_input("買入平均成本", min_value=0.0)
            qty = col_b.number_input("持有股數", min_value=0.0)
            
            if st.form_submit_button("💾 儲存至雲端"):
                if name and ticker:
                    st.session_state.db[u]["s"].append({"n": name, "t": ticker.upper(), "p": price, "q": qty})
                    sav(st.session_state.db)
                    st.success(f"已成功新增 {name}！")
                    st.rerun()
                else:
                    st.error("請完整填寫名稱與代碼。")

    st.subheader("📊 現有資產一覽")
    sk_data = st.session_state.db[u].get("s", [])
    if sk_data:
        df = pd.DataFrame(sk_data)
        df.columns = ["名稱", "代碼", "成本", "股數"]
        st.table(df)
    else:
        st.info("目前尚無持股資料，請點擊上方「新增投資項目」。")

# --- 7. 功能邏輯：攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平試算")
    st.write("計算加碼後的新平均成本：")
    
    c1, c2 = st.columns(2)
    p1 = c1.number_input("現有成本價", value=100.0)
    q1 = c1.number_input("現有持有股數", value=1000.0)
    p2 = c2.number_input("計畫加碼價格", value=90.0)
    q2 = c2.number_input("計畫加碼股數", value=1000.0)
    
    if (q1 + q2) > 0:
        avg_cost = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.divider()
        st.metric("💡 攤平後預估均價", f"{round(avg_cost, 2)} 元")
        st.write(f"總投入資金預估：{round((p1 * q1) + (p2 * q2), 0)} 元")
