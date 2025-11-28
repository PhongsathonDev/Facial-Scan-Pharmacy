# config.py

# =========================================
# 📢 LINE NOTIFY SETTINGS
# =========================================
LINE_ACCESS_TOKEN = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU=" 
LINE_USER_ID = "Uaa30a62f505cfb7a3e546ed644e4755f"

# =========================================
# ☁️ GOOGLE SHEETS / WEB APP SETTINGS
# =========================================
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzbxWYrMm4hLpA70R3MqH9_St1djR3P-DDduRYsnpXxjWBDxCf0zjSfVxD_Ycjl6vzS/exec"
SHEET_NAME = "Patient"
OFFLINE_LOG_FILE = "offline_logs.json"

# =========================================
# 🔌 HARDWARE & SERIAL (ESP32)
# =========================================
SERIAL_PORT = "/dev/ttyUSB0" 
SERIAL_BAUDRATE = 115200

# =========================================
# 👤 FACE RECOGNITION SETTINGS
# =========================================
KNOWN_IMAGE_PATH = "patient.jpeg"
KNOWN_NAME = "patient"
FACE_ID = "patient_001"

TOLERANCE = 0.45
HOLD_SECONDS = 3.0

# =========================================
# 📷 CAMERA SETTINGS
# =========================================
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# =========================================
# ⏰ ALARM & UI SETTINGS
# =========================================
ALARM_HOUR = 20
ALARM_MINUTE = 0
BG_IMAGE_PATH = "bg.png"

# =========================================
# ⏱️ TIMEOUT SETTINGS (เพิ่มส่วนนี้)
# =========================================
SCAN_TIMEOUT = 30.0

# =========================================
# 💊 DATA STORAGE (AUTO SAVE)
# =========================================
EAT_DAYS = 0