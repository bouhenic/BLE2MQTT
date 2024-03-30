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

const int relayPin = 2; // Use the appropriate GPIO pin for your setup
const int soilPin = 1;

// Valeur du potentiomètre
int soilValue = 0;

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

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
            Serial.println(static_cast<int>(value[0])); // Print the integer value

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
  pinMode(soilPin,INPUT_PULLUP);

  // Create the BLE Device
  BLEDevice::init("MyBleDevice");

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pSensorCharacteristic = pService->createCharacteristic(
                      SENSOR_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ   |
                      BLECharacteristic::PROPERTY_WRITE  |
                      BLECharacteristic::PROPERTY_NOTIFY |
                      BLECharacteristic::PROPERTY_INDICATE
                    );

  // Create the ON button Characteristic
  pRelayCharacteristic = pService->createCharacteristic(
                      RELAY_CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_WRITE
                    );

  // Register the callback for the ON button characteristic
  pRelayCharacteristic->setCallbacks(new MyCharacteristicCallbacks());

  // https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.descriptor.gatt.client_characteristic_configuration.xml
  // Create a BLE Descriptor
  pSensorCharacteristic->addDescriptor(new BLE2902());
  pRelayCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(false);
  pAdvertising->setMinPreferred(0x0);  // set value to 0x00 to not advertise this parameter
  BLEDevice::startAdvertising();
  Serial.println("Waiting a client connection to notify...");
}

void loop() {
  if (deviceConnected) {
        pSensorCharacteristic->setValue(String(soilValue).c_str());
        pSensorCharacteristic->notify();
        soilValue = analogRead(soilPin);
        Serial.print("New value notified: ");
        Serial.println(soilValue);
        delay(6000); 
    }

    if (!deviceConnected && oldDeviceConnected) {
    Serial.println("Device disconnected. Preparing for restart.");
    delay(1000); // Délai pour permettre la fin de toutes les opérations en cours
    esp_restart(); // Redémarre l'ESP32
}
    if (deviceConnected && !oldDeviceConnected) {
        Serial.println("Device Connected");
        oldDeviceConnected = deviceConnected;
    }
}

// Déplacez la configuration initiale du BLE dans une fonction appelée `setupBLE()`
void setupBLE() {
    BLEDevice::init("MyBleDevice");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    BLEService *pService = pServer->createService(SERVICE_UUID);
    // Ajoutez les caractéristiques et les descripteurs comme dans `setup()`
    // ...
    pService->start();
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->start();
}


