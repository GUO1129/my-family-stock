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

# --- 2. 介面美化 ---
st.set_page_config(page_title="家族投資", layout="wide")
st.markdown("""<style>
 [data-testid="stMetric"] {background:rgba(28,131,225,0.1); border:1px solid rgba(28,131,225,0.3); padding:20px; border-radius:15px;}
 [data-testid="stExpander"] {border-radius:15px;}
 .stDataFrame {border: 1px solid #e0e0e0; border-radius: 10px;}
</style>""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 3. 登入 ---
if not u:
 st.title("🛡️ 家族投資安全系統")
 uid = st.text_input("帳號")
 upw = st.text_input("密碼", type="password")
 if st.button("確認登入"):
  if uid and upw:
   ph=hsh(upw); db=st.session_state.db
   if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
   if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
 st.stop()

# --- 4. 選單 ---
st.sidebar.title(f"👤 {u}")
m = st.sidebar.radio("功能選單", ["📈 資產儀表板", "📅 股利日曆", "🧮 攤平計算機"])
if st.sidebar.button("安全登出"): st.session_state.u=None; st.rerun()
sk = st.session_state.db[u].get("s", [])

# --- 5. 資產儀表板 (新增預估漲跌功能) ---
if m == "📈 資產儀表板":
 st.title("💎 投資座艙")
 with st.expander("➕ 新增持股"):
  c1, c2 = st.columns(2)
  n = c1.text_input("名稱"); t = c1.text_input("代碼 (例: 2330.TW)")
  p = c2.number_input("平均成本", 0.0); q = c2.number_input("持有股數", 1.0)
  tg = c1.number_input("停利目標價", 0.0); sp = c2.number_input("停損預警價", 0.0)
  dv = c1.number_input("年股利", 0.0)
  if st.button("儲存資料"):
   if n and t:
    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
    sav(st.session_state.db); st.rerun()

 if sk:
  res = []
  for i in sk:
   try:
    tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
    curr = round(df_h["Close"].values[-1], 2)
    # --- 預估漲跌計算 ---
    target = i.get("tg", 0)
    stop_p = i.get("sp", 0)
    dist_tg = round(((target - curr) / curr) * 100, 1) if target > 0 else 0
    # --- 狀態判斷 ---
    stt = "⚖️ 穩定"
    if target > 0 and curr >= target: stt = "🎯 停利"
    if stop_p > 0 and curr <= stop_p: stt = "⚠️ 停損"
    
    mv = round(curr * i["q"])
    pf = mv - (i["p"] * i["q"])
    res.append({"股票":i["n"],"現價":curr,"狀態":stt,"離目標價":f"{dist_tg}%","市值":mv,"損益":int(pf),"年股利":round(i.get("dv",0)*i["q"]),"代碼":i["t"]})
   except: continue
  
  if res:
   df = pd.DataFrame(res)
   st.dataframe(df, use_container_width=True)
   
   st.write("### 💰 財務總覽")
   c1, c2, c3 = st.columns(3)
   c1.metric("總市值", f"{df['市值'].sum():,} 元")
   c2.metric("總損益", f"{df['損益'].sum():,} 元", delta=int(df['損益'].sum()))
   c3.metric("預估年利", f"{df['年股利'].sum():,} 元")
   
   st.divider()
   l, r = st.columns([1, 1.5])
   l.plotly_chart(px.pie(df, values='市值', names='股票', title="資產比例", hole=0.4), use_container_width=True)
   with r:
    sel = st.selectbox("切換歷史趨勢", df["股票"].tolist())
    cod = df[df["股票"]==sel]["代碼"].values[0]
    hist = yf.Ticker(cod).history(period="6mo")
    if not hist.empty:
     fig = px.line(hist, y="Close", title=f"{sel} 半年走勢")
     st.plotly_chart(fig, use_container_width=True)
 else: st.info("目前無持股，請展開上方選單新增。")

# --- 其他功能維持穩定 ---
elif m == "📅 股利日曆":
 st.title("📅 重要事件")
 if sk:
  ev = [{"股票":i["n"],"日期":yf.Ticker(i["t"]).calendar.iloc[0,0].strftime('%Y-%m-%d')} for i in sk if yf.Ticker(i["t"]).calendar is not None]
  if ev: st.table(pd.DataFrame(ev))
  else: st.info("近期無事件")

elif m == "🧮 攤平計算機":
 st.title("🧮 成本攤平")
 c1, c2 = st.columns(2)
 p1, q1 = c1.number_input("原價", 100.0), c1.number_input("原量", 1000.0)
 p2, q2 = c2.number_input("新價", 90.0), c2.number_input("新量", 1000.0)
 st.metric("均價結果", f"{round(((p1*q1)+(p2*q2))/(q1+q2), 2)}")
