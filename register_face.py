import cv2
import face_recognition
import os
import time
import numpy as np

def register_new_face(filename="patient.jpeg"):
    # เปิดกล้อง
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("--------------------------------------------------")
    print("📷 ระบบลงทะเบียนใบหน้า (Hand-free Mode)")
    print("--------------------------------------------------")
    print("  👉 พยักหน้า 1 ครั้ง เพื่อเริ่มนับถอยหลัง")
    print("  👉 หรือกด 's' เพื่อบันทึกทันที")
    print("  👉 กด 'q' เพื่อยกเลิก")
    print("--------------------------------------------------")

    # ตัวแปรสำหรับการตรวจจับการพยักหน้า
    nose_y_history = []
    nod_state = "WAITING" # WAITING -> DOWN -> UP (Trigger)
    nod_threshold = 15    # ความไวในการพยักหน้า (ค่ายิ่งน้อยยิ่งไว)
    
    # ตัวแปรสำหรับการนับถอยหลัง
    is_counting_down = False
    countdown_start_time = 0
    countdown_duration = 3 # วินาที

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ ไม่สามารถเปิดกล้องได้")
            break

        # กลับด้านภาพกระจก (เพื่อให้พยักหน้าแล้วไม่งงทิศทาง)
        frame = cv2.flip(frame, 1)
        
        display_frame = frame.copy()
        height, width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ---------------------------------------------------------
        # 1. ส่วนการตรวจจับการพยักหน้า (Nod Detection)
        # ---------------------------------------------------------
        if not is_counting_down:
            # ลดขนาดภาพลงเพื่อให้ประมวลผลไวขึ้น (เฉพาะตอนตรวจจับพยักหน้า)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
            face_landmarks_list = face_recognition.face_landmarks(small_frame)

            if face_landmarks_list:
                # เอาตำแหน่งปลายจมูก (Nose Tip)
                nose_tip = face_landmarks_list[0]['nose_tip'][0]
                nose_y = nose_tip[1] # แกน Y

                # เก็บค่าเฉลี่ยตำแหน่งจมูกเพื่อหาจุดอ้างอิง (Baseline)
                if len(nose_y_history) < 10:
                    nose_y_history.append(nose_y)
                    avg_nose_y = sum(nose_y_history) / len(nose_y_history)
                else:
                    # Rolling average
                    nose_y_history.pop(0)
                    nose_y_history.append(nose_y)
                    avg_nose_y = sum(nose_y_history) / len(nose_y_history)

                # ตรรกะการพยักหน้า: จมูกต้องต่ำกว่าค่าเฉลี่ย (ก้ม) แล้วกลับมาที่เดิม
                # หมายเหตุ: ใน Computer Vision แกน Y ยิ่งมากคือยิ่งต่ำ
                
                if nod_state == "WAITING":
                    if nose_y > avg_nose_y + 3: # เริ่มก้ม (ค่า Y เพิ่มขึ้น)
                        nod_state = "DOWN"
                elif nod_state == "DOWN":
                    if nose_y < avg_nose_y - 1: # เงยกลับขึ้นมา
                        print("💡 ตรวจพบการพยักหน้า! เริ่มนับถอยหลัง...")
                        is_counting_down = True
                        countdown_start_time = time.time()
                        nod_state = "WAITING" # Reset

                # แสดงสถานะบนหน้าจอ (Debug)
                # cv2.putText(display_frame, f"State: {nod_state}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # ---------------------------------------------------------
        # 2. ส่วนการวาดกราฟิกและนับถอยหลัง
        # ---------------------------------------------------------
        box_size = 400
        x1 = (width - box_size) // 2
        y1 = (height - box_size) // 2
        x2 = x1 + box_size
        y2 = y1 + box_size

        color = (161, 214, 162) # สีเขียวปกติ
        
        if is_counting_down:
            elapsed_time = time.time() - countdown_start_time
            time_left = countdown_duration - elapsed_time
            
            if time_left > 0:
                # แสดงตัวเลขนับถอยหลังกลางจอ
                color = (0, 165, 255) # สีส้มตอนนับถอยหลัง
                cv2.putText(display_frame, str(int(time_left) + 1), (width//2 - 30, height//2 + 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10)
                cv2.putText(display_frame, "Smile!", (width//2 - 80, y1 - 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
            else:
                # หมดเวลา -> สั่งบันทึกภาพ (เหมือนกด 's')
                key = ord('s') 
                # ต้อง Reset ค่าเพื่อให้ Loop ข้างล่างทำงาน
                is_counting_down = False 

        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
        if not is_counting_down:
             cv2.putText(display_frame, "Nod to Capture", (x1 + 80, y1 - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Register New Face", display_frame)

        # ---------------------------------------------------------
        # 3. ส่วนควบคุมปุ่มกดและการบันทึก
        # ---------------------------------------------------------
        # ตรวจสอบ key press หรือ trigger จากการนับถอยหลัง
        if 'key' not in locals(): # ถ้าไม่ได้ถูกสั่งจาก Countdown
            key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            print("⏳ กำลังตรวจสอบใบหน้า... ")
            
            # ตรวจสอบใบหน้าในรูปที่จะบันทึก
            face_locations = face_recognition.face_locations(rgb_frame)

            if len(face_locations) > 0:
                cv2.imwrite(filename, frame) # บันทึกภาพ Original (ไม่มี Text)
                print(f"✅ บันทึกรูปภาพเรียบร้อย! ({filename})")
                
                # Effect แจ้งเตือนความสำเร็จ
                cv2.rectangle(display_frame, (0,0), (width, height), (255, 255, 255), 10)
                cv2.putText(display_frame, "SAVED!", (width//2 - 150, height//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                cv2.imshow("Register New Face", display_frame)
                cv2.waitKey(1500)
                break
            else:
                print("⚠️ ไม่พบใบหน้า! กรุณาลองใหม่")
                is_counting_down = False # Reset ถ้ารูปใช้ไม่ได้

        elif key == ord('q'):
            break
        
        # ล้างค่า key เพื่อไม่ให้ loop วนซ้ำคำสั่งเดิม
        key = -1 

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_new_face()