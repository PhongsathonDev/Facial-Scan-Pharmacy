import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
import requests, json, threading
from Facescan import FaceVerifier
from register_face import register_new_face 

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tuberbox System")
        
        # ตั้งค่า Fullscreen
        self.root.attributes("-fullscreen", True)
        
        # ขนาดหน้าจอ
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()

        self.Outline = 0  # ความหนาขอบปุ่ม (0 = มองไม่เห็น)

        # ============================
        # 1. โหลดรูปภาพทั้งหมดเตรียมไว้
        # ============================
        self.assets = {}
        self.load_assets()

        # ============================
        # 2. สร้าง Canvas และ Background
        # ============================
        self.canvas = tk.Canvas(root, width=self.screen_width, height=self.screen_height, highlightthickness=0, bg="white")
        self.canvas.pack(fill="both", expand=True)
        
        # สร้าง Background เริ่มต้น (Main)
        self.bg_item = self.canvas.create_image(0, 0, image=self.assets['bg'], anchor="nw")

        # ============================
        # 3. จัดการกลุ่ม UI (Main vs Manual)
        # ============================
        self.main_ui_items = []   # เก็บ ID ของปุ่มและข้อความหน้าหลัก
        self.manual_ui_items = [] # เก็บ ID ของปุ่มหน้าคู่มือ

        # ============================
        # 4. ตัวแปรระบบ
        # ============================
        self.eat_days = 0
        self.eatday_text_id = None
        self.time_text_id = None
        self.manual_lang = "TH"  # ภาษาเริ่มต้นของคู่มือ
        self.is_scanning = False # ป้องกันการกดปุ่มรัวๆ

        # ตั้งค่า LINE
        self.CHANNEL_ACCESS_TOKEN = "90PR4QmENVZ8HgX6H9Ee7lrByaFndu4+VBjrC3iUJN0kmXQ7zma/srxGsx4gCQ3bdwPaqS38zcVjtuANVYZoqAgey4AhockHFJ+OK/3K6aGnEa11RuGpM51rDltAT8lXe69f6wbkatpra28B7WLdFAdB04t89/1O/w1cDnyilFU="
        self.USER_ID = "Uaa30a62f505cfb7a3e546ed644e4755f"
        
        # ตั้งเวลาแจ้งเตือน
        self.alarm_hour = 20
        self.alarm_minute = 0
        
        # ตั้งค่า Face Scan
        WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"
        self.verifier = FaceVerifier(
            known_image_path="patient.jpeg",
            known_name="patient",
            tolerance=0.5,
            hold_seconds=2.0,
            camera_index=0,
            webapp_url=WEBAPP_URL,
            sheet_name="Patient",
            face_id="patient",
            serial_port="/dev/ttyUSB0",
            serial_baudrate=115200
        )

        # ============================
        # 5. สร้าง UI ทั้งหมด (Main และ Manual)
        # ============================
        self.build_main_ui()
        self.build_manual_ui()

        # เริ่มการทำงาน Loop
        self.update_time()
        self.check_alarm_time()
        
        # กด q เพื่อปิดโปรแกรมฉุกเฉิน
        self.root.bind('q', lambda event: self.root.destroy())

    def load_assets(self):
        """โหลดและย่อขยายรูปภาพทั้งหมดรอไว้ใน Memory"""
        files = {
            "bg": "bg.png",
            "manual_th": "ManualTH.png",
            "manual_en": "ManualEN.png"
        }
        for key, path in files.items():
            try:
                img = Image.open(path)
                img = img.resize((self.screen_width, self.screen_height))
                self.assets[key] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                # สร้างภาพสีเทาสำรองกรณีหาไฟล์ไม่เจอ
                img = Image.new('RGB', (self.screen_width, self.screen_height), color=(200, 200, 200))
                self.assets[key] = ImageTk.PhotoImage(img)

    def build_main_ui(self):
        """สร้างองค์ประกอบของหน้าหลัก"""
        # --- ข้อความ (Text) ---
        # 1. จำนวนวันที่กินยา
        self.eatday_text_id = self.canvas.create_text(132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold"), fill="white")
        self.main_ui_items.append(self.eatday_text_id)

        # 2. วันที่ปัจจุบัน
        current_date = datetime.now().strftime("%d/%m/%Y")
        date_id = self.canvas.create_text(280, 180, text=current_date, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(date_id)

        # 3. เวลาแจ้งเตือน
        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        alarm_id = self.canvas.create_text(1100, 180, text=alarm_str, font=("Prompt", 28, "bold"), fill="white")
        self.main_ui_items.append(alarm_id)

        # 4. เวลาปัจจุบัน (Dynamic)
        self.time_text_id = self.canvas.create_text(650, 425, text="", font=("Prompt", 50, "bold"), fill="white")
        self.main_ui_items.append(self.time_text_id)

        # --- ปุ่ม (Buttons) ---
        # 1. ปุ่มกินยา (ตรงกลาง)
        btn_eat = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline, tags="btn_eat")
        self.canvas.tag_bind(btn_eat, "<Button-1>", self.on_button_click)
        self.main_ui_items.append(btn_eat)

        # 2. ปุ่มทดสอบ (ขวาบน)
        btn_test = self.canvas.create_rectangle(900, 100, 1280, 250, outline="black", width=self.Outline, tags="btn_test")
        self.canvas.tag_bind(btn_test, "<Button-1>", self.test_send_alert)
        self.main_ui_items.append(btn_test)

        # 3. ปุ่มเปิดคู่มือ (ซ้ายล่าง) -> กดแล้วไปโหมด Manual
        btn_manual = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline, tags="btn_manual")
        self.canvas.tag_bind(btn_manual, "<Button-1>", self.switch_to_manual_mode)
        self.main_ui_items.append(btn_manual)

        # [2] สร้างปุ่มใหม่: ลงทะเบียนใบหน้า (มุมขวาล่าง)
        # สร้างกรอบปุ่ม
        btn_register = self.canvas.create_rectangle(950, 550, 1280, 700, outline="black", width=self.Outline, tags="btn_register")
        self.canvas.tag_bind(btn_register, "<Button-1>", self.on_register_click)
        self.main_ui_items.append(btn_register)

    def build_manual_ui(self):
        """สร้างองค์ประกอบของหน้าคู่มือ (ซ่อนไว้ก่อน)"""
        # 1. ปุ่มย้อนกลับ (ซ้ายล่าง - ตำแหน่งเดียวกับปุ่มเปิดคู่มือ)
        btn_back = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline, state='hidden')
        self.canvas.tag_bind(btn_back, "<Button-1>", self.switch_to_main_mode)
        self.manual_ui_items.append(btn_back)

        # 2. ปุ่มเปลี่ยนภาษา (ขวาบน)
        btn_lang = self.canvas.create_rectangle(1050, 20, 1280, 90, outline="black", width=self.Outline, state='hidden')
        self.canvas.tag_bind(btn_lang, "<Button-1>", self.toggle_manual_language)
        self.manual_ui_items.append(btn_lang)

    # ============================
    # ฟังก์ชันสำหรับปุ่มลงทะเบียนใบหน้า
    # ============================
    def on_register_click(self, event):
        if self.is_scanning: return
        self.is_scanning = True
        
        print("⚙️ กำลังเข้าสู่โหมดลงทะเบียนใบหน้า...")
        
        # 1. ซ่อนหน้าต่างหลักชั่วคราว เพื่อให้หน้ากล้อง OpenCV ขึ้นมาแทน
        
        # self.root.withdraw()
        
        try:
            # 2. เรียกฟังก์ชันจากไฟล์ register_face.py
            self.root.after(10, register_new_face)
            
            # 3. สั่งให้ระบบ FaceVerifier โหลดไฟล์ภาพใหม่ทันที (ไม่ต้องปิดเปิดโปรแกรมใหม่)
            print("🔄 กำลังอัปเดตข้อมูลใบหน้าในระบบ...")
            self.verifier.known_face_encodings, self.verifier.known_face_names = self.verifier._load_known_faces()
            print("✅ อัปเดตข้อมูลใบหน้าเสร็จสิ้น")
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการลงทะเบียน: {e}")
        
        # 4. เรียกหน้าต่างหลักกลับมา
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.focus_force() # ดึงโฟกัสกลับมาที่โปรแกรม
        self.is_scanning = False

    # ============================
    # 6. Logic การสลับหน้าจอ (หัวใจสำคัญ)
    # ============================
    def switch_to_manual_mode(self, event):
        print("📖 เข้าสู่โหมดคู่มือ")
        self.update_manual_bg()
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='hidden')
        for item in self.manual_ui_items:
            self.canvas.itemconfigure(item, state='normal')

    def switch_to_main_mode(self, event):
        print("🏠 กลับสู่หน้าหลัก")
        self.canvas.itemconfig(self.bg_item, image=self.assets['bg'])
        for item in self.manual_ui_items:
            self.canvas.itemconfigure(item, state='hidden')
        for item in self.main_ui_items:
            self.canvas.itemconfigure(item, state='normal')

    def toggle_manual_language(self, event):
        self.manual_lang = "EN" if self.manual_lang == "TH" else "TH"
        print(f"🌐 เปลี่ยนภาษาเป็น: {self.manual_lang}")
        self.update_manual_bg()

    def update_manual_bg(self):
        if self.manual_lang == "TH":
            self.canvas.itemconfig(self.bg_item, image=self.assets['manual_th'])
        else:
            self.canvas.itemconfig(self.bg_item, image=self.assets['manual_en'])

    # ============================
    # 7. Logic อื่นๆ ของระบบ
    # ============================
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
        if now.hour == self.alarm_hour and now.minute == self.alarm_minute and now.second == 0:
             threading.Thread(target=self.send_line_alert, args=("⏰ ถึงเวลาทานยาแล้วนะคะ อย่าลืมกดปุ่มและสแกนหน้านะคะ 💊",)).start()
        self.root.after(1000, self.check_alarm_time)

    def send_line_alert(self, message_text):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.CHANNEL_ACCESS_TOKEN}"
        }
        data = {
            "to": self.USER_ID,
            "messages": [{"type": "text", "text": message_text}]
        }
        try:
            requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(data), timeout=5)
            print("LINE sent.")
        except Exception as e:
            print("Error sending LINE:", e)

    def test_send_alert(self, event):
        print("🚀 ทดสอบแจ้งเตือน...")
        threading.Thread(target=self.send_line_alert, args=("โปรดรับประทานยา ในเวลานี้ครับ 20.00",)).start()
        self.verifier.send_command_to_esp32("a")

    def on_button_click(self, event):
        if self.is_scanning:
            print("⏳ กำลังสแกนอยู่ กรุณารอสักครู่...")
            return

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
        else:
            print("❌ ไม่ผ่าน")
        
        self.root.after(1000, lambda: setattr(self, 'is_scanning', False))

if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenImageApp(root)
    root.mainloop()