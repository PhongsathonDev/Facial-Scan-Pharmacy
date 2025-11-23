import face_recognition
import cv2
import numpy as np
import time
import requests
import serial

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

    # ---------- Send Google Sheet ----------
    def send_log_to_sheet(self, note: str = "Face verified") -> bool:
        if not self.webapp_url:
            return False
        payload = {
            "sheet": self.sheet_name,
            "data": {
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
            return response.status_code == 200
        except Exception:
            return False

    # ---------- Send ESP32 ----------
    def send_command_to_esp32(self, cmd: str = "f"):
        if self.ser is None:
            return
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
        except Exception:
            pass

    # ---------- Face Recognition Core ----------
    def _load_known_faces(self):
        try:
            image = face_recognition.load_image_file(self.known_image_path)
            encoding = face_recognition.face_encodings(image)[0]
            return [encoding], [self.known_name]
        except Exception as e:
            print(f"❌ Error: {e}")
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
    # 🎨 UI: TUBERBOX THEME (Sage Green + Glassmorphism)
    # ========================================================
    def _draw_tuberbox_ui(self, frame, face_locations, face_names):
        height, width, _ = frame.shape
        
        # --- Color Palette (ดึงมาจากรูป Main Menu) ---
        # BGR Format
        COLOR_SAGE_GREEN = (161, 214, 162)   # เขียวพาสเทลแบบปุ่มรับยา
        COLOR_DARK_GLASS = (40, 40, 40)      # สีดำจางๆ แบบกล่องข้อความ
        COLOR_WHITE = (255, 255, 255)
        COLOR_ALERT = (150, 150, 255)        # สีแดงอ่อนๆ (ใช้แดงสดจะดูดุไป)

        # 1. Header Bar (แถบบนเหมือนในภาพ)
        # สร้าง overlay สีดำจางๆ ด้านบน
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (30, 30, 30), -1) 
        alpha = 0.8 # ความโปร่งแสง
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # ข้อความ Header
        cv2.putText(frame, "Face Verification", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_WHITE, 2)
        
        # เวลา Realtime มุมขวาบน (เหมือนใน UI หลัก)
        time_str = time.strftime("%H:%M:%S")
        text_size = cv2.getTextSize(time_str, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        
        # วาดกล่องเวลา (Glass Box)
        box_x1 = width - 180
        box_y1 = 15
        box_x2 = width - 20
        box_y2 = 65
        
        # Time Box Overlay
        overlay_time = frame.copy()
        cv2.rectangle(overlay_time, (box_x1, box_y1), (box_x2, box_y2), (100, 100, 100), -1)
        cv2.addWeighted(overlay_time, 0.4, frame, 0.6, 0, frame) # จางๆ
        
        # Time Text
        cv2.putText(frame, time_str, (box_x1 + 25, box_y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_WHITE, 2)

        # 2. Logic การแสดงผลหน้า
        if self.verified:
            # --- SUCCESS STATE (โทนเขียว Sage) ---
            center_x, center_y = width // 2, height // 2
            
            # กล่องข้อความ Success ตรงกลาง (Glassmorphism)
            box_w, box_h = 500, 150
            bx1, by1 = center_x - box_w//2, center_y - box_h//2
            bx2, by2 = center_x + box_w//2, center_y + box_h//2
            
            overlay_success = frame.copy()
            # ใช้สีเขียว Sage เป็นพื้นหลังแบบจางๆ
            cv2.rectangle(overlay_success, (bx1, by1), (bx2, by2), COLOR_SAGE_GREEN, -1)
            cv2.addWeighted(overlay_success, 0.85, frame, 0.15, 0, frame)
            
            # กรอบขาวรอบกล่อง
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), COLOR_WHITE, 2)
            
            # ข้อความ
            msg = "VERIFIED"
            ts = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            cv2.putText(frame, msg, (center_x - ts[0]//2, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_WHITE, 3)
            
        else:
            # --- SCANNING STATE ---
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4; right *= 4; bottom *= 4; left *= 4
                
                color = COLOR_WHITE # ปกติสีขาว
                if name == "Unknown":
                    color = COLOR_ALERT # ไม่รู้จักเป็นสีแดงอ่อน
                
                # วาดกรอบหน้า (มุมมนจำลอง - ใช้เส้นสั้นๆ ที่มุม)
                line_len = 30
                th = 3
                # มุมบนซ้าย
                cv2.line(frame, (left, top), (left + line_len, top), color, th)
                cv2.line(frame, (left, top), (left, top + line_len), color, th)
                # มุมบนขวา
                cv2.line(frame, (right, top), (right - line_len, top), color, th)
                cv2.line(frame, (right, top), (right, top + line_len), color, th)
                # มุมล่างซ้าย
                cv2.line(frame, (left, bottom), (left + line_len, bottom), color, th)
                cv2.line(frame, (left, bottom), (left, bottom - line_len), color, th)
                # มุมล่างขวา
                cv2.line(frame, (right, bottom), (right - line_len, bottom), color, th)
                cv2.line(frame, (right, bottom), (right, bottom - line_len), color, th)

                # --- Progress Bar (แถบโหลดสีเขียว Sage) ---
                if self.hold_start_time is not None and name != "Unknown":
                    elapsed = time.time() - self.hold_start_time
                    progress = min(elapsed / self.hold_seconds, 1.0)
                    
                    # วาดพื้นหลังแถบ (สีเทาจาง)
                    bar_h = 8
                    bar_y = bottom + 20
                    cv2.rectangle(frame, (left, bar_y), (right, bar_y + bar_h), (100,100,100), -1)
                    
                    # วาดเนื้อแถบ (สีเขียว Sage)
                    fill_w = int((right - left) * progress)
                    if fill_w > 0:
                        cv2.rectangle(frame, (left, bar_y), (left + fill_w, bar_y + bar_h), COLOR_SAGE_GREEN, -1)
                    
                    # ข้อความกำลังตรวจสอบ
                    cv2.putText(frame, "HOLD STILL...", (left, bar_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_SAGE_GREEN, 1)

    def _update_hold_state(self, recognized_this_frame: bool):
        if recognized_this_frame:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            else:
                elapsed = time.time() - self.hold_start_time
                if elapsed >= self.hold_seconds and not self.verified:
                    self.verified = True
                    print("✅ สแกนผ่านแล้ว")
                    ok = self.send_log_to_sheet(note="Face verified from camera")
                    if ok:
                        self.send_command_to_esp32("f")
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
                
                # เรียกใช้ UI ธีม Tuberbox
                self._draw_tuberbox_ui(frame, locs, names)

                cv2.imshow(window_name, frame)

                if self.verified:
                    cv2.waitKey(2000)
                    break
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.close_camera()

if __name__ == "__main__":
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"
    verifier = FaceVerifier(
        known_image_path="paper.jpeg",
        known_name="Paper",
        webapp_url=WEBAPP_URL,
        sheet_name="Patient",
        face_id="Paper"
    )
    verifier.run()