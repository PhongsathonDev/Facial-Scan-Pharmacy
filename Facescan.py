

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

        # UI Animation State
        self.scan_line_y = 0
        self.scan_direction = 1
        self.animation_frame = 0

    # ---------- ส่วนส่งไป Google Sheet ----------

    def send_log_to_sheet(self, note: str = "Face verified") -> bool:
        if not self.webapp_url:
            print("⚠️ ยังไม่ได้ตั้งค่า WEBAPP_URL ข้ามการส่ง Google Sheet")
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
        except Exception as e:
            print("❌ ส่งข้อมูลไป Google Sheet ไม่สำเร็จ:", e)
            return False

    # ---------- ส่วนคุยกับ ESP32 ----------

    def send_command_to_esp32(self, cmd: str = "f"):
        if self.ser is None:
            return
        try:
            self.ser.write(cmd.encode("utf-8"))
            self.ser.flush()
        except Exception as e:
            print("❌ ส่งคำสั่งไป ESP32 ไม่สำเร็จ:", e)

    # ---------- ส่วน Face Recognition ----------

    def _load_known_faces(self):
        try:
            image = face_recognition.load_image_file(self.known_image_path)
            encoding = face_recognition.face_encodings(image)[0]
            return [encoding], [self.known_name]
        except Exception as e:
            print(f"❌ ไม่สามารถโหลดรูปภาพต้นแบบได้: {e}")
            return [], []

    def open_camera(self):
        self.video_capture = cv2.VideoCapture(self.camera_index)
        if not self.video_capture.isOpened():
            raise RuntimeError("ไม่สามารถเปิดกล้องได้")
        
        # ตั้งค่าความละเอียดกล้องให้สูงขึ้นถ้าทำได้ (เพื่อความคมชัด)
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def close_camera(self):
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    # ---------- ส่วน UI / Drawing ----------

    def _draw_hud_overlay(self, frame):
        """วาด HUD พื้นหลังและเส้น Grid"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # สีธีม (Cyan/Blue)
        color_primary = (255, 255, 0)  # Cyan (BGR)
        color_secondary = (50, 50, 50) # Dark Gray

        # 1. ขอบมุมจอ 4 ด้าน
        line_len = 40
        thick = 2
        # Top-Left
        cv2.line(overlay, (20, 20), (20 + line_len, 20), color_primary, thick)
        cv2.line(overlay, (20, 20), (20, 20 + line_len), color_primary, thick)
        # Top-Right
        cv2.line(overlay, (w-20, 20), (w-20 - line_len, 20), color_primary, thick)
        cv2.line(overlay, (w-20, 20), (w-20, 20 + line_len), color_primary, thick)
        # Bottom-Left
        cv2.line(overlay, (20, h-20), (20 + line_len, h-20), color_primary, thick)
        cv2.line(overlay, (20, h-20), (20, h-20 - line_len), color_primary, thick)
        # Bottom-Right
        cv2.line(overlay, (w-20, h-20), (w-20 - line_len, h-20), color_primary, thick)
        cv2.line(overlay, (w-20, h-20), (w-20, h-20 - line_len), color_primary, thick)

        # 2. เส้น Grid บางๆ
        # วาดเส้นแนวนอน
        for y in range(0, h, 100):
            cv2.line(overlay, (0, y), (w, y), color_secondary, 1)
        # วาดเส้นแนวตั้ง
        for x in range(0, w, 100):
            cv2.line(overlay, (x, 0), (x, h), color_secondary, 1)

        # 3. Header Text
        cv2.putText(overlay, "SYSTEM: ONLINE", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_primary, 1)
        cv2.putText(overlay, f"CAM_ID: {self.camera_index}", (40, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_primary, 1)

        # ผสมภาพเพื่อให้ดูโปร่งใส (HUD ดูล้ำๆ)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    def _draw_scanning_line(self, frame):
        """วาดเส้นสแกนวิ่งขึ้นลง"""
        h, w = frame.shape[:2]
        
        # อัปเดตตำแหน่งเส้น
        speed = 5
        self.scan_line_y += speed * self.scan_direction
        
        if self.scan_line_y >= h:
            self.scan_direction = -1
        elif self.scan_line_y <= 0:
            self.scan_direction = 1

        # วาดเส้น
        color_scan = (0, 255, 255) # Yellow/Cyan mix
        cv2.line(frame, (0, self.scan_line_y), (w, self.scan_line_y), color_scan, 2)
        
        # Effect แสงฟุ้งๆ รอบเส้น (วาดเส้นจางๆ ประกบ)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, self.scan_line_y - 20), (w, self.scan_line_y + 20), color_scan, cv2.FILLED)
        cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)

    def _draw_modern_box(self, frame, location, name, is_known):
        """วาดกรอบใบหน้าแบบ Sci-fi"""
        top, right, bottom, left = location
        
        # สี: เขียวถ้ารู้จัก, แดงถ้าไม่รู้จัก
        color = (0, 255, 0) if is_known else (0, 0, 255)
        
        # วาดมุมกรอบ (Corner Brackets) แทนสี่เหลี่ยมทื่อๆ
        line_len = int((right - left) * 0.2)
        thick = 2
        
        # Top-Left
        cv2.line(frame, (left, top), (left + line_len, top), color, thick)
        cv2.line(frame, (left, top), (left, top + line_len), color, thick)
        # Top-Right
        cv2.line(frame, (right, top), (right - line_len, top), color, thick)
        cv2.line(frame, (right, top), (right, top + line_len), color, thick)
        # Bottom-Left
        cv2.line(frame, (left, bottom), (left + line_len, bottom), color, thick)
        cv2.line(frame, (left, bottom), (left, bottom - line_len), color, thick)
        # Bottom-Right
        cv2.line(frame, (right, bottom), (right - line_len, bottom), color, thick)
        cv2.line(frame, (right, bottom), (right, bottom - line_len), color, thick)

        # ชื่อและสถานะ
        font = cv2.FONT_HERSHEY_SIMPLEX
        label = f"{name} [{'MATCH' if is_known else 'UNKNOWN'}]"
        
        # พื้นหลังตัวหนังสือ
        (w, h), _ = cv2.getTextSize(label, font, 0.6, 1)
        cv2.rectangle(frame, (left, top - 30), (left + w + 10, top - 5), color, cv2.FILLED)
        cv2.putText(frame, label, (left + 5, top - 12), font, 0.6, (0, 0, 0), 1)

    def _draw_progress_bar(self, frame, progress):
        """วาด Progress Bar ตรงกลางจอล่าง"""
        h, w = frame.shape[:2]
        bar_w = 400
        bar_h = 20
        center_x = w // 2
        start_x = center_x - (bar_w // 2)
        start_y = h - 100

        # กรอบ Bar
        cv2.rectangle(frame, (start_x, start_y), (start_x + bar_w, start_y + bar_h), (100, 100, 100), 2)
        
        # เนื้อ Bar
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            # สีไล่จากเหลืองไปเขียว (ง่ายๆ คือใช้สีเขียวเมื่อใกล้เต็ม)
            color = (0, 255, 255) if progress < 0.8 else (0, 255, 0)
            cv2.rectangle(frame, (start_x + 2, start_y + 2), (start_x + fill_w - 2, start_y + bar_h - 2), color, cv2.FILLED)

        # ข้อความ
        text = f"VERIFYING... {int(progress * 100)}%"
        cv2.putText(frame, text, (start_x, start_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def _recognize_faces(self, frame):
        # ย่อภาพเพื่อ Face Recog (แต่ใช้วาดบน Frame ใหญ่)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        recognized_this_frame = False

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Scale กลับมาขนาดจริง
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=self.tolerance
            )
            name = "Unknown"
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

            is_known = False
            if best_match_index is not None and matches[best_match_index] and face_distances[best_match_index] < self.tolerance:
                name = self.known_face_names[best_match_index]
                is_known = True
                recognized_this_frame = True

            # วาดกรอบแบบใหม่
            self._draw_modern_box(frame, (top, right, bottom, left), name, is_known)

        return frame, recognized_this_frame

    def _update_hold_state(self, frame, recognized_this_frame: bool):
        """อัปเดตสถานะและวาด Progress"""
        if recognized_this_frame:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            
            elapsed = time.time() - self.hold_start_time
            progress = min(elapsed / self.hold_seconds, 1.0)
            
            # วาด Progress Bar
            self._draw_progress_bar(frame, progress)

            if elapsed >= self.hold_seconds and not self.verified:
                self.verified = True
                print("✅ สแกนใบหน้าผ่านแล้ว")
                
                # วาดข้อความ Success
                h, w = frame.shape[:2]
                cv2.putText(frame, "ACCESS GRANTED", (w//2 - 200, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                cv2.imshow('Video', frame)
                cv2.waitKey(500) # โชว์ค้างไว้แป๊บนึง

                ok = self.send_log_to_sheet(note="Face verified from camera")
                if ok:
                    self.send_command_to_esp32("f")
                else:
                    print("⚠️ ไม่ส่งคำสั่งไป ESP32 เพราะส่ง Google Sheet ไม่สำเร็จ")
        else:
            self.hold_start_time = None
            # Reset progress visual? (Optional, but handled by not drawing it)

    def run(self):
        self.hold_start_time = None
        self.verified = False

        self.open_camera()
        print("กำลังเปิดกล้อง... มองตรงเข้ากล้องให้ครบเวลาที่กำหนด")
        print("กด 'q' เพื่อยกเลิก")

        window_name = 'Video'
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        try:
            while True:
                ret, frame = self.video_capture.read()
                if not ret:
                    print("ไม่สามารถอ่านข้อมูลจากกล้องได้")
                    break
                
                # กลับด้านภาพ (Mirror) เพื่อความธรรมชาติ
                frame = cv2.flip(frame, 1)

                # 1. วาด HUD พื้นหลัง
                self._draw_hud_overlay(frame)

                # 2. วาดเส้นสแกน
                self._draw_scanning_line(frame)

                # 3. Face Recognition & Draw Boxes
                frame, recognized_this_frame = self._recognize_faces(frame)

                # 4. Update Logic & Draw Progress
                self._update_hold_state(frame, recognized_this_frame)

                cv2.imshow(window_name, frame)

                if self.verified:
                    time.sleep(1) # โชว์ความสำเร็จอีกนิด
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("ยกเลิกการสแกนโดยผู้ใช้")
                    break

        finally:
            self.close_camera()
            print("ปิดโปรแกรมเรียบร้อย")

        return self.verified


if __name__ == "__main__":
    WEBAPP_URL = "https://script.google.com/macros/s/AKfycbypFJrwXJVcEPNyveBYXplgGsO2CxZLnWvaHQgKbVLbThRwd7vbksIqAItmVtRLD-4v/exec"

    verifier = FaceVerifier(
        known_image_path="paper.jpeg",
        known_name="Paper",
        tolerance=0.5,
        hold_seconds=2.0,
        camera_index=0,
        webapp_url=WEBAPP_URL,
        sheet_name="Patient",
        face_id="Paper",
        serial_port="/dev/ttyUSB0",
        serial_baudrate=115200
    )
    verifier.run()