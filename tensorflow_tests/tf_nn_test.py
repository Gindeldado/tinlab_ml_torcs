'''working old'''
import tensorflow as tf
import pandas as pd
import numpy as np

from sklearn.preprocessing import OneHotEncoder

actuators = [ "ACCEL_STATE", "STEERING"]
selectedSensors = [ 
        "SPEED",
        "ANGLE_TO_TRACK_AXIS",
        "TRACK_POSITION",
        "TRACK_EDGE_0",
        "TRACK_EDGE_1",
        "OPPONENT_0",
        "OPPONENT_1",
        "OPPONENT_2",
        "OPPONENT_3",
        "OPPONENT_4",
        "OPPONENT_5",
        "OPPONENT_6",
        "OPPONENT_7",
        "OPPONENT_8",
]
dfCollected = pd.read_csv(
        "logger/aalborg_solo_fast_full.csv",
        sep=',', 
        index_col=False
    )

# split data between train en test data
train_data = dfCollected.iloc[:len(dfCollected)//2,:]
test_data = dfCollected.iloc[len(dfCollected)//2:,:]
# print(test_data)

# divide input and correct output for training set
# Extract input features and labels
train_data_inp = train_data[selectedSensors].values
# labels(output)
train_pedal_classification_labels_encoded = train_data['ACCEL_STATE'].values
train_steering_labels = train_data['STEERING'].values

test_data_inp = test_data[selectedSensors].values
# labels(output)
test_data_out = test_data[actuators].values
test_pedal_classification_labels = test_data['ACCEL_STATE'].values
test_steering_labels = test_data['STEERING'].values

# Input layer
input_layer = tf.keras.Input(shape=(train_data_inp.shape[1],))

# One-hot encode classification labels
encoder = OneHotEncoder(categories=[[0, 0.5, 1]], drop=None)
train_pedal_classification_labels_encoded = encoder.fit_transform(train_pedal_classification_labels_encoded.reshape(-1, 1))
print(train_pedal_classification_labels_encoded[0])
print(train_data['ACCEL_STATE'][0])
# Shared layers
x = tf.keras.layers.Dense(len(selectedSensors) * 4, activation='relu')(input_layer)  # Input layer must be provided here
x = tf.keras.layers.Dense(len(selectedSensors) * 2, activation='relu')(x)
x = tf.keras.layers.Dense(len(selectedSensors), activation='relu')(x)

# Regression output (for steering)
steering_out =  tf.keras.layers.Dense(units=1, activation=tf.nn.tanh, name='steering_output')(x)
# Classification output (0, 0.5, 1)
pedal_classification_out = tf.keras.layers.Dense(3, activation=tf.nn.softmax, name='pedal_action_classification_output')(x)

# Create the model
model = tf.keras.Model(inputs=input_layer, outputs=[steering_out, pedal_classification_out])

# Compile the model with appropriate losses
model.compile(optimizer='adam',
              loss={'steering_output': 'mean_squared_error',
                    'pedal_action_classification_output': 'categorical_crossentropy'},
              metrics={'steering_output': 'mse',
                       'pedal_action_classification_output': 'accuracy'})
# test_model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])

# Summary of the model
model.summary()

# Train the model
model.fit(train_data_inp,
          {'steering_output': train_steering_labels,
           'pedal_action_classification_output': train_pedal_classification_labels_encoded},
          epochs=50,
          batch_size=32,
          validation_split=0.2)


# test_loss, test_acc = test_model.evaluate(ev_features, ev_labels, batch_size=100)
# print("loss: ",test_loss)
# print("acc: ",test_acc)

# test met random test data of het overeen komt !je moet het resahpen anders werkt niet 
print("hmm: ", test_data_out[110])
# pred = model.predict(test_data_inp[110].reshape(1,len(selectedSensors)))
# print("pred: ", pred)
print("\ncorr inp: ", test_data_inp[110])
print("corr out: ", test_data_out[110])