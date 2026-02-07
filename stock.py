import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json, os, hashlib
from io import BytesIO

# --- 1. DATA ---
F = "data.json"
def hsh(p): return hashlib.sha256(p.encode()).hexdigest()
def lod():
    if os.path.exists(F):
        try:
            with open(F, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. LOGIN ---
st.set_page_config(layout="wide")
if 'db' not in st.session_state: st.session_state.db = lod()
u = st.session_state.get('u')

if not u:
    st.title("🛡️ Family Stock System")
    id = st.sidebar.text_input("ID")
    pw = st.sidebar.text_input("PW", type="password")
    if st.sidebar.button("Login"):
        if id and pw:
            ph = hsh(pw)
            if id not in st.session_state.db:
                st.session_state.db[id] = {"p": ph, "s": []}
                sav(st.session_state.db)
            if st.session_state.db[id]["p"] == ph:
                st.session_state.u = id
                st.rerun()
    st.stop()

# --- 3. MENU ---
st.sidebar.write(f"USER: {u}")
m = st.sidebar.radio("MENU", ["Stock", "Tool"])
if st.sidebar.button("Logout"):
    st.session_state.u = None
    st.rerun()

# --- 4. STOCK ---
if m == "Stock":
    st.title("📈 儀表板")
    with st.expander("Add New"):
        with st.form("f", clear_on_submit=True):
            n = st.text_input("Name")
            t = st.text_input("Code (e.g. 2330.TW)")
            p = st.number_input("Price", min_value=0.0)
            q = st.number_input("Qty", min_value=1)
            if st.form_submit_button("Save"):
                if n and t:
                    st.session_state.db[u]["s"].append({"n":n,"t":t.upper(),"p":p,"q":q})
                    sav(st.session_state.db)
                    st.rerun()

    sk = st.session_state.db[u]["s"]
    if sk:
        res = []
        for i in sk:
            try:
                o = yf.Ticker(i["t"])
                h = o.history(period="1d")
                c = round(h["Close"].iloc[-1], 2)
                v = round(c * i["q"])
                res.append({"Name":i["n"],"Price":c,"Value":v,"Code":i["t"]})
            except: continue
        
        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            
            # Excel Export
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine='xlsxwriter') as w:
                df.to_excel(w, index=False)
            st.download_button("Download Excel", bio.getvalue(), "list.xlsx")

            st.divider()
            l, r = st.columns(2)
            l.plotly_chart(px.pie(df, values='Value', names='Name', title="Asset Pie"), use_container_width=True)
            with r:
                sel = st.selectbox("View Trend", df["Name"].tolist())
                cod = df[df["Name"]==sel]["Code"].values[0]
                hd = yf.Ticker(cod).history(period="6mo")
                if not hd.empty:
                    st.plotly_chart(px.line(hd, y="Close", title=sel), use_container_width=True)
            
            if st.sidebar.button("Clear All"):
                st.session_state.db[u]["s"] = []
                sav(st.session_state.db)
                st.rerun()
    else: st.info("No Data")

# --- 5. TOOL ---
elif m == "Tool":
    st.title("🧮 成本攤平")
    p1 = st.number_input("Old Price", value=100.0)
    q1 = st.number_input("Old Qty", value=1000)
    p2 = st.number_input("New Price", value=90.0)
    q2
