#define IN1 19
#define IN2 21
#define LIMIT_SENSOR 14

#define CONTROL_PIN 18  // ต่อกับ ENA ของ L298N

// ตั้งค่าช่อง PWM สำหรับ ESP32
const int PWM_CHANNEL = 0;
const int PWM_FREQ    = 5000; // 5 kHz
const int PWM_RES     = 8;    // 8-bit → ค่าความเร็ว 0–255

int motorSpeed = 200; // ความเร็วเริ่มต้น (0–255)

bool faceDetected = false; // ตัวแปรจำลองว่ามีการแสกนหน้าสำเร็จหรือไม่

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(LIMIT_SENSOR, INPUT_PULLUP); // YL-99 ใช้ pullup ได้เลย

  // ตั้งค่า PWM ที่ CONTROL_PIN
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttachPin(CONTROL_PIN, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 0); // เริ่มต้นปิดมอเตอร์

  stopMotor();
  Serial.println("ระบบจ่ายยาเริ่มทำงาน...");
}

void loop() {
  // ========================
  // จำลองการแสกนใบหน้า
  // ========================
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'f') { 
      // f = แสกนใบหน้าสำเร็จ
      faceDetected = true;
      Serial.println("✅ ตรวจจับใบหน้าสำเร็จ! กำลังจ่ายยา...");
      dispenseMedicine();
    }

    // ปรับความเร็วผ่าน Serial (เช่น พิมพ์ s150 แล้ว Enter)
    if (cmd == 's') {
      int newSpeed = Serial.parseInt(); // อ่านตัวเลขตามหลัง s
      if (newSpeed < 0)   newSpeed = 0;
      if (newSpeed > 255) newSpeed = 255;
      motorSpeed = newSpeed;
      Serial.print("🔧 ตั้งความเร็วใหม่ = ");
      Serial.println(motorSpeed);
    }
  }
}

// -----------------------------
// ฟังก์ชันควบคุมมอเตอร์
// -----------------------------
void dispenseMedicine() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  while (digitalRead(LIMIT_SENSOR) == HIGH) {
    // เปิดมอเตอร์
    ledcWrite(PWM_CHANNEL, 185);  // ใช้ค่าที่หมุนแน่ ๆ
    delay(5);                    // หมุน 50 ms

    // ปิดมอเตอร์
    ledcWrite(PWM_CHANNEL, 0);
    delay(5);                    // หยุด 50 ms

    // ถ้าอยากให้เนียนขึ้นก็ลด delay ให้สั้นลง
  }

  stopMotor();
  Serial.println("🟢 ถาดจ่ายยาหยุดเรียบร้อยแล้ว");
  faceDetected = false;
}


// -----------------------------
// ฟังก์ชันเริ่มหมุน/หยุด
// -----------------------------
void startMotor() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  ledcWrite(PWM_CHANNEL, motorSpeed); // ✅ หมุนตามความเร็วที่ตั้งไว้
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  ledcWrite(PWM_CHANNEL, 0); // ✅ ปิด PWM = หยุดมอเตอร์
}