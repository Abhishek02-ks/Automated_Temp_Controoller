import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping


df = pd.read_csv("final_saffron_temperature_dataset.csv")

print("Dataset shape:", df.shape)

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

scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data)

def create_sequences(dataset, lookback=24):
    X, y = [], []
    for i in range(len(dataset) - lookback):
        X.append(dataset[i:i+lookback])
        y.append(dataset[i+lookback, 0])  # temperature target
    return np.array(X), np.array(y)

LOOKBACK = 24

X, y = create_sequences(scaled_data, LOOKBACK)

print("X shape:", X.shape)
print("y shape:", y.shape)

split = int(0.8 * len(X))

X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

model = Sequential([
    LSTM(128, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
    Dropout(0.2),

    LSTM(64),
    Dropout(0.2),

    Dense(1)
])

model.compile(
    optimizer="adam",
    loss="mse"
)

model.summary()


early_stop = EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

history = model.fit(
    X_train,
    y_train,
    epochs=80,
    batch_size=32,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

y_pred = model.predict(X_test)

temp_index = features.index("temperature")

y_test_actual = scaler.inverse_transform(
    np.concatenate([y_test.reshape(-1,1),
                    np.zeros((len(y_test), len(features)-1))], axis=1)
)[:,0]

y_pred_actual = scaler.inverse_transform(
    np.concatenate([y_pred,
                    np.zeros((len(y_pred), len(features)-1))], axis=1)
)[:,0]

plt.show()
