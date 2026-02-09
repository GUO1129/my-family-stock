import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json, os, hashlib
from datetime import datetime

# --- 1. 後端資料核心 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if not os.path.exists(F): return {}
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F = "data.json"): return {}
# --- 2. 介面樣式 ---
st.set_page_config(page_title="家族投資系統", layout="wide", initial_sidebar_state="expanded")

# 融入更多專業UI/UX設計，兼顧質感與深色模式友好
st.markdown("""
<style>
    /* 全局背景和文字 */
    body {
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
        color: #333333;
    }
    .stApp {
        background-color: #f9fafb; /* 淺灰色背景 */
        background-image: linear-gradient(to bottom, #f9fafb, #edf2f7); /* 輕微漸變 */
    }

    /* 標題與側邊欄 */
    h1, h2, h3, h4, h5, h6 {
        color: #1a202c; /* 深色標題 */
        font-weight: 600;
    }
    .stSidebar {
        background-color: #ffffff; /* 側邊欄白色 */
        box-shadow: 2px 0 5px rgba(0,0,0,0.05); /* 輕微陰影 */
    }
    .stSidebar [data-testid="stMarkdownContainer"] p {
        color: #333333;
    }
    
    /* 輸入框和按鈕 */
    input[type="text"], input[type="password"], input[type="number"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 15px;
        color: #2d3748;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
    }
    .stButton > button {
        background-color: #2563EB; /* 藍色按鈕 */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        background-color: #1E40AF; /* 深藍色 */
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    .stForm button {
        background-color: #38a169; /* 綠色儲存按鈕 */
    }
    .stForm button:hover {
        background-color: #2f855a;
    }

    /* 指標卡片 (Metrics) */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.08); /* 更明顯的陰影 */
        transition: all 0.2s ease-in-out;
        border-left: 5px solid #2563EB; /* 左側藍色邊框 */
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important; /* 灰色標籤 */
        font-weight: 500;
        font-size: 1.0em;
    }
    [data-testid="stMetricValue"] {
        color: #1a202c !important; /* 深色數值 */
        font-size: 2.2em; /* 更大的字體 */
        font-weight: 700;
        margin-top: 5px;
        display: flex;
        align-items: center;
    }
    [data-testid="stMetricDelta"] {
        font-size: 1.1em;
        font-weight: 600;
        margin-left: 10px;
        padding: 4px 8px;
        border-radius: 6px;
        background-color: rgba(0,0,0,0.05); /* 輕微背景 */
    }

    /* 盈虧顏色 */
    .st-emotion-cache-1wq0v1f.eqr7sfz1 { /* 針對 Delta (變化值) 的容器 */
        color: unset !important; /* 重置 Streamlit 預設顏色 */
    }
    .st-emotion-cache-1wq0v1f.eqr7sfz1 div[data-testid="stMetricDelta"] { /* 針對 Delta (變化值) 的實際數值 */
        color: white !important; /* 確保文字為白色 */
    }
    
    /* 損益為正值 */
    .st-emotion-cache-1wq0v1f.eqr7sfz1 div[data-testid="stMetricDelta"][data-delta-type="increased"] {
        background-color: #ef4444 !important; /* 紅色背景 */
    }
    /* 損益為負值 */
    .st-emotion-cache-1wq0v1f.eqr7sfz1 div[data-testid="stMetricDelta"][data-delta-type="decreased"] {
        background-color: #22c55e !important; /* 綠色背景 */
    }

    /* 表格 */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden; /* 確保圓角 */
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    }
    .dataframe-row-even {
        background-color: #f7fafc; /* 隔行變色 */
    }
    .dataframe-row-odd {
        background-color: #ffffff;
    }
    
    /* 損益表格內容顏色 */
    .stDataFrame div {
        color: #333333; /* 確保表格文字為深色 */
    }
    .positive-profit {
        color: #ef4444; /* 紅色文字 */
        font-weight: 600;
    }
    .negative-profit {
        color: #22c55e; /* 綠色文字 */
        font-weight: 600;
    }
    
    /* 展開器 Expander */
    .streamlit-expanderHeader {
        background-color: #f0f4f8; /* 淺藍灰色 */
        border-radius: 8px;
        padding: 10px 15px;
        color: #2d3748;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .streamlit-expanderContent {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .stPlotlyChart {
        border-radius: 12px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.08);
        overflow: hidden;
        background-color: #ffffff;
    }

</style>
""", unsafe_allow_html=True)


