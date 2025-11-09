import face_recognition
import cv2
import numpy as np
import time

# --- 1. การเตรียมพร้อม ---

# โหลดรูปภาพต้นแบบ (คนที่คุณต้องการจดจำ) และแปลงเป็น Encoding
known_image = face_recognition.load_image_file("paper.jpeg")
known_face_encoding = face_recognition.face_encodings(known_image)[0]

known_face_encodings = [known_face_encoding]
known_face_names = ["Paper"]

# ตั้งค่าให้เข้มงวดขึ้น
TOLERANCE = 0.45          # ยิ่งน้อยยิ่งเข้มงวด (default ของ lib ~0.6)
HOLD_SECONDS = 3.0        # ต้องให้หน้าตรง/ตรงคนเดิมต่อเนื่องกี่วินาทีก่อนผ่าน

# ตัวแปรนับเวลา
hold_start_time = None    # เวลาเริ่มที่เจอหน้า "Paper"
verified = False          # ผ่านแล้วหรือยัง

# --- 2. เปิดกล้องและประมวลผล ---

video_capture = cv2.VideoCapture(0)

print("กำลังเปิดกล้อง... มองตรงเข้ากล้องให้ระบบสแกนให้ครบเวลาที่กำหนด")
print("กด 'q' เพื่อยกเลิก")

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("ไม่สามารถอ่านข้อมูลจากกล้องได้")
        break

    # ย่อรูปเพื่อให้ประมวลผลเร็วขึ้น
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    recognized_this_frame = False   # เจอ Paper (ผ่านเกณฑ์) ในเฟรมนี้ไหม

    for face_encoding in face_encodings:
        # เปรียบเทียบด้วย tolerance ที่เข้มงวดขึ้น
        matches = face_recognition.compare_faces(
            known_face_encodings,
            face_encoding,
            tolerance=TOLERANCE
        )

        name = "Unknown"
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            # เพิ่มเงื่อนไขเข้มงวด: ต้องต่ำกว่า TOLERANCE จริง ๆ
            if face_distances[best_match_index] < TOLERANCE:
                name = known_face_names[best_match_index]
                recognized_this_frame = True
        face_names.append(name)

    # --- 3. การจัดการเวลาให้ต้องมองตรงค้างไว้ ---

    if recognized_this_frame:
        # ถ้าเพิ่งเจอครั้งแรก ให้เริ่มจับเวลา
        if hold_start_time is None:
            hold_start_time = time.time()
        else:
            # คำนวณเวลาที่มองค้างไว้แล้ว
            elapsed = time.time() - hold_start_time
            if elapsed >= HOLD_SECONDS and not verified:
                verified = True
                print("✅ สแกนใบหน้าผ่านแล้ว")

    else:
        # ถ้าเฟรมนี้ไม่ตรงคนเดิม / ไม่ตรงเกณฑ์ ให้รีเซ็ตเวลาใหม่
        hold_start_time = None

    # --- 4. วาดกรอบและแสดงสถานะบนหน้าจอ ---

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = (0, 0, 255)  # แดง = Unknown
        if name != "Unknown":
            color = (0, 255, 0)  # เขียว = รู้จัก

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6),
                    font, 1.0, (255, 255, 255), 1)

    # แสดง progress การมองค้างไว้
    font = cv2.FONT_HERSHEY_DUPLEX
    if hold_start_time is not None and not verified:
        elapsed = time.time() - hold_start_time
        text = f"Hold still: {elapsed:.1f}/{HOLD_SECONDS:.0f} sec"
        cv2.putText(frame, text, (30, 40), font, 0.8, (0, 255, 255), 2)
    elif verified:
        cv2.putText(frame, "Face Verified", (30, 40), font, 0.8, (0, 255, 0), 2)

    cv2.imshow('Video', frame)

    # ถ้า verify แล้ว แสดงผลให้เห็นสักแป๊บแล้วปิดกล้องอัตโนมัติ
    if verified:
        cv2.waitKey(1000)  # หน่วง 1 วินาทีให้เห็นข้อความ
        break

    # หรือกด q เพื่อออกเอง
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 5. คืนค่าทรัพยากร ---
video_capture.release()
cv2.destroyAllWindows()
print("ปิดโปรแกรมเรียบร้อย")
