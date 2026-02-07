import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
# --- 後端 ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
 if not os.path.exists(F): return {}
 with open(F,"r",encoding="utf-8") as f: return json.load(f)
def sav(d):
 with open(F,"w",encoding="utf-8") as f: json.dump(d,f,indent=2)
# --- 設定 ---
st.set_page_config(page_title="家族投資", layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')
# --- 登入 ---
if not u:
 st.title("🛡️ 家族投資系統")
 uid = st.sidebar.text_input("帳號")
 upw = st.sidebar.text_input("密碼", type="password")
 if st.sidebar.button("登入"):
  if uid and upw:
   ph=hsh(upw); db=st.session_state.db
   if uid not in db: db[uid]={"p":ph,"s":[]}; sav(db)
   if db[uid]["p"]==ph: st.session_state.u=uid; st.rerun()
 st.stop()
# --- 選單 ---
m = st.sidebar.radio("選單", ["資產","日曆","攤平"])
if st.sidebar.button("登出"): st.session_state.u=None; st.rerun()
# --- 邏輯 ---
sk = st.session_state.db[u].get("s", [])
if m == "資產":
 st.title("📈 投資儀表板")
 n = st.text_input("股票名稱")
 t = st.text_input("代碼(例:2330.TW)")
 p = st.number_input("買價", 0.0)
 q = st.number_input("股數", 1.0)
 dv = st.number_input("年股利", 0.0)
 if st.button("儲存持股"):
  if n and t:
   st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q,"dv":dv})
   sav(st.session_state.db); st.rerun()
 if sk:
  res = []
  for i in sk:
   try:
    tk_id = i["t"]
    tk = yf.Ticker(tk_id)
    h =
