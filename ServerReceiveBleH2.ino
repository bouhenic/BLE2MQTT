#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "esp_system.h"

BLEServer* pServer = NULL;
BLECharacteristic* pSensorCharacteristic = NULL;
BLECharacteristic* pRelayCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint32_t value = 0;

const int relayPin = 2; // Utilisez le GPIO approprié pour votre configuration
const int soilPin = 1;  // Capteur d'humidité du sol

// Valeur du capteur d'humidité du sol
int soilValue = 0;

// UUIDs pour les services et les caractéristiques
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define SENSOR_CHARACTERISTIC_UUID "beb5483d-36e1-4688-b7f5-ea07361b26a8"
#define RELAY_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
    }
};

class MyCharacteristicCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pRelayCharacteristic) {
        auto value = pRelayCharacteristic->getValue();
        if (value.length() > 0) {
            Serial.print("Characteristic event, written: ");
            Serial.println(static_cast<int>(value[0])); // Affiche la valeur entière

            int receivedValue = static_cast<int>(value[0]);
            if (receivedValue == 1) {
                digitalWrite(relayPin, HIGH);
                Serial.println("Trigger");
            } else {
                digitalWrite(relayPin, LOW);
                Serial.println("No trigger");                
            }
        }
    }
};

void setup() {
  Serial.begin(115200);
  pinMode(relayPin, OUTPUT);
  pinMode(soilPin, INPUT_PULLUP);

  // Création du dispositif BLE
  BLEDevice::init("MyBleDevice");

  // Création du serveur BLE
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Création du service BLE
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Création de la caractéristique du capteur de sol
  pSensorCharacteristic = pService->createCharacteristic(
                      SENSOR_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_WRITE  |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );

  // Ajout d'un descripteur de nom pour la caractéristique du capteur de sol
  BLEDescriptor pSensorCharacteristicNameDescriptor((uint16_t)0x2901);
  pSensorCharacteristicNameDescriptor.setValue("Capteur de Sol");
  pSensorCharacteristic->addDescriptor(&pSensorCharacteristicNameDescriptor);

  // Création de la caractéristique pour le relais
  pRelayCharacteristic = pService->createCharacteristic(
                      RELAY_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_WRITE
                    );

  // Ajout d'un descripteur de nom pour la caractéristique du relais
  BLEDescriptor pRelayCharacteristicNameDescriptor((uint16_t)0x2901);
  pRelayCharacteristicNameDescriptor.setValue("Relais");
  pRelayCharacteristic->addDescriptor(&pRelayCharacteristicNameDescriptor);

  // Enregistrement du rappel pour la caractéristique du relais
  pRelayCharacteristic->setCallbacks(new MyCharacteristicCallbacks());

  // Ajout de descripteurs BLE 2902 pour activer les notifications
  pSensorCharacteristic->addDescriptor(new BLE2902());
  pRelayCharacteristic->addDescriptor(new BLE2902());

  // Démarrage du service
  pService->start();

  // Démarrage de la publicité
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  
  BLEDevice::startAdvertising();
  Serial.println("En attente de connexion d'un client pour notifier...");
}

void loop() {
  if (deviceConnected) {
        pSensorCharacteristic->setValue(String(soilValue).c_str());
        pSensorCharacteristic->notify();
        soilValue = analogRead(soilPin);
        Serial.print("Nouvelle valeur notifiée: ");
        Serial.println(soilValue);
        delay(6000); 
    }

    if (!deviceConnected && oldDeviceConnected) {
    Serial.println("Appareil déconnecté. Préparation au redémarrage.");
    delay(1000);
    esp_restart(); // Redémarrage de l'ESP32
    }
    if (deviceConnected && !oldDeviceConnected) {
        Serial.println("Appareil connecté.");
        oldDeviceConnected = deviceConnected;
    }
}

