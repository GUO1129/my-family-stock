def ask_gemini(prompt):
    """2026 終極自動偵測：解決所有 404 與模型找不到的問題"""
    if not STABLE_KEY: return "❌ Secrets 中找不到 GEMINI_KEY"
    
    # 按照成功率排列的所有可能路徑組合
    test_configs = [
        ("v1beta", "gemini-1.5-flash"),       # 最推薦：新帳號首選
        ("v1beta", "gemini-1.5-flash-latest"),# 強制最新版
        ("v1", "gemini-1.5-flash"),           # 正式版路徑
        ("v1beta", "gemini-pro")              # 舊版保底
    ]
    
    refined_prompt = f"你是一位專業股票顧問。請針對以下問題給出短期漲跌預估：\n{prompt}"
    payload = {"contents": [{"parts": [{"text": refined_prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    last_err = ""
    for api_ver, model_id in test_configs:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_id}:generateContent?key={STABLE_KEY}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                # 成功連線，直接回傳結果
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                last_err = result.get('error', {}).get('message', '未知錯誤')
                # 如果報錯不是 404 (找不到)，代表可能是 Key 本身有問題，直接中斷循環
                if response.status_code != 404: break
        except Exception as e:
            last_err = str(e)
            continue
            
    return f"❌ AI 連線路徑皆失敗。最後報錯：{last_err}\n💡 提示：請確認您的 API Key 是否來自 Google AI Studio 的 'New Project'。"
