import paho.mqtt.client as mqtt
import serial
import time
import json
import sys

# --- 시리얼 포트 설정 ---
SERIAL_PORT = "/dev/cu.usbserial-120" # 아두이노 포트
BAUD_RATE = 9600

# --- MQTT 설정 ---
BROKER_ADDRESS = "10.129.59.145" # MQTT 브로커 주소
BROKER_PORT = 1883

# --- 토픽 정의 ---
ORDER_TOPIC = "bssm/wodnr"  # 주문을 받아오는 토픽
STOCK_TOPIC = "stock/topic"  # 재고 정보를 발행할 토픽

# --- 재고 상태 임시 저장 변수 ---
current_light_state = None
current_liquid_stock = None

# --- 시리얼 연결 초기화 ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # 아두이노 초기화 대기
    print("Arduino 시리얼 연결 성공.")
except serial.SerialException as e:
    print(f"시리얼 연결 실패: {e}")
    sys.exit(1)

# --- MQTT 콜백 함수 ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("MQTT 브로커 연결 성공.")
        client.subscribe(ORDER_TOPIC)
        print(f"'{ORDER_TOPIC}' 토픽 구독 시작.")
    else:
        print(f"MQTT 브로커 연결 실패: {reason_code}")
        sys.exit(1)

def on_message(client, userdata, msg):
    # 주문 토픽에서 메시지가 오면 처리
    if msg.topic == ORDER_TOPIC:
        try:
            data = json.loads(msg.payload.decode().strip())

            # 서보 모터 제어
            if "sugar" in data:
                command_to_arduino = "S" + str(data["sugar"])
                ser.write(command_to_arduino.encode())
                print(f"서보 제어 명령 아두이노로 전송 (설탕 주문): {command_to_arduino}")

            # 펌프 제어
            if "water" in data:
                command_to_arduino = "W" + str(data["water"])
                ser.write(command_to_arduino.encode())
                print(f"펌프 제어 명령 아두이노로 전송 (물 주문): {command_to_arduino}")
        except Exception as e:
            print(f"MQTT 메시지 처리 중 오류 발생: {e}")
    else:
        pass

# --- MQTT 클라이언트 설정 ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

# --- 브로커 연결 시도 ---
try:
    client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
except Exception as e:
    print(f"MQTT 연결 실패: {e}")
    sys.exit(1)

client.loop_start()
print("시스템 시작: MQTT 메시지 수신/발신 대기 중.")

# --- 메인 루프: 아두이노 시리얼 읽기 및 MQTT 발행 ---
try:
    while True:
        if ser.in_waiting > 0:
            arduino_data = ser.readline().decode('utf-8').strip()

            # 조도 센서 상태 업데이트
            if arduino_data.startswith("LIGHT_STATE:"):
                light_state = arduino_data.replace("LIGHT_STATE:", "").strip()
                if light_state in ["HIGH", "LOW"]:
                    current_light_state = light_state

            # 플로트 스위치 상태 업데이트
            elif arduino_data.startswith("FLOAT_STATE:"):
                float_state = arduino_data.replace("FLOAT_STATE:", "").strip()
                if float_state in ["EMPTY", "FULL"]:
                    current_liquid_stock = float_state

            # 두 센서 상태가 모두 업데이트되면 통합 JSON 발행
            if current_light_state is not None and current_liquid_stock is not None:
                combined_stock_json = {
                    "light_sensor": current_light_state,
                    "liquid_stock": current_liquid_stock
                }
                client.publish(STOCK_TOPIC, json.dumps(combined_stock_json))
                print(f"통합 재고 상태 MQTT 발행 ('{STOCK_TOPIC}'): {json.dumps(combined_stock_json)}")

                # 발행 후 상태 초기화
                current_light_state = None
                current_liquid_stock = None

        time.sleep(0.05)
except KeyboardInterrupt:
    print("프로그램 종료 요청.")
finally:
    client.loop_stop()
    client.disconnect()
    ser.close()
    print("연결 해제 및 프로그램 종료.")