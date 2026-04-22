#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

const char* SSID     = "realme 6";
const char* PASSWORD = "abhishek";

int pinList[] = {5, 18, 26, 27};
int pinCount = 4;

#define RELAY_ON       HIGH     
#define RELAY_OFF      LOW      

WebServer server(80);
String fanState = "off";

void setFan(bool turnOn) {
    int level = turnOn ? RELAY_ON : RELAY_OFF;
    for(int i=0; i<pinCount; i++) {
        digitalWrite(pinList[i], level);
    }
    fanState = turnOn ? "on" : "off";
    Serial.printf("[Fan] DigitalWrite %s to all pins (5, 18, 26, 27)\n", turnOn ? "ON" : "OFF");
}

void handleFan() {
    if (server.hasArg("state")) {
        String state = server.arg("state");
        state.toLowerCase();
        if (state == "on") setFan(true);
        else if (state == "off") setFan(false);
    }
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", "{\"fan\":\"" + fanState + "\"}");
}

void handleStatus() {
    String json = "{";
    json += "\"board\":\"fan_controller\",";
    json += "\"fan\":\"" + fanState + "\",";
    json += "\"active_pins\":\"5, 18, 26, 27\",";
    json += "\"logic\":\"Active-High\",";
    json += "\"uptime_ms\":" + String(millis());
    json += "}";
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", json);
}

void setup() {
    Serial.begin(115200);
    delay(500);

    // Init ALL candidate pins
    for(int i=0; i<pinCount; i++) {
        pinMode(pinList[i], OUTPUT);
        digitalWrite(pinList[i], RELAY_OFF);
    }
    
    Serial.println("[Fan] Hardware init complete. Triggering Pins: 5, 18, 26, 27");

    // Connect WiFi
    WiFi.begin(SSID, PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n[WiFi] Connected! IP: " + WiFi.localIP().toString());

    server.on("/fan", HTTP_GET, handleFan);
    server.on("/status", HTTP_GET, handleStatus);
    server.begin();
}

void loop() {
    server.handleClient();
}
