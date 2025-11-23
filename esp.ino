#include <SoftwareSerial.h>
#include "RedMP3.h"
#define IN1 19
#define IN2 21
#define LIMIT_SENSOR 14
#define CONTROL_PIN 18 


#define MP3_RX 15
#define MP3_TX 2
MP3 mp3(MP3_RX, MP3_TX);
const int PWM_CHANNEL = 0;
const int PWM_FREQ    = 5000;
const int PWM_RES     = 8;

int motorSpeed = 200;
bool faceDetected = false;

// ✅ เพิ่มตัวแปรสำหรับ Timeout
const unsigned long TIMEOUT_MS = 5000; // ตัดการทำงานถ้าหมุนเกิน 5 วินาที

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(LIMIT_SENSOR, INPUT_PULLUP);

  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttachPin(CONTROL_PIN, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 0);

  stopMotor();
  Serial.println("ระบบจ่ายยาเริ่มทำงาน...");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'f') { 
      faceDetected = true;
      Serial.println("✅ ตรวจจับใบหน้าสำเร็จ! กำลังจ่ายยา...");
      dispenseMedicine();
    }
    if (cmd == 'a') { 
      mp3.playWithVolume(002, 30);
    }
mp3.playWithVolume(001, 30);
    if (cmd == 's') {
      int newSpeed = Serial.parseInt();
      if (newSpeed < 0)   newSpeed = 0;
      if (newSpeed > 255) newSpeed = 255;
      motorSpeed = newSpeed;
      Serial.print("🔧 ตั้งความเร็วใหม่ = ");
      Serial.println(motorSpeed);
    }
  }
}

// -----------------------------
// ฟังก์ชันควบคุมมอเตอร์ (ปรับปรุงใหม่)
// -----------------------------
void dispenseMedicine() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // 1. (Optional) ถ้าเริ่มมาทับเซนเซอร์อยู่แล้ว ให้ขยับออกก่อนเล็กน้อย
  if (digitalRead(LIMIT_SENSOR) == LOW) {
     Serial.println("⚠️ ถาดทับเซนเซอร์อยู่ กำลังขยับออก...");
     ledcWrite(PWM_CHANNEL, 185);
     delay(500); // ขยับออก 0.5 วินาที
  }

  // ✅ เก็บเวลาเริ่มต้น
  unsigned long startTime = millis();
  bool isError = false;

  // 2. ลูปหมุนจนกว่าจะเจอเซนเซอร์ หรือ หมดเวลา
  while (digitalRead(LIMIT_SENSOR) == HIGH) {
    
    // ✅ ตรวจสอบ Timeout
    if (millis() - startTime > TIMEOUT_MS) {
      Serial.println("❌ Error: มอเตอร์หมุนนานเกินกำหนด (Timeout)!");
      isError = true;
      break; // ออกจากลูปทันที
    }

    // โค้ดเดิมของคุณ (Pulse Motor)
    ledcWrite(PWM_CHANNEL, 185); 
    delay(5);                 
    ledcWrite(PWM_CHANNEL, 0);
    delay(5);                 
  }

  stopMotor();
  mp3.playWithVolume(001, 30);
  if (!isError) {
    Serial.println("🟢 ถาดจ่ายยาทำงานเสร็จสมบูรณ์");
  } else {
    Serial.println("🔴 ระบบหยุดฉุกเฉิน กรุณาตรวจสอบฮาร์ดแวร์");
  }
  
  faceDetected = false;
}

void startMotor() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(PWM_CHANNEL, motorSpeed);
}

void stopMotor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  ledcWrite(PWM_CHANNEL, 0);
}