import requests

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwccadFbmRmLNJVAIxbPpj6XYB5alogmmN9WIIfWO2abITZ9OuxuLMYFgp3ATVDFFkXYA/exec"  # แทนด้วย URL ของเรา

# ตัวอย่าง: เลือกส่งไปที่ชีตชื่อ "LogFace"
payload = {
    "sheet": "sheet1",   # <- ชื่อชีตในไฟล์ Google Sheet (แท็บข้างล่าง)
    "data": {
        # KEY ต้องตรงกับ "ชื่อหัวตาราง" ในแถวแรกของชีตนั้น
        "Timestamp": "",               # ปล่อยว่างได้ เดี๋ยว Script ใส่เวลาให้
        "Name": "Paper",
        "FaceID": "user_001",
        "Status": "Detected",
        "Note": "ทดสอบส่งจาก Python รอบ"
    }
}

response = requests.post(WEBAPP_URL, json=payload)

print("Status code:", response.status_code)
print("Response text:", response.text)
