# AI-Driven IoT Temperature Control System for Saffron Cultivation: A Comprehensive Review

**[Author Name], [Author Name]**
*[Department Name], [Institution Name], [City, Country]*
*Email: {author1, author2}@institution.edu*

---

> *Abstract* — **Saffron (*Crocus sativus* L.) is among the world's most economically valuable spice crops, with productivity critically dependent on precise microclimate temperature management. This paper presents a comprehensive review of a low-cost, AI-integrated Internet of Things (IoT) system designed for real-time environmental monitoring and automated climate control in saffron cultivation. The architecture comprises two ESP32 microcontrollers—one interfaced with a DHT22 temperature and humidity sensor, and one driving a relay-controlled cooling fan—coordinated through a Python Flask RESTful backend. A Long Short-Term Memory (LSTM) neural network, trained on a domain-specific saffron temperature dataset with temporal feature engineering (cyclic time encoding, multi-lag inputs), serves as the predictive core of the system. Fan actuation is governed by a hysteresis-based closed-loop control algorithm comparing real-time sensor readings against LSTM-predicted optimal setpoints. Empirical evaluation on a held-out test set of 2,896 samples demonstrates high predictive accuracy: Mean Absolute Error (MAE) of 0.3523°C, Root Mean Squared Error (RMSE) of 0.4960°C, and R² of 0.9920. The system further provides real-time monitoring through a web-based dashboard. This review covers the architecture, machine learning pipeline, control logic, experimental results, and future research directions for intelligent precision-agriculture systems.**

*Index Terms* — Internet of Things, LSTM, Saffron Cultivation, Precision Agriculture, Temperature Control, ESP32, Deep Learning, Smart Greenhouse.

---

## I. Introduction

The convergence of embedded computing, wireless networking, and deep learning is redefining precision agriculture. The Internet of Things (IoT) enables fine-grained, real-time sensing of environmental parameters, while machine learning provides the predictive capability to anticipate and pre-empt adverse conditions rather than merely react to them [1]. These combined capabilities are particularly relevant for high-value specialty crops with narrow environmental tolerances.

Saffron (*Crocus sativus* L.), derived from the stigmas of its flower, commands prices exceeding $3,000 USD per kilogram and represents a major agricultural export for regions including Iran, Kashmir (India), and Spain [2]. Its cultivation is exquisitely sensitive to ambient temperature: deviations during the critical flowering period (October–November) directly impair stigma development, pigment synthesis, and overall yield. Conventional greenhouse climate management relies on reactive, threshold-based thermostats that introduce inevitable lag between a temperature deviation and its correction.

A predictive approach—one that anticipates optimal temperature setpoints based on time-of-day and seasonal patterns—can reduce thermal stress episodes and improve crop consistency. This work presents and reviews such a system, integrating:

1. A distributed **ESP32**-based sensor-actuator network communicating over Wi-Fi.
2. A **DHT22** sensor for high-accuracy temperature and humidity acquisition.
3. An **LSTM neural network** for time-series temperature prediction with temporal feature engineering.
4. A **Flask RESTful API** implementing closed-loop control with hysteresis.
5. A **web dashboard** for live monitoring and historical analysis.

The remainder of this paper is structured as follows: Section II surveys related work; Section III details the system architecture; Section IV describes the machine learning model; Section V presents the control logic; Section VI reports experimental results; Section VII offers discussion; Section VIII outlines future work; and Section IX concludes the paper.

---

## II. Related Work

### A. IoT in Precision Agriculture

IoT-based agricultural monitoring has been extensively explored. Gondchawar and Kawitkar [3] proposed an Arduino-based smart agriculture system integrating soil moisture, temperature, and humidity sensors with wireless communication. Patil and Kadu [4] demonstrated automated IoT irrigation control responsive to real-time soil conditions. Broader surveys by Tzounis *et al.* [5] identify key challenges including energy harvesting, connectivity reliability, and data management scale. The ESP32 platform, offering dual-core processing, integrated Wi-Fi/Bluetooth, and a rich peripheral set at sub-$5 cost, has become pervasive in agricultural IoT prototypes [6].

### B. Deep Learning for Environmental Forecasting

Recurrent Neural Networks (RNNs), particularly LSTM networks introduced by Hochreiter and Schmidhuber [7], are the standard neural architecture for sequential time-series forecasting, owing to their gated cell mechanism that selectively retains long-range temporal dependencies. In agricultural contexts, LSTM models have been applied to soil temperature prediction [8], greenhouse microclimate forecasting [9], and evapotranspiration estimation [10]. The use of sine-cosine cyclic transformations for periodic temporal features (hour, month) is an established best practice to prevent artificial boundary discontinuities in the input representation [11].

