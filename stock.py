import streamlit as st
import yfinance as yf
import pandas as pd
import json, os, hashlib, requests
import plotly.express as px

# --- 1. 後端資料核心 ---
F = "data.json"

# 從 Streamlit Secrets 讀取金鑰
if "GEMINI_KEY" in st.secrets:
    STABLE_KEY = st.secrets["GEMINI_KEY"]
else:
    st.warning("🔑 請在 Streamlit Secrets 設定 GEMINI_KEY")
    STABLE_KEY = ""

def ask_gemini(prompt):
    """2026 終極救援連線邏輯"""
    if not STABLE_KEY: return "❌ 未設定 API Key"
    targets = [
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}"
    ]
    payload = {"contents": [{"parts": [{"text": f"你是專業投資顧問，請分析：{prompt}"}]}]}
    headers = {'Content-Type': 'application/json'}
    for url in targets:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
        except: continue
    return "❌ AI 顧問連線失敗，請檢查金鑰權限。"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 漲跌停計算 (台股精確版) ---
def calc_limit(price, is_tw=True, direction="up"):
    change = 1.1 if direction == "up" else 0.9
    raw = price * change
    return round(raw, 2)

# --- 3. 介面與樣式 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #d1d5db; }
    .main { background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 4. 登入系統 ---
if not u:
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.2, 1])
    with c2:
        uid = st.text_input("👤 帳號")
        upw = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 進入系統", use_container_width=True):
            db = lod()
            if uid and upw:
                ph = hsh(upw)
                if uid not in db: 
                    db[uid] = {"p": ph, "s": []}
                    sav(db)
                if db[uid]["p"] == ph: 
                    st.session_state.u = uid; st.session_state.db = db; st.rerun()
                else: st.error("密碼錯誤")
    st.stop()

# --- 5. 側邊導覽 ---
st.sidebar.markdown(f"### 👤 使用者: **{u}**")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None; st.rerun()

# --- 6. AI 助手頻道 ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 投資顧問")
    st.info("顧問目前已連結至 Gemini 1.5 Flash，可進行深度漲跌預估。")
    p = st.chat_input("請輸入股票代碼或投資問題（例如：分析 2330.TW 的未來走勢）")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問正在讀取最新數據並預估漲跌..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"): st.write(ans)

# --- 7. 資產儀表板 ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except:
        ex_rate = 32.5
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('正在同步市場實時數據...'):
            for i in sk:
                sym = i.get("t", "").strip().upper()
                try:
                    tk = yf.Ticker(sym)
                    df_h = tk.history(period="5d")
                    curr = df_h["Close"].iloc[-1]
                    prev = df_h["Close"].iloc[-2]
                    is_tw = ".TW" in sym or ".TWO" in sym
                    rate = ex_rate if not is_tw else 1.0
                    
                    mv = round(curr * rate * i.get("q", 0))
                    cost = round(i.get("p", 0) * rate * i.get("q", 0))
                    pf = int(mv - cost)
                    pf_p = (pf / cost * 100) if cost > 0 else 0
                    
                    res.append({
                        "名稱": i.get("n", ""), "代碼": sym,
                        "昨日收盤": round(prev, 2), "今日現價": round(curr, 2),
                        "預估漲停": calc_limit(prev, is_tw, "up"),
                        "預估跌停": calc_limit(prev, is_tw, "down"),
                        "持股數": i.get("q", 0), "市值": mv, "損益": pf, "報酬率%": round(pf_p, 2)
                    })
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 總市值 (TWD)", f"{df['市值'].sum():,} 元")
            c2.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=f"{df['損益'].sum():,}")
            c3.metric("💵 美金匯率", f"{ex_rate}")
            
            st.subheader("🔥 漲跌即時監控表")
            # 損益高亮顯示
            def color_pf(val):
                color = '#f87171' if val < 0 else '#4ade80' # 紅跌綠漲（台股風格可自行調整）
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(df.style.map(color_pf, subset=['損益', '報酬率%']).format("{:,}", subset=['市值', '損益']), use_container_width=True)
            
            # 圖表分析
            col_l, col_r = st.columns(2)
            with col_l:
                st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4, title="資產配置分佈"), use_container_width=True)
            with col_r:
                st.plotly_chart(px.bar(df, x='名稱', y='損益', color='損益', title="個股損益比較", color_continuous_scale='RdYlGn'), use_container_width=True)

            if st.button("🔮 讓 AI 診斷目前持股漲跌"):
                names = ", ".join([f"{x['名稱']}({x['代碼']})" for x in res])
                with st.spinner("AI 分析中..."):
                    report = ask_gemini(f"我的持股：{names}。請分別給予簡短漲跌預估。")
                    st.success("AI 持股診斷報告：")
                    st.write(report)

    with st.expander("🛠️ 持股管理倉儲"):
        with st.form("add_stock"):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("股票名稱")
            t = c2.text_input("代碼 (例: 2330.TW)")
            p = c3.number_input("平均買入成本", value=0.0)
            q = c4.number_input("持有股數", value=0.0)
            if st.form_submit_button("➕ 確認新增"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n, "t":t.upper(), "p":p, "q":q})
                    sav(db); st.rerun()

# --- 8. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平精算")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📍 現有持股")
            p1 = st.number_input("原成本價", value=100.0)
            q1 = st.number_input("原持股數", value=1000.0)
        with c2:
            st.markdown("### 📍 預計加碼")
            p2 = st.number_input("加碼價格", value=90.0)
            q2 = st.number_input("加碼股數", value=1000.0)
    
    if (q1 + q2) > 0:
        total_cost = (p1 * q1) + (p2 * q2)
        total_qty = q1 + q2
        avg = total_cost / total_qty
        st.markdown("---")
        st.metric("💡 攤平後預估均價", f"{round(avg, 2)} 元")
        st.info(f"總投入資金將增加至：{int(total_cost):,} 元")
