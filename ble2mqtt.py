import asyncio
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt
import threading
import yaml

# Charger la configuration à partir du fichier YAML
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configuration MQTT
MQTT_BROKER = config['mqtt']['broker']
MQTT_PORT = config['mqtt']['port']
MQTT_TOPIC_SENSOR = config['mqtt']['topic_sensor']
MQTT_TOPIC_LED_COMMAND = config['mqtt']['topic_led_command']

# Configuration BLE
DEVICE_NAME = config['ble']['device_name']
SENSOR_CHARACTERISTIC_UUID = config['ble']['sensor_characteristic_uuid']
LED_CHARACTERISTIC_UUID = config['ble']['led_characteristic_uuid']

ble_client = None
mqtt_client = None
exit_event = asyncio.Event()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code", rc)
    client.subscribe(MQTT_TOPIC_LED_COMMAND)

async def handle_mqtt_message(client, userdata, message):
    global ble_client
    if message.topic == MQTT_TOPIC_LED_COMMAND and ble_client is not None:
        try:
            led_value = int(message.payload.decode())
            print(f"Setting LED to {led_value}")
            await ble_client.write_gatt_char(LED_CHARACTERISTIC_UUID, bytes([led_value]))
        except Exception as e:
            print(f"Error writing to LED characteristic: {e}")

def setup_mqtt(loop):
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = lambda c, u, m: asyncio.run_coroutine_threadsafe(handle_mqtt_message(c, u, m), loop)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    return mqtt_client

async def sensor_data_handler(sender, data):
    global mqtt_client
    # Convertit le bytearray en chaîne et le publie
    value_str = data.decode('utf-8')  # Conversion des données en chaîne de caractères
    print(f"Sensor data received: {value_str}")
    mqtt_client.publish(MQTT_TOPIC_SENSOR, value_str)

async def run_ble_client():
    global ble_client
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == DEVICE_NAME:
            ble_client = BleakClient(device.address)
            await ble_client.connect()
            print(f"Connected to BLE device: {ble_client.is_connected}")

            # Souscrire aux notifications de la caractéristique du capteur
            await ble_client.start_notify(SENSOR_CHARACTERISTIC_UUID, sensor_data_handler)

            # Attendre l'événement de sortie
            await exit_event.wait()

            # Se désabonner des notifications avant de se déconnecter
            await ble_client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
            await ble_client.disconnect()
            print("Disconnected from BLE device.")
            break
    else:
        print(f"Device {DEVICE_NAME} not found.")
        exit_event.set()

def user_input_thread():
    input("Press 'Enter' to quit...\n")
    exit_event.set()

async def main():
    loop = asyncio.get_running_loop()

    setup_mqtt(loop)
    threading.Thread(target=user_input_thread, daemon=True).start()

    await run_ble_client()

    if mqtt_client is not None:
        mqtt_client.disconnect()
        print("Disconnected from MQTT broker.")

if __name__ == "__main__":
    asyncio.run(main())

