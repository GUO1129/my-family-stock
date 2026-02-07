import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO

# --- 1. 資料處理函數 ---
DB_FILE = "users_stock_data.json"

def make_hash(p):
    return hashlib.sha256(str.encode(p)).hexdigest()

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 2. 登入介面 ---
st.set_page_config(page_title="家族投資究極系統", layout="wide")
if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()

user = st.session_state.get('user', None)

if not user:
    st.title("🛡️ 家族投資管理系統")
    u_in = st.sidebar.text_input("帳號")
    p_in = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if u_in and p_in:
            h = make_hash(p_in)
            if u_in not in st.session_state.all_data:
                st.session_state.all_data[u_in] = {"password": h, "stocks": []}
                save_data(st.session_state.all_data)
            if st.session_state.all_data[u_in]["password"] == h:
                st.session_state.user = u_in
                st.rerun()
            else:
                st.sidebar.error("密碼錯誤")
    st.stop()

# --- 3. 側邊欄與選單 ---
st.sidebar.title(f"👤 {user}")
menu = st.sidebar.radio("功能選單", ["📈 我的資產", "🧮 成本攤平", "📅 行事曆"])
if st.sidebar.button("登出"):
    del st.session_state.user
    st.rerun()

# --- 4. 功能：我的資產 ---
if menu == "📈 我的資產":
    st.title("📈 投資儀表板")
    
    with st.expander("📝 新增持股"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("股票名稱")
            code = c2.text_input("代碼 (如 2330.TW)")
            b_p = c3.number_input("買入均價", min_value=0.0)
            qty = c1.number_input("股數", min_value=1)
            tgt = c2.number_input("停利價", min_value=0.0)
            stp = c3.number_input("停損價", min_value=0.0)
            if st.form_submit_button("➕ 存入清單"):
                if name and code:
                    st.session_state.all_data[user]["stocks"].append({
                        "name": name, "code": code.upper(), 
                        "buy_price": b_p, "qty": qty, 
                        "target": tgt, "stop": stp
                    })
                    save_data(st.session_state.all_data)
                    st.rerun()

    stocks = st.session_state.all_data[user]["stocks"]
    if stocks:
        res_list = []
        t_tw, t_us = 0.0, 0.0
        
        with st.spinner('同步最新市場數據中...'):
            for s in stocks:
                try:
                    # 拆解抓取邏輯，避免單行過長
                    ticker = yf.Ticker(s["code"])
                    hist = ticker.history(period="1d")
                    if hist.empty:
                        continue
                        
                    curr = round(hist['Close'].iloc[-1], 2)
                    m_v = curr * s["qty"]
                    
                    # 計算盈虧
                    profit = m_v - (s["buy_price"] * s["qty"])
                    
                    res_list.append({
                        "股票": s["name"], 
                        "現價": curr, 
                        "市值": round(m_v), 
                        "損益": round(profit),
                        "代碼": s["code"]
                    })
                    
                    if ".TW" in s["code"]:
                        t_tw += m_v
                    else:
                        t_us += m_v
                except Exception as e:
                    # 發生錯誤時跳過該檔股票
                    continue

        if res_list:
            col1, col2 = st.columns(2)
            col1.metric("🇹🇼 台股總市值", f"{round(t_tw):,} TWD")
            col2.metric("🇺🇸 美股總市值", f"{round(t_us):,} USD")
            
            df = pd.DataFrame(res_list)
            st.dataframe(df, use_container_width=True)

            with st.expander("🗑️ 管理持股 (刪除)"):
                d_n = st.selectbox("請選擇要移除的股票", [x["name"] for x in stocks])
                if st.button("確認移除"):
                    st.session_state.all_data[user]["stocks"] = [x for x in stocks if x["name"] != d_n]
                    save_data(st.session_state.all_data)
                    st.rerun()
            
            st.plotly_chart(px.pie(df, values='市值', names='股票', title="資產比例分析"), use_container_width=True)
    else:
        st.info("目前清單是空的，請先新增股票。")

# --- 5. 功能：成本攤平 ---
elif menu == "🧮 成本攤平":
    st.title("🧮 成本攤平計算器")
    c1, c2 = st.columns(2)
    p1 = c1.number_input("原始買入均價", min_value=0.0, value=100.0)
    q1 = c1.number_input("原始持有股數", min_value=1, value=1000)
    p2 = c2.number_input("預計加碼價格", min_value=0.0, value=90.0)
    q2 = c2.number_input("預計加碼股數", min_value=1, value=1000)
    
    total_q = q1 + q2
    avg = ((p1 * q1) + (p2 * q2)) / total_q
    st.divider()
    st.metric("試算攤平後均價", f"{round(avg, 2)} 元")

# --- 6. 功能：行事曆 ---
elif menu == "📅 行事曆":
    st.title("📅 家族持股行事曆")
    stocks = st.session_state.all_data[user]["stocks"]
    if stocks:
        events = []
        for s in stocks:
            try:
                cal = yf.Ticker(s["code"]).calendar
                if cal is not None and not cal.empty:
                    events.append({
                        "股票": s["name"], 
                        "日期": cal.iloc[0, 0].strftime('%Y-%m-%d'), 
                        "事件": cal.index[0]
                    })
            except:
                continue
        if events:
            st.table(pd.DataFrame(events))
        else:
            st.info("目前沒有查到近期的重大事件。")

# 側邊欄底部清空
st.sidebar.divider()
if st.sidebar.button("⚠️ 清空全部紀錄"):
    if st.sidebar.checkbox("確定刪除所有持股數據"):
        st.session_state.all_data[user]["stocks"] = []
        save_data(st.session_state.all_data)
        st.rerun()
