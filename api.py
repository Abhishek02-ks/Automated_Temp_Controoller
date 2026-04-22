
import threading
import datetime
import math
import time
import json
import traceback

import numpy as np
import pandas as pd
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

app = Flask(__name__)
CORS(app)

SENSOR_ESP32_IP = "10.39.146.79"   # ESP32 with DHT22
FAN_ESP32_IP    = "10.39.146.232"   # ESP32 with relay on D5
REQUEST_TIMEOUT = 5                  # seconds

FEATURES = [
    "temperature",
    "hour_sin", "hour_cos",
    "month_sin", "month_cos",
    "temp_lag_1", "temp_lag_3",
    "temp_lag_6", "temp_lag_12", "temp_lag_24"
]

print("[API] Loading dataset for scaler ...")
df = pd.read_csv("final_saffron_temperature_dataset.csv")

LATEST_DATASET_TEMP = float(df["temperature"].iloc[-1])

scaler = MinMaxScaler()
scaler.fit(df[FEATURES])

print("[API] Loading LSTM model ...")
model = load_model("saffron_temperature_lstm_model.h5", compile=False)
model.compile(optimizer="adam", loss="mse")
print("[API] Model loaded OK.")

HYSTERESIS   = 0.5      
state_lock   = threading.Lock()
runtime = {
    "current_temp":    None,
    "humidity":        None,
    "predicted_temp":  None,
    "fan_state":       "unknown",
    "last_updated":    None,
    "sensor_online":   False,
    "history":         []
}

INTERNAL_REF_TEMP = 10.0

def build_input_vector(hour: int, day: int, month: int) -> np.ndarray:
 
    hour_sin  = math.sin(2 * math.pi * hour  / 24)
    hour_cos  = math.cos(2 * math.pi * hour  / 24)
    month_sin = math.sin(2 * math.pi * month / 12)
    month_cos = math.cos(2 * math.pi * month / 12)

    raw = np.array([[
        INTERNAL_REF_TEMP,
        hour_sin,  hour_cos,
        month_sin, month_cos,
        INTERNAL_REF_TEMP, INTERNAL_REF_TEMP,
        INTERNAL_REF_TEMP, INTERNAL_REF_TEMP,
        INTERNAL_REF_TEMP
    ]])

    scaled = scaler.transform(raw)
    return scaled.reshape(1, 1, scaled.shape[1])

def predict_temp(hour: int, day: int, month: int) -> float:
    inp = build_input_vector(hour, day, month)
    pred = model.predict(inp, verbose=0)
    
    inv = scaler.inverse_transform(
        np.concatenate([pred, np.zeros((1, len(FEATURES) - 1))], axis=1)
    )
    return float(inv[0][0])

def read_sensor():
    """Returns (temp, humidity) or (None, None) on failure."""
    try:
        r = requests.get(
            f"http://{SENSOR_ESP32_IP}/temperature",
            timeout=REQUEST_TIMEOUT
        )
        data = r.json()
        temp, humi = float(data["temperature"]), float(data["humidity"])
        
        return temp, humi
    except Exception as e:
        print(f"[Sensor] Error reading from {SENSOR_ESP32_IP}: {e}")
        return None, None

def send_fan_command(state: str) -> bool:
    """state: 'on' or 'off'. Returns True on success."""
    try:
        url = f"http://{FAN_ESP32_IP}/fan"
        r = requests.get(
            url,
            params={"state": state},
            timeout=REQUEST_TIMEOUT
        )
        success = r.status_code == 200
        if success:
            print(f"[Fan] Command '{state}' sent to {FAN_ESP32_IP} OK.")
        else:
            print(f"[Fan] FAILED to send '{state}' to {FAN_ESP32_IP}. Status: {r.status_code}")
        return success
    except Exception as e:
        print(f"[Fan] ERROR connecting to {FAN_ESP32_IP}: {e}")
        return False

def run_control_cycle():
    now = datetime.datetime.now()
    # 1. Read sensor
    current_temp, humidity = read_sensor()
    if current_temp is None:
        with state_lock:
            runtime["sensor_online"] = False
        return

    predicted = predict_temp(now.hour, now.day, now.month)
    
    with state_lock:
        current_fan = runtime["fan_state"]

    new_fan_state = current_fan
    
    if current_temp > (predicted + HYSTERESIS):
        new_fan_state = "on"
    elif current_temp < (predicted - HYSTERESIS):
        new_fan_state = "off"
    
    if new_fan_state != current_fan:
        send_fan_command(new_fan_state)
    
    # 4. Update State
    entry = {
        "time":          now.strftime("%H:%M"),
        "date":          now.strftime("%d-%m-%Y"),
        "current_temp":  round(current_temp, 2),
        "predicted_temp": round(predicted, 2),
        "humidity":      round(humidity, 2),
        "fan_state":     new_fan_state
    }

    with state_lock:
        runtime["current_temp"]   = round(current_temp, 2)
        runtime["humidity"]       = round(humidity, 2)
        runtime["predicted_temp"] = round(predicted, 2)
        runtime["fan_state"]      = new_fan_state
        runtime["last_updated"]   = now.isoformat()
        runtime["sensor_online"]  = True
        runtime["history"].append(entry)
        if len(runtime["history"]) > 24:
            runtime["history"] = runtime["history"][-24:]

    print(f"[Control] {now.strftime('%H:%M')} | Temp:{current_temp:.1f}C Pred:{predicted:.1f}C | Fan:{new_fan_state.upper()}")

def control_loop():
    print("[Thread] Real-time control loop started (5s interval).")
    while True:
        try:
            run_control_cycle()
        except Exception:
            traceback.print_exc()
        time.sleep(2)            

@app.route("/predict", methods=["GET"])
def predict_endpoint():
    """
    Manual prediction for UI Panel 1.
    Uses generic 'seed' values (no sensor dependence).
    Query params: hour (0-23), day (1-31), month (10-1)
    """
    now = datetime.datetime.now()
    try:
        hour  = int(request.args.get("hour",  now.hour))
        day   = int(request.args.get("day",   now.day))
        month = int(request.args.get("month", now.month))
    except ValueError:
        return jsonify({"error": "Invalid parameter. Use integers."}), 400

    predicted = predict_temp(hour, day, month)

    return jsonify({
        "hour":               hour,
        "day":                day,
        "month":              month,
        "predicted_temperature": round(predicted, 2)
    })


@app.route("/status", methods=["GET"])
def status_endpoint():
    """Return full runtime state for UI Panel 2."""
    with state_lock:
        snap = dict(runtime)
        snap["history"] = list(runtime["history"])
    return jsonify(snap)


@app.route("/control", methods=["GET"])
def control_endpoint():
    """Trigger an immediate control cycle."""
    try:
        run_control_cycle()
        with state_lock:
            snap = {
                "current_temp":    runtime["current_temp"],
                "predicted_temp":  runtime["predicted_temp"],
                "fan_state":       runtime["fan_state"],
                "last_updated":    runtime["last_updated"]
            }
        return jsonify({"status": "ok", **snap})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history_endpoint():
    with state_lock:
        return jsonify({"history": list(runtime["history"])})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "server": "saffron-temp-controller"})


if __name__ == "__main__":
    
    init_thread = threading.Thread(target=run_control_cycle, daemon=True)
    init_thread.start()

    
    bg = threading.Thread(target=control_loop, daemon=True)
    bg.start()

    print("[API] Flask server starting on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)