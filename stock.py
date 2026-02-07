import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 後端 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    with open(F, "r", encoding="utf-8") as f: return json.load(f)

def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 登入系統 ---
st.set_page_config(page_title="家族投資管理系統", layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ 家族投資管理系統")
    uid = st.sidebar.text_input("請輸入帳號")
    upw = st.sidebar.text_input("請輸入密碼", type="password")
    if st.sidebar.button("登入 / 註冊"):
        if uid and upw:
            ph = hsh(upw)
            if uid not in st.session_state.db:
                st.session_state.db[uid] = {"p": ph, "s": []}
                sav(st.session_state.db)
            if st.session_state.db[uid]["p"] == ph:
                st.session_state.u = uid
                st.rerun()
    st.stop()

# --- 3. 選單 ---
st.sidebar.write(f"👤 使用者: {u}")
m = st.sidebar.radio("功能選單", ["📊 資產管理", "🧮 攤平工具"])
if st.sidebar.button("安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產管理 ---
if m == "📊 資產管理":
    st.title("📈 我的投資即時儀表板")
    with st.expander("📝 新增持股資料"):
        with st.form("add_f"):
            n = st.text_input("股票名稱 (例：台積電)")
            t = st.text_input("代碼 (例：2330.TW)")
            p = st.number_input("買入平均價格", min_value=0.0)
            q = st.number_input("持有股數", min_value=1.0)
            tg = st.number_input("停利目標價", min_value=0.0)
            sp = st.number_input("停損預警價", min_value=0.0)
            if st.form_submit_button("儲存至清單"):
                if n and t:
                    # 這裡是之前的斷點，現在拆成單行賦值，絕對不會斷
                    new_s = {}
                    new_s["n"] = n
                    new_s["t"] = t.upper()
                    new_s["p"] = p
                    new_s["q"] = q
                    new_s["tg"] = tg
                    new_s["sp"] = sp
                    st.session_state.db[u]["s"].append(new_s)
                    sav(st.session_state.db)
                    st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('讀取即時股價...'):
            for i in sk:
                try:
                    tk = yf.Ticker(i["t"])
                    h = tk.history(period="1d")
                    curr = round(h["Close"].iloc[-1], 2)
                    stt = "⚖️ 穩定"
                    if i.get("tg") and curr >= i["tg"]: stt = "🎯 停利"
                    if i.get("sp") and curr <= i["sp"]: stt = "⚠️ 停損"
                    mv = round(curr * i["q"])
                    pf = mv - (i["p"] * i["q"])
                    # 這裡也拆開寫
                    d = {}
                    d["股票"] = i["n"]
                    d["現價"] = curr
                    d["狀態"] = stt
                    d["市值"] = mv
                    d["損益"] = round(pf)
                    d["代碼"] = i["t"]
                    res.append(d)
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w:
                df.to_excel(w, index=False)
            st.download_button("📥 匯出 Excel 報表", bio.getvalue(), "list.xlsx")
            st.divider()
            l, r = st.columns(2)
            # 圓餅圖
            f_p = px.pie(df, values='市值', names='股票', title="資產比例")
            l.plotly_chart(f_p, use_container_width=True)
            # 走勢圖
            with r:
                sel = st.selectbox("查看歷史走勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h_df = yf.Ticker(cod).history(period="6mo")
                if not h_df.empty:
                    f_l = px.line(h_df, y="Close", title=f"{sel} 半年走勢")
                    st.plotly_chart(f_l, use_container_width=True)
            if st.sidebar.button("🗑️ 清空所有紀錄"):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db)
                st.rerun()
    else: st.info("目前清單是空的，請先新增股票。")

# --- 5. 攤平工具 ---
elif m == "🧮 攤平工具":
    st.title("🧮 成本攤平計算器")
    p1 = st.number_input("原始買入價格", value=100.0)
    q1 = st.number_input("原始持有股數", value=1000.0)
    p2 = st.number_input("加碼買入價格", value=90.0)
    q2 = st.number_input("加碼買入股數", value=1000.0)
    st.metric("攤平後平均成本", round(((p1*q1)+(p2*q2))/(q1+q2), 2))