if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

# --- 登入頁面 ---
if not u:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A; font-size: 2.5em;'>🛡️ 家族投資安全系統</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4A5568; font-size: 1.1em;'>請輸入您的專屬帳號密碼，開始管理家族財富。</p>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.2, 1])
    with c2:
        uid = st.text_input("👤 帳號")
        upw = st.text_input("🔑 密碼", type="password")
        if st.button("🚀 登入系統", use_container_width=True):
            if uid and upw:
                ph=hsh(upw); db=st.session_state.db
                if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db); st.success("新帳號建立成功！")
                if db[uid]["p"]==ph: 
                    st.session_state.u=uid
                    st.rerun()
                else: st.error("密碼錯誤或帳號不存在！")
    st.stop()

# --- 登入後的側邊欄 ---
st.sidebar.markdown(f"## 💎 {u} 的投資領航艙")
st.sidebar.markdown(f"✨ **歡迎回來！{u}！**") # 歡迎詞
st.sidebar.markdown("---")

m = st.sidebar.radio("🚀 功能導覽", ["📈 資產儀表板", "📅 股利日曆", "🧮 交易精算大師"])

# 修改密碼小功能
with st.sidebar.expander("🔐 帳號安全設定"):
    old_p = st.text_input("輸入舊密碼", type="password", key="old_pw_sidebar")
    new_p = st.text_input("設定新密碼", type="password", key="new_pw_sidebar")
    if st.button("更新密碼", use_container_width=True):
        db = st.session_state.db
        if hsh(old_p) == db[u]["p"]:
            db[u]["p"] = hsh(new_p)
            sav(db)
            st.success("密碼修改成功！請重新登入")
            st.session_state.u = None
            st.rerun()
        else:
            st.error("舊密碼驗證失敗！")

if st.sidebar.button("🔒 安全登出", use_container_width=True): 
    st.session_state.u=None; st.rerun()

sk = st.session_state.db[u].get("s", [])

