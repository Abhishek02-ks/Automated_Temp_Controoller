#include <WiFi.h>
#include <WebServer.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Yrealme 6";
const char* password = "abhishek";

WebServer server(80);

float temperature;

void sendTemperature() {

  temperature = dht.readTemperature();

  String json = "{\"temperature\":" + String(temperature) + "}";

  server.send(200,"application/json",json);
}

void setup() {

  Serial.begin(115200);
  dht.begin();

  WiFi.begin(ssid,password);

  while(WiFi.status()!=WL_CONNECTED){
    delay(1000);
  }

  Serial.println(WiFi.localIP());

  server.on("/temperature", sendTemperature);

  server.begin();
}

void loop() {
  server.handleClient();
}