import streamlit as st import yfinance as yf import pandas as pd import json, os, hashlib, requests

🔑 這裡就是你的金鑰
BACKEND_GEMINI_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw"

--- 1. 資料處理 ---
F = "data.json" def hsh(p): return hashlib.sha256(p.encode()).hexdigest() def lod(): if not os.path.exists(F): return {} try: with open(F, "r", encoding="utf-8") as f: return json.load(f) except: return {} def sav(d): with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

--- 2. 登入系統 ---
if 'db' not in st.session_state: st.session_state.db = lod() if 'u' not in st.session_state: st.session_state.u = None u = st.session_state.u

if not u: st.title("🛡️ 家族投資系統：請登入") uid = st.text_input("👤 帳號") upw = st.text_input("🔑 密碼", type="password") if st.button("🚀 登入"): if uid and upw: db = st.session_state.db ph = hsh(upw) if uid not in db: db[uid] = {"p": ph, "s": []} sav(db) if db[uid]["p"] == ph: st.session_state.u = uid st.rerun() else: st.error("密碼錯誤") st.stop()

--- 3. 選單 ---
m = st.sidebar.radio("功能", ["📈 資產儀表板", "🤖 AI 投資助手", "🧮 攤平計算機"]) if st.sidebar.button("🔒 登出"): st.session_state.u = None st.rerun()

--- 4. 功能邏輯 ---
if m == "🤖 AI 投資助手": st.title("🤖 家族 AI 顧問") prompt = st.chat_input("輸入問題...") if prompt: with st.chat_message("user"): st.write(prompt) url = f"{BACKEND_GEMINI_KEY}" res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10) if res.status_code == 200: ans = res.json()['candidates'][0]['content']['parts'][0]['text'] with st.chat_message("assistant"): st.write(ans) else: st.error("AI 連線失敗")

elif m == "📈 資產儀表板": st.title("📈 我的持股") with st.form("add"): n = st.text_input("股票名稱"); t = st.text_input("代碼"); p = st.number_input("成本", 0.0); q = st.number_input("股數", 0.0) if st.form_submit_button("儲存"): db = lod(); db[u]["s"].append({"n":n,"t":t,"p":p,"q":q}); sav(db); st.rerun() st.write(pd.DataFrame(st.session_state.db[u]["s"]))

elif m == "🧮 攤平計算機": st.title("🧮 攤平計算") p1 = st.number_input("原價", 100.0); q1 = st.number_input("原數", 1000.0) p2 = st.number_input("加碼", 90.0); q2 = st.number_input("加碼數", 1000.0) if (q1+q2) > 0: st.metric("💡 均價", f"{round(((p1q1)+(p2q2))/(q1+q2), 2)} 元")
