import time
from bluepy import btle
from paho.mqtt import client as mqtt_client

broker_address = "localhost"
port = 1883
topic = "your/topic"
client_id = "your_client_id"
# Si votre broker MQTT requiert une authentification
mqtt_username = "your_username"
mqtt_password = "your_password"

class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleNotification(self, cHandle, data):
        print("Data received:", data)
        # Ici, les données reçues de BLE sont simplement imprimées et non publiées sur MQTT

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(topic)  # S'abonner au topic pour recevoir les messages
    else:
        print("Failed to connect, return code %d\n", rc)

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
    client.on_message = on_message
    client.connect(broker_address, port)
    client.loop_start()
    return client

mqtt_client = connect_to_mqtt()

while True:
    try:
        device_address = "48:31:B7:C0:35:0B"
        print("Trying to connect to BLE device...")
        dev = btle.Peripheral(device_address)
        dev.setDelegate(MyDelegate())
        print("Connected to BLE device")
        
        service_uuid = btle.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
        characteristic_uuid = btle.UUID("beb5483e-36e1-4688-b7f5-ea07361b26a8")
        svc = dev.getServiceByUUID(service_uuid)
        ch = svc.getCharacteristics(characteristic_uuid)[0]
        
        while True:
            if dev.waitForNotifications(1.0):
                # handleNotification() a été appelé
                continue
            print("Waiting for notifications...")
    except btle.BTLEException as e:
        print(f"BLE connection error: {e}, trying to reconnect...")
        time.sleep(5)  # Attendre avant de retenter une connexion
    except KeyboardInterrupt:
        print("Disconnecting...")
        dev.disconnect()
        break

