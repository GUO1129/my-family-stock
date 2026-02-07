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
    try:
        with open(F, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def sav(d):
    with open(F, "w", encoding="utf-8") as f: json.dump(d, f, indent=2)

# --- 2. 強化對比 CSS (針對字體顏色優化) ---
st.set_page_config(page_title="家族投資系統", layout="wide")
st.markdown("""
<style>
    /* 背景與基礎字體 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    /* 強制所有段落與標籤為白色 */
    p, label, .stMarkdown, .stText {
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 1.05rem !important;
    }
    /* 側邊欄文字強化 */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    /* 表格內部文字強化 (最重要) */
    .stDataFrame [data-testid="stTable"] td, .stDataFrame [data-testid="stTable"] th {
        color: #ffffff !important;
    }
    /* Metric 數字發光與標題 */
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    [data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: bold !important; }
    
    /* 卡片與輸入框 */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.
