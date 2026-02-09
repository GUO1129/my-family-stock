import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib

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
                    st.session_state.db = db # 確保 session 內的 db 是最新的
                    st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])

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

# --- 5. 資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    # 取得匯率
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    # 儲存持股的表單 (簡化版，確保必能儲存)
    with st.expander("📝 新增持股項目", expanded=True):
        with st.form("simple_add_form"):
            c1, c2 = st.columns(2)
            new_n = c1.text_input("股票名稱 (如: 大井泵浦)")
            new_t = c1.text_input("代碼 (如: 6982.TWO)")
            new_p = c2.number_input("平均成本", 0.0)
            new_q = c2.number_input("持有股數", 1.0)
            new_dv = c2.number_input("單股年股利", 0.0)
            
            submit = st.form_submit_button("💾 立即儲存")
            if submit:
                if new_n and new_t:
                    # 讀取最新 DB，增加資料，儲存
                    current_db = lod()
                    current_db[u]["s"].append({
                        "n": new_n, 
                        "t": new_t.upper().strip(), 
                        "p": new_p, 
                        "q": new_q, 
                        "dv": new_dv
                    })
                    sav(current_db)
                    st.session_state.db = current_db # 同步更新 session
                    st.success(f"✅ {new_n} 已儲存！")
                    st.rerun()
                else:
                    st.warning("請填寫名稱與代碼")

    # 顯示列表
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        for i in sk:
            try:
                sym = i.get("t", "")
                tk = yf.Ticker(sym)
                df_h = tk.history(period="1d")
                
                if not df_h.empty:
                    curr = round(df_h["Close"].values[-1], 2)
                    is_us = ".TW" not in sym and ".TWO" not in sym
                    rate = ex_rate if is_us else 1.0
                    mv = round(curr * rate * i.get("q", 0))
                    pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                    res.append({
                        "股票": i.get("n", ""), "現價": f"{curr} {'USD' if is_us else 'TWD'}",
                        "市值(台幣)": mv, "損益(台幣)": pf, "代碼": sym
                    })
                else:
                    res.append({
                        "股票": i.get("n", ""), "現價": "讀取失敗",
                        "市值(台幣)": 0, "損益(台幣)": 0, "代碼": sym
                    })
            except:
                continue
        
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
                    col_a.write(
