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
    """2026 終極自動偵測連線：解決所有 404/忙線問題"""
    if not STABLE_KEY: return "❌ 未設定 API Key"
    
    # 自動嘗試所有可能的路徑與模型組合
    test_configs = [
        ("v1beta", "gemini-1.5-flash"),       # 成功率最高
        ("v1", "gemini-1.5-flash"),           # 正式版路徑
        ("v1beta", "gemini-1.5-flash-latest"),# 最新測試版
        ("v1beta", "gemini-pro")              # 舊版保底
    ]
    
    refined_prompt = f"你是一位專業股票顧問。請針對以下個股或問題，給出精確的短期漲跌預估分析與操作建議：\n{prompt}"
    payload = {"contents": [{"parts": [{"text": refined_prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    last_err = ""
    for api_ver, model_id in test_configs:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_id}:generateContent?key={STABLE_KEY}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=12)
            result = response.json()
            if response.status_code == 200:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                last_err = result.get('error', {}).get('message', '未知錯誤')
                if response.status_code != 404: break # 若不是 404 就不用試其他路徑了
        except: continue
    return f"❌ AI 連線失敗：{last_err}"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 漲跌計算邏輯 ---
def calc_limit(price, is_tw=True, direction="up"):
    """計算漲跌停價 (10%)"""
    change = 1.1 if direction == "up" else 0.9
    raw = price * change
    return round(raw, 2)

# --- 3. 頁面配置與自定義樣式 ---
st.set_page_config(page_title="家族投資戰情室", layout="wide")
st.markdown("""
<style>
    .stMetric { background-color: #f1f5f9; padding: 15px; border-radius: 12px; border: 1px solid #cbd5e1; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 4. 登入系統 (落實密碼保護) ---
if not u:
    st.markdown("<h1 style='text-align: center; color: #1e40af;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
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
                else: st.error("密碼錯誤，請重新輸入。")
    st.stop()

# --- 5. 導覽選單 ---
st.sidebar.markdown(f"### 👤 使用者: **{u}**")
m = st.sidebar.radio("功能導覽", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"])
if st.sidebar.button("🔒 安全登出"):
    st.session_state.u = None; st.rerun()

# --- 6. AI 助手頻道 (漲跌預估) ---
if m == "🤖 AI 投資助手":
    st.title("🤖 家族 AI 投資顧問")
    st.info("輸入股票代碼（如 2330.TW）獲取專業的漲跌分析與建議。")
    p = st.chat_input("請輸入您的投資疑問...")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.spinner("AI 顧問正在運算漲跌預估報告..."):
            ans = ask_gemini(p)
            with st.chat_message("assistant"): st.write(ans)

# --- 7. 資產儀表板 (含漲跌停監控) ---
elif m == "📈 資產儀表板":
    st.title("💎 家族資產戰情室")
    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except:
        ex_rate = 32.5
    
    sk = st.session_state.db[u].get("s", [])
    if sk:
        res = []
        with st.spinner('實時同步全球市場數據...'):
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
                        "市值": mv, "損益": pf, "報酬率%": round(pf_p, 2)
                    })
                except: continue
        
        if res:
            df = pd.DataFrame(res)
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 總市值 (TWD)", f"{df['市值'].sum():,} 元")
            c2.metric("📊 總盈虧", f"{df['損益'].sum():,} 元", delta=f"{df['損益'].sum():,}")
            c3.metric("💵 美金匯率", f"{ex_rate}")
            
            st.subheader("🔥 漲跌即時監控表")
            def color_pf(val):
                return f'color: {"#4ade80" if val >= 0 else "#f87171"}; font-weight: bold'
            
            st.dataframe(df.style.map(color_pf, subset=['損益', '報酬率%']).format("{:,}", subset=['市值', '損益']), use_container_width=True)
            
            # 視覺化分析
            col_l, col_r = st.columns(2)
            with col_l:
                st.plotly_chart(px.pie(df, values='市值', names='名稱', hole=0.4, title="資產分佈"), use_container_width=True)
            with col_r:
                if st.button("🔮 讓 AI 分析現有持股短期漲跌", use_container_width=True):
                    names = ", ".join([f"{x['名稱']}({x['代碼']})" for x in res])
                    with st.spinner("AI 分析中..."):
                        report = ask_gemini(f"我的持股：{names}。請給予漲跌預估。")
                        st.success("AI 持股分析報告：")
                        st.write(report)

    with st.expander("🛠️ 管理持股"):
        with st.form("add"):
            ca, cb, cc, cd = st.columns(4)
            n, t, p, q = ca.text_input("名稱"), cb.text_input("代碼"), cc.number_input("成本"), cd.number_input("股數")
            if st.form_submit_button("➕ 新增"):
                if n and t:
                    db = lod(); db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q}); sav(db); st.rerun()

# --- 8. 攤平計算機 ---
elif m == "🧮 攤平計算機":
    st.title("🧮 成本攤平精算")
    c1, c2 = st.columns(2)
    p1 = c1.number_input("原成本價", value=100.0)
    q1 = c1.number_input("原持股數", value=1000.0)
    p2 = c2.number_input("加碼價格", value=90.0)
    q2 = c2.number_input("加碼股數", value=1000.0)
    if (q1 + q2) > 0:
        avg = ((p1 * q1) + (p2 * q2)) / (q1 + q2)
        st.metric("💡 攤平後預估均價", f"{round(avg, 2)} 元")
