def ask_gemini(prompt):
    """2026 年最強連線邏輯：精準對接模型 ID 與路徑"""
    # 按照優先順序排列最穩定的路徑組合
    targets = [
        ("v1beta", "gemini-1.5-flash"), # 新帳號首選
        ("v1beta", "gemini-1.5-flash-latest"), # 強制最新版
        ("v1", "gemini-1.5-flash"), # 標準版
        ("v1", "gemini-1.0-pro")    # 保底版
    ]
    
    last_err = ""
    for api_ver, model_name in targets:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={STABLE_KEY}"
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                last_err = result.get('error', {}).get('message', '未知錯誤')
                # 只有 404 (找不到模型) 才繼續試下一個，其他錯誤 (如 403) 代表 Key 有問題
                if response.status_code != 404: break
        except:
            continue
            
    return f"❌ AI 顧問連線失敗：{last_err}\n💡 提示：這代表您的金鑰權限尚未開通此模型。請確認您在 AI Studio 點選的是 'New Project'。"
