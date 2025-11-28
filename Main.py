import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
import requests, json, threading
import importlib  # ใช้สำหรับ Reload Config

# Import คลาสต่างๆ
from Facescan import FaceVerifier
from register_face import register_new_face 
from Manual import ManualUI
import config

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tuberbox System")
        self.root.attributes("-fullscreen", True)
        
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.Outline = 0 

        # ============================
        # 1. โหลด Asset
        # ============================
        self.assets = {}
        self.load_main_assets()

        # ============================
        # 2. สร้าง Canvas และ Background
        # ============================
        self.canvas = tk.Canvas(root, width=self.screen_width, height=self.screen_height, highlightthickness=0, bg="white")
        self.canvas.pack(fill="both", expand=True)
        
        self.bg_item = self.canvas.create_image(0, 0, image=self.assets['bg'], anchor="nw")

        # ============================
        # 3. แยกส่วนจัดการ UI
        # ============================
        self.main_ui_items = []   
        
        # หน้าคู่มือ (Manual)
        self.manual_page = ManualUI(self.canvas, self.screen_width, self.screen_height, on_back_callback=self.show_main_ui)

        # ตัวแปรระบบ
        self.eat_days = getattr(config, 'EAT_DAYS', 0)
        
        self.eatday_text_id = None
        self.time_text_id = None
        self.is_scanning = False 

        # ดึงค่าจาก config
        self.CHANNEL_ACCESS_TOKEN = config.LINE_ACCESS_TOKEN
        self.USER_ID = config.LINE_USER_ID
        self.alarm_hour = config.ALARM_HOUR
        self.alarm_minute = config.ALARM_MINUTE
        
        # ✅ สร้าง FaceVerifier ครั้งแรกครั้งเดียว
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
            serial_baudrate=config.SERIAL_BAUDRATE,
            scan_timeout=config.SCAN_TIMEOUT
        )

        # สร้าง UI หน้าหลัก
        self.build_main_ui()

        # เริ่ม Loop
        self.update_time()
        self.check_alarm_time()
        self.root.bind('q', lambda event: self.root.destroy())

    def load_main_assets(self):
        try:
            img = Image.open(config.BG_IMAGE_PATH)
            img = img.resize((self.screen_width, self.screen_height))
            self.assets['bg'] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading bg.png: {e}")
            img = Image.new('RGB', (self.screen_width, self.screen_height), color=(200, 200, 200))
            self.assets['bg'] = ImageTk.PhotoImage(img)

    def build_main_ui(self):
        self.eatday_text_id = self.canvas.create_text(132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold"), fill="white")
        self.main_ui_items.append(self.eatday_text_id)

        current_date = datetime.now().strftime("%d/%m/%Y")
        date_id = self.canvas.create_text(280, 180, text=current_date, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(date_id)

        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        alarm_id = self.canvas.create_text(1100, 180, text=alarm_str, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(alarm_id)

        self.time_text_id = self.canvas.create_text(650, 425, text="", font=("Prompt", 50, "bold"), fill="white")
        self.main_ui_items.append(self.time_text_id)

        btn_eat = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline, tags="btn_eat")
        self.canvas.tag_bind(btn_eat, "<Button-1>", self.on_button_click)
        self.main_ui_items.append(btn_eat)

        btn_test = self.canvas.create_rectangle(900, 100, 1280, 250, outline="black", width=self.Outline, tags="btn_test")
        self.canvas.tag_bind(btn_test, "<Button-1>", self.test_send_alert)
        self.main_ui_items.append(btn_test)

        btn_manual = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline, tags="btn_manual")
        self.canvas.tag_bind(btn_manual, "<Button-1>", self.open_manual_mode)
        self.main_ui_items.append(btn_manual)

        btn_register = self.canvas.create_rectangle(950, 550, 1280, 700, outline="black", width=self.Outline, tags="btn_register")
        self.canvas.tag_bind(btn_register, "<Button-1>", self.on_register_click)
        self.main_ui_items.append(btn_register)

    def open_manual_mode(self, event):
        print("📖 เข้าสู่โหมดคู่มือ")
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='hidden')
        self.manual_page.show()

    def show_main_ui(self):
        print("🏠 กลับสู่หน้าหลัก")
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='normal')

    def on_register_click(self, event):
        if self.is_scanning: return
        self.is_scanning = True
        print("⚙️ เข้าสู่โหมดลงทะเบียนใบหน้า...")

        def process_registration():
            try:
                # 1. ลงทะเบียนใบหน้า
                register_new_face()
                
                print("🔄 กำลังอัปเดตการตั้งค่าใหม่...")
                
                # 2. Reload config
                importlib.reload(config)
                
                # 🟢 [แก้ไข] รีเซ็ตจำนวนวันเป็น 0 สำหรับผู้ป่วยคนใหม่
                self.eat_days = 0
                self.save_eat_days_to_config(0)
                if self.eatday_text_id:
                    self.canvas.itemconfigure(self.eatday_text_id, text="0")
                
                print(f"✅ โหลดค่า Config ใหม่: Sheet -> {config.SHEET_NAME}, Name -> {config.KNOWN_NAME}")

                # 3. อัปเดตค่าใน Object เดิม
                if hasattr(self, 'verifier'):
                    self.verifier.update_settings(
                        new_sheet_name=config.SHEET_NAME,
                        new_known_name=config.KNOWN_NAME,
                        new_image_path=config.KNOWN_IMAGE_PATH
                    )
                    self.verifier.scan_timeout = config.SCAN_TIMEOUT
                else:
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
                        serial_baudrate=config.SERIAL_BAUDRATE,
                        scan_timeout=config.SCAN_TIMEOUT
                    )
                
                print("✅ ระบบพร้อมใช้งานสำหรับผู้ป่วยคนใหม่แล้ว!")

            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการอัปเดต: {e}")
                import traceback
                traceback.print_exc()
            
            self.root.deiconify()
            self.root.attributes("-fullscreen", True)
            self.root.focus_force()
            self.is_scanning = False

        self.root.after(10, process_registration)

    def increment_eatday(self):
        self.eat_days += 1
        # อัปเดต UI
        if self.eatday_text_id:
            self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))
        
        # 🟢 [เพิ่ม] บันทึกลง config.py ทันที
        self.save_eat_days_to_config(self.eat_days)

    def save_eat_days_to_config(self, days):
        """ฟังก์ชันสำหรับบันทึกค่า EAT_DAYS ลงไฟล์ config.py"""
        try:
            config_path = "config.py"
            # อ่านข้อมูลเดิม
            with open(config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # เขียนข้อมูลใหม่
            with open(config_path, "w", encoding="utf-8") as f:
                found = False
                for line in lines:
                    if line.strip().startswith("EAT_DAYS ="):
                        f.write(f"EAT_DAYS = {days} # อัปเดตอัตโนมัติ\n")
                        found = True
                    else:
                        f.write(line)
                # ถ้ายังไม่มีตัวแปรนี้ ให้เพิ่มต่อท้าย
                if not found:
                    f.write(f"\nEAT_DAYS = {days} # อัปเดตอัตโนมัติ\n")
            
            print(f"💾 บันทึกจำนวนวัน ({days}) ลง config.py เรียบร้อย")
        except Exception as e:
            print(f"❌ ไม่สามารถบันทึก config.py: {e}")

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        if self.time_text_id:
            self.canvas.itemconfigure(self.time_text_id, text=now)
        self.root.after(1000, self.update_time)

    def check_alarm_time(self):
        now = datetime.now()
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
        # สั่ง Test ESP32 ด้วย
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