import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib

# --- 1. 後端資料 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 介面樣式 (維持 12.0/13.0 清爽風) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    :root { color-scheme: light; }
    .stApp { background-color: #FFFFFF !important; }
    .main .block-container p, .main .block-container label, .main .block-container span, .main .block-container div { 
        color: #000000 !important; font-weight: 500; 
    }
    h1, h2, h3 { color: #1E3A8A !important; }
    [data-testid="stMetricValue"] { color: #2563EB !important; }
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; }
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
                if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
    st.stop()

# --- 4. 側邊欄 ---
st.sidebar.markdown(f"### 👤 使用者: {u}")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "📅 股利日曆", "🧮 交易精算大師"])
if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u=None; st.rerun()

sk = st.session_state.db[u].get("s", [])

# --- 5. 資產儀表板 (核心邏輯升級) ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    # 獲取即時美金匯率 (智慧背景處理)
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except:
        ex_rate = 32.5 # 失敗時的預設保底匯率

    with st.expander("📝 新增持股項目"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n, t = c1.text_input("股票名稱"), c1.text_input("代碼 (例: AAPL 或 2330.TW)")
            p, q = c2.number_input("平均成本", 0.0), c2.number_input("持有股數", 1.0)
            tg, sp = c1.number_input("停利目標", 0.0), c2.number_input("停損預警", 0.0)
            dv = c1.number_input("單股年股利", 0.0)
            if st.form_submit_button("💾 儲存持股"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.rerun()

    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
                curr = round(df_h["Close"].values[-1], 2)
                
                # --- 智慧匯率邏輯 ---
                # 如果代碼沒有 .TW 或 .TWO，視為美股
                is_us = ".TW" not in i["t"]
                rate = ex_rate if is_us else 1.0
                curr_twd = curr * rate
                cost_twd = i["p"] * rate
                
                mv_twd = round(curr_twd * i["q"])
                pf_twd = mv_twd - (cost_twd * i["q"])
                dv_twd = round(i.get("dv", 0) * i["q"] * rate)
                
                unit = "USD" if is_us else "TWD"
                res.append({
                    "股票": i["n"],
                    "現價": f"{curr} {unit}",
                    "市值(台幣)": mv_twd,
                    "損益(台幣)": int(pf_twd),
                    "年股利(台幣)": dv_twd,
                    "代碼": i["t"]
                })
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.caption(f"💡 目前參考匯率：USD/TWD = {ex_rate}")
            
            st.markdown("### 📊 財務總覽 (已換算為台幣)")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值(台幣)'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益(台幣)'].sum():,} 元", delta=int(df['損益(台幣)'].sum()))
            cc.metric("預計年股利", f"{df['年股利(台幣)'].sum():,} 元")
            
            with st.expander("🗑️ 管理/刪除持股"):
                for idx, item in enumerate(sk):
                    if st.button(f"刪除 {item['n']} ({item['t']})", key=f"del_{idx}"):
                        st.session_state.db[u]["s"].pop(idx); sav(st.session_state.db); st.rerun()

            st.divider()
            l, r = st.columns([1, 1.5])
            with l:
                st.plotly_chart(px.pie(df, values='市值(台幣)', names='股票', hole=0.4, title="資產配比"), use_container_width=True)
            with r:
                sel = st.selectbox("分析趨勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    st.plotly_chart(px.line(h, y="Close", title=f"{sel} 趨勢 (原始幣別)"), use_container_width=True)
    else:
        st.info("目前清單為空。")

# --- 6. 股利日曆 ---
elif m == "📅 股利日曆":
    st.title("📅 事件追蹤")
    st.info("系統將自動抓取您清單中股票的最新除息資訊。")

# --- 7. 交易精算大師 ---
elif m == "🧮 交易精算大師":
    st.title("🧮 交易獲利精算 (台股專用)")
    st.write("計算買賣股票時，扣除手續費與稅金後的「真正淨利」。")
    c1, c2, c3 = st.columns(3)
    buy_p = c1.number_input("買入價格", 100.0)
    sell_p = c2.number_input("預計賣出價格", 102.0)
    shares = c3.number_input("成交股數", 1000)
    
    discount = st.slider("手續費折扣 (例如: 2.8折)", 1.0, 10.0, 2.8)
    is_dt = st.checkbox("這是當沖交易 (交易稅減半)")
    
    fee_r, tax_r = 0.001425 * (discount / 10.0), (0.0015 if is_dt else 0.003)
    b_fee = max(20, int(buy_p * shares * fee_r))
    s_fee = max(20, int(sell_p * shares * fee_r))
    tax = int(sell_p * shares * tax_r)
    profit = int((sell_p * shares - s_fee - tax) - (buy_p * shares + b_fee))
    
    st.metric("💰 最終純利 (台幣)", f"{profit:,} 元", delta=profit)
    st.caption(f"保本價：約 {round((buy_p*(1+fee_r))/(1-fee_r-tax_r), 2)} 元")
