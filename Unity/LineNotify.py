import requests
import json

# ===== ตั้งค่า =====
CHANNEL_ACCESS_TOKEN = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU="  # ใส่ Access Token จาก LINE Developer Console
USER_ID = "Uaa30a62f505cfb7a3e546ed644e4755f"         # userId ของผู้ใช้ที่ต้องการส่งหา

# ===== สร้างข้อความ =====
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
}

data = {
    "to": USER_ID,
    "messages": [
        {
            "type": "text",
            "text": "สวัสดีค่ะ ส่งจาก LINE OA ด้วย Python"
        }
    ]
}

# ===== ส่งข้อความ =====
response = requests.post(
    "https://api.line.me/v2/bot/message/push",
    headers=headers,
    data=json.dumps(data)
)

print("Status:", response.status_code)
print("Response:", response.text)