# --- 5. 資產儀表板 (核心邏輯升級與視覺強化) ---
if m == "📈 資產儀表板":
    st.markdown("<h2 style='color: #1a202c;'>🚀 家族資產儀表板</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #4a5568;'>一覽您的持股概況與財務動態。</p>", unsafe_allow_html=True)

    try:
        ex_rate = round(yf.Ticker("USDTWD=X").history(period="1d")["Close"].values[-1], 2)
    except: ex_rate = 32.5

    with st.expander("📝 新增/編輯持股項目", expanded=False): # 預設折疊，保持簡潔
        with st.form("add_form", clear_on_submit=True):
            st.markdown("#### 填寫持股詳細資訊")
            c1, c2 = st.columns(2)
            n = c1.text_input("股票名稱", help="例如：台積電、Apple")
            t = c1.text_input("代碼 (例: AAPL 或 2330.TW)", help="美股直接輸代碼，台股加 .TW")
            p = c2.number_input("平均成本 (每股)", min_value=0.0, format="%.2f", help="買入的平均價格")
            q = c2.number_input("持有股數/單位", min_value=1.0, format="%.0f", help="持有的股數或單位數量")
            
            c3, c4 = st.columns(2)
            tg = c3.number_input("停利目標 (每股)", min_value=0.0, format="%.2f", help="達到此價格考慮獲利了結")
            sp = c4.number_input("停損預警 (每股)", min_value=0.0, format="%.2f", help="跌破此價格觸發風險警示")
            dv = c3.number_input("單股年股利 (預估)", min_value=0.0, format="%.2f", help="預估每年每股可領的股利")
            
            if st.form_submit_button("✅ 儲存持股", type="primary"):
                if n and t and p >= 0 and q >= 1: # 確保基本資料完整
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"tg":tg,"sp":sp,"dv":dv})
                    sav(st.session_state.db); st.success(f"已成功新增 {n}！"); st.rerun()
                else:
                    st.error("請檢查所有必填欄位並確保數值有效！")

    if sk:
        res = []
        for i in sk:
            try:
                tk = yf.Ticker(i["t"]); df_h = tk.history(period="1d")
                if df_h.empty:
                    st.warning(f"⚠️ 無法取得 {i['n']} ({i['t']}) 的即時數據，請檢查代碼。")
                    continue

                curr = round(df_h["Close"].values[-1], 2)
                is_us = ".TW" not in i["t"] and ".TWO" not in i["t"] # 更精確判斷美股
                rate = ex_rate if is_us else 1.0
                curr_twd, cost_twd = curr * rate, i["p"] * rate
                mv_twd = round(curr_twd * i["q"])
                pf_twd = mv_twd - (cost_twd * i["q"])
                dv_twd = round(i.get("dv", 0) * i["q"] * rate)
                unit = "USD" if is_us else "TWD"

                # 停利/停損狀態判斷
                status_emoji = ""
                if i["tg"] > 0 and curr >= i["tg"]: status_emoji = "🎯"
                elif i["sp"] > 0 and curr <= i["sp"]: status_emoji = "🚨"

                res.append({
                    "股票": f"{i['n']} {status_emoji}",
                    "代碼": i['t'],
                    "現價": f"{curr:.2f} {unit}",
                    "平均成本": f"{i['p']:.2f} {unit}",
                    "持有股數": f"{int(i['q'])}",
                    "市值(台幣)": mv_twd,
                    "損益(台幣)": int(pf_twd),
                    "年股利(台幣)": dv_twd,
                    "停利目標": f"{i['tg']:.2f} {unit}" if i['tg'] > 0 else "-",
                    "停損預警": f"{i['sp']:.2f} {unit}" if i['sp'] > 0 else "-",
                    "_損益值_": pf_twd # 用於後續顏色判斷
                })
            except Exception as e:
                st.warning(f"⚠️ 處理 {i['n']} ({i['t']}) 時發生錯誤: {e}")
                continue
        
        if res:
            df = pd.DataFrame(res)
            
            # --- 動態著色表格 ---
            def color_profit(val):
                if val > 0: return 'color: #ef4444; font-weight: 600;' # 紅色 (賺)
                elif val < 0: return 'color: #22c55e; font-weight: 600;' # 綠色 (賠)
                else: return 'color: #333333;' # 黑色 (平)

            styled_df = df.style.applymap(color_profit, subset=['損益(台幣)'])
            
            st.markdown("### 📋 您的投資組合", unsafe_allow_html=True)
            st.dataframe(styled_df.hide(subset=["_損益值_"]), use_container_width=True) # 隱藏_損益值_欄位
            st.caption(f"💡 目前參考匯率：USD/TWD = **{ex_rate}**")
            
            # --- 總覽大型卡片 ---
            st.markdown("### 📈 財務關鍵數據 (台幣總計)", unsafe_allow_html=True)
            total_market_value = df['市值(台幣)'].sum()
            total_profit = df['損益(台幣)'].sum()
            total_dividend = df['年股利(台幣)'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("總市值", f"{total_market_value:,.0f} 元")
            with col2:
                # 總盈虧的顏色自動變化
                delta_color = "inverse" if total_profit < 0 else "normal"
                st.metric("總盈虧", f"{total_profit:,.0f} 元", delta=f"{total_profit:,.0f} 元", delta_color=delta_color)
            with col3:
                st.metric("預計年股利", f"{total_dividend:,.0f} 元")
            
            st.markdown("---") # 分隔線
            
            # --- 圓餅圖/趨勢圖 ---
            l, r = st.columns([1, 1.5])
            with l:
                # 升級為互動式環形圖
                fig_pie = go.Figure(data=[go.Pie(labels=df['股票'], values=df['市值(台幣)'], hole=.4)])
                fig_pie.update_layout(title_text='資產配比', title_x=0.5, 
                                      font=dict(color="#333333"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
            with r:
                sel = st.selectbox("👉 選擇個股查看歷史趨勢", df["股票"].tolist(), key="trend_selector")
                cod = df[df["股票"] == sel.split(' ')[0]]["代碼"].values[0] # 移除 emoji
                h = yf.Ticker(cod).history(period="6mo")
                if not h.empty:
                    fig_line = px.line(h, y="Close", title=f"{sel.split(' ')[0]} 6個月趨勢 (原始幣別)")
                    fig_line.update_layout(title_x=0.5, font=dict(color="#333333"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    fig_line.update_traces(line_color='#2563EB', line_width=2) # 藍色線條
                    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("暫無趨勢數據可顯示。")
    else: st.info("目前清單為空。請點擊上方'新增持股項目'開始建立您的投資組合！")

# --- 6. 股利日曆 ---
elif m == "📅 股利日曆":
    st.markdown("<h2 style='color: #1a202c;'>📅 股利與事件日曆</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #4a5568;'>追蹤您的持股除息日、財報公告等關鍵日期。</p>", unsafe_allow_html=True)
    
    # 這裡可以加入更多實用的事件追蹤邏輯
    st.info("功能持續擴充中，將自動抓取您清單中股票的最新除息與財報資訊。")

# --- 7. 交易精算大師 ---
elif m == "🧮 交易精算大師":
    st.markdown("<h2 style='color: #1a202c;'>🧮 交易獲利精算 (台股專用)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #4a5568;'>精確計算買賣股票時，扣除手續費與稅金後的「真正淨利」。</p>", unsafe_allow_html=True)
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        buy_p = c1.number_input("買入價格", value=100.0, step=0.1, format="%.2f", help="您買入股票的每股價格")
        sell_p = c2.number_input("預計賣出價格", value=102.0, step=0.1, format="%.2f", help="您預期賣出股票的每股價格")
        shares = c3.number_input("成交股數", value=1000, step=100, format="%d", help="買賣的總股數")
        
        st.markdown("---")
        
        c4, c5 = st.columns(2)
        discount = c4.slider("手續費折扣 (例如: 2.8折 -> 輸入2.8)", 0.0, 10.0, 2.8, step=0.1, help="您的券商給予的手續費折扣，0為免手續費，10為無折扣")
        is_day_trade = c5.checkbox("這是當沖交易 (交易稅減半)", help="當沖交易的交易稅為0.15%，非當沖為0.3%")

    # 運算邏輯
    fee_rate = 0.001425 * (discount / 10.0) # 千分之1.425 * 折扣
    tax_rate = 0.0015 if is_day_trade else 0.003
    
    buy_fee = int(max(20, buy_p * shares * fee_rate)) # 買入手續費，最低20元
    sell_fee = int(max(20, sell_p * shares * fee_rate)) # 賣出手續費，最低20元
    
    tax = int(sell_p * shares * tax_rate) # 交易稅
    
    total_cost = int((buy_p * shares) + buy_fee)
    total_get = int((sell_p * shares) - sell_fee - tax)
    net_profit = total_get - total_cost
    
    # 保本價計算
    # 讓 (賣出價 * (1 - 費率 - 稅率)) - 20 (最低手續費) = 買入價 * (1 + 費率) + 20 (最低手續費)
    # 簡化公式：breakeven_point * (1 - fee_rate - tax_rate) = buy_price * (1 + fee_rate)
    # 忽略最低手續費對保本價的微小影響，簡化計算
    breakeven = (buy_p * (1 + fee_rate)) / (1 - fee_rate - tax_rate)

    st.divider()
    res_a, res_b = st.columns(2)
    # 最終純利顏色根據盈虧變化
    profit_color_style = "color: #ef4444;" if net_profit > 0 else "color: #22c55e;" if net_profit < 0 else ""
    res_a.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); border-left: 5px solid #2563EB;'>"
                   f"<p style='color: #64748b; font-size: 1.0em; margin-bottom: 5px;'>💰 最終純利 (已扣稅費)</p>"
                   f"<p style='font-size: 2.2em; font-weight: 700; {profit_color_style}'>{net_profit:,} 元</p>"
                   f"</div>", unsafe_allow_html=True)
    
    res_b.markdown(f"<div style='background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); border-left: 5px solid #10b981;'>"
                   f"<p style='color: #64748b; font-size: 1.0em; margin-bottom: 5px;'>🛡️ 損益平價 (保本價)</p>"
                   f"<p style='font-size: 2.2em; font-weight: 700; color: #1a202c;'>{round(breakeven, 2)} 元</p>"
                   f"</div>", unsafe_allow_html=True)
    
    st.info(f"💡 試算詳情：買入手續費 ${buy_fee}，賣出手續費 ${sell_fee}，交易稅 ${tax}。")
