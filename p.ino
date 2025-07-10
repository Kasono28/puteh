#include <Servo.h> 
Servo sv;         

// 핀 정의
const int DIGITAL_LIGHT_SENSOR_PIN = 8;  // 디지털 조도 센서 핀
const int SERVO_PIN = 5;                 // 서보 모터 신호 핀
const int LASER_PIN = 7;                 // 레이저 모듈 제어 핀 
const int FLOAT_SWITCH_PIN = 2;          // 플로트 스위치 핀
const int PUMP_RELAY_PIN = 4;            // 펌프 제어를 위한 릴레이 모듈 핀

// 서보 모터의 열림/닫힘 각도
const int SERVO_CLOSED_ANGLE = 0;   // 서보가 슬라이드 게이트를 닫는 각도
const int SERVO_OPEN_ANGLE = 90;    // 서보가 슬라이드 게이트를 여는 각도 

// 센서 값 전송 주기
unsigned long previousMillis = 0;
const long interval = 1000; // 1초마다 센서 값 전송

void setup() {
  Serial.begin(9600); // 시리얼 통신 시작

  pinMode(DIGITAL_LIGHT_SENSOR_PIN, INPUT);   // 디지털 조도 센서 핀 설정 
  pinMode(SERVO_PIN, OUTPUT);                 // 서보 모터 핀 설정
  pinMode(LASER_PIN, OUTPUT);                 // 레이저 모듈 핀 설정 
  pinMode(FLOAT_SWITCH_PIN, INPUT_PULLUP);    // 플로트 스위치 핀 설정 
  pinMode(PUMP_RELAY_PIN, OUTPUT);            // 펌프 릴레이 핀을 출력으로 설정

  sv.attach(SERVO_PIN); // 서보 모터를 핀에 연결
  sv.write(SERVO_CLOSED_ANGLE); // 서보 초기 상태: 게이트 닫힘
  delay(1000); // 서보 초기화 시간 대기

  digitalWrite(LASER_PIN, HIGH);      // 레이저 모듈 상시 ON
  digitalWrite(PUMP_RELAY_PIN, LOW);  // 릴레이 초기 상태: 펌프 OFF (대부분의 릴레이는 LOW일 때 OFF)
}

void loop() {
  // ------------- 센서 값 주기적 전송 (1초마다) --------------
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // ------------- 조도 센서 (고체 재고) 상태 --------------
    // HIGH: 레이저 빛 감지 (재고 없음, 레이저가 통과)
    // LOW: 레이저 빛 차단 (재고 있음, 레이저가 가려짐)
    int digitalLightState = digitalRead(DIGITAL_LIGHT_SENSOR_PIN);
    Serial.print("LIGHT_STATE:"); 
    if (digitalLightState == HIGH) {
      Serial.println("HIGH"); // 재고 없음
    } else {
      Serial.println("LOW"); // 재고 있음
    }

    // ------------- 플로트 스위치 (액체 재고) 상태 --------------
    // INPUT_PULLUP 사용 시:
    // HIGH: 스위치 열림 (액체 없음, 플로트 내려감)
    // LOW: 스위치 닫힘 (액체 있음, 플로트 올라감)
    int floatSwitchState = digitalRead(FLOAT_SWITCH_PIN);
    Serial.print("FLOAT_STATE:");
    if (floatSwitchState == HIGH) {
      Serial.println("EMPTY"); // 액체 없음
    } else {
      Serial.println("FULL");  // 액체 있음
    }
  }

  // ------------- 아두이노 시리얼 명령 처리 (MQTT 주문 수신 시) --------------
  if (Serial.available()) { 
    String commandString = Serial.readStringUntil('\n'); 
    commandString.trim(); 

    if (commandString.startsWith("S")) { // 'S'(Sugar)로 시작하면 서보 작동
      float floatValue = commandString.substring(1).toFloat(); 
      int openDurationMs = (int)(floatValue * 1000); 

      if (openDurationMs > 0) { 
        sv.write(SERVO_OPEN_ANGLE);  
        delay(openDurationMs);       
        sv.write(SERVO_CLOSED_ANGLE); 
      }
    } 
    
    else if (commandString.startsWith("W")) { // 'W'ㅅ작하면 펌프 작동
      float floatValue = commandString.substring(1).toFloat();
      int pumpDurationMs = (int)(floatValue * 1000);

      if (pumpDurationMs > 0) {
        digitalWrite(PUMP_RELAY_PIN, HIGH); // 릴레이 ON -> 펌프 작동 
        delay(pumpDurationMs);             // 지정된 시간 동안 펌프 작동 유지
        digitalWrite(PUMP_RELAY_PIN, LOW);  // 릴레이 OFF -> 펌프 정지
      }
    }

    // 시리얼 버퍼 비우기
    while (Serial.available()) {
      Serial.read();
    }
  }
}