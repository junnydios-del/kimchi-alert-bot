import requests
TELEGRAM_TOKEN = "봇토큰"
CHAT_ID = "채팅ID"
requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
              data={"chat_id": CHAT_ID, "text": "테스트 메시지"})
