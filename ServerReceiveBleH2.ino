#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

bool shouldAdvertise = true; // Indicateur pour contrôler la publicité

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        Serial.println("Client Connected");
        shouldAdvertise = false; // Arrêter la publicité lorsqu'un client est connecté
    }

    void onDisconnect(BLEServer* pServer) override {
        Serial.println("Client Disconnected");
        shouldAdvertise = true; // Indiquer que la publicité doit être redémarrée
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) override {
        auto value = pCharacteristic->getValue();

        Serial.print("Received Value: ");
        for (size_t i = 0; i < value.length(); i++) {
            Serial.print((char)value[i]);
        }
        Serial.println();

        if (value == "arrosage") {
            Serial.println("Activating pin 2 for irrigation!");
            digitalWrite(2, HIGH);
        } else if (value == "stop") {
            Serial.println("Deactivating pin 2.");
            digitalWrite(2, LOW);
        } else {
            Serial.println("Bad order");
        }
    }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE work!");

  pinMode(2, OUTPUT); // Configure le pin 2 comme sortie
  digitalWrite(2, LOW); // Initialise le pin 2 à l'état bas

  BLEDevice::init("MyBleDevice");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks()); // Enregistrer les callbacks de serveur

  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                          CHARACTERISTIC_UUID,
                                          BLECharacteristic::PROPERTY_READ |
                                          BLECharacteristic::PROPERTY_WRITE);

  pCharacteristic->setCallbacks(new MyCallbacks());
  pCharacteristic->setValue("Hello World says Neil");
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("Characteristic defined! Now you can read it in your phone!");
}

void loop() {
  // Vérifie si la publicité doit être redémarrée
  if (shouldAdvertise) {
      BLEDevice::startAdvertising(); // Redémarre directement la publicité
      Serial.println("Restarting advertising...");
  }
  delay(1000); // Attente passive et laisse les callbacks BLE gérer les données.
}



