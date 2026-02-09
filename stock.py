import streamlit as st import yfinance as yf import pandas as pd import json, os, hashlib, requests

BACKEND_GEMINI_KEY = "AIzaSyC9YhUvSazgUlT0IU7Cd8RrpWnqgcBkWrw" F = "data.json"

def hsh(p): return hashlib.sha256(p.encode()).hexdigest() def lod(): if not os.path.exists(F): return {} try: with open(F, "r", encoding="utf-8") as f: return json.load(f) except: return {} def sav(d): with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

st.set_page_config(page_title="家族投資系統", layout="wide") if 'db' not in st.session_state: st.session_state.db = lod() if 'u' not in st.session_state: st.session_state.u = None

if not st.session_state.u: st.title("🛡️ 登入系統") uid = st.text_input("帳號") upw = st.text_input("密碼", type="password") if st.button("登入"): if uid and upw: db = st.session_state.db if uid not in db: db[uid] = {"p": hsh(upw), "s": []} sav(db) if db[uid]["p"] == hsh(upw): st.session_state.u = uid st.rerun() else: st.error("密碼錯誤") st.stop()

u = st.session_state.u m = st.sidebar.radio("功能", ["📈 資產儀表板", "🤖 AI 助手", "🧮 攤平計算"])

if m == "🤖 AI 助手": st.title("🤖 AI 顧問") p = st.chat_input("輸入問題") if p: with st.chat_message("user"): st.write(p) url = f"{BACKEND_GEMINI_KEY}" res = requests.post(url, json={"contents": [{"parts": [{"text": p}]}]}) if res.status_code == 200: ans = res.json()['candidates'][0]['content']['parts'][0]['text'] with st.chat_message("assistant"): st.write(ans)

elif m == "📈 資產儀表板": st.title("📈 持股清單") with st.form("a"): n = st.text_input("名稱"); t = st.text_input("代碼"); c = st.number_input("成本", 0.0); q = st.number_input("股數", 0.0) if st.form_submit_button("存"): st.session_state.db[u]["s"].append({"n":n,"t":t,"p":c,"q":q}) sav(st.session_state.db); st.rerun() st.write(pd.DataFrame(st.session_state.db[u]["s"]))

elif m == "🧮 攤平計算": st.title("🧮 攤平計算") p1 = st.number_input("原價", 100.0); q1 = st.number_input("原數", 1000.0) p2 = st.number_input("加碼", 90.0); q2 = st.number_input("加碼數", 1000.0) if (q1+q2) > 0: st.metric("均價", f"{round(((p1q1)+(p2q2))/(q1+q2), 2)}")
