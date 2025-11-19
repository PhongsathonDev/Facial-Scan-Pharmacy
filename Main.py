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
        try:
            image = Image.open(self.IMAGE_PATH)
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            image = image.resize((screen_width, screen_height))
            self.photo = ImageTk.PhotoImage(image)

            self.canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        except Exception as e:
            print(f"Error loading background: {e}")
            # Fallback if bg.png is missing
            self.canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), bg="white")
            self.canvas.pack(fill="both", expand=True)

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
        self.TestAlert_button()  # ปุ่มทดสอบแจ้งเตือน (ขวา)
        self.Manual_button()     # <<< [ใหม่] ปุ่ม Manual (ซ้าย)

        # เริ่มตรวจเวลาแจ้งเตือนจริง
        self.check_alarm_time()

        # ปิดโปรแกรมเมื่อกด q
        self.root.bind('q', lambda event: self.root.destroy())

    # ---------- ปุ่ม "กินยา" (ตรงกลาง) ----------
    def Eat_button(self):
        btn = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline)
        self.canvas.tag_bind(btn, "<Button-1>", self.on_button_click)

    # ---------- ปุ่ม "ทดสอบแจ้งเตือน" (ขวา) ----------
    def TestAlert_button(self):
        test_btn = self.canvas.create_rectangle(900, 100, 1280, 250, outline="black", width=self.Outline)
        self.canvas.tag_bind(test_btn, "<Button-1>", self.test_send_alert)

    # ---------- [ใหม่] ปุ่ม "Manual" (ซ้าย) ----------
    def Manual_button(self):

        btn = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline)
        self.canvas.tag_bind(btn, "<Button-1>", self.show_manual)

    def show_manual(self, event):
        print("📖 กำลังเปิดคู่มือการใช้งาน...")
        
        top = tk.Toplevel(self.root)
        top.title("คู่มือการใช้งาน")
        top.attributes("-fullscreen", True)

        # เก็บสถานะภาษาปัจจุบัน (เริ่มที่ TH)
        # ใช้ list เพื่อให้อ้างอิงและแก้ไขได้ภายในฟังก์ชันย่อย (pass by reference)
        current_lang_state = ["TH"] 
        
        try:
            screen_width = top.winfo_screenwidth()
            screen_height = top.winfo_screenheight()
            
            # สร้าง Canvas ใหม่สำหรับหน้านี้
            canvas = tk.Canvas(top, width=screen_width, height=screen_height, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            # ตัวแปรเก็บ ID ของรูปภาพบน Canvas
            bg_image_id = None

            # --- ฟังก์ชันภายในสำหรับโหลด/เปลี่ยนรูป ---
            def update_manual_image():
                nonlocal bg_image_id
                lang = current_lang_state[0]
                filename = f"Manual{lang}.png" # จะเป็น ManualTH.png หรือ ManualEN.png
                
                try:
                    img = Image.open(filename)
                    img = img.resize((screen_width, screen_height))
                    photo = ImageTk.PhotoImage(img)
                    
                    if bg_image_id is None:
                        # สร้างรูปภาพครั้งแรก
                        bg_image_id = canvas.create_image(0, 0, image=photo, anchor="nw")
                        # ส่งรูปไปไว้ข้างหลังสุด เพื่อไม่ให้บังปุ่มที่เราจะวาด (ถึงแม้จะวาดทีหลังแต่กันเหนียว)
                        canvas.tag_lower(bg_image_id) 
                    else:
                        # อัปเดตรูปภาพเดิมถ้ามีอยู่แล้ว
                        canvas.itemconfig(bg_image_id, image=photo)
                    
                    # ต้องเก็บ reference รูปไว้เสมอ ไม่งั้นรูปจะหาย
                    canvas.image = photo 
                    print(f"✅ แสดงผลคู่มือ: {filename}")

                except Exception as e:
                    print(f"❌ ไม่สามารถโหลดรูป {filename} ได้: {e}")

            # 1. แสดงรูปครั้งแรก
            update_manual_image()

            # 2. สร้างปุ่ม "กลับ" (ตำแหน่งเดิม ซ้ายล่าง)
            close_btn = canvas.create_rectangle(0, 560, 150, 690, outline="black", width=self.Outline)
            canvas.tag_bind(close_btn, "<Button-1>", lambda e: top.destroy())
            
            # 3. สร้างปุ่ม "เปลี่ยนภาษา" (ตำแหน่งเดิม ขวาบน)
            languages_btn = canvas.create_rectangle(1050, 20, 1280, 90, outline="black", width=self.Outline)
            
            # ฟังก์ชันสลับภาษาเมื่อกดปุ่ม
            def toggle_language(e):
                if current_lang_state[0] == "TH":
                    current_lang_state[0] = "EN"
                else:
                    current_lang_state[0] = "TH"
                # โหลดรูปใหม่ตามสถานะ
                update_manual_image()

            # ผูกปุ่มกับฟังก์ชันสลับภาษา
            canvas.tag_bind(languages_btn, "<Button-1>", toggle_language)
            
            # Key bind สำหรับกด q เพื่อออก
            top.bind("q", lambda e: top.destroy())
            
        except Exception as e:
            print(f"❌ Error manual setup: {e}")
            err_label = tk.Label(top, text=f"Error: {e}", font=("Prompt", 20), fg="red")
            err_label.pack(expand=True)
            err_label.bind("<Button-1>", lambda e: top.destroy())

    # ---------- นับวันกินยา ----------
    def EatDay(self):
        self.eat_days = 0
        self.eatday_text_id = self.canvas.create_text(132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold"), fill="white")

    def increment_eatday(self):
        self.eat_days += 1
        self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))

    # ---------- วันที่ ----------
    def DateNow(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.canvas.create_text(280, 180, text=current_date, font=("Prompt", 28, "bold"), fill="white")

    # ---------- เวลาแจ้งเตือน (20:00) ----------
    def AlarmTime(self):
        alarm_str = f"{self.alarm_hour:02d}:{self.alarm_minute:02d}"
        self.canvas.create_text(1100, 180, text=alarm_str, font=("Prompt", 28, "bold"), fill="white")

    # ---------- เวลาแสดงปัจจุบัน ----------
    def Time(self):
        self.time_text_id = self.canvas.create_text(650, 425, text="", font=("Prompt", 50, "bold"), fill="white")
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
        try:
            response = requests.post("https://api.line.me/v2/bot/message/push",
                                     headers=headers, data=json.dumps(data), timeout=5)
            print("LINE ส่งแล้ว:", response.status_code)
        except Exception as e:
            print("Error sending LINE:", e)

    # ---------- ปุ่มทดสอบส่งแจ้งเตือน ----------
    def test_send_alert(self, event):
        print("🚀 ทดสอบส่ง LINE แจ้งเตือนทันที...")
        threading.Thread(target=self.send_line_alert, args=("โปรดรับประทานยา ในเวลานี้ครับ 20.00",)).start()
        
        print("➡️  ทดสอบส่งคำสั่ง 'a' ไปยัง ESP32...")
        self.verifier.send_command_to_esp32("a")

    # ---------- Event ปุ่มกินยา ----------
    def on_button_click(self, event):
        print("เริ่มสแกนใบหน้าเพื่อตรวจว่ากินยานะคะ...")
        self.root.update()
        
        # เรียก Face Verification
        verified = self.verifier.run()
        
        # เมื่อสแกนเสร็จ (หรือกด q) ให้กลับมาทำหน้าจอ Fullscreen ใหม่ (กันหน้าจอหลุด)
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