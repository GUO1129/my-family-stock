# ... (前面代碼不變)
            with st.spinner("AI 正在分析市場數據..."):
                try:
                    my_stocks = st.session_state.db[u].get("s", [])
                    context = f"你現在是一位專業分析師。我的持股資料是：{my_stocks}。請以此為基礎回答我的問題：{prompt}"
                    
                    # 這是針對 403 錯誤優化過的請求格式
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": context}]
                        }]
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'candidates' in data:
                            ans = data['candidates'][0]['content']['parts'][0]['text']
                            with st.chat_message("assistant"):
                                st.write(ans)
                            st.session_state.chat_history.append({"role": "assistant", "content": ans})
                        else:
                            st.error("AI 回傳格式異常，請再試一次。")
                    elif response.status_code == 403:
                        st.error("❌ 錯誤碼 403：API Key 權限不足或無效。請確認您的 Key 是否已在 Google AI Studio 啟用，且沒有限制存取 IP。")
                    else:
                        st.error(f"連線失敗 (錯誤碼: {response.status_code})")
                except Exception as e:
                    st.error(f"發生預期外錯誤: {e}")
# ... (後面代碼不變)