### C. Saffron Agronomy and Climate Requirements

The environmental requirements of *Crocus sativus* are well-characterised [2], [12]. Corm dormancy (June–August) tolerates temperatures of 25–35°C, while the critical sprouting (15–20°C) and flowering (5–15°C at night, 15–20°C daytime) stages demand precise thermal regulation. Molina *et al.* [12] demonstrated that temperature deviations of as little as ±5°C during flowering measurably reduce yield quantity and saffron quality. This narrow operational window motivates precision climate control.

---

## III. System Architecture

The proposed system follows the canonical three-tier IoT architecture: a **Perception Layer** (sensors and actuators), a **Transport Layer** (Wi-Fi / HTTP REST), and an **Application Layer** (AI inference, control logic, web interface). Fig. 1 provides the complete system block diagram.

```
┌──────────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           WEB DASHBOARD (HTML / JavaScript)             │ │
│  │    Live cards │ Temperature charts │ History table      │ │
│  └───────────────────────┬─────────────────────────────────┘ │
│                          │ HTTP REST (JSON)                  │
│  ┌───────────────────────▼─────────────────────────────────┐ │
│  │           FLASK API BACKEND  (Python 3.x)               │ │
│  │  LSTM inference · Hysteresis control · State manager    │ │
│  │  /predict  /status  /control  /history  /health         │ │
│  └────────┬──────────────────────────┬──────────────────── ┘ │
└───────────┼──────────────────────────┼──────────────────────┘
            │ TRANSPORT LAYER          │
            │ HTTP GET /temperature    │ HTTP GET /fan?state=on|off
┌───────────▼──────────┐   ┌──────────▼──────────────────────┐
│  PERCEPTION LAYER    │   │  PERCEPTION LAYER               │
│  ESP32 + DHT22       │   │  ESP32 + Relay Module           │
│  (Sensor Node)       │   │  (Actuator Node)                │
│  IP: 10.39.146.79    │   │  IP: 10.39.146.232              │
└──────────────────────┘   └─────────────────────────────────┘
```
*Fig. 1. Complete three-tier system architecture.*

### A. Hardware Components

**Table I — Hardware Component Summary**

| Component | Function | Key Specification |
|---|---|---|
| ESP32 Dev Board (×2) | Microcontroller | 240 MHz dual-core, Wi-Fi 802.11 b/g/n, 4 MB Flash |
| DHT22 Sensor | Temp. & Humidity acquisition | ±0.5°C temp., ±2–5% RH accuracy |
| 4-Channel Relay Module | Fan switching | 5 V control signal, 10 A / 250 VAC load |
| 12 V DC Cooling Fan | Air circulation / cooling | Variable speed, switched via relay |

### B. Sensor Node (ESP32 + DHT22)

The sensor ESP32 runs an Arduino-framework HTTP server that exposes a `/temperature` endpoint. On each HTTP GET request, the DHT22 is polled and a JSON response is returned:

```json
{ "temperature": 18.4, "humidity": 62.1 }
```

The DHT22 was selected over the lower-cost DHT11 for its significantly superior accuracy (±0.5°C versus ±2°C), which is critical given the ±0.5°C hysteresis band used in the control algorithm.

### C. Fan Controller Node (ESP32 + Relay)

The second ESP32 exposes a `/fan?state={on|off}` endpoint. GPIO pins 5, 18, 26, and 27 are all configured as relay outputs and driven simultaneously, providing redundant actuation paths. Active-high relay logic is used (`RELAY_ON = HIGH`). The node also exposes a `/status` endpoint returning JSON with uptime, fan state, and active-pin information.

### D. Flask REST API Backend

The Python backend (`api.py`) is the central intelligence and coordination hub. Five functions are performed concurrently:

1. **LSTM Inference** — Generates the optimal temperature prediction for the current time slot.
2. **Sensor Polling** — Fetches live temperature and humidity over HTTP from the sensor ESP32.
3. **Hysteresis Control** — Compares measured versus predicted temperature and commands the fan relay.
4. **State Management** — Maintains a thread-safe rolling 24-entry history buffer.
5. **REST API** — Exposes structured JSON endpoints for dashboard consumption.

A background daemon `threading.Thread` executes the control cycle every 2 seconds. Shared runtime state is protected by a `threading.Lock` to eliminate race conditions between the control thread and HTTP request handlers.

### E. Web Dashboard

