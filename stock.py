import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib
import time

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
    h1, h2, h3 { color: #1E3A8A !important; }
    input { color: #000000 !important; background-color: #FFFFFF !important; border: 1px solid #d1d5db !important; }
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 10px; }
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
            db = lod()
            if uid and upw:
                ph=hsh(upw)
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid
                    st.session_state.db = db
                    st.rerun()
                else: st.error("密碼錯誤")
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"): st.session_state.u=None; st.rerun()

# --- 5. 資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    # 取得匯率 (增加錯誤容忍)
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增持股項目", expanded=True):
        with st.form("add_form"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("正確代碼 (如: 6982.TWO)")
            p = c2.number_input("平均成本", 0.0)
            q = c2.number_input("持有股數", 1.0)
            if st.form_submit_button("💾 儲存持股"):
                if n and t:
                    db = lod()
                    # 強制格式化代碼：去空格、轉大寫
                    clean_t = t.strip().upper()
                    db[u]["s"].append({"n":n, "t":clean_t, "p":p, "q":q})
                    sav(db)
                    st.session_state.db = db
                    st.success(f"已儲存 {n} ({clean_t})")
                    time.sleep(1) # 給一點緩衝時間
                    st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('正在從交易所抓取最新行情...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    # 使用快速抓取法
                    tk = yf.Ticker(sym)
                    # 嘗試抓取最近一天的數據
                    data = tk.history(period="5d") 
                    if not data.empty:
                        curr = round(data["Close"].iloc[-1], 2)
                        is_us = ".TW" not in sym and ".TWO" not in sym
                        rate = ex_rate if is_us else 1.0
                        mv = round(curr * rate * i.get("q", 0))
                        pf = int(mv - (i.get("p", 0) * rate * i.get("q", 0)))
                        res.append({
                            "股票": i.get("n", ""), 
                            "現價": f"{curr} {'USD' if is_us else 'TWD'}",
                            "市值(台幣)": mv, 
                            "損益(台幣)": pf, 
                            "代碼": sym
                        })
                    else:
                        res.append({"股票": i.get("n", ""), "現價": "⚠️ 代碼無效", "市值(台幣)": 0, "損益(台幣)": 0, "代碼": sym})
                except:
                    res.append({"股票": i.get("n", ""), "現價": "❌ 連線失敗", "市值(台幣)": 0, "損益(台幣)": 0, "代碼": sym})
        
        if res:
            df = pd.DataFrame(res)
            # 獲利變色
            def color_p(v):
                c = 'red' if v > 0 else 'green' if v < 0 else 'black'
                return f'color: {c}; font-weight: bold;'
            
            st.dataframe(df.style.applymap(color_p, subset=['損益(台幣)']), use_container_width=True)
            
            c1, c2 = st.columns(2)
            total_mv = df['市值(台幣)'].sum()
            total_pf = df['損益(台幣)'].sum()
            c1.metric("總市值", f"{total_mv:,} 元")
            c2.metric("總盈虧", f"{total_pf:,} 元", delta=int(total_pf))

            with st.expander("🗑️ 刪除持股"):
                for idx, item in enumerate(sk):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"**{item.get('n')}** ({item.get('t')})")
                    if col_b.button("刪除", key=f"del_{idx}"):
                        db = lod()
                        db[u]["s"].pop(idx); sav(db)
                        st.session_state.db = db
                        st.rerun()
    else:
        st.info("請新增持股。")

elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平工具")
    p1 = st.number_input("原單價", value=100.0); q1 = st.number_input("原股數", value=1000.0)
    p2 = st.number_input("加碼價", value=90.0); q2 = st.number_input("加碼數", value=1000.0)
    avg = round(((p1 * q1) + (p2 * q2)) / (q1 + q2), 2)
    st.metric("💡 攤平後均價", f"{avg} 元")
