import tkinter as tk
from PIL import Image, ImageTk

# ---------- ตั้งค่าหลัก ----------
root = tk.Tk()
root.title("แสดงรูปภาพเต็มจอ")

# ให้หน้าต่างเต็มจอ
root.attributes("-fullscreen", True)

# ---------- โหลดรูปภาพ ----------
IMAGE_PATH = "bg.png"
image = Image.open(IMAGE_PATH)

# ปรับขนาดรูปให้พอดีกับหน้าจออัตโนมัติ
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
image = image.resize((screen_width, screen_height))

photo = ImageTk.PhotoImage(image)

# ---------- แสดงรูป ----------
label = tk.Label(root, image=photo)
label.pack(fill="both", expand=True)
label.image = photo  # ป้องกัน garbage collection


# ---------- ฟังก์ชันปิดหน้าต่างเมื่อกด q ----------
def close_on_q(event):
    root.destroy()

# ผูกปุ่ม q ให้ปิดโปรแกรม
root.bind('q', close_on_q)

# ---------- เริ่มรัน ----------
root.mainloop()