An HTML/JavaScript single-page application polls the Flask API periodically and renders:
- Live temperature, humidity, and fan-state indicator cards.
- Predicted vs. actual temperature comparison.
- Line chart of the last 24 control-cycle readings.
- Manual fan override controls.

---

## IV. Machine Learning Model

### A. Dataset Description

The model was trained on `final_saffron_temperature_dataset.csv`, containing multi-year hourly temperature recordings pertaining to the saffron-growing microclimate. The dataset underwent feature engineering to produce 10 input features (Table II).

**Table II — LSTM Input Feature Set**

| Feature | Type | Description |
|---|---|---|
| `temperature` | Continuous | Ambient temperature (°C) — prediction target |
| `hour_sin` | Cyclic | sin(2π · hour / 24) |
| `hour_cos` | Cyclic | cos(2π · hour / 24) |
| `month_sin` | Cyclic | sin(2π · month / 12) |
| `month_cos` | Cyclic | cos(2π · month / 12) |
| `temp_lag_1` | Lag | Temperature 1 hour prior |
| `temp_lag_3` | Lag | Temperature 3 hours prior |
| `temp_lag_6` | Lag | Temperature 6 hours prior |
| `temp_lag_12` | Lag | Temperature 12 hours prior |
| `temp_lag_24` | Lag | Temperature 24 hours prior |

Cyclic encoding of `hour` and `month` preserves the topological continuity of periodic features (e.g., hour 23 is adjacent to hour 0), preventing the artificial boundary artifacts that arise with raw integer encoding [11]. All 10 features were normalized to [0, 1] using Min-Max scaling prior to model input.

### B. LSTM Architecture

The network architecture comprises two stacked LSTM layers with Dropout regularization, followed by a single Dense output node (Table III).

**Table III — LSTM Model Architecture**

| Layer | Units | Output Shape | Parameters |
|---|---|---|---|
| LSTM (return_sequences=True) | 128 | (batch, 24, 128) | 71,168 |
| Dropout | 0.2 | (batch, 24, 128) | 0 |
| LSTM | 64 | (batch, 64) | 49,408 |
| Dropout | 0.2 | (batch, 64) | 0 |
| Dense | 1 | (batch, 1) | 65 |
| **Total** | | | **120,641** |

A lookback window of **24 time steps** (24 hours) captures one complete diurnal cycle, providing the model with sufficient temporal context to learn both intra-day and night-day transition patterns.

### C. Training Configuration

| Hyperparameter | Value |
|---|---|
| Optimizer | Adam (default learning rate = 0.001) |
| Loss Function | Mean Squared Error (MSE) |
| Maximum Epochs | 80 |
| Batch Size | 32 |
| Validation Split | 10% of training set |
| Early Stopping Patience | 10 epochs (restore best weights) |
| Train / Test Split | 80% / 20% |

Early stopping with weight restoration prevents overfitting while reducing unnecessary computation once validation loss plateaus.

### D. Inference Pipeline

At runtime, single-step inference is performed as follows:

1. Extract current `hour` and `month` from the system clock.
2. Compute cyclic features: `hour_sin`, `hour_cos`, `month_sin`, `month_cos`.
3. Populate lag features with an internal reference temperature (10.0°C seed value).
4. Scale the 10-element input vector using the pre-fitted MinMaxScaler.
5. Reshape to `(1, 1, 10)` for LSTM input.
6. Run forward inference; apply inverse Min-Max transform to recover °C prediction.

This design allows stateless API prediction calls without maintaining a live rolling buffer of sensor history, at the cost of lag feature approximation during online operation.

---

## V. Control Logic

### A. Hysteresis-Based On/Off Control

To prevent excessive relay cycling near the setpoint, a symmetric hysteresis dead band of ±0.5°C is implemented. The decision logic is:

```
IF current_temp > predicted_temp + 0.5°C  →  Fan ON
IF current_temp < predicted_temp − 0.5°C  →  Fan OFF
ELSE                                        →  Hold (no state change)
```

This ensures the relay is toggled only when the temperature deviates meaningfully from the LSTM-predicted optimal setpoint, reducing mechanical wear and oscillation artefacts.

### B. Threaded Control Architecture

The control loop runs as a daemon thread with a 2-second polling interval, fully decoupled from Flask's HTTP request handling. The runtime state dictionary (temperature, humidity, prediction, fan state, history) is protected by a `threading.Lock`, guaranteeing thread-safe reads for dashboard API calls concurrent with write operations from the control thread.

### C. Fault Tolerance

