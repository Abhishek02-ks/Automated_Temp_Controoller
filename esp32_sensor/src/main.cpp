#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DHT.h>

const char* SSID     = "realme 6";
const char* PASSWORD = "abhishek";

#define DHTPIN  4          
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

float lastTemperature = 0.0;
float lastHumidity    = 0.0;
unsigned long lastRead = 0;
const unsigned long READ_INTERVAL = 2000UL;  

void readSensor() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
        lastTemperature = t;
        lastHumidity    = h;
        Serial.printf("[Sensor] Temp: %.2f °C  |  Humidity: %.2f %%\n", t, h);
    } else {
        Serial.println("[Sensor] WARNING: Read failed, using cached value.");
    }
}

void handleTemperature() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t)) lastTemperature = t;
    if (!isnan(h)) lastHumidity    = h;
    String json = "{";
    json += "\"temperature\":" + String(lastTemperature, 2) + ",";
    json += "\"humidity\":"    + String(lastHumidity, 2);
    json += "}";
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", json);
}

void handleStatus() {
    String json = "{";
    json += "\"board\":\"sensor\",";
    json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
    json += "\"uptime_ms\":" + String(millis()) + ",";
    json += "\"last_temp\":" + String(lastTemperature, 2) + ",";
    json += "\"last_humidity\":" + String(lastHumidity, 2);
    json += "}";
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", json);
}

void handleNotFound() {
    server.send(404, "application/json", "{\"error\":\"Not found\"}");
}

void setup() {
    Serial.begin(115200);
    delay(500);

    dht.begin();
    Serial.println("[Sensor] DHT22 initialised.");

    Serial.printf("[WiFi] Connecting to %s ", SSID);
    WiFi.begin(SSID, PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(10);
        Serial.print(".");
    }
    Serial.println();
    Serial.printf("[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());

    delay(2000);
    readSensor();

    server.on("/temperature", HTTP_GET, handleTemperature);
    server.on("/status",      HTTP_GET, handleStatus);
    server.onNotFound(handleNotFound);
    server.begin();
    Serial.println("[HTTP] Server started on port 80");
}

void loop() {
    server.handleClient();
    if (millis() - lastRead >= READ_INTERVAL) {
        lastRead = millis();
        readSensor();
    }
}
