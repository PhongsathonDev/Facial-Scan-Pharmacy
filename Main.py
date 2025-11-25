import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
import requests, json, threading

# Import คลาสต่างๆ
from Facescan import FaceVerifier
from register_face import register_new_face 
from Manual import ManualUI
import config  # <--- นำเข้าไฟล์ตั้งค่าที่เราสร้างใหม่

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tuberbox System")
        self.root.attributes("-fullscreen", True)
        
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.Outline = 0 

        # ============================
        # 1. โหลด Asset (เฉพาะของหน้า Main)
        # ============================
        self.assets = {}
        self.load_main_assets()

        # ============================
        # 2. สร้าง Canvas และ Background หลัก
        # ============================
        self.canvas = tk.Canvas(root, width=self.screen_width, height=self.screen_height, highlightthickness=0, bg="white")
        self.canvas.pack(fill="both", expand=True)
        
        self.bg_item = self.canvas.create_image(0, 0, image=self.assets['bg'], anchor="nw")

        # ============================
        # 3. แยกส่วนจัดการ UI
        # ============================
        self.main_ui_items = []   # เก็บ ID Widget หน้าหลัก
        
        # สร้าง Logic ของหน้าคู่มือ (Manual) แยกไปไว้ที่คลาส ManualUI
        # ส่ง self.show_main_ui เป็น callback เมื่อกดปุ่มย้อนกลับ
        self.manual_page = ManualUI(self.canvas, self.screen_width, self.screen_height, on_back_callback=self.show_main_ui)

        # ตัวแปรระบบต่างๆ
        self.eat_days = 0
        self.eatday_text_id = None
        self.time_text_id = None
        self.is_scanning = False 

        # ============================
        # ⚙️ ดึงค่าจาก config.py
        # ============================
        self.CHANNEL_ACCESS_TOKEN = config.LINE_ACCESS_TOKEN
        self.USER_ID = config.LINE_USER_ID
        self.alarm_hour = config.ALARM_HOUR
        self.alarm_minute = config.ALARM_MINUTE
        
        # ตั้งค่า FaceVerifier โดยใช้ค่าจาก config
        self.verifier = FaceVerifier(
            known_image_path=config.KNOWN_IMAGE_PATH,
            known_name=config.KNOWN_NAME,
            tolerance=config.TOLERANCE,
            hold_seconds=config.HOLD_SECONDS,
            camera_index=config.CAMERA_INDEX,
            webapp_url=config.WEBAPP_URL,
            sheet_name=config.SHEET_NAME,
            face_id=config.FACE_ID,
            serial_port=config.SERIAL_PORT,
            serial_baudrate=config.SERIAL_BAUDRATE
        )

        # สร้าง UI หน้าหลัก
        self.build_main_ui()

        # เริ่ม Loop
        self.update_time()
        self.check_alarm_time()
        self.root.bind('q', lambda event: self.root.destroy())

    def load_main_assets(self):
        """โหลดเฉพาะรูปพื้นหลังหน้าหลัก"""
        try:
            # ใช้ path จาก config
            img = Image.open(config.BG_IMAGE_PATH)
            img = img.resize((self.screen_width, self.screen_height))
            self.assets['bg'] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading bg.png: {e}")
            img = Image.new('RGB', (self.screen_width, self.screen_height), color=(200, 200, 200))
            self.assets['bg'] = ImageTk.PhotoImage(img)

    def build_main_ui(self):
        """สร้างปุ่มและข้อความสำหรับหน้าหลัก"""
        # Text: จำนวนวัน
        self.eatday_text_id = self.canvas.create_text(132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold"), fill="white")
        self.main_ui_items.append(self.eatday_text_id)

        # Text: วันที่ปัจจุบัน
        current_date = datetime.now().strftime("%d/%m/%Y")
        date_id = self.canvas.create_text(280, 180, text=current_date, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(date_id)

        # Text: เวลาแจ้งเตือน
        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        alarm_id = self.canvas.create_text(1100, 180, text=alarm_str, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(alarm_id)

        # Text: เวลาปัจจุบัน
        self.time_text_id = self.canvas.create_text(650, 425, text="", font=("Prompt", 50, "bold"), fill="white")
        self.main_ui_items.append(self.time_text_id)

        # Button: กินยา (กลาง)
        btn_eat = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline, tags="btn_eat")
        self.canvas.tag_bind(btn_eat, "<Button-1>", self.on_button_click)
        self.main_ui_items.append(btn_eat)

        # Button: ทดสอบ (ขวาบน)
        btn_test = self.canvas.create_rectangle(900, 100, 1280, 250, outline="black", width=self.Outline, tags="btn_test")
        self.canvas.tag_bind(btn_test, "<Button-1>", self.test_send_alert)
        self.main_ui_items.append(btn_test)

        # Button: เปิดคู่มือ (ซ้ายล่าง) -> เรียกฟังก์ชันเปิด Manual
        btn_manual = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline, tags="btn_manual")
        self.canvas.tag_bind(btn_manual, "<Button-1>", self.open_manual_mode)
        self.main_ui_items.append(btn_manual)

        # Button: ลงทะเบียน (ขวาล่าง)
        btn_register = self.canvas.create_rectangle(950, 550, 1280, 700, outline="black", width=self.Outline, tags="btn_register")
        self.canvas.tag_bind(btn_register, "<Button-1>", self.on_register_click)
        self.main_ui_items.append(btn_register)

    # ============================
    # Logic การสลับหน้าจอ
    # ============================
    def open_manual_mode(self, event):
        """ซ่อนหน้าหลัก และเรียกหน้าคู่มือให้แสดงผล"""
        print("📖 เข้าสู่โหมดคู่มือ")
        # ซ่อน items หน้าหลัก
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='hidden')
        
        # สั่งให้คลาส ManualUI แสดงผล
        self.manual_page.show()

    def show_main_ui(self):
        """callback เมื่อกดกลับจากหน้าคู่มือ"""
        print("🏠 กลับสู่หน้าหลัก")
        # แสดง items หน้าหลักกลับมา
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='normal')

    # ============================
    # ฟังก์ชันการทำงานอื่นๆ
    # ============================
    def on_register_click(self, event):
        if self.is_scanning: return
        self.is_scanning = True
        print("⚙️ เข้าสู่โหมดลงทะเบียนใบหน้า...")
        try:
            # เรียกฟังก์ชันลงทะเบียน (อาจจะต้องปรับให้รับค่าจาก config ในอนาคตถ้าต้องการ)
            self.root.after(10, register_new_face)
            print("🔄 อัปเดตข้อมูลใบหน้า...")
            # โหลดใบหน้าใหม่เข้าระบบ
            self.verifier.known_face_encodings, self.verifier.known_face_names = self.verifier._load_known_faces()
        except Exception as e:
            print(f"❌ Error Register: {e}")
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.focus_force()
        self.is_scanning = False

    def increment_eatday(self):
        self.eat_days += 1
        if self.eatday_text_id:
            self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        if self.time_text_id:
            self.canvas.itemconfigure(self.time_text_id, text=now)
        self.root.after(1000, self.update_time)

    def check_alarm_time(self):
        now = datetime.now()
        # ตรวจสอบเวลาให้ตรงกับที่ตั้งไว้ใน config
        if now.hour == self.alarm_hour and now.minute == self.alarm_minute and now.second == 0:
             threading.Thread(target=self.send_line_alert, args=("⏰ ถึงเวลาทานยาแล้วนะคะ อย่าลืมกดปุ่มและสแกนหน้านะคะ 💊",)).start()
        self.root.after(1000, self.check_alarm_time)

    def send_line_alert(self, message_text):
        if not self.CHANNEL_ACCESS_TOKEN or not self.USER_ID:
            print("⚠️ LINE Token หรือ User ID ไม่ถูกต้อง")
            return

        headers = { "Content-Type": "application/json", "Authorization": f"Bearer {self.CHANNEL_ACCESS_TOKEN}" }
        data = { "to": self.USER_ID, "messages": [{"type": "text", "text": message_text}] }
        try:
            requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(data), timeout=5)
        except Exception as e:
            print("Error sending LINE:", e)

    def test_send_alert(self, event):
        threading.Thread(target=self.send_line_alert, args=("Test Alert",)).start()
        self.verifier.send_command_to_esp32("a")

    def on_button_click(self, event):
        if self.is_scanning: return
        self.is_scanning = True
        print("📷 เริ่มสแกนใบหน้า...")
        self.root.after(10, self._run_scan_process)

    def _run_scan_process(self):
        verified = self.verifier.run()
        self.root.attributes("-fullscreen", True)
        self.root.focus_force()
        if verified:
            print("✅ ผ่าน")
            self.increment_eatday()
        self.root.after(1000, lambda: setattr(self, 'is_scanning', False))

if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenImageApp(root)
    root.mainloop()