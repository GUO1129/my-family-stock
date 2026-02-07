import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
import hashlib
from io import BytesIO
from datetime import datetime

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
st.set_page_config(page_title="家族投資究極系統 3.0", layout="wide")

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_all_data()

current_user = st.session_state.get('current_user', None)

if not current_user:
    st.title("🛡️ 家族投資管理系統 3.0")
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
                else: st.sidebar.error("❌ 密碼錯誤")
    st.stop()

# --- 3. 側邊欄：功能選單 ---
st.sidebar.title(f"👤 {current_user}")
menu = st.sidebar.radio("功能選單", ["📈 我的資產", "🧮 成本攤平計算器", "📅 財經行事曆"])

if st.sidebar.button("登出系統"):
    del st.session_state.current_user
    st.rerun()

st.sidebar.divider()
fee_discount = st.sidebar.slider("手續費折數", 0.1, 1.0, 0.28, 0.01)

# --- 4. 主功能：我的資產 ---
if menu == "📈 我的資產":
    st.title(f"📈 {current_user} 的投資即時儀表板")
    
    with st.expander("📝 新增/修改持股資料"):
        with st.form("add_new_stock_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("股票名稱")
            code = col2.text_input("代碼 (.TW)")
            buy_price = col3.number_input("買入均價", min_value=0.0)
            qty = col1.number_input("股數", min_value=1)
            target = col2.number_input("停利價", min_value=0.0)
            stop = col3.number_input("停損價", min_value=0.0)
            submit_clicked = st.form_submit_button("➕ 加入清單")
            
            if submit_clicked:
                if name and code:
                    st.session_state.all_data[current_user]["stocks"].append({
                        "name": name, "code": code, "buy_price": buy_price, "qty": qty, 
                        "target": target, "stop": stop
                    })
                    save_all_data(st.session_state.all_data)
                    st.success(f"已成功加入 {name}！")
                    st.rerun()
                else:
                    st.error("請填寫股票名稱與代碼")

    user_stocks = st.session_state.all_data[current_user]["stocks"]
    if user_stocks:
        results = []
        total_mkt_val = 0
        total_cost_sum = 0
        
        with st.spinner('同步市場數據中...'):
            for s in user_stocks:
                try:
                    t = yf.Ticker(s["code"])
                    df = t.history(period="1d")
                    info = t.info
                    if not df.empty:
                        curr = round(df['Close'].iloc[-1], 2)
                        div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                        status = "⚖️ 穩定"
                        if s.get("target", 0) > 0 and curr >= s["target"]: status = "🎯 達標(停利)"
                        elif s.get("stop", 0) > 0 and curr <= s["stop"]: status = "⚠️ 破底(停損)"
                        mkt_val = curr * s["qty"]
                        results.append({
                            "股票": s["name"], "現價": curr, "殖利率%": f"{round(div_yield, 2)}%",
                            "狀態": status, "淨損益": round(mkt_val - (s["buy_price"] * s["qty"])),
                            "市值": round(mkt_val), "代碼": s["code"]
                        })
                        total_mkt_val += mkt_val
                        total_cost_sum += (s["buy_price"] * s["qty"])
                except: pass

        if results:
            c1, c2, c3 = st.columns(3)
            c1.metric("總市值", f"{round(total_mkt_val):,} 元")
            c2.metric("總損益", f"{round(total_mkt_val - total_cost_sum):,} 元", delta=f"{round(total_mkt_val - total_cost_sum)}")
            c3.metric("持股數", f"{len(results)} 檔")

            st.subheader("📊 持股明細")
            df_show = pd.DataFrame(results)
            st.dataframe(df_show, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(px.pie(df_show, values='市值', names='股票', hole=0.5, title="資產分配"), use_container_width=True)
            with col_b:
                st.plotly_chart(px.line(yf.Ticker(results[0]["代碼"]).history(period="6mo"), y="Close", title=f"{results[0]['股票']} 半年走勢"), use_container_width=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_show.to_excel(writer, index=False)
            st.download_button("📥 匯出 Excel 報表", output.getvalue(), f"{current_user}_stocks.xlsx")
    else: st.info("目前清單是空的。")

# --- 5. 功能：成本攤平計算器 ---
elif menu == "🧮 成本攤平計算器":
    st.title("🧮 成本攤平計算器")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💡 目前持股")
        old_price = st.number_input("目前買入均價", min_value=0.0, value=100.0, step=0.1)
        old_qty = st.number_input("目前持有股數", min_value=1, value=1000, step=100)
    with col2:
        st.subheader("💸 預計加碼")
        new_price = st.number_input("預計加碼股價", min_value=0.0, value=90.0, step=0.1)
        new_qty = st.number_input("預計加碼股數", min_value=1, value=1000, step=100)
    
    total_shares = old_qty + new_qty
    if total_shares > 0:
        avg_price = ((old_price * old_qty) + (new_price * new_qty)) / total_shares
        st.divider()
        res1, res2 = st.columns(2)
        res1.metric("攤平後新均價", f"{round(avg_price, 2)} 元")
        res2.metric("成本降幅", f"{round(((old_price - avg_price) / old_price) * 100, 2) if old_price > 0 else 0} %", delta=f"-{round(old_price-avg_price, 2)}")

# --- 6. 功能：財經行事曆 ---
elif menu == "📅 財經行事曆":
    st.title("📅 財經行事曆 (持股相關)")
    user_stocks = st.session_state.all_data[current_user]["stocks"]
    if user_stocks:
        calendar_events = []
        with st.spinner('查詢中...'):
            for s in user_stocks:
                try:
                    t = yf.Ticker(s["code"])
                    cal = t.calendar
                    if cal is not None and not cal.empty:
                        event_date = cal.iloc[0, 0]
                        event_name = cal.index[0]
                        calendar_events.append({"股票": s["name"], "日期": event_date.strftime('%Y-%m-%d'), "事件": event_name})
                except: pass
        if calendar_events:
            st.table(pd.DataFrame(calendar_events))
        else: st.info("暫時沒有查到最近的重大事件。")
    else: st.info("請先回到資產頁面新增股票。")

if st.sidebar.button("🗑️ 清空所有紀錄"):
    st.session_state.all_data[current_user]["stocks"] = []
    save_all_data(st.session_state.all_data)
    st.rerun()
