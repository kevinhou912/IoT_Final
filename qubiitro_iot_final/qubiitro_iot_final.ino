#include <M5StickCPlus.h>
#include <QubitroMqttClient.h>
#include <WiFi.h>
#include <Wire.h>

WiFiClient wifiClient;
QubitroMqttClient mqttClient(wifiClient);

// Temperature index
float cTemp    = 0;
float fTemp    = 0;
float humidity = 0;

// Device Parameters
char deviceID[] = "148ee57d-2e50-4f1a-8cfb-1a562f188697";
char deviceToken[] = "bgsJy7t9YK2crFizTUZS5cepEciQiKtsoT4XKP4S";

// WiFi Parameters

const char* ssid = "Wifi-name";
const char* password = "Wifi password";


void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  M5.Lcd.println();
  M5.Lcd.print("Connecting to ");
  M5.Lcd.println(ssid);

  //WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
  }
  M5.Lcd.println("");
  M5.Lcd.println("WiFi connected");
  M5.Lcd.println("IP address: ");
  M5.Lcd.println(WiFi.localIP());
}

void setup() {
    M5.begin();
    Wire.begin(0,26);
    setup_wifi();
  
    qubitro_init();
    M5.Lcd.setRotation(3);
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setCursor(0, 0, 4);
}

void qubitro_init() {
  char host[] = "broker.qubitro.com";
  int port = 1883;
  mqttClient.setId(deviceID);
  mqttClient.setDeviceIdToken(deviceID, deviceToken);
  M5.Lcd.println("Connecting to Qubitro...");
  if (!mqttClient.connect(host, port)){
    M5.Lcd.print("Connection failed. Error code: ");
    M5.Lcd.println(mqttClient.connectError());
    M5.Lcd.println("Visit docs.qubitro.com or create a new issue on github.com/qubitro");
  }
  M5.Lcd.println("Connected to Qubitro.");
  mqttClient.subscribe(deviceID);
  delay(5000);
}

float *temp_cal(){
  unsigned int data[6];
  float *result = new float[2];
  // Start I2C Transmission
  Wire.beginTransmission(0x44);
  // Send measurement command
  Wire.write(0x2C);
  Wire.write(0x06);
  // Stop I2C transmission
  if (Wire.endTransmission() != 0){
    Serial.println("ERROR -- endTransmission Error!");
  }
  else{
    delay(500);
    // Request 6 bytes of data
    Wire.requestFrom(0x44, 6);

    // Read 6 bytes of data
    // cTemp msb, cTemp lsb, cTemp crc, humidity msb, humidity lsb, humidity crc
    for (int i = 0; i < 6; i++) {
      data[i] = Wire.read();
    };
    delay(50);

    if (Wire.available() != 0){
      Serial.println("ERROR -- Wire.available still has data!");
    }
    else{
      // Convert the data
      cTemp    = ((((data[0] * 256.0) + data[1]) * 175) / 65535.0) - 45;
      fTemp    = (cTemp * 1.8) + 32;
      humidity = ((((data[3] * 256.0) + data[4]) * 100) / 65535.0);
      Serial.print("celsius: ");
      Serial.println(cTemp);
      M5.Lcd.setCursor(0, 30, 2);
      M5.Lcd.printf("Temp: %2.1f Humi: %2.0f", cTemp, humidity);
      M5.Lcd.println(" ");
    }
  }
  result[0] = cTemp;
  result[1] = humidity;
  return result;
}

void loop() {
  M5.update();

  float *temp_data = temp_cal();
  float temp = temp_data[0];
  float humidity = temp_data[1];
  mqttClient.poll();
  // int number = random(0, 40);
  static char payload[256];


  snprintf(payload, sizeof(payload)-1, "{\"temp\":%f , \"humidity\" :%f}", temp, humidity);
  mqttClient.beginMessage(deviceID);
  mqttClient.print(payload); 
  mqttClient.endMessage();  
  M5.Lcd.print("Publishing new data-> ");
  M5.Lcd.println(payload);
  
  delete[] temp_data;
  delay(1000);

}
