import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
# --- 1. 後端 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
 if not os.path.exists(F): return {}
 with open(F,"r",encoding="utf-8") as f: return json.load(f)
def sav(d):
 with open(F,"w",encoding="utf-8") as f: json.dump(d,f,indent=2)
# --- 2. 介面美化 (玻璃質感 CSS) ---
st.set_page_config(page_title="家族投資", layout="wide")
st.markdown("""<style>
 [data-testid="stMetric"] {background:rgba(28,131,225,0.1); border:1px solid rgba(28,131,225,0.3); padding:20px; border-radius:15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
 [data-testid="stExpander"] {border-radius:15px; border:1px solid #e0e0e0;}
 .stButton>button {border-radius:10px; width:100%; transition: 0.3s;}
</style>""", unsafe_allow_html=True)
# --- 3. 登入邏輯 ---
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')
if not u:
 st.title("🛡️ 家族投資安全門戶")
 with st.container():
  uid = st.text_input("帳號")
  upw = st.text_input("密碼", type="password")
  if st.button("進入系統"):
   if uid and upw:
    ph=hsh(upw); db=st.session_state.db
    if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
    if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
 st.stop()
# --- 4. 主選單 ---
st.sidebar.title(f"👤 {u}")
m = st.sidebar.radio("導覽菜單", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
if st.sidebar.button("安全登出"): st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])
# --- 5. 功能：資產管理 ---
if m == "📈 資產儀表板":
 st.title("💎 投資座艙")
 with st.expander("➕ 新增投資項目"):
  c1, c2 = st.columns(2)
  n = c1.text_input("股票名稱")
  t = c1.text_input("代碼(例:2330.TW)")
  p = c2.number_input("成本價格", 0.0)
  q = c2.number_input("持有股數", 1.0)
  dv = c1.number_input("預估年股利", 0.0)
  if st.button("儲存至雲端"):
   if n and t:
    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"dv":dv})
    sav(st.session_state.db); st.rerun()
 if sk:
  res = []
  for i in sk:
   try:
    tk = yf.Ticker(i["t"])
    df_h = tk.history(period="1d")
    curr = round(df_h["Close"].values[-1], 2)
    mv = round(curr * i["q"])
    pf = mv - (i["p"] * i["q"])
    res.append({"股票":i["n"],"現價":curr,"市值":mv,"損益":int(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
   except: continue
  if res:
   df = pd.DataFrame(res)
   st.dataframe(df, use_container_width=True)
   st.write("### 📊 財務概況")
   c1, c2, c3 = st.columns(3)
   c1.metric("總市值", f"{df['市值'].sum():,} 元")
   c2.metric("預估年股利", f"{df['年股利'].sum():,} 元")
   c3.metric("總盈虧", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
   st.divider()
   l, r = st.columns([1, 1.5])
   l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產配置", hole=0.4), use_container_width=True)
   with r:
    sel = st.selectbox("切換個股趨勢", df["股票"].tolist())
    cod = df[df["股票"]==sel]["代碼"].values[0]
    hist = yf.Ticker(cod).history(period="6mo")
    if not hist.empty:
     fig = px.line(hist, y="Close", title=f"{sel} 6個月走勢")
     fig.update_traces(line_color='#1c83e1')
     st.plotly_chart(fig, use_container_width=True)
# --- 6. 功能：日曆 ---
elif m == "📅 股利日曆":
 st.title("📅 重要事件紀錄")
 if sk:
  ev = []
  for i in sk:
   try:
    c = yf.Ticker(i["t"]).calendar
    if c is not None:
     ev.append({"股票":i["n"],"日期":c.iloc[0,0].strftime('%Y-%m-%d'),"內容":"財務公告/除權息"})
   except: continue
  if ev: st.table(pd.DataFrame(ev))
  else: st.info("近期無重大事件")
# --- 7. 功能：攤平 ---
elif m == "🧮 攤平計算機":
 st.title("🧮 成本攤平工具")
 with st.container():
  c1, c2 = st.columns(2)
  p1 = c1.number_input("原買入價", 100.0)
  q1 = c1.number_input("原持股數", 1000.0)
  p2 = c2.number_input("新加碼價", 90.0)
  q2 = c2.number_input("新加碼數", 1000.0)
  avg = round(((p1*q1)+(p2*q2))/(q1+q2), 2)
  st.divider()
  st.metric("試算均價結果", f"{avg} 元")
