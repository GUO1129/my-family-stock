import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

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
    [data-testid="stMetricValue"] { color: #2563EB !important; }
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #000000 !important; }
    .stDataFrame div, .stDataFrame span { color: #000000 !important; }
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

# --- 5. 資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    with st.expander("📝 新增持股項目"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n, t = c1.text_input("股票名稱"), c1.text_input("代碼 (例: 2330.TW)")
            p, q = c2.number_input("平均成本", min_value=0.0), c2.number_input("持有股數", min_value=1.0)
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
                mv = round(curr * i["q"]); pf = mv - (i["p"] * i["q"])
                res.append({"股票":i["n"],"現價":curr,"市值":mv,"損益":int(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
            except: continue
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 下載資產報表", df.to_csv(index=False).encode('utf-8-sig'), "assets.csv", "text/csv")
            ca, cb, cc = st.columns(3)
            ca.metric("總市值", f"{df['市值'].sum():,} 元")
            cb.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
            cc.metric("預計年股利", f"{df['年股利'].sum():,} 元")
            with st.expander("🗑️ 管理/刪除持股"):
                for idx, item in enumerate(sk):
                    if st.button(f"刪除 {item['n']} ({item['t']})", key=f"del_{idx}"):
                        st.session_state.db[u]["s"].pop(idx); sav(st.session_state.db); st.rerun()

# --- 6. 股利日曆 (略，保持不變) ---
elif m == "📅 股利日曆":
    st.title("📅 事件追蹤")
    st.info("功能正常運作中，將自動抓取最新公告。")

# --- 7. 交易精算大師 (當沖/買賣損益精算) ---
elif m == "🧮 交易精算大師":
    st.title("🧮 交易獲利精算 (台股專用)")
    st.write("計算買賣股票時，扣除手續費與稅金後的「真正淨利」。")
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        buy_p = c1.number_input("買入價格", value=100.0, step=0.1)
        sell_p = c2.number_input("預計賣出價格", value=102.0, step=0.1)
        shares = c3.number_input("成交股數", value=1000, step=1000)
        
        c4, c5 = st.columns(2)
        discount = c4.slider("手續費折扣 (例如: 2.8折)", 1.0, 10.0, 2.8)
        is_day_trade = c5.checkbox("這是當沖交易 (交易稅減半)")

    # 運算邏輯
    fee_rate = 0.001425 * (discount / 10.0)
    tax_rate = 0.0015 if is_day_trade else 0.003
    
    buy_fee = int(buy_p * shares * fee_rate)
    if buy_fee < 20: buy_fee = 20 # 台北股市低消 20 元
    
    sell_fee = int(sell_p * shares * fee_rate)
    if sell_fee < 20: sell_fee = 20
    
    tax = int(sell_p * shares * tax_rate)
    
    total_cost = int((buy_p * shares) + buy_fee)
    total_get = int((sell_p * shares) - sell_fee - tax)
    net_profit = total_get - total_cost
    
    # 保本價計算
    breakeven = (buy_p * (1 + fee_rate)) / (1 - fee_rate - tax_rate)

    st.divider()
    res_a, res_b = st.columns(2)
    res_a.metric("💰 最終純利 (已扣稅費)", f"{net_profit:,} 元", delta=net_profit)
    res_b.metric("🛡️ 損益平價 (保本價)", f"{round(breakeven, 2)} 元")
    
    st.info(f"💡 試算詳情：買入手續費 ${buy_fee}，賣出手續費 ${sell_fee}，交易稅 ${tax}。")
