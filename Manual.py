import tkinter as tk
from PIL import Image, ImageTk

class ManualUI:
    def __init__(self, canvas, screen_width, screen_height, on_back_callback):
        """
        คลาสสำหรับจัดการหน้าคู่มือการใช้งาน
        :param canvas: Canvas หลักจาก Main.py
        :param screen_width: ความกว้างหน้าจอ
        :param screen_height: ความสูงหน้าจอ
        :param on_back_callback: ฟังก์ชันที่จะเรียกเมื่อกดปุ่มย้อนกลับ
        """
        self.canvas = canvas
        self.width = screen_width
        self.height = screen_height
        self.on_back = on_back_callback
        
        self.current_lang = "TH"
        self.assets = {}
        self.ui_items = [] # เก็บ ID ของ widget ทุกตัวในหน้านี้
        
        # โหลดรูปภาพและสร้าง UI เตรียมไว้ (แต่ยังซ่อนอยู่)
        self.load_assets()
        self.create_widgets()

    def load_assets(self):
        """โหลดรูปภาพคู่มือทั้ง 2 ภาษา"""
        files = {
            "TH": "ManualTH.png",
            "EN": "ManualEN.png"
        }
        for lang, path in files.items():
            try:
                img = Image.open(path)
                img = img.resize((self.width, self.height))
                self.assets[lang] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                # สร้างภาพสีเทาสำรองกรณีหาไฟล์ไม่เจอ
                img = Image.new('RGB', (self.width, self.height), color=(150, 150, 150))
                self.assets[lang] = ImageTk.PhotoImage(img)

    def create_widgets(self):
        """สร้างองค์ประกอบ UI (Background และปุ่ม) แต่ตั้งค่าเป็น hidden"""
        
        # 1. Background Image (จะซ้อนทับ Main BG)
        self.bg_item = self.canvas.create_image(0, 0, image=self.assets["TH"], anchor="nw", state='hidden')
        self.ui_items.append(self.bg_item)

        Outline = 0  # ความหนาขอบปุ่ม (0=มองไม่เห็น)

        # 2. ปุ่มย้อนกลับ (ตำแหน่งซ้ายล่าง)
        self.btn_back = self.canvas.create_rectangle(0, 560, 150, 690, outline="black", width=Outline, state='hidden', tags="manual_btn_back")
        self.canvas.tag_bind(self.btn_back, "<Button-1>", self.go_back)
        self.ui_items.append(self.btn_back)

        # 3. ปุ่มเปลี่ยนภาษา (ตำแหน่งขวาบน)
        self.btn_lang = self.canvas.create_rectangle(1050, 20, 1280, 90, outline="black", width=Outline, state='hidden', tags="manual_btn_lang")
        self.canvas.tag_bind(self.btn_lang, "<Button-1>", self.toggle_language)
        self.ui_items.append(self.btn_lang)

    def show(self):
        """แสดงหน้าคู่มือ"""
        # อัปเดตภาพพื้นหลัง
        self.canvas.itemconfig(self.bg_item, image=self.assets[self.current_lang])
        
        # แสดง item ทุกตัว
        for item in self.ui_items:
            self.canvas.itemconfigure(item, state='normal')
        
        # ดัน Layer มาข้างหน้าสุด เพื่อให้ทับหน้า Main
        self.canvas.tag_raise(self.bg_item)
        self.canvas.tag_raise(self.btn_back)
        self.canvas.tag_raise(self.btn_lang)

    def hide(self):
        """ซ่อนหน้าคู่มือ"""
        for item in self.ui_items:
            self.canvas.itemconfigure(item, state='hidden')

    def toggle_language(self, event=None):
        """สลับภาษา TH/EN"""
        self.current_lang = "EN" if self.current_lang == "TH" else "TH"
        print(f"🌐 Manual Language: {self.current_lang}")
        self.canvas.itemconfig(self.bg_item, image=self.assets[self.current_lang])

    def go_back(self, event=None):
        """กดปุ่มย้อนกลับ -> เรียก callback ไปที่ Main"""
        self.hide()
        if self.on_back:
            self.on_back()