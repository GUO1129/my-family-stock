def ask_gemini(prompt):
    """2026 終極救援版：徹底解決 404 問題"""
    if not STABLE_KEY: return "❌ Secrets 中找不到 GEMINI_KEY"
    
    # 根據你的報錯，我們改嘗試 v1 正式版路徑
    # 這是目前針對 'v1beta not found' 的唯一解藥
    urls = [
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={STABLE_KEY}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={STABLE_KEY}"
    ]
    
    refined_prompt = f"你是一位專業投資顧問。請分析以下問題並預估短期漲跌：\n{prompt}"
    payload = {"contents": [{"parts": [{"text": refined_prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    last_err = ""
    for url in urls:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            result = response.json()
            if response.status_code == 200:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                last_err = result.get('error', {}).get('message', '未知錯誤')
        except Exception as e:
            last_err = str(e)
            continue
            
    return f"❌ 系統路徑匹配失敗：{last_err}\n💡 請確認您在 Google AI Studio 申請 Key 時，左側是否顯示為 'Generative Language API'。"
