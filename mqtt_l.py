import paho.mqtt.client as mqtt
import serial
import time
import sys
import json # JSON 처리를 위해 json 라이브러리 추가

# --- 시리얼 포트 설정 ---
SERIAL_PORT = "/dev/cu.usbserial-1120"  # 아두이노 포트로 변경 (사용자 설정)
BAUD_RATE = 9600  # 아두이노와 동일한 보드레이트 설정 (아두이노 코드와 일치해야 함)

# 시리얼 연결 초기화
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # 아두이노 초기화 대기 (필요 시 조절)
    print(f"Arduino에 시리얼 연결 성공: {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"시리얼 연결 실패: {e}")
    sys.exit(1) # 연결 실패 시 프로그램 종료

# --- MQTT 콜백 함수 ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("MQTT 브로커에 성공적으로 연결되었습니다!")
        client.subscribe("bssm/wodnr") # 구독할 토픽
        print("토픽 구독 시작: bssm/wodnr")
    else:
        print(f"MQTT 브로커 연결 실패, 에러 코드: {reason_code}")
        # 연결 실패 시 시리얼 포트 닫고 종료
        if ser and ser.is_open:
            ser.close()
        sys.exit(1)

def on_message(client, userdata, msg):
    # 메시지 수신 시 토픽과 원본 페이로드 출력
    raw_payload = msg.payload.decode().strip() # 수신된 메시지 디코딩 및 공백 제거
    print(f"\n--- MQTT 메시지 수신 ---")
    print(f"토픽: {msg.topic}")
    print(f"원본 메시지 (JSON): '{raw_payload}'")
    print(f"---------------------------\n")

    try:
        # JSON 문자열을 파싱
        # JSON 객체 형태 ({"key": value, ...})를 가정합니다.
        data = json.loads(raw_payload) 

        # 모든 키-값 쌍 콘솔에 출력
        print("JSON 데이터 파싱 완료:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print("---------------------------\n")

        # 'sugar' 키의 값만 아두이노로 전송
        if "sugar" in data:
            value_to_send = str(data["sugar"]) # 'sugar' 값을 문자열로 변환하여 전송
            try:
                ser.write(value_to_send.encode())  # 아두이노로 'sugar' 값 전송
                print(f"아두이노로 전송 완료 ('sugar' 값): '{value_to_send}'")
            except serial.SerialException as e:
                print(f"아두이노로 전송 실패: {e}")
        else:
            print("오류: JSON 데이터에 'sugar' 키가 없습니다. 아두이노로 보낼 값이 없습니다.")

    except json.JSONDecodeError as e:
        print(f"오류: JSON 파싱 실패 - {e}")
        print(f"수신된 메시지가 올바른 JSON 형식이 아닙니다: '{raw_payload}'")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")


# --- MQTT 클라이언트 설정 ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) 
client.on_connect = on_connect
client.on_message = on_message

# --- 브로커 연결 설정 ---
broker_address = "10.150.2.255"  # 원격 데스크톱 IP 주소 (사용자 설정)
port = 1883 # 기본 MQTT 포트

# (선택 사항) 만약 Mosquitto 브로커에 사용자명/비밀번호가 설정되어 있다면 아래 주석을 해제하고 입력하세요.
# client.username_pw_set("your_mosquitto_username", "your_mosquitto_password")

# 브로커에 연결 시도
try:
    print(f"MQTT 브로커 '{broker_address}:{port}'에 연결 시도 중...")
    client.connect(broker_address, port, 60)
except Exception as e:
    print(f"MQTT 연결 실패: {e}")
    if ser and ser.is_open:
        ser.close()
    sys.exit(1)

# --- 네트워크 루프 시작 및 프로그램 유지 ---
client.loop_start() 

print("MQTT 메시지 수신 대기 중입니다. 프로그램을 종료하려면 Ctrl+C를 누르세요.")

try:
    while True:
        # 아두이노에서 시리얼로 데이터를 보낸다면 여기서 읽을 수 있습니다.
        if ser.in_waiting > 0:
            arduino_data = ser.readline().decode('utf-8').strip()
            if arduino_data:
                print(f"아두이노로부터 수신: {arduino_data}")
        time.sleep(0.1) 
except KeyboardInterrupt:
    print("\n프로그램 종료 요청 감지. 연결을 해제합니다...")
finally:
    if client:
        client.loop_stop() 
        client.disconnect() 
        print("MQTT 클라이언트 연결 해제 완료.")
    if ser and ser.is_open:
        ser.close() 
        print("아두이노 시리얼 포트 닫기 완료.")
    print("프로그램이 종료되었습니다.")