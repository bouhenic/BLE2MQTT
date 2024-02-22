import asyncio
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt
import threading
import yaml  # Assurez-vous d'avoir installé pyyaml

# Charger la configuration à partir du fichier YAML
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

MQTT_BROKER = config['mqtt']['broker']
MQTT_PORT = config['mqtt']['port']
MQTT_TOPIC_SENSOR = config['mqtt']['topic_sensor']
MQTT_TOPIC_LED_COMMAND = config['mqtt']['topic_led_command']

DEVICE_NAME = config['ble']['device_name']
SENSOR_CHARACTERISTIC_UUID = config['ble']['sensor_characteristic_uuid']
LED_CHARACTERISTIC_UUID = config['ble']['led_characteristic_uuid']

ble_client = None
exit_event = asyncio.Event()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code", rc)
    client.subscribe(MQTT_TOPIC_LED_COMMAND)

async def handle_mqtt_message(client, userdata, message):
    print(f"MQTT Message Received: {message.payload}")
    if ble_client and ble_client.is_connected:
        try:
            led_value = int(message.payload.decode())
            print(f"Setting LED to {led_value}")
            await ble_client.write_gatt_char(LED_CHARACTERISTIC_UUID, bytes([led_value]))
        except Exception as e:
            print(f"Error writing to LED characteristic: {e}")

def setup_mqtt(loop):
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = lambda c, u, m: asyncio.run_coroutine_threadsafe(handle_mqtt_message(c, u, m), loop)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    return mqtt_client

async def run_ble_client():
    global ble_client
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == DEVICE_NAME:
            ble_client = BleakClient(device.address)
            await ble_client.connect()
            print(f"Connected to BLE device: {ble_client.is_connected}")
            break
    else:
        print(f"Device {DEVICE_NAME} not found.")
        exit_event.set()

def user_input_thread():
    input("Press 'Enter' to quit...\n")
    exit_event.set()

async def main():
    loop = asyncio.get_running_loop()
    
    mqtt_client = setup_mqtt(loop)
    threading.Thread(target=user_input_thread, daemon=True).start()
    
    await run_ble_client()
    await exit_event.wait()

    if ble_client and ble_client.is_connected:
        await ble_client.disconnect()
        print("Disconnected from BLE device.")

    mqtt_client.disconnect()
    print("Disconnected from MQTT broker.")

if __name__ == "__main__":
    asyncio.run(main())
