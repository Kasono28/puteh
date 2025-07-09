#include <Servo.h> 
Servo sv;         

// 핀 정의
const int DIGITAL_LIGHT_SENSOR_PIN = A0; // 디지털 조도 센서 핀
const int SERVO_PIN = 5;                 // 서보 모터 신호 핀
const int LASER_PIN = 7;                 // 레이저 모듈 제어 핀 
const int FLOAT_SWITCH_PIN = 2;          // 플로트 스위치 핀

// 서보 모터의 열림/닫힘 각도
const int SERVO_CLOSED_ANGLE = 0;   
const int SERVO_OPEN_ANGLE = 90;    

// 센서 값 전송 주기
unsigned long previousMillis = 0;
const long interval = 1000; // 1초마다 센서 값 전송

void setup() {
  Serial.begin(9600); 

  pinMode(DIGITAL_LIGHT_SENSOR_PIN, INPUT);   // 디지털 조도 센서 핀 설정
  pinMode(SERVO_PIN, OUTPUT);                 // 서보 모터 핀 설정
  pinMode(LASER_PIN, OUTPUT);                 // 레이저 모듈 핀 설정
  pinMode(FLOAT_SWITCH_PIN, INPUT_PULLUP);    // 플로트 스위치 핀 설정

  sv.attach(SERVO_PIN); 
  sv.write(SERVO_CLOSED_ANGLE); // 서보 초기 상태: 닫힘
  delay(1000); 

  digitalWrite(LASER_PIN, HIGH);      // 레이저 상시 ON
}

void loop() {
  // ------------- (1초마다) --------------
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // ------------- 조도 센서 --------------
    // 조도 센서 상태
    int digitalLightState = digitalRead(DIGITAL_LIGHT_SENSOR_PIN);
    Serial.print("LIGHT_STATE:"); 
    if (digitalLightState == HIGH) {
      Serial.println("HIGH"); 
    } else {
      Serial.println("LOW"); 
    }

    // ------------- 플로트 스위치 --------------
    // 플로트 스위치 상태
    int floatSwitchState = digitalRead(FLOAT_SWITCH_PIN);
    Serial.print("FLOAT_STATE:");
    if (floatSwitchState == HIGH) {
      Serial.println("EMPTY"); 
    } else {
      Serial.println("FULL");  
    }
  }

  // ------------- 아두이노 시리얼 명령 처리 --------------
  if (Serial.available()) { 
    String commandString = Serial.readStringUntil('\n'); 
    commandString.trim(); 

    if (commandString.startsWith("S")) { // 'S'(sugar)로 시작하면 서보 작동
      float floatValue = commandString.substring(1).toFloat(); 
      int openDurationMs = (int)(floatValue * 1000); 

      if (openDurationMs > 0) {
        sv.write(SERVO_OPEN_ANGLE);  
        delay(openDurationMs);       
        sv.write(SERVO_CLOSED_ANGLE); 
      }
    } 
    
    // 시리얼 버퍼 비우기
    while (Serial.available()) {
      Serial.read();
    }
  }
}