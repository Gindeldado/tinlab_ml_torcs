'''working old'''
import tensorflow as tf
import pandas as pd
import numpy as np

actuators = [ "ACCELERATION", "BRAKE", "STEERING"]
selectedSensors = [ 
        "SPEED",
        "TRACK_POSITION",
        "ANGLE_TO_TRACK_AXIS",
        "TRACK_EDGE_0",
        "TRACK_EDGE_1",
        "TRACK_EDGE_2",
        "TRACK_EDGE_3",
        "TRACK_EDGE_4",
        "TRACK_EDGE_5",
        "TRACK_EDGE_6",
        "TRACK_EDGE_7",
]
dfCollected = pd.read_csv(
        "traindata/Alpine_Track_1_prepared.csv",
        sep=',', 
        index_col=False
    )
# split data between train en test data
train_data = dfCollected.iloc[:len(dfCollected)//2,:]
test_data = dfCollected.iloc[len(dfCollected)//2:,:]
# print(test_data)

# divide input and correct output for training set
train_data_inp = train_data[selectedSensors].values
train_data_out = train_data[actuators].values
# a = [12,55,19]
# b = np.array(a)
# print(type(b))
# print(type(train_data[actuators].values[0]))
# train_data_out = train_data[:, 3:].values
# ''''
test_data_inp = test_data[selectedSensors].values
test_data_out = test_data[actuators].values
# Create TensorFlow datasets
# train_data_inp_tf = tf.data.Dataset.from_tensor_slices(test_data_inp)
# train_data_out_tf = tf.data.Dataset.from_tensor_slices(test_data_out)

# test_data_inp_tf = tf.data.Dataset.from_tensor_slices(test_data[selectedSensors].values)
# test_data_out_tf = tf.data.Dataset.from_tensor_slices(test_data[actuators].values)
# test_dataset = tf.data.Dataset.zip((test_data_inp_tf, test_data_out_tf))

# # Zip the datasets together
# dataset = tf.data.Dataset.zip((train_data_inp_tf, train_data_out_tf))

# # Shuffle and batch the dataset
# dataset = dataset.shuffle(buffer_size=10000).batch(32)

# input_shape is hoe de inoput eruit ziet bvb image 20x20 heeft een van (20,20)

# test_features = dfCollected.iloc[:len(dfCollected)//2,:]["ANGLE_TO_TRACK_AXIS"]
# test_labels = dfCollected.iloc[:len(dfCollected)//2,:]["STEERING"]

# ev_features = dfCollected.iloc[len(dfCollected)//2:,:]["ANGLE_TO_TRACK_AXIS"]
# ev_labels = dfCollected.iloc[len(dfCollected)//2:,:]["STEERING"]
steering_out =  tf.keras.layers.Dense(units=2, activation=tf.nn.sigmoid)

test_model = tf.keras.Sequential([
  tf.keras.layers.Dense(10, activation='relu'),
  tf.keras.layers.Dense(15, activation='relu'),
  tf.keras.layers.Dense(3)
])

test_model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])

norm = tf.keras.layers.BatchNormalization()

test_model.fit(norm(test_data_inp), test_data_out, epochs=50)


# test_loss, test_acc = test_model.evaluate(ev_features, ev_labels, batch_size=100)
# print("loss: ",test_loss)
# print("acc: ",test_acc)

# test met random test data of het overeen komt !je moet het resahpen anders werkt niet 
print("hmm: ", test_data_out[110])
pred = test_model.predict(test_data_inp[110].reshape(1,11))
print("pred: ", pred)
print("corr inp: ", test_data_inp[110])
print("corr out: ", test_data_out[110])