import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib

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

# --- 2. 網頁初始化與登入 ---
st.set_page_config(page_title="家族投資究極系統", layout="wide")

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_all_data()

st.sidebar.title("🔐 私人投資後台")
user_id_input = st.sidebar.text_input("使用者帳號", key="login_user_id")
password_input = st.sidebar.text_input("密碼", type="password", key="login_password")

if st.sidebar.button("登入 / 建立帳號"):
    if user_id_input and password_input:
        pw_hash = make_hash(password_input)
        if user_id_input not in st.session_state.all_data:
            st.session_state.all_data[user_id_input] = {"password": pw_hash, "stocks": []}
            save_all_data(st.session_state.all_data)
            st.session_state.current_user = user_id_input
            st.sidebar.success("帳號建立成功！")
        else:
            if st.session_state.all_data[user_id_input]["password"] == pw_hash:
                st.session_state.current_user = user_id_input
                st.sidebar.success("登入成功！")
            else:
                st.sidebar.error("❌ 密碼錯誤")
    else:
        st.sidebar.warning("請輸入帳號密碼")

current_user = st.session_state.get('current_user', None)

if not current_user:
    st.title("🛡️ 家族投資管理系統")
    st.info("👈 請在左側登入。若是第一次使用，請直接自訂帳密即可完成註冊。")
    st.stop()

# --- 3. 登入後的側邊欄設定 ---
st.sidebar.divider()
st.sidebar.header(f"⚙️ {current_user} 的設定")
fee_discount = st.sidebar.slider("手續費折數", 0.1, 1.0, 0.28, 0.01)
alert_threshold = st.sidebar.slider("漲跌預警門檻 (%)", 0.5, 5.0, 1.5, 0.5)

if st.sidebar.button("登出系統"):
    del st.session_state.current_user
    st.rerun()

# --- 4. 股票輸入區 ---
st.sidebar.header("📝 新增/修改持股")
with st.sidebar.form("add_stock_form", clear_on_submit=True):
    name = st.text_input("股票名稱", key="input_stock_name")
    code = st.text_input("代碼 (.TW)", key="input_stock_code")
    buy_price = st.number_input("買入均價", min_value=0.0, key="input_buy_price")
    qty = st.number_input("股數", min_value=1, key="input_qty")
    is_day_trade = st.checkbox("這筆是當沖嗎？", key="input_is_day_trade")
    if st.form_submit_button("➕ 加入清單"):
        st.session_state.all_data[current_user]["stocks"].append({
            "name": name, "code": code, "buy_price": buy_price, "qty": qty, "is_day_trade": is_day_trade
        })
        save_all_data(st.session_state.all_data)
        st.rerun()

# --- 5. 計算核心 ---
st.title(f"📈 {current_user} 的投資即時儀表板")
user_stocks = st.session_state.all_data[current_user]["stocks"]

if user_stocks:
    results = []
    total_mkt_val = 0
    total_cost_sum = 0

    with st.spinner('同步市場數據中...'):
        for s in user_stocks:
            ticker = yf.Ticker(s["code"])
            df = ticker.history(period="1d")
            if not df.empty:
                curr = round(df['Close'].iloc[-1], 2)
                open_p = df['Open'].iloc[0]
                
                # 漲跌計算
                change_pct = ((curr - open_p) / open_p) * 100
                if change_pct >= alert_threshold: 
                    status = "🔥 強勢"
                elif change_pct <= -alert_threshold: 
                    status = "❄️ 弱勢"
                else: 
                    status = "⚖️ 穩定"
                
                # 稅費計算
                buy_fee = max(20, s["buy_price"] * s["qty"] * 0.001425 * fee_discount)
                sell_fee = max(20, curr * s["qty"] * 0.001425 * fee_discount)
                tax = curr * s["qty"] * (0.0015 if s.get("is_day_trade", False) else 0.003)
                
                mkt_val = curr * s["qty"]
                net_profit = mkt_val - (s["buy_price"] * s["qty"] + buy_fee + sell_fee + tax)
                
                results.append({
                    "股票": s["name"], 
                    "現價": curr, 
                    "今日漲跌": f"{round(change_pct, 2)}%",
                    "預估狀態": status,
                    "淨損益": round(net_profit), 
                    "市值": round(mkt_val)
                })
                total_mkt_val += mkt_val
                total_cost_sum += (s["buy_price"] * s["qty"])

    # 頂部儀表板
    profit_all = round(total_mkt_val - total_cost_sum)
    c1, c2, c3 = st.columns(3)
    c1.metric("總市值", f"{round(total_mkt_val):,} 元")
    c2.metric("總損益", f"{profit_all:,} 元", delta=f"{profit_all}")
    c3.metric("持股數", f"{len(results)} 檔")

    # 資料明細表格
    df_show = pd.DataFrame(results)
    st.dataframe(df_show, use_container_width=True)
    
    # 視覺化圖表
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.pie(df_show, values='市值', names='股票', hole=0.5, title="資產比例分配"), use_container_width=True)
    with col_b:
        st.plotly_chart(px.bar(df_show, x='股票', y='淨損益', color='淨損益', title="各股盈虧分析"), use_container_width=True)

else:
    st.info("👋 歡迎登入！目前清單是空的，請先在左側填寫持股資料。")

if st.sidebar.button("🗑️ 清空我的所有紀錄", key="clear_all_btn"):
    st.session_state.all_data[current_user]["stocks"] = []
    save_all_data(st.session_state.all_data)
    st.rerun()