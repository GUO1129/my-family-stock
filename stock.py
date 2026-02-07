import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. 後端與安全 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    with open(F, "r", encoding="utf-8") as f: return json.load(f)
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 深色模式與頁面設定 ---
st.set_page_config(page_title="家族投資系統", layout="wide")
# 強制優化黑色背景下的文字顯示
st.markdown("""<style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; }
</style>""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ 家族投資管理系統")
    uid = st.sidebar.text_input("帳號")
    upw = st.sidebar.text_input("密碼", type="password")
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

# --- 3. 側邊選單 ---
st.sidebar.write(f"👤 使用者: {u}")
m = st.sidebar.radio("功能選單", ["📊 資產管理", "📅 股利行事曆", "🧮 攤平工具"])
if st.sidebar.button("安全登出"):
    st.session_state.u = None
    st.rerun()

# --- 4. 資產管理 (含損益與股利) ---
if m == "📊 資產管理":
    st.title("📈 我的投資即時儀表板")
    with st.expander("📝 新增持股與股利目標"):
        with st.form("add_f"):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱")
            t = c1.text_input("代碼 (例: 2330.TW)")
            p = c2.number_input("買入均價", min_value=0.0)
            q = c2.number_input("持有股數", min_value=1.0)
            tg = c1.number_input("停利價", min_value=0.0)
            sp = c2.number_input("停損價", min_value=0.0)
            div = c1.number_input("預估年股利 (單股)", min_value=0.0)
            if st.form_submit_button("儲存至清單"):
                if n and t:
                    new_s = {"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":div}
                    st.session_state.db[u]["s"].append(new_s)
                    sav(st.session_state.db); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('同步數據中...'):
            for i in sk:
                try:
                    tk = yf.Ticker(i["t"])
                    curr = round(tk.history(period="1d")["Close"].iloc[-1], 2)
                    stt = "⚖️ 穩定"
                    if i.get("tg") and curr >= i["tg"]: stt = "🎯 停利"
                    if i.get("sp") and curr <= i["sp"]: stt = "⚠️ 停損"
                    mv = round(curr * i["q"])
                    pf = mv - (i["p"] * i["q"])
                    y_div = round(i.get("dv", 0) * i["q"]) # 總股利
                    res.append({"股票":i["n"],"現價":curr,"狀態":stt,"市值":mv,"損益":round(pf),"年領股利":y_div,"代碼":i["t"]})
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            # 總結算卡片
            c_a, c_b = st.columns(2)
            c_a.metric("資產總市值", f"{df['市值'].sum():,} 元")
            c_b.metric("預估年總股利", f"{df['年領股利'].sum():,} 元")
            
            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產佔比"), use_container_width=True)
            with r:
                sel = st.selectbox("切換歷史走勢", df["股票"].tolist())
                cod = df[df["股票"]==sel]["代碼"].values[0]
                h_df = yf.Ticker(cod).history(period="6mo")
                if not h_df.empty:
                    fig = px.line(h_df, y="Close", title=f"{sel} 半年走勢")
                    st.plotly_chart(fig, use_container_width=True)
            if st.sidebar.button("🗑️ 清空紀錄"):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db); st.rerun()
    else: st.info("清單是空的")

# --- 5. 股利行事曆 ---
elif m == "📅 股利行事曆":
    st.title("📅 重要財經行事曆")
    sk = st.session_state.db[u].get("s",
