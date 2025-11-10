import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
import requests                    # สำหรับส่ง LINE
from Facescan import FaceVerifier  # ดึงคลาสจาก main.py

# ==== ตั้งค่า LINE Notify ====
LINE_TOKEN = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU="

def send_line_notify(message: str):
    """ส่งข้อความไป LINE Notify"""
    if not LINE_TOKEN or LINE_TOKEN == "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU=":
        print("⚠ ยังไม่ได้ใส่ LINE_TOKEN เลยนะคะ เลยส่ง LINE ไม่ได้")
        return

    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "message": message
    }

    try:
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        print("LINE Notify status:", resp.status_code, resp.text)
    except Exception as e:
        print("ส่ง LINE ไม่สำเร็จ:", e)


class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("แสดงรูปภาพเต็มจอ")
        self.root.attributes("-fullscreen", True)

        self.Outline = 0  # ความหนาเส้นขอบปุ่ม

        # ---------- ตั้งค่า Alarm ----------
        self.alarm_hour = 20       # 20 นาฬิกา
        self.alarm_minute = 0      # นาที 00
        self.alarm_triggered_today = False  # กันยิงซ้ำในวันเดียว

        # ---------- โหลดรูปภาพพื้นหลัง ----------
        self.IMAGE_PATH = "bg.png"
        image = Image.open(self.IMAGE_PATH)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        image = image.resize((screen_width, screen_height))
        self.photo = ImageTk.PhotoImage(image)

        # แสดงรูปบน Canvas
        self.canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

        # ----- ตัวแปรนับวันกินยา -----
        self.eat_days = 0
        self.eatday_text_id = None

        # ----- ตัวแปรสำหรับแสดงเวลา -----
        self.time_text_id = None

        # ----- สร้างอ็อบเจ็กต์ FaceVerifier -----
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
            serial_port="/dev/ttyUSB0",  # ถ้าเป็น /dev/ttyACM0 ก็เปลี่ยนตรงนี้
            serial_baudrate=115200
        )

        # วาด UI หลัก
        self.Eat_button()
        self.EatDay()
        self.DateNow()
        self.AlarmTime()
        self.Time()               # นาฬิกา + เช็ก alarm

        # >>> ปุ่มจำลองแจ้งเตือน <<<
        self.AlarmTest_button()

        # ปิดโปรแกรมเมื่อกด q
        self.root.bind('q', lambda event: self.root.destroy())

    # ---------- ปุ่มกินยา ----------
    def Eat_button(self):
        button_frame = self.canvas.create_rectangle(
            450, 540, 820, 670,
            outline="black", width=self.Outline
        )
        self.canvas.tag_bind(button_frame, "<Button-1>", self.on_button_click)

    # ---------- แสดงจำนวนวันที่กินยาแล้ว ----------
    def EatDay(self):
        self.eat_days = 0
        self.eatday_text_id = self.canvas.create_text(
            132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold")
        )

    def increment_eatday(self):
        self.eat_days += 1
        if self.eatday_text_id is not None:
            self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))

    # ---------- วันที่ปัจจุบัน ----------
    def DateNow(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.canvas.create_text(
            280, 180, text=current_date,
            font=("Prompt", 28, "bold")
        )

    # ---------- เวลาแจ้งเตือน (AlarmTime) แสดงเป็นเวลา 20:00 คงที่ ----------
    def AlarmTime(self):
        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        self.canvas.create_text(
            1120, 180, text=alarm_str,
            font=("Prompt", 28, "bold")
        )

    # ---------- เวลา ณ ปัจจุบัน (อัปเดตทุกวินาที) ----------
    def Time(self):
        # สร้าง text ครั้งเดียว
        self.time_text_id = self.canvas.create_text(
            650, 425, text="--:--:--",
            font=("Prompt", 36, "bold")
        )
        # แล้วเริ่ม loop อัปเดต
        self.update_time()

    def update_time(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        if self.time_text_id is not None:
            self.canvas.itemconfigure(self.time_text_id, text=time_str)

        # เช็ก alarm ทุกครั้งที่อัปเดตเวลา
        self.check_alarm(now)

        # เรียกตัวเองใหม่ทุก 1000 ms (1 วินาที)
        self.root.after(1000, self.update_time)

    # ---------- เช็กว่าได้เวลา Alarm หรือยัง ----------
    def check_alarm(self, now: datetime):
        # รีเซ็ตสถานะตอนเที่ยงคืน
        if now.hour == 0 and now.minute == 0 and now.second < 5:
            self.alarm_triggered_today = False

        # ถ้าตรงเวลา alarm และยังไม่ส่งในวันนี้
        if (now.hour == self.alarm_hour and
            now.minute == self.alarm_minute and
            not self.alarm_triggered_today):

            print("🔔 ถึงเวลา 20:00 น. แล้วนะคะ กำลังส่งแจ้งเตือนไป LINE")
            send_line_notify("🔔 ถึงเวลา 20:00 น. ทานยาด้วยนะคะ 🕗")
            self.alarm_triggered_today = True

    # ---------- ปุ่มจำลอง Alarm ----------
    def AlarmTest_button(self):
        # สร้างปุ่มด้านขวาของปุ่มกินยา (ปรับตำแหน่งได้ตามใจเลยนะคะ)
        rect = self.canvas.create_rectangle(
            880, 540, 1250, 670,
            outline="black", width=self.Outline
        )
        text = self.canvas.create_text(
            1065, 605, text="TEST ALARM",
            font=("Prompt", 20, "bold")
        )

        # ผูก event ให้ทั้ง rect และ text
        self.canvas.tag_bind(rect, "<Button-1>", self.on_alarm_test_click)
        self.canvas.tag_bind(text, "<Button-1>", self.on_alarm_test_click)

    def on_alarm_test_click(self, event):
        print("🔔 [TEST] กดปุ่มจำลองแจ้งเตือน 20:00 → ส่ง LINE ทันที")
        msg = "🔔 [TEST] จำลองว่าเป็นเวลา 20:00 แล้วนะคะ ทานยาด้วยน้า 🕗"
        send_line_notify(msg)

    # ---------- Event ตอนกดปุ่มกินยา ----------
    def on_button_click(self, event):
        print("เริ่มสแกนใบหน้าเพื่อตรวจว่ากินยานะคะ...")

        # อัปเดต UI ให้เรียบร้อยก่อน
        self.root.update()

        # เรียกตัวสแกนหน้า (บล็อกจนกว่าจะสแกนเสร็จ / กดยกเลิก)
        verified = self.verifier.run()

        # กลับมาหน้า UI
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.update()

        # ถ้าสแกนผ่าน -> เพิ่มวันกินยา
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
