import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
from Facescan import FaceVerifier   # <<< ดึงคลาสจาก main.py

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("แสดงรูปภาพเต็มจอ")
        self.root.attributes("-fullscreen", True)

        self.Outline = 0  # ความหนาเส้นขอบปุ่ม

        # โหลดรูปภาพและปรับขนาดให้เต็มจอ
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

        # ----- สร้างอ็อบเจ็กต์ FaceVerifier ไว้ใช้ซ้ำ -----
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

        # วาด UI
        self.Eat_button()
        self.EatDay()
        self.DateNow()
        self.AlarmTime()
        self.Time()

        # ปิดโปรแกรมเมื่อกด q
        self.root.bind('q', lambda event: self.root.destroy())

    # ---------- ปุ่มกินยา ----------
    def Eat_button(self):
        # วาดสี่เหลี่ยมเป็นปุ่ม
        button_frame = self.canvas.create_rectangle(450, 540, 820, 670,outline="black", width=self.Outline)
        # ผูก event คลิก
        self.canvas.tag_bind(button_frame, "<Button-1>", self.on_button_click)

    # ---------- แสดงจำนวนวันที่กินยาแล้ว ----------
    def EatDay(self):
        self.eat_days = 0
        # เก็บ id ไว้เพื่ออัปเดตข้อความทีหลัง
        self.eatday_text_id = self.canvas.create_text(
            132, 325, text=str(self.eat_days), font=("Prompt", 32, "bold")
        )

    def increment_eatday(self):
        self.eat_days += 1
        self.canvas.itemconfigure(self.eatday_text_id, text=str(self.eat_days))

    # ---------- วันที่ปัจจุบัน ----------
    def DateNow(self):
        current_date = datetime.now().strftime("%d/%m/%Y")
        self.canvas.create_text(280, 180, text=current_date,
                                font=("Prompt", 28, "bold"))

    # ---------- เวลาแจ้งเตือน/เวลาแสดงบนหน้าจอ ----------
    def AlarmTime(self):
        current_time = datetime.now().strftime("%H:%M")
        self.canvas.create_text(1120, 180, text=current_time,font=("Prompt", 28, "bold"))
        
    def Time(self):
        time_str = datetime.now().strftime("%H:%M:%S")
        
        self.canvas.create_text(650, 425, text=time_str, font=("Prompt", 36, "bold"))

    # ---------- Event ตอนกดปุ่มกินยา ----------
    def on_button_click(self, event):
        print("เริ่มสแกนใบหน้าเพื่อตรวจว่ากินยานะคะ...")

        # ซ่อนหน้า UI ชั่วคราว (จะเหลือแต่หน้าต่างกล้อง)
        self.root.withdraw()
        self.root.update()

        # เรียกตัวสแกนหน้า (บล็อกจนกว่าจะสแกนเสร็จ / กดยกเลิก)
        verified = self.verifier.run()

        # กลับมาหน้า UI
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)  # เผื่อหลุด fullscreen
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