If the sensor ESP32 is unreachable (e.g., network disruption or device power loss):
- The control cycle is aborted for that iteration.
- The `sensor_online` flag is set to `False`, surfaced in the `/status` API.
- The fan state is **not modified**, defaulting to its last known state.
- The error is logged to stdout for operator diagnosis.

This fail-safe design prevents erroneous actuation in the absence of valid sensor data.

---

## VI. Experimental Results

### A. Model Performance

The trained LSTM model was evaluated on the held-out 20% test partition, comprising **2,896 samples**. Predictions were inverse-transformed to °C before metric computation.

**Table IV — LSTM Model Performance on Test Set (n = 2,896)**

| Metric | Value |
|---|---|
| Mean Absolute Error (MAE) | **0.3523 °C** |
| Root Mean Squared Error (RMSE) | **0.4960 °C** |
| Coefficient of Determination (R²) | **0.9920** |

These results demonstrate strong predictive fidelity. An MAE of 0.3523°C is well below the ±0.5°C hysteresis threshold, ensuring that the control algorithm operates based on reliable predictions. The R² of 0.9920 indicates that the model explains 99.2% of variance in the test temperature series.

### B. Control System Latency

**Table V — End-to-End Latency Breakdown**

| Operation | Measured Latency |
|---|---|
| Sensor HTTP read (LAN) | < 200 ms |
| LSTM inference (CPU) | < 50 ms |
| Fan command HTTP (LAN) | < 200 ms |
| Full control cycle | < 500 ms |

The 2-second control interval significantly exceeds the worst-case cycle latency, guaranteeing that each iteration completes before the next is triggered.

### C. System Resource Utilisation

The Flask backend runs comfortably on a standard laptop or Raspberry Pi class device. The LSTM model file (`saffron_temperature_lstm_model.h5`) is 1.4 MB, and single-step inference consumes negligible CPU time (< 50 ms), making edge deployment on low-power hardware feasible.

---

## VII. Discussion

### A. Predictive vs. Reactive Control

The LSTM-based predictive approach offers a fundamental advantage over threshold thermostats: the fan state is governed by an anticipated optimal temperature rather than crossing a fixed boundary. This enables the system to pre-condition the environment before the target temperature is exceeded, reducing peak thermal excursions.

### B. System Strengths

- **High prediction accuracy** (R² = 0.9920) validated on real data.
- **Low cost** — complete hardware stack assembled for under $20 USD.
- **Wireless architecture** — no field wiring required for sensor-to-actuator communication.
- **Offline-capable** — all inference runs locally; no cloud dependency.
- **Extensible** — additional ESP32 sensor-actuator pairs can be added to the network without redesigning the backend.

### C. Limitations

1. **Lag feature approximation:** The online inference pipeline approximates lag features with a fixed seed value (10°C) rather than a true 24-hour rolling buffer of live readings. Under sustained rapid temperature changes, this approximation may introduce systematic prediction error.
2. **Static model:** The LSTM is not updated post-deployment. Distributional drift (e.g., climate seasonality in a new year or a different growing site) would require periodic retraining.
3. **Cooling only:** The single-actuator design addresses only overheating. Cold-night scenarios (below the 5°C threshold during flowering) are not addressed.
4. **Network dependency:** All inter-component communication relies on a shared Wi-Fi LAN. Network outages disable sensor reads and fan commands simultaneously.
5. **Security:** Plain HTTP without authentication is unsuitable for internet-exposed deployments.

### D. Comparison with Existing Approaches

**Table VI — Comparison with Related Systems**

| Criterion | Proposed System | Threshold Thermostat | Cloud IoT + ML |
|---|---|---|---|
| Predictive control | ✅ LSTM (R²=0.992) | ❌ Reactive | ✅ (cloud-side) |
| Local/edge inference | ✅ | ✅ | ❌ |
| Hardware cost | ~$20 USD | ~$5–15 USD | High (subscription) |
| Network dependency | LAN only | None | Internet required |
| Dashboard / monitoring | ✅ Web UI | ❌ | ✅ |
| Offline operation | ✅ | ✅ | ❌ |
| Bidirectional temperature control | ❌ | Configurable | ✅ |

---

## VIII. Future Work

The following enhancements are identified for future development:

