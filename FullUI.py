import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime

class FullScreenImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("แสดงรูปภาพเต็มจอ")
        self.root.attributes("-fullscreen", True)

        self.Outline = 4  # ความหนาเส้นขอบปุ่ม

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

        # เพิ่มปุ่ม (เป็นสี่เหลี่ยมคลิกได้)
        self.create_button()
        self.EatDay()
        self.DateNow()
        self.AlarmTime()
        self.Time()

        # ผูกปุ่ม q ให้ปิดโปรแกรม
        self.root.bind('q', lambda event: self.root.destroy())

    def create_button(self):
        # วาดสี่เหลี่ยมเป็นปุ่ม
        button_frame = self.canvas.create_rectangle(450, 540, 820, 670, outline="black", width=self.Outline)
        self.canvas.tag_bind(button_frame, "<Button-1>", self.on_button_click)
    
    def EatDay(self):
        self.canvas.create_text(132, 325, text="3", font=("Prompt", 32, "bold"))
        
    def Time(self):
        time_str = datetime.now().strftime("%H:%M:%S")
        
        self.canvas.create_text(650, 425, text=time_str, font=("Prompt", 36, "bold"))
        
    def DateNow(self):
        current_date = datetime.now().strftime("%d/%m/%Y")

        self.canvas.create_text(280, 180, text=current_date,font=("Prompt", 28, "bold"))
        
    def AlarmTime(self):
        alarm = "18:30"

        self.canvas.create_text(1120, 180, text=alarm,font=("Prompt", 28, "bold"))

    def on_button_click(self, event):
        print("คลิกปุ่มแล้วนะคะ 💕")
        # จะให้ทำอะไรเพิ่มเติมก็เขียนต่อในนี้ได้ เช่น:
        # self.set_floor_and_go(3, "Page 3")

# ---------- เริ่มโปรแกรม ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = FullScreenImageApp(root)
    root.mainloop()
