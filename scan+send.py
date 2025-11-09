import face_recognition
import cv2
import numpy as np
import time
import requests  # <<< เพิ่มอันนี้

class FaceVerifier:
    def __init__(
        self,
        known_image_path: str,
        known_name: str = "User",
        tolerance: float = 0.45,
        hold_seconds: float = 3.0,
        camera_index: int = 0,
        webapp_url: str | None = None,
        sheet_name: str = "sheet1",
        face_id: str = "user_001"
    ):
        """
        known_image_path : path รูปต้นแบบ
        known_name       : ชื่อที่จะแสดงเมื่อรู้จักใบหน้า
        tolerance        : ยิ่งน้อยยิ่งเข้มงวด
        hold_seconds     : ต้องมองตรงค้างกี่วินาทีก่อนจะถือว่าผ่าน
        camera_index     : index กล้อง (0 = กล้องหลัก)
        webapp_url       : URL Google Apps Script Web App
        sheet_name       : ชื่อชีตใน Google Sheet
        face_id          : รหัสประจำตัวใบหน้า
        """
        self.known_image_path = known_image_path
        self.known_name = known_name
        self.tolerance = tolerance
        self.hold_seconds = hold_seconds
        self.camera_index = camera_index

        self.webapp_url = webapp_url
        self.sheet_name = sheet_name
        self.face_id = face_id

        # โหลดและเตรียมข้อมูลใบหน้าต้นแบบ
        self.known_face_encodings, self.known_face_names = self._load_known_faces()

        # state เวลาการมองค้าง
        self.hold_start_time = None
        self.verified = False

        # ตัวจัดการกล้อง
        self.video_capture = None

    # ---------- ส่วน Google Sheet ----------

    def send_log_to_sheet(self, note: str = "Face verified"):
        """ส่งข้อมูลไปยัง Google Sheet ผ่าน Web App"""
        if not self.webapp_url:
            print("⚠️ ยังไม่ได้ตั้งค่า WEBAPP_URL ข้ามการส่ง Google Sheet")
            return

        payload = {
            "sheet": self.sheet_name,
            "data": {
                # Timestamp ว่างไว้ให้ Apps Script ใส่เอง
                "Date": "",
                "Time": "",
                "Name": self.known_name,
                "FaceID": self.face_id,
                "Status": "Verified",
                "Note": note
            }
        }

        try:
            response = requests.post(self.webapp_url, json=payload, timeout=10)
            print("ส่งไป Google Sheet → Status code:", response.status_code)
            print("Response text:", response.text)
        except Exception as e:
            print("❌ ส่งข้อมูลไป Google Sheet ไม่สำเร็จ:", e)

    # ---------- ส่วน Face Recognition ----------

    def _load_known_faces(self):
        image = face_recognition.load_image_file(self.known_image_path)
        encoding = face_recognition.face_encodings(image)[0]

        known_face_encodings = [encoding]
        known_face_names = [self.known_name]

        return known_face_encodings, known_face_names

    def open_camera(self):
        self.video_capture = cv2.VideoCapture(self.camera_index)
        if not self.video_capture.isOpened():
            raise RuntimeError("ไม่สามารถเปิดกล้องได้")

    def close_camera(self):
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    def _recognize_faces(self, frame):
        # ย่อภาพเพื่อให้เร็วขึ้น
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        recognized_this_frame = False

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=self.tolerance
            )

            name = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index] and face_distances[best_match_index] < self.tolerance:
                name = self.known_face_names[best_match_index]
                recognized_this_frame = True

            face_names.append(name)

        # วาดกรอบชื่อ
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

        return frame, recognized_this_frame

    def _update_hold_state(self, recognized_this_frame: bool):
        """อัปเดตสถานะเวลามองค้าง + เช็กว่าครบ hold_seconds หรือยัง"""
        if recognized_this_frame:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            else:
                elapsed = time.time() - self.hold_start_time
                if elapsed >= self.hold_seconds and not self.verified:
                    self.verified = True
                    print("✅ สแกนใบหน้าผ่านแล้ว")
                    # ✨ เรียกส่ง Google Sheet ตรงนี้เลยตอนผ่านครั้งแรก
                    self.send_log_to_sheet(note="Face verified from camera")
        else:
            self.hold_start_time = None

    def _draw_status_text(self, frame):
        font = cv2.FONT_HERSHEY_DUPLEX

        if self.hold_start_time is not None and not self.verified:
            elapsed = time.time() - self.hold_start_time
            text = f"Hold still: {elapsed:.1f}/{self.hold_seconds:.0f} sec"
            cv2.putText(frame, text, (30, 40), font, 0.8, (0, 255, 255), 2)
        elif self.verified:
            cv2.putText(frame, "Face Verified", (30, 40), font, 0.8, (0, 255, 0), 2)

        return frame

    def run(self):
        self.open_camera()
        print("กำลังเปิดกล้อง... มองตรงเข้ากล้องให้ครบเวลาที่กำหนด")
        print("กด 'q' เพื่อยกเลิก")

        try:
            while True:
                ret, frame = self.video_capture.read()
                if not ret:
                    print("ไม่สามารถอ่านข้อมูลจากกล้องได้")
                    break

                frame, recognized_this_frame = self._recognize_faces(frame)
                self._update_hold_state(recognized_this_frame)
                frame = self._draw_status_text(frame)

                cv2.imshow('Video', frame)

                if self.verified:
                    cv2.waitKey(1000)
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            self.close_camera()
            print("ปิดโปรแกรมเรียบร้อย")


if _name_ == "_main_":
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"

    verifier = FaceVerifier(
        known_image_path="paper.jpeg",
        known_name="Paper",
        tolerance=0.5,
        hold_seconds=2.0,
        camera_index=0,
        webapp_url=WEBAPP_URL,
        sheet_name="Patient",
        face_id="Paper"
    )
    verifier.run()
