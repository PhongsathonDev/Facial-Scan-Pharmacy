import tkinter as tk
from PIL import Image, ImageTk

# ---------- ตั้งค่าหลัก ----------
root = tk.Tk()
root.title("แสดงรูปภาพด้วย Tkinter")

# ---------- โหลดรูปภาพ ----------
# แก้ชื่อไฟล์ให้ตรงกับรูปของพี่ เช่น "cat.png", "photo.jpg"
IMAGE_PATH = "bg.png"

# เปิดรูปด้วย Pillow
image = Image.open(IMAGE_PATH)

# ถ้าอยากย่อขนาดรูปให้พอดีหน้าจอ ก็ใช้ resize ได้ (ไม่บังคับ)
# image = image.resize((600, 400))

# แปลงให้ Tkinter ใช้ได้
photo = ImageTk.PhotoImage(image)

# ---------- เอารูปไปใส่ใน Label ----------
label = tk.Label(root, image=photo)
label.pack(padx=10, pady=10)

# ต้องเก็บ reference ไว้ ไม่งั้นรูปจะหาย
label.image = photo

# ---------- เริ่มรันหน้าต่าง ----------
root.mainloop()
