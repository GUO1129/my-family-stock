import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO

# --- 1. 資料庫與安全邏輯 ---
DB_FILE = "users_stock_data.json"

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_all_data(all_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# --- 2. 網頁初始化 ---
st.set_page_config(page_title="家族投資究極系統 2.0", layout="wide")

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_all_data()

current_user = st.session_state.get('current_user', None)

if not current_user:
    st.title("🛡️ 家族投資管理系統 2.0")
    st.markdown("### 🔒 請先在左側登入或建立帳號")
    st.sidebar.title("🔐 系統登入")
    user_id_input = st.sidebar.text_input("使用者帳號", key="login_user_id")
    password_input = st.sidebar.text_input("密碼", type="password", key="login_password")

    if st.sidebar.button("登入 / 建立帳號"):
        if user_id_input and password_input:
            pw_hash = make_hash(password_input)
            if user_id_input not in st.session_state.all_data:
                st.session_state.all_data[user_id_input] = {"password": pw_hash, "stocks": []}
                save_all_data(st.session_state.all_data)
                st.session_state.current_user = user_id_input
                st.rerun()
            else:
                if st.session_state.all_data[user_id_input]["password"] == pw_hash:
                    st.session_state.current_user = user_id_input
                    st.rerun()
                else:
                    st.sidebar.error("❌ 密碼錯誤")
    st.stop()

# --- 3. 登入後功能區 ---
st.sidebar.title(f"👤 {current_user}")
if st.sidebar.button("登出系統"):
    del st.session_state.current_user
    st.rerun()

st.sidebar.divider()
fee_discount = st.sidebar.slider("手續費折數", 0.1, 1.0, 0.28, 0.01)

# --- 4. 股票輸入區 (升級版：含停損停利) ---
st.sidebar.header("📝 新增/修改持股")
with st.sidebar.form("add_stock_form", clear_on_submit=True):
    name = st.text_input("股票名稱")
    code = st.text_input("代碼 (例如: 2330.TW)")
    buy_price = st.number_input("買入均價", min_value=0.0)
    qty = st.number_input("股數", min_value=1)
    target_price = st.number_input("停利目標價 (0為不設定)", min_value=0.0)
    stop_price = st.number_input("停損警示價 (0為不設定)", min_value=0.0)
    is_day_trade = st.checkbox("這筆是當沖嗎？")
    
    if st.form_submit_button("➕ 加入清單"):
        st.session_state.all_data[current_user]["stocks"].append({
            "name": name, "code": code, "buy_price": buy_price, "qty": qty, 
            "target": target_price, "stop": stop_price, "is_day_trade": is_day_trade
        })
        save_all_data(st.session_state.all_data)
        st.rerun()

# --- 5. 計算核心與數據抓取 ---
st.title(f"📈 {current_user} 的投資即時儀表板")
user_stocks = st.session_state.all_data[current_user]["stocks"]

if user_stocks:
    results = []
    total_mkt_val = 0
    total_cost_sum = 0

    with st.spinner('正在抓取即時報價與股利資訊...'):
        for s in user_stocks:
            t = yf.Ticker(s["code"])
            df = t.history(period="1d")
            info = t.info
            
            if not df.empty:
                curr = round(df['Close'].iloc[-1], 2)
                # 抓取股利資訊 (若無則顯示 0)
                div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                last_div = info.get('lastDividendValue', 0)
                
                # 警示邏輯
                status = "⚖️ 穩定"
                if s.get("target") > 0 and curr >= s["target"]: status = "🎯 達標(停利)"
                elif s.get("stop") > 0 and curr <= s["stop"]: status = "⚠️ 破底(停損)"
                
                # 稅費計算
                buy_fee = max(20, s["buy_price"] * s["qty"] * 0.001425 * fee_discount)
                sell_fee = max(20, curr * s["qty"] * 0.001425 * fee_discount)
                tax = curr * s["qty"] * (0.0015 if s.get("is_day_trade") else 0.003)
                
                mkt_val = curr * s["qty"]
                net_profit = mkt_val - (s["buy_price"] * s["qty"] + buy_fee + sell_fee + tax)
                
                results.append({
                    "股票": s["name"],
                    "現價": curr,
                    "殖利率%": f"{round(div_yield, 2)}%",
                    "預估年配息": round(last_div * s["qty"]),
                    "狀態": status,
                    "淨損益": round(net_profit),
                    "市值": round(mkt_val),
                    "代碼": s["code"]
                })
                total_mkt_val += mkt_val
                total_cost_sum += (s["buy_price"] * s["qty"])

    # 儀表板數據顯示
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("總市值", f"{round(total_mkt_val):,} 元")
    c2.metric("總損益", f"{round(total_mkt_val - total_cost_sum):,} 元")
    c3.metric("預計年領股息", f"{sum(d['預估年配息'] for d in results):,} 元")
    
    df_show = pd.DataFrame(results)
    
    # --- 6. 停損停利上色功能 ---
    def color_status(val):
        color = 'white'
        if val == "🎯 達標(停利)": color = '#FFD700' # 金色
        elif val == "⚠️ 破底(停損)": color = '#FF4B4B' # 紅色
        return f'background-color: {color}; color: black'

    st.subheader("📊 持股明細")
    st.dataframe(df_show.style.applymap(color_status, subset=['狀態']), use_container_width=True)

    # --- 7. 匯出 Excel ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_show.to_excel(writer, index=False, sheet_name='我的持股')
    st.download_button(label="📥 匯出 Excel 報表", data=output.getvalue(), file_name=f"{current_user}_stocks.xlsx")

    # --- 8. 歷史走勢圖 ---
    st.divider()
    st.subheader("📉 歷史走勢與技術分析")
    sel_stock = st.selectbox("選取持股查看歷史：", [d["股票"] for d in results])
    sel_code = next(d["代碼"] for d in results if d["股票"] == sel_stock)
    period = st.select_slider("查詢區間", options=["1mo", "3mo", "6mo", "1y", "2y"], value="6mo")
    
    hist_data = yf.Ticker(sel_code).history(period=period)
    fig = px.line(hist_data, y="Close", title=f"{sel_stock} ({sel_code}) 走勢圖")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 目前清單空空的，請先在左側輸入持股資料！")

if st.sidebar.button("🗑️ 清空所有紀錄"):
    st.session_state.all_data[current_user]["stocks"] = []
    save_all_data(st.session_state.all_data)
    st.rerun()
