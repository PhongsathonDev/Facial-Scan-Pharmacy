import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
import requests, json, threading
from Facescan import FaceVerifier

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("แสดงรูปภาพเต็มจอ")
        self.root.attributes("-fullscreen", True)

        self.Outline = 0

        # โหลดรูปภาพพื้นหลัง
        self.IMAGE_PATH = "bg.png"
        image = Image.open(self.IMAGE_PATH)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        image = image.resize((screen_width, screen_height))
        self.photo = ImageTk.PhotoImage(image)

        self.canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

        # ----- ตัวแปร -----
        self.eat_days = 0
        self.eatday_text_id = None

        # ----- ตั้งค่าการส่ง LINE -----
        self.CHANNEL_ACCESS_TOKEN = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU="
        self.USER_ID = "Uaa30a62f505cfb7a3e546ed644e4755f"

        # ----- ตั้งเวลาแจ้งเตือนจริง -----
        self.alarm_hour = 20
        self.alarm_minute = 0

        # ----- Face Recognition -----
        WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"
        self.verifier = FaceVerifier(
            known_image_path="paper.jpeg",
            known_name="Paper",
            tolerance=0.5,
            hold_seconds=2.0,
            camera_index=0,
            webapp_url=WEBAPP_URL,
            sheet_name="Patient",
            face_id="Paper",
            serial_port="/dev/ttyUSB0",
            serial_baudrate=115200
        )

        # ----- วาด UI -----
        self.Eat_button()
        self.EatDay()
        self.DateNow()
        self.AlarmTime()
        self.Time()
        self.TestAlert_button()  # <<< เพิ่มปุ่มทดสอบการส่ง LINE

        # เริ่มตรวจเวลาแจ้งเตือนจริง
        self.check_alarm_time()

        # ปิดโปรแกรมเมื่อกด q
        self.root.bind('q', lambda event: self.root.destroy())

    # ---------- ปุ่ม "กินยา" ----------
    def Eat_button(self):
        btn = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline)
        self.canvas.tag_bind(btn, "<Button-1>", self.on_button_click)

    # ---------- ปุ่ม "ทดสอบแจ้งเตือน" ----------
    def TestAlert_button(self):
        # วาดปุ่มสี่เหลี่ยมเล็กลงหน่อยทางขวา
        test_btn = self.canvas.create_rectangle(950, 540, 1280, 670, outline="black", width=self.Outline)
        self.canvas.create_text(1115, 605, text="ทดสอบแจ้งเตือน", font=("Prompt", 22, "bold"))
        self.canvas.tag_bind(test_btn, "<Button-1>", self.test_send_alert)

    # ---------- นับวันกินยา ----------
    def EatDay(self):
        self.eat_days = 0
        self.eatday_text_id = self.canvas.create_text(132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold"))

    def increment_eatday(self):
        self.eat_days += 1
        self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))

    # ---------- วันที่ ----------
    def DateNow(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.canvas.create_text(280, 180, text=current_date, font=("Prompt", 28, "bold"))

    # ---------- เวลาแจ้งเตือน (20:00) ----------
    def AlarmTime(self):
        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        self.canvas.create_text(1120, 180, text=alarm_str, font=("Prompt", 28, "bold"))

    # ---------- เวลาแสดงปัจจุบัน ----------
    def Time(self):
        self.time_text_id = self.canvas.create_text(650, 425, text="", font=("Prompt", 36, "bold"))
        self.update_time()

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.canvas.itemconfigure(self.time_text_id, text=now)
        self.root.after(1000, self.update_time)

    # ---------- ตรวจจับเวลาปลุก ----------
    def check_alarm_time(self):
        now = datetime.now()
        if now.hour == self.alarm_hour and now.minute == self.alarm_minute:
            threading.Thread(target=self.send_line_alert, args=("⏰ ถึงเวลาทานยาแล้วนะคะ อย่าลืมกดปุ่มและสแกนหน้านะคะ 💊",)).start()
        self.root.after(60000, self.check_alarm_time)  # ตรวจทุก 60 วิ

    # ---------- ฟังก์ชันส่งข้อความ LINE ----------
    def send_line_alert(self, message_text):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.CHANNEL_ACCESS_TOKEN}"
        }

        data = {
            "to": self.USER_ID,
            "messages": [
                {
                    "type": "text",
                    "text": message_text
                }
            ]
        }

        response = requests.post("https://api.line.me/v2/bot/message/push",
                                 headers=headers, data=json.dumps(data))

        print("LINE ส่งแล้ว:", response.status_code, response.text)

    # ---------- ปุ่มทดสอบส่งแจ้งเตือน ----------
    def test_send_alert(self, event):
        print("🚀 ทดสอบส่ง LINE แจ้งเตือนทันที...")
        threading.Thread(target=self.send_line_alert, args=("โปรดรับประทานยา ในเวลานี้ครับ 20.00",)).start()

    # ---------- Event ปุ่มกินยา ----------
    def on_button_click(self, event):
        print("เริ่มสแกนใบหน้าเพื่อตรวจว่ากินยานะคะ...")
        self.root.update()
        verified = self.verifier.run()
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.update()

        if verified:
            print("✅ สแกนผ่าน → นับว่ากินยาเรียบร้อย เพิ่ม EatDay +1")
            self.increment_eatday()
        else:
            print("❌ ไม่ผ่าน/ยกเลิกการสแกน → ไม่เพิ่ม EatDay")

# ---------- เริ่มโปรแกรม ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenImageApp(root)
    root.mainloop()
