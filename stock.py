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
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; }
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

with st.sidebar.expander("🔐 帳號安全"):
    old_p = st.text_input("舊密碼", type="password")
    new_p = st.text_input("新密碼", type="password")
    if st.button("確認修改"):
        db = st.session_state.db
        if hsh(old_p) == db[u]["p"]:
            db[u]["p"] = hsh(new_p); sav(db); st.success("成功！請重新登入"); st.session_state.u = None; st.rerun()
        else: st.error("舊密碼錯誤")

# --- 5. 資產儀表板 ---
if m == "📈 資產儀表板":
    st.title("💎 持股戰情室")
    
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增持股項目 (請正確輸入代碼)"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱 (如: 大井泵浦)")
            t = c1.text_input("代碼 (台股請加 .TW 或 .TWO, 如: 6982.TWO)")
            p = c2.number_input("平均成本", 0.0)
            q = c2.number_input("持有股數", 1.0)
            dv = c2.number_input("預估年股利", 0.0)
            if st.form_submit_button("💾 儲存持股"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper().strip(),"p":p,"q":q,"dv":dv})
                    sav(st.session_state.db); st.rerun()

    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        errors = []
        for i in sk:
            try:
                symbol = i["t"]
                # 測試抓取
                tk = yf.Ticker(symbol)
                df_h = tk.history(period="1d")
                
                # 如果失敗，嘗試自動補全 (針對台股)
                if df_h.empty and "." not in symbol:
                    for suffix in [".TW", ".TWO"]:
                        tk = yf.Ticker(symbol + suffix)
                        df_h = tk.history(period="1d")
                        if not df_h.empty:
                            symbol = symbol + suffix
                            break
                
                if not df_h.empty:
                    curr = round(df_h["Close"].values[-1], 2)
                    is_us = ".TW" not in symbol and ".TWO" not in symbol
                    rate = ex_rate if is_us else 1.0
                    mv = round(curr * rate * i["q"])
                    pf = int(mv - (i["p"] * rate * i["q"]))
                    res.append({
                        "股票": i["n"], "現價": f"{curr} {'USD' if is_us else 'TWD'}",
                        "市值(台幣)": mv, "損益(台幣)": pf, "代碼": symbol
                    })
                else:
                    errors.append(f"{i['n']} ({symbol})")
            except:
                errors.append(f"{i['n']} ({i['t']})")
        
        if errors:
            st.warning(f"⚠️ 以下股票暫時抓不到資料：{', '.join(errors)}。請確認代碼是否正確（如：6982.TWO）。")

        if res:
            df = pd.DataFrame(res)
            def color_pf(val):
                return f'color: {"red" if val > 0 else "green" if val < 0 else "black"}; font-weight: bold;'
            
            st.dataframe(df.style.applymap(color_pf, subset=['損益(台幣)']), use_container_width=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("總市值", f"{df['市值(台幣)'].sum():,} 元")
            c2.metric("總盈虧", f"{df['損益(台幣)'].sum():,} 元", delta=int(df['損益(台幣)'].sum()))
            
            with st.expander("🗑️ 刪除持股"):
                for idx, item in enumerate(sk):
                    if st.button(f"刪除 {item['n']}", key=f"del_{idx}"):
                        st.session_state.db[u]["s"].pop(idx); sav(st.session_state.db); st.rerun()
    else:
        st.info("目前清單空空的，快去新增股票吧！")

# --- 其他功能保持不變 ---
elif m == "📅 股利日曆":
    st.title("📅 事件追蹤")
elif m == "🧮 交易精算大師":
    st.title("🧮 交易獲利精算 (台股)")
