# Smart Saffron: AI-Integrated IoT Temperature Control

**Smart Saffron** is an AI-integrated Internet of Things (IoT) system designed for real-time temperature prediction and automated climate control in saffron cultivation. 

Saffron (*Crocus sativus* L.) yield and quality are critically sensitive to ambient temperature. This project combines distributed sensing, deep learning-based forecasting, and autonomous actuation to maintain optimal growing conditions.

## 🚀 Key Features
- **AI-Driven Control**: Uses a stacked **LSTM (Long Short-Term Memory)** neural network for high-precision temperature forecasting.
- **Distributed IoT Architecture**: Deploys multi-node ESP32 microcontrollers for sensing (DHT22) and actuation (Relay-controlled fan).
- **Edge Analytics**: A Python Flask backend implements a hysteresis-based closed-loop control system with predictive setpoints.
- **Predictive Performance**: The model achieves an **MAE of 0.3523°C** and an **R² of 0.9920**, providing industry-leading climate regulation.
- **Real-Time Monitoring**: Includes a modern web-based dashboard for live temperature tracking and system status.
- **Cost-Effective & Local**: Built for under $20 USD in hardware and operates fully offline without cloud dependencies.

## 🛠️ Tech Stack
- **Firmware**: C++ (Arduino/PlatformIO) on ESP32
- **Backend**: Python, Flask, TensorFlow/Keras, NumPy, Pandas
- **Frontend**: HTML5, Vanilla JavaScript, CSS3
- **ML Model**: LSTM Time-Series Forecasting
- **Hardware**: ESP32, DHT22 Sensor, 12V DC Fan, 4-Channel Relay

## 📊 Performance
The system was evaluated on a dataset of saffron-growing microclimates:
- **MAE**: 0.3523°C
- **RMSE**: 0.4960°C
- **R²**: 0.9920

## 📂 Project Structure
- `/api.py`: RESTful backend and control logic.
- `/Lstm_prediction.py`: Neural network training and feature engineering.
- `/esp32_sensor/`: Firmware for the environmental sensing node.
- `/esp32_fan/`: Firmware for the fan actuation node.
- `/index.html`: Web dashboard for real-time visualization.
- `/research_paper.md`: Full documentation of the system's design and results.

---
*Developed for AI-driven precision agriculture.*
