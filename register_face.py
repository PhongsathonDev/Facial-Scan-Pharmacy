import cv2
import face_recognition
import mediapipe as mp
import time
import os

def register_new_face(filename="patient.jpeg"):
    # --- ตั้งค่า MediaPipe ---
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    mp_draw = mp.solutions.drawing_utils

    # --- ตัวแปรระบบนับถอยหลัง ---
    is_counting_down = False 
    start_time = 0
    countdown_duration = 3.0 # เวลานับถอยหลังก่อนถ่าย (3 วินาที)

    # --- [ใหม่] ตัวแปรสำหรับหน่วงเวลาจับมือ 1.5 วินาที ---
    hand_hold_start_time = 0  # เวลาที่เริ่มตรวจเจอ 5 นิ้ว
    REQUIRED_HOLD_TIME = 1.5  # ต้องค้างไว้นานเท่าไหร่ (วินาที)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # ========================================================
    # ตั้งค่าหน้าจอ Full Screen
    # ========================================================
    window_name = "Register New Face"
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("--------------------------------------------------")
    print("📷 ระบบถ่ายภาพอัตโนมัติ (Auto Selfie)")
    print("--------------------------------------------------")
    print(f"  🖐️  ชู 5 นิ้ว ค้างไว้ {REQUIRED_HOLD_TIME} วินาที เพื่อเริ่ม")
    print("  ⬇️  เมื่อเลขนับถอยหลังขึ้น เอามือลงได้เลย")
    print("  👉 กด 'q' เพื่อยกเลิก")
    print("--------------------------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # กลับด้านภาพ (Mirror)
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        height, width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # --- ส่วนที่ 1: ตรวจจับมือ (ทำงานเฉพาะตอนที่ยังไม่เริ่มนับถอยหลังถ่ายรูป) ---
        if not is_counting_down:
            results = hands.process(rgb_frame)
            
            hand_detected_5_fingers = False
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    lm_list = hand_landmarks.landmark
                    fingers_up = []
                    
                    # Logic เช็คนิ้วชี้, กลาง, นาง, ก้อย
                    tips_ids = [8, 12, 16, 20]
                    pip_ids = [6, 10, 14, 18]

                    for tip, pip in zip(tips_ids, pip_ids):
                        if lm_list[tip].y < lm_list[pip].y:
                            fingers_up.append(True)
                        else:
                            fingers_up.append(False)
                    
                    # เช็คว่าชู 4 นิ้วหลักหรือไม่ (เป็นตัวแทนของการแบมือ)
                    if fingers_up.count(True) == 4:
                        hand_detected_5_fingers = True

            # --- [Logic ใหม่] การหน่วงเวลา 1.5 วินาที ---
            if hand_detected_5_fingers:
                # ถ้าเพิ่งเริ่มเจอ 5 นิ้ว ให้เริ่มจับเวลา
                if hand_hold_start_time == 0:
                    hand_hold_start_time = time.time()
                
                # คำนวณเวลาที่ค้างไว้
                hold_elapsed = time.time() - hand_hold_start_time
                
                # คำนวณ % เพื่อวาดแถบโหลด (สวยงาม)
                progress = min(hold_elapsed / REQUIRED_HOLD_TIME, 1.0)
                
                # วาด Progress Bar สีเขียวที่ด้านบน
                bar_width = int(400 * progress)
                cv2.rectangle(display_frame, (width//2 - 200, 100), 
                              (width//2 - 200 + bar_width, 130), (0, 255, 0), -1)
                cv2.rectangle(display_frame, (width//2 - 200, 100), 
                              (width//2 + 200, 130), (255, 255, 255), 2)
                cv2.putText(display_frame, f"Hold: {hold_elapsed:.1f}s", (width//2 - 60, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # ถ้าค้างไว้ครบเวลาที่กำหนด -> เริ่มนับถอยหลังจริง!
                if hold_elapsed >= REQUIRED_HOLD_TIME:
                    is_counting_down = True
                    start_time = time.time()
                    hand_hold_start_time = 0 # รีเซ็ต
                    print("🚀 ครบเวลา! เริ่มนับถอยหลังถ่ายภาพ...")

            else:
                # ถ้ามือหาย หรือไม่ได้ชู 5 นิ้ว ให้รีเซ็ตเวลาเป็น 0 ทันที
                hand_hold_start_time = 0
                
                # แสดงข้อความปกติ
                cv2.putText(display_frame, "Show 5 Fingers & Hold", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # --- ส่วนที่ 2: การทำงานตอนนับถอยหลัง (เหมือนเดิม) ---
        else:
            elapsed_time = time.time() - start_time
            time_left = countdown_duration - elapsed_time

            if time_left > 0:
                seconds_display = int(time_left) + 1
                text_size = cv2.getTextSize(str(seconds_display), cv2.FONT_HERSHEY_SIMPLEX, 10, 20)[0]
                text_x = (width - text_size[0]) // 2
                text_y = (height + text_size[1]) // 2
                
                cv2.putText(display_frame, str(seconds_display), (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 10, (0, 255, 255), 20)
                
                cv2.putText(display_frame, "Put hand down & Smile!", (width//2 - 200, height - 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            else:
                # ถ่ายรูป
                print("📸 แชะ!")
                face_locations = face_recognition.face_locations(rgb_frame)

                if len(face_locations) > 0:
                    cv2.imwrite(filename, frame)
                    print(f"✅ บันทึกเรียบร้อย: {filename}")

                    # Flash Effect
                    cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), -1)
                    cv2.imshow(window_name, display_frame)
                    cv2.waitKey(100)
                    
                    cv2.putText(display_frame, "SAVED!", (width//2 - 150, height//2), 
                                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                    cv2.imshow(window_name, display_frame)
                    cv2.waitKey(2000)
                    break 
                else:
                    print("⚠️ ไม่พบใบหน้า! ลองใหม่อีกครั้ง")
                    is_counting_down = False
                    
        # วาดกรอบไกด์ไลน์
        box_size = 400
        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        cv2.rectangle(display_frame, (x1, y1), (x1 + box_size, y1 + box_size), (161, 214, 162), 2)

        cv2.imshow(window_name, display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face()