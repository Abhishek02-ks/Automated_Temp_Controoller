import requests
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import datetime
import time

# ----------------------------
# Load dataset
# ----------------------------
df = pd.read_csv("final_saffron_temperature_dataset.csv")

features = [
    "temperature",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "temp_lag_1",
    "temp_lag_3",
    "temp_lag_6",
    "temp_lag_12",
    "temp_lag_24"
]

data = df[features]

# Fit scaler
scaler = MinMaxScaler()
scaler.fit(data)

# Load trained LSTM model
model = load_model("saffron_temperature_lstm_model.h5")

# ESP32 address
SENSOR_ESP32 = "192.168.1.110"
FAN_ESP32 = "192.168.1.120"
print("AI Climate Control Started")

while True:

    # ----------------------------
    # Get current date and time
    # ----------------------------
    now = datetime.datetime.now()

    day = now.day
    month = now.month
    hour = now.hour

    print("\nCurrent Time:", now)

    # ----------------------------
    # Get current temperature from ESP32
    # ----------------------------
    try:
        response = requests.get(f"http://{ESP32_IP}/temperature")
        sensor_data = response.json()

        current_temp = sensor_data["temperature"]

    except:
        print("Sensor read failed")
        time.sleep(60)
        continue

    print("Current Temperature:", current_temp)

    # ----------------------------
    # Create cyclic features
    # ----------------------------
    hour_sin = np.sin(2*np.pi*hour/24)
    hour_cos = np.cos(2*np.pi*hour/24)

    month_sin = np.sin(2*np.pi*month/12)
    month_cos = np.cos(2*np.pi*month/12)

    # Use current temperature for lag inputs
    input_data = np.array([[
        current_temp,
        hour_sin,
        hour_cos,
        month_sin,
        month_cos,
        current_temp,
        current_temp,
        current_temp,
        current_temp,
        current_temp
    ]])

    # ----------------------------
    # Scale input
    # ----------------------------
    scaled = scaler.transform(input_data)
    scaled = scaled.reshape((1,1,scaled.shape[1]))

    # ----------------------------
    # Predict temperature
    # ----------------------------
    prediction = model.predict(scaled)

    predicted_temp = scaler.inverse_transform(
        np.concatenate([prediction,
                        np.zeros((1,len(features)-1))],axis=1)
    )[0][0]

    print("Predicted Temperature:", predicted_temp)

    # ----------------------------
    # AI Fan Control Decision
    # ----------------------------

    

    sensor = requests.get(f"http://{SENSOR_ESP32}/temperature").json()
    current_temp = sensor["temperature"]

    if predicted_temp > current_temp:
        requests.get(f"http://{FAN_ESP32}/fan?state=on")
    else:
        requests.get(f"http://{FAN_ESP32}/fan?state=off")

    # ----------------------------
    # Wait until next hour
    # ----------------------------
    print("Waiting for next hour...")

    time.sleep(3600)