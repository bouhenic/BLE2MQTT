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
        # Ici, les données reçues de BLE sont simplement imprimées et non 
publiées sur MQTT

# Callback appelé lors de la connexion au broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(topic)  # S'abonner au topic pour recevoir les 
messages
    else:
        print("Failed to connect, return code %d\n", rc)

# Callback pour gérer les messages MQTT entrants
def on_message(client, userdata, msg):
    print(f"MQTT Message received: {msg.payload}")
    # Écrire les données reçues sur la caractéristique BLE
    try:
        ch.write(msg.payload)
        print("Data sent to BLE device")
    except Exception as e:
        print("Failed to send data to BLE device:", e)

# Configuration du client MQTT
client = mqtt_client.Client(client_id)
client.username_pw_set(mqtt_username, mqtt_password)  # Commenter si 
l'authentification n'est pas requise
client.on_connect = on_connect
client.on_message = on_message  # Définir la fonction de callback pour les 
messages MQTT
client.connect(broker_address, port)
client.loop_start()

# Connexion au dispositif BLE
device_address = "48:31:B7:C0:35:0B"
print("Connecting to BLE device...")
dev = btle.Peripheral(device_address)
dev.setDelegate(MyDelegate())

# Obtenir le service et la caractéristique BLE
service_uuid = btle.UUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b")
characteristic_uuid = btle.UUID("beb5483e-36e1-4688-b7f5-ea07361b26a8")
svc = dev.getServiceByUUID(service_uuid)
ch = svc.getCharacteristics(characteristic_uuid)[0]
print("Connected and waiting for data from MQTT...")

# Boucle principale inutile car la réception et l'envoi de données sont 
gérés par les callbacks
while True:
    time.sleep(1)  # Cette boucle maintient le script en exécution

