import cv2
import face_recognition
import mediapipe as mp
import time
import os
import re

# ฟังก์ชันสำหรับอัปเดตไฟล์ config.py (คงเดิม)
def update_config(sheet_number):
    config_path = "config.py"
    new_sheet_name = f"Patient{sheet_number}"
    new_known_name = f"Patient{sheet_number}"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        with open(config_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip().startswith("SHEET_NAME ="):
                    f.write(f'SHEET_NAME = "{new_sheet_name}"      # อัปเดตอัตโนมัติจากหน้าลงทะเบียน\n')
                elif line.strip().startswith("KNOWN_NAME ="):
                    f.write(f'KNOWN_NAME = "{new_known_name}"      # อัปเดตอัตโนมัติจากหน้าลงทะเบียน\n')
                else:
                    f.write(line)
        print(f"✅ อัปเดต config.py เรียบร้อย: Sheet -> {new_sheet_name}")
        return new_sheet_name
    except Exception as e:
        print(f"❌ ไม่สามารถแก้ไข config.py: {e}")
        return None

# ==========================================
# 🎮 ส่วนจัดการ Numpad แบบใหม่ (รองรับหลายหลัก)
# ==========================================
selected_number = None
current_input_str = ""  # ตัวแปรเก็บข้อความที่พิมพ์

# กำหนดตำแหน่งปุ่ม (Layout)
# โครงสร้าง: [label, value, row, col] (row 0-3, col 0-2)
BUTTONS_LAYOUT = [
    ['1', '1', 0, 0], ['2', '2', 0, 1], ['3', '3', 0, 2],
    ['4', '4', 1, 0], ['5', '5', 1, 1], ['6', '6', 1, 2],
    ['7', '7', 2, 0], ['8', '8', 2, 1], ['9', '9', 2, 2],
    ['DEL', 'del', 3, 0], ['0', '0', 3, 1], ['OK', 'ok', 3, 2]
]

# ตั้งค่าขนาดและตำแหน่งเริ่มต้นของ Numpad
BTN_SIZE = 100
GAP = 20
START_X = 440
START_Y = 250  # ขยับลงมาหน่อยเพื่อให้มีที่แสดงผลด้านบน

def mouse_callback(event, x, y, flags, param):
    global selected_number, current_input_str
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # วนลูปเช็คว่ากดโดนปุ่มไหน
        for btn in BUTTONS_LAYOUT:
            label, val, r, c = btn
            bx = START_X + (c * (BTN_SIZE + GAP))
            by = START_Y + (r * (BTN_SIZE + GAP))
            
            # เช็คขอบเขตการกด
            if bx < x < bx + BTN_SIZE and by < y < by + BTN_SIZE:
                if val == 'del':
                    # ลบตัวอักษรตัวสุดท้าย
                    current_input_str = current_input_str[:-1]
                elif val == 'ok':
                    # กดยืนยัน (ต้องมีตัวเลขอย่างน้อย 1 ตัว)
                    if len(current_input_str) > 0:
                        selected_number = int(current_input_str)
                else:
                    # กดตัวเลข (จำกัดไม่เกิน 5 หลัก เพื่อความสวยงาม)
                    if len(current_input_str) < 5:
                        current_input_str += val
                return

def draw_numpad(frame):
    height, width, _ = frame.shape
    overlay = frame.copy()
    
    # 1. พื้นหลังจางๆ สีดำ
    cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # 2. หัวข้อ
    cv2.putText(frame, "Enter Patient ID", (width//2 - 200, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    # 3. ช่องแสดงผลตัวเลข (Display Box)
    display_box_y = START_Y - 120
    cv2.rectangle(frame, (START_X, display_box_y), 
                  (START_X + (3*BTN_SIZE) + (2*GAP), display_box_y + 100), (255, 255, 255), -1)
    
    # แสดงตัวเลขที่พิมพ์
    display_text = current_input_str if current_input_str else "_"
    text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 4)[0]
    
    # จัดกึ่งกลางกล่องข้อความ
    center_x_box = START_X + ((3*BTN_SIZE) + (2*GAP)) // 2
    text_x = center_x_box - (text_size[0] // 2)
    text_y = display_box_y + 70
    
    # สีตัวหนังสือ (ถ้ายังไม่พิมพ์เป็นสีเทา, พิมพ์แล้วเป็นสีดำ)
    txt_color = (0, 0, 0) if current_input_str else (200, 200, 200)
    cv2.putText(frame, display_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 2, txt_color, 4)

    # 4. วาดปุ่มกด
    for btn in BUTTONS_LAYOUT:
        label, val, r, c = btn
        bx = START_X + (c * (BTN_SIZE + GAP))
        by = START_Y + (r * (BTN_SIZE + GAP))
        
        # กำหนดสีปุ่ม
        if val == 'ok':
            color = (100, 200, 100) # สีเขียว
        elif val == 'del':
            color = (100, 100, 200) # สีแดงอ่อน/ส้ม
        else:
            color = (161, 214, 162) # สีธีมเดิม
            
        cv2.rectangle(frame, (bx, by), (bx + BTN_SIZE, by + BTN_SIZE), color, -1)
        cv2.rectangle(frame, (bx, by), (bx + BTN_SIZE, by + BTN_SIZE), (255, 255, 255), 2)
        
        # วาดตัวหนังสือบนปุ่ม
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        tx = bx + (BTN_SIZE - label_size[0]) // 2
        ty = by + (BTN_SIZE + label_size[1]) // 2
        cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

    # คำแนะนำด้านล่าง
    cv2.putText(frame, "Type ID and press OK to save", (width//2 - 280, height - 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

def register_new_face(filename="patient.jpeg"):
    # --- ตั้งค่า MediaPipe ---
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # --- ตัวแปรระบบ ---
    is_counting_down = False 
    start_time = 0
    countdown_duration = 3.0 
    hand_hold_start_time = 0  
    REQUIRED_HOLD_TIME = 1.5  

    cap = cv2.VideoCapture(0)
    # ปรับความละเอียด
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    window_name = "Register New Face"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # ตั้งค่า Mouse Callback
    cv2.setMouseCallback(window_name, mouse_callback)

    print("--------------------------------------------------")
    print("📷 ระบบถ่ายภาพอัตโนมัติ (Auto Selfie)")
    print("--------------------------------------------------")

    face_saved = False 

    # รีเซ็ตค่า Input ทุกครั้งที่เริ่มฟังก์ชันใหม่
    global selected_number, current_input_str
    selected_number = None
    current_input_str = ""

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1) # Mirror
        
        # ==========================================
        # PHASE 1: ถ่ายรูป (Code เดิม)
        # ==========================================
        if not face_saved:
            display_frame = frame.copy()
            height, width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if not is_counting_down:
                results = hands.process(rgb_frame)
                hand_detected_5_fingers = False
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        lm_list = hand_landmarks.landmark
                        fingers_up = []
                        tips_ids = [8, 12, 16, 20]
                        pip_ids = [6, 10, 14, 18]
                        for tip, pip in zip(tips_ids, pip_ids):
                            if lm_list[tip].y < lm_list[pip].y: fingers_up.append(True)
                            else: fingers_up.append(False)
                        if fingers_up.count(True) == 4: hand_detected_5_fingers = True

                if hand_detected_5_fingers:
                    if hand_hold_start_time == 0: hand_hold_start_time = time.time()
                    hold_elapsed = time.time() - hand_hold_start_time
                    progress = min(hold_elapsed / REQUIRED_HOLD_TIME, 1.0)
                    bar_width = int(400 * progress)
                    cv2.rectangle(display_frame, (width//2 - 200, 100), (width//2 - 200 + bar_width, 130), (0, 255, 0), -1)
                    cv2.rectangle(display_frame, (width//2 - 200, 100), (width//2 + 200, 130), (255, 255, 255), 2)
                    cv2.putText(display_frame, f"Hold: {hold_elapsed:.1f}s", (width//2 - 60, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    if hold_elapsed >= REQUIRED_HOLD_TIME:
                        is_counting_down = True
                        start_time = time.time()
                        hand_hold_start_time = 0
                else:
                    hand_hold_start_time = 0
                    cv2.putText(display_frame, "Show 5 Fingers & Hold", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            else:
                elapsed_time = time.time() - start_time
                time_left = countdown_duration - elapsed_time
                if time_left > 0:
                    seconds_display = int(time_left) + 1
                    text_size = cv2.getTextSize(str(seconds_display), cv2.FONT_HERSHEY_SIMPLEX, 10, 20)[0]
                    cv2.putText(display_frame, str(seconds_display), ((width - text_size[0]) // 2, (height + text_size[1]) // 2), cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 255), 20)
                else:
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if len(face_locations) > 0:
                        cv2.imwrite(filename, frame)
                        print(f"✅ บันทึกรูปภาพเรียบร้อย: {filename}")
                        cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), -1)
                        cv2.imshow(window_name, display_frame)
                        cv2.waitKey(100)
                        face_saved = True 
                    else:
                        print("⚠️ ไม่พบใบหน้า! ลองใหม่อีกครั้ง")
                        is_counting_down = False
            
            if not face_saved:
                box_size = 400
                x1, y1 = (width - box_size) // 2, (height - box_size) // 2
                cv2.rectangle(display_frame, (x1, y1), (x1 + box_size, y1 + box_size), (161, 214, 162), 2)
                cv2.imshow(window_name, display_frame)

        # ==========================================
        # PHASE 2: เลือก ID ผู้ป่วย (Input Numpad)
        # ==========================================
        else:
            # วาดหน้า Numpad
            draw_numpad(frame)
            cv2.imshow(window_name, frame)
            
            # ตรวจสอบว่ามีการกด OK หรือยัง
            if selected_number is not None:
                print(f"🔢 Selected Patient ID: {selected_number}")
                
                # แสดงข้อความยืนยัน
                cv2.putText(frame, f"Saving to Patient{selected_number}...", (200, 600), 
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                cv2.imshow(window_name, frame)
                cv2.waitKey(500)
                
                # อัปเดตไฟล์ Config
                update_config(selected_number)
                
                cv2.waitKey(1000)
                break 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    selected_number = None

if __name__ == "__main__":
    register_new_face()