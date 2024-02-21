import time
from bluepy import btle
from paho.mqtt import client as mqtt_client
import yaml

def load_config(file_path):
    with open(file_path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

# Charger la configuration
config = load_config('config.yaml')

# Utiliser les valeurs du fichier YAML
broker_address = config['mqtt']['broker_address']
port = config['mqtt']['port']
topic = config['mqtt']['topic']
client_id = config['mqtt']['client_id']
mqtt_username = config['mqtt']['username']
mqtt_password = config['mqtt']['password']
device_address = config['ble']['device_address']
service_uuid = btle.UUID(config['ble']['service_uuid'])
characteristic_uuid = btle.UUID(config['ble']['characteristic_uuid'])


class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleNotification(self, cHandle, data):
        print("Data received:", data)
        # Les données reçues de BLE sont simplement imprimées et non publiées sur MQTT

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(topic)  # S'abonner au topic pour recevoir les messages
    else:
        print("Failed to connect, return code %d\n", rc)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Attempting to reconnect.")
        client.reconnect()

def on_message(client, userdata, msg):
    print(f"MQTT Message received: {msg.payload}")
    try:
        if dev is not None and ch is not None:
            ch.write(msg.payload)
            print("Data sent to BLE device")
    except Exception as e:
        print("Failed to send data to BLE device:", e)

def connect_to_mqtt():
    client = mqtt_client.Client(client_id)
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(broker_address, port)
    client.loop_start()
    return client

mqtt_client = connect_to_mqtt()

while True:
    try:
        print("Trying to connect to BLE device...")
        dev = btle.Peripheral(device_address)
        dev.setDelegate(MyDelegate())
        print("Connected to BLE device")
        
        svc = dev.getServiceByUUID(service_uuid)
        ch = svc.getCharacteristics(characteristic_uuid)[0]
        
        while True:
            if dev.waitForNotifications(1.0):
                continue  # handleNotification() a été appelé
            print("Waiting for notifications...")
    except btle.BTLEException as e:
        print(f"BLE connection error: {e}, trying to reconnect...")
        time.sleep(5)  # Attendre avant de retenter une connexion
    except KeyboardInterrupt:
        print("Disconnecting...")
        if dev:
            dev.disconnect()
        break