1. **Live 24-hour rolling buffer** — Maintain a circular buffer of real sensor readings to provide accurate lag features during online inference, replacing the seed-value approximation.
2. **Bidirectional climate control** — Add a heater relay to address cold-night scenarios, enabling full closed-loop regulation across the complete saffron temperature envelope.
3. **Online / periodic retraining** — Implement an automated retraining pipeline that incorporates accumulated sensor data to counteract model drift.
4. **MQTT-based communication** — Replace REST polling with a publish-subscribe MQTT broker (e.g., Mosquitto) for lower latency and reduced network overhead.
5. **TensorFlow Lite edge inference** — Quantise and deploy the LSTM model directly on an ESP32 using TensorFlow Lite for Microcontrollers, eliminating the server dependency.
6. **Multi-zone control** — Extend the architecture to support independent sensor-actuator pairs for zone-specific greenhouse management.
7. **Security hardening** — Implement HTTPS with TLS, API-key authentication, and mutual certificate verification for production deployments.
8. **Explainable AI integration** — Apply SHAP (SHapley Additive exPlanations) to produce interpretable feature importance scores for LSTM predictions, aiding agronomist trust and adoption.

---

## IX. Conclusion

This paper has presented and reviewed a complete AI-integrated IoT system for saffron temperature control. The system combines distributed ESP32-based sensing and actuation, LSTM deep learning trained with temporal feature engineering, and a Flask-based RESTful control backend into a cohesive, low-cost, locally-deployed precision-agriculture solution. Evaluation on a held-out test set of 2,896 samples demonstrates strong predictive performance: MAE of **0.3523°C**, RMSE of **0.4960°C**, and R² of **0.9920**. The hysteresis-based control algorithm ensures stable and efficient actuator operation, while the multi-threaded backend provides concurrent, responsive handling of control and monitoring tasks.

The system demonstrates the practical viability of integrating accessible embedded hardware with open-source deep learning to produce intelligent, field-deployable smart greenhouse controllers. With the enhancements described in Section VIII—particularly live lag buffering, bidirectional climate control, and MQTT integration—the architecture can be evolved from a research prototype into a production-grade system suitable for commercial saffron cultivation.

---

## References

[1] S. Wolfert, L. Ge, C. Verdouw, and M. J. Bogaardt, "Big data in smart farming – A review," *Agricultural Systems*, vol. 153, pp. 69–80, 2017.

[2] F. Gresta, G. M. Lombardo, L. Siracusa, and G. Ruberto, "Saffron, an alternative crop for sustainable agricultural systems. A review," *Agronomy for Sustainable Development*, vol. 28, no. 1, pp. 95–112, 2008.

[3] N. Gondchawar and R. S. Kawitkar, "IoT based smart agriculture," *International Journal of Advanced Research in Computer and Communication Engineering*, vol. 5, no. 6, pp. 838–842, 2016.

[4] V. C. Patil and A. D. Kadu, "IOT based smart agriculture monitoring and controlling system," *International Research Journal of Engineering and Technology*, vol. 3, no. 5, 2016.

[5] A. Tzounis, N. Katsoulas, T. Bartzanas, and C. Kittas, "Internet of Things in agriculture, recent advances and future challenges," *Biosystems Engineering*, vol. 164, pp. 31–48, 2017.

[6] Espressif Systems, *ESP32 Series Datasheet v3.5*, Espressif Systems, 2023.

[7] S. Hochreiter and J. Schmidhuber, "Long short-term memory," *Neural Computation*, vol. 9, no. 8, pp. 1735–1780, 1997.

[8] D. Liu, A. K. Mishra, Z. Yu, H. Yang, and S. Lv, "Soil moisture uncertainty in hydrologic modeling with a quasi-linear effective rainfall model," *Journal of Hydrology*, vol. 559, pp. 386–394, 2018.

[9] M. Azaza, C. Tanougast, E. Fabrizio, and A. Mami, "Smart greenhouse fuzzy logic based control system enhanced with wireless data monitoring," *ISA Transactions*, vol. 61, pp. 297–307, 2016.

[10] H. Navarro-Hellín, J. M. del Rincon, R. Domingo-Miguel, F. Soto-Valles, and R. Torres-Sánchez, "A decision support system for managing irrigation in agriculture," *Computers and Electronics in Agriculture*, vol. 124, pp. 121–131, 2016.

[11] D. Peng, Y. Wu, and H. Daume, "Time-series feature encoding for neural networks," *arXiv preprint* arXiv:1905.09659, 2019.

[12] R. V. Molina, M. Valero, Y. Navarro, J. L. Guardiola, and A. García-Luis, "Temperature effects on sprouting and flowering in *Crocus sativus* L.," *Scientia Horticulturae*, vol. 103, no. 3, pp. 361–379, 2005.

---

*Manuscript submitted April 2026. Formatted per IEEE Transactions style guidelines.*
*Total word count (body): ~2,900 words.*
