import cv2
import face_recognition
import os
import time
import numpy as np

def register_new_face(filename="patient.jpeg"):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("--------------------------------------------------")
    print("📷 ระบบลงทะเบียนใบหน้า (โหมดเบาเครื่อง)")
    print("--------------------------------------------------")
    print("  👉 พยักหน้า เพื่อเริ่มนับถอยหลัง")
    print("  👉 หรือกด 's' เพื่อบันทึกทันที")

    # ตัวแปรสำหรับการตรวจจับ (Logic)
    nose_y_history = []
    nod_state = "WAITING" 
    avg_nose_y = 0
    
    # ตัวแปรนับถอยหลัง
    is_counting_down = False
    countdown_start_time = 0
    countdown_duration = 3

    # *** ตัวแปรสำหรับลดภาระเครื่อง (Optimization) ***
    frame_count = 0
    process_every_n_frames = 4 # ตรวจจับจมูกทุกๆ 4 เฟรม (ปรับเลขนี้ได้ ถ้ายังแลคให้เพิ่มเป็น 5-6)
    last_nose_y = 0 # จำค่าเดิมไว้ใช้ในเฟรมที่ข้ามไป

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ ไม่สามารถเปิดกล้องได้")
            break

        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        height, width, _ = frame.shape
        
        # นับจำนวนเฟรม
        frame_count += 1

        # ---------------------------------------------------------
        # 1. ส่วนการตรวจจับพยักหน้า (ทำงานเฉพาะรอบที่กำหนด)
        # ---------------------------------------------------------
        if not is_counting_down:
            # ทำงานเฉพาะเมื่อหารลงตัว (เช่น เฟรมที่ 0, 4, 8...) เพื่อลดกระตุก
            if frame_count % process_every_n_frames == 0:
                
                # ย่อภาพเล็กมากเพื่อให้ไวสุดๆ (0.2)
                small_frame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame)

                if face_landmarks_list:
                    nose_tip = face_landmarks_list[0]['nose_tip'][0]
                    nose_y = nose_tip[1]
                    last_nose_y = nose_y # อัปเดตค่าล่าสุด
                else:
                    nose_y = last_nose_y # ถ้าหาไม่เจอ ให้ใช้ค่าเดิมไปก่อน
            else:
                # เฟรมที่ข้ามไป ให้ใช้ค่าเดิม (ไม่ต้องคำนวณใหม่)
                nose_y = last_nose_y

            # --- Logic พยักหน้า (ใช้ค่า nose_y ที่ได้) ---
            if nose_y != 0: # ป้องกันค่า 0 ตอนเริ่มโปรแกรม
                if len(nose_y_history) < 10:
                    nose_y_history.append(nose_y)
                    avg_nose_y = sum(nose_y_history) / len(nose_y_history)
                else:
                    nose_y_history.pop(0)
                    nose_y_history.append(nose_y)
                    avg_nose_y = sum(nose_y_history) / len(nose_y_history)

                # ความไว (Sensitivity)
                sensitivity = 2 
                
                if nod_state == "WAITING":
                    if nose_y > avg_nose_y + sensitivity: # ก้ม
                        nod_state = "DOWN"
                elif nod_state == "DOWN":
                    if nose_y < avg_nose_y - sensitivity: # เงย
                        print("💡 พยักหน้าสำเร็จ! (Nod Detected)")
                        is_counting_down = True
                        countdown_start_time = time.time()
                        nod_state = "WAITING"

        # ---------------------------------------------------------
        # 2. ส่วนแสดงผลกราฟิก (วาดทุกเฟรมเพื่อให้ภาพลื่น)
        # ---------------------------------------------------------
        box_size = 400
        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size
        
        color = (161, 214, 162)

        if is_counting_down:
            elapsed_time = time.time() - countdown_start_time
            time_left = countdown_duration - elapsed_time
            
            if time_left > 0:
                color = (0, 165, 255)
                # วาดเลขตัวใหญ่
                cv2.putText(display_frame, str(int(time_left) + 1), 
                           (width//2 - 30, height//2 + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
                cv2.putText(display_frame, "Smile!", (width//2 - 80, y1 - 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            else:
                key = ord('s') 
                is_counting_down = False 

        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
        if not is_counting_down:
             cv2.putText(display_frame, "Nod to Capture", (x1 + 80, y1 - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Register New Face", display_frame)

        # ---------------------------------------------------------
        # 3. ควบคุมปุ่มกด
        # ---------------------------------------------------------
        if 'key' not in locals():
            key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            # ตอนบันทึก ค่อยเรียก face_recognition แบบเต็มสตรีม (ยอมแลคแป๊บนึง)
            print("⏳ Saving...")
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            if len(face_locations) > 0:
                cv2.imwrite(filename, frame)
                print(f"✅ Saved: {filename}")
                
                cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), 10)
                cv2.putText(display_frame, "SAVED!", (width//2 - 150, height//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                cv2.imshow("Register New Face", display_frame)
                cv2.waitKey(1500)
                break
            else:
                print("⚠️ No face found")
                is_counting_down = False 

        elif key == ord('q'):
            break
        
        key = -1 

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face()