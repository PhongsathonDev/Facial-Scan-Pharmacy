import face_recognition
import cv2
import numpy as np
import time
import requests
import serial
import threading
import json
import os

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
        face_id: str = "user_001",
        serial_port: str | None = "/dev/ttyUSB0",
        serial_baudrate: int = 115200
    ):
        self.known_image_path = known_image_path
        self.known_name = known_name
        self.tolerance = tolerance
        self.hold_seconds = hold_seconds
        self.camera_index = camera_index

        self.webapp_url = webapp_url
        self.sheet_name = sheet_name
        self.face_id = face_id
        
        # ชื่อไฟล์สำหรับเก็บข้อมูลตอนไม่มีเน็ต
        self.offline_file = "offline_logs.json"

        # ====== Serial ไปยัง ESP32 ======
        self.serial_port = serial_port
        self.serial_baudrate = serial_baudrate
        self.ser = None

        if self.serial_port is not None:
            try:
                self.ser = serial.Serial(self.serial_port, self.serial_baudrate, timeout=1)
                time.sleep(2)
                print(f"✅ เปิดพอร์ต Serial ไป ESP32 ที่ {self.serial_port} เรียบร้อย")
            except Exception as e:
                print("❌ เปิดพอร์ต Serial ไป ESP32 ไม่สำเร็จ:", e)
                self.ser = None

        self.known_face_encodings, self.known_face_names = self._load_known_faces()
        self.hold_start_time = None
        self.verified = False
        self.video_capture = None

    # ---------- Send Google Sheet (System Offline Support) ----------
    def send_log_to_sheet(self, note: str = "Face verified"):
        """เรียกใช้งานใน Thread แยก เพื่อไม่ให้โปรแกรมหลักสะดุด"""
        threading.Thread(target=self._send_log_worker, args=(note,), daemon=True).start()

    def _send_log_worker(self, note):
        """ฟังก์ชันเบื้องหลังสำหรับจัดการการส่งข้อมูล"""
        # 1. เตรียมข้อมูล Payload
        payload = {
            "sheet": self.sheet_name,
            "data": {
                "Date": "", # Google Script จะใส่เวลาให้
                "Time": "",
                "Name": self.known_name,
                "FaceID": self.face_id,
                "Status": "Verified",
                "Note": note
            }
        }

        # 2. ลองส่งข้อมูลเก่าที่ค้างอยู่ก่อน (ถ้ามีเน็ตจะส่งออกไป)
        self._retry_offline_logs()

        # 3. ส่งข้อมูลปัจจุบัน
        success = self._post_to_webapp(payload)
        
        # 4. ถ้าส่งไม่ผ่าน ให้บันทึกลงไฟล์ไว้ส่งทีหลัง
        if not success:
            print(f"⚠️ ไม่สามารถเชื่อมต่อเน็ตได้ บันทึกข้อมูลลง {self.offline_file}")
            self._save_offline_log(payload)

    def _post_to_webapp(self, payload):
        """ยิง Request จริง"""
        if not self.webapp_url:
            return False
        try:
            # timeout 3 วินาทีพอ ถ้าช้ากว่านี้ถือว่าเน็ตไม่ดี ตัดไป offline เลย
            response = requests.post(self.webapp_url, json=payload, timeout=3)
            if response.status_code == 200:
                print(f"☁️ ส่งข้อมูล {payload['data']['Name']} สำเร็จ")
                return True
        except Exception as e:
            pass # เงียบไว้ แล้ว return False
        return False

    def _save_offline_log(self, payload):
        """บันทึกข้อมูลลง JSON File ต่อท้าย"""
        logs = []
        # อ่านของเก่าขึ้นมา
        if os.path.exists(self.offline_file):
            try:
                with open(self.offline_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(payload)
        
        # เขียนกลับลงไฟล์
        with open(self.offline_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def _retry_offline_logs(self):
        """พยายามส่งข้อมูลที่ค้างอยู่ในไฟล์"""
        if not os.path.exists(self.offline_file):
            return

        try:
            with open(self.offline_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            return

        if not logs:
            return

        print(f"🔄 กำลังทยอยส่งข้อมูล Offline จำนวน {len(logs)} รายการ...")
        remaining_logs = []
        sent_count = 0

        for log in logs:
            if self._post_to_webapp(log):
                sent_count += 1
            else:
                remaining_logs.append(log) # ยังส่งไม่ได้ เก็บไว้ก่อน
        
        if sent_count > 0:
            print(f"✅ ส่งข้อมูลย้อนหลังสำเร็จ {sent_count} รายการ")

        # บันทึกส่วนที่เหลือกลับลงไฟล์ (ถ้าส่งหมดแล้วก็ลบไฟล์ หรือบันทึก list ว่าง)
        if remaining_logs:
            with open(self.offline_file, "w", encoding="utf-8") as f:
                json.dump(remaining_logs, f, ensure_ascii=False, indent=2)
        else:
            # ส่งหมดแล้ว ลบไฟล์ทิ้ง
            os.remove(self.offline_file)

    # ---------- Send ESP32 ----------
    def send_command_to_esp32(self, cmd: str = "f"):
        if self.ser is None:
            # ถ้าไม่มี Serial จริง ให้ข้ามไป (หรือ print test)
            # print(f"Simulation: Sent '{cmd}' to ESP32")
            return
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
            print(f"➡️ ส่งคำสั่ง '{cmd}' ไปยัง ESP32")
        except Exception as e:
            print(f"❌ ส่ง Serial ไม่ได้: {e}")

    # ---------- Face Recognition Core ----------
    def _load_known_faces(self):
        try:
            image = face_recognition.load_image_file(self.known_image_path)
            encoding = face_recognition.face_encodings(image)[0]
            return [encoding], [self.known_name]
        except Exception as e:
            print(f"❌ Error loading face: {e}")
            return [], []

    def open_camera(self):
        self.video_capture = cv2.VideoCapture(self.camera_index)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not self.video_capture.isOpened():
            raise RuntimeError("Cannot open camera")

    def close_camera(self):
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    def _process_frame(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        recognized_this_frame = False

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
            name = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < self.tolerance:
                    name = self.known_face_names[best_match_index]
                    recognized_this_frame = True
            face_names.append(name)

        return face_locations, face_names, recognized_this_frame

    # ========================================================
    # 🎨 UI: TUBERBOX THEME
    # ========================================================
    def _draw_tuberbox_ui(self, frame, face_locations, face_names):
        height, width, _ = frame.shape
        COLOR_SAGE_GREEN = (161, 214, 162)
        COLOR_WHITE = (255, 255, 255)
        COLOR_ALERT = (150, 150, 255)

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (30, 30, 30), -1) 
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        cv2.putText(frame, "Face Verification", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_WHITE, 2)
        
        if self.verified:
            center_x, center_y = width // 2, height // 2
            box_w, box_h = 500, 150
            bx1, by1 = center_x - box_w//2, center_y - box_h//2
            bx2, by2 = center_x + box_w//2, center_y + box_h//2
            
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), COLOR_SAGE_GREEN, -1)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), COLOR_WHITE, 2)
            
            msg = "VERIFIED"
            ts = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            cv2.putText(frame, msg, (center_x - ts[0]//2, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_WHITE, 3)
            
        else:
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4; right *= 4; bottom *= 4; left *= 4
                color = COLOR_WHITE if name != "Unknown" else COLOR_ALERT
                
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                if self.hold_start_time is not None and name != "Unknown":
                    elapsed = time.time() - self.hold_start_time
                    progress = min(elapsed / self.hold_seconds, 1.0)
                    
                    bar_y = bottom + 20
                    cv2.rectangle(frame, (left, bar_y), (right, bar_y + 8), (100,100,100), -1)
                    fill_w = int((right - left) * progress)
                    if fill_w > 0:
                        cv2.rectangle(frame, (left, bar_y), (left + fill_w, bar_y + 8), COLOR_SAGE_GREEN, -1)

    def _update_hold_state(self, recognized_this_frame: bool):
        if recognized_this_frame:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            else:
                elapsed = time.time() - self.hold_start_time
                if elapsed >= self.hold_seconds and not self.verified:
                    self.verified = True
                    print("✅ สแกนผ่านแล้ว")
                    
                    # 🚀 แก้ไข 1: สั่งจ่ายยาทันที (Priority สูงสุด ไม่ต้องรอเน็ต)
                    self.send_command_to_esp32("f")
                    
                    # ☁️ แก้ไข 2: ส่ง Log ไปทำเบื้องหลัง (Background Thread)
                    # ถ้าไม่มีเน็ต มันจะเก็บลงไฟล์ให้อัตโนมัติ
                    self.send_log_to_sheet(note="Face verified from camera")
        else:
            self.hold_start_time = None

    def run(self):
        self.hold_start_time = None
        self.verified = False
        self.open_camera()
        
        window_name = 'Tuberbox Scan'
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        try:
            while True:
                ret, frame = self.video_capture.read()
                if not ret: break

                locs, names, rec = self._process_frame(frame)
                self._update_hold_state(rec)
                self._draw_tuberbox_ui(frame, locs, names)

                cv2.imshow(window_name, frame)

                if self.verified:
                    cv2.waitKey(2000) # โชว์หน้า Verified 2 วินาทีแล้วปิด
                    break
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.close_camera()

if __name__ == "__main__":
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"
    verifier = FaceVerifier(
        known_image_path="patient.jpeg",
        known_name="patient",
        webapp_url=WEBAPP_URL,
        sheet_name="Patient",
        face_id="patient"
    )
    verifier.run()