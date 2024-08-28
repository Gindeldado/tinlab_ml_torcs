import tensorflow as tf
import pandas as pd
import numpy as np
# print("TensorFlow version:", tf.__version__)

class MLP_TF():
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
  def __init__(self) -> None:
        self.norm = None
        steering_out =  tf.keras.layers.Dense(units=2, activation=tf.nn.sigmoid)
        
        self.mlp = tf.keras.Sequential([
          tf.keras.layers.Dense(10, activation='relu'),
          tf.keras.layers.Dense(15, activation='relu'),
          tf.keras.layers.Dense(10, activation='sigmoid'),
          # alleen voor sturen relu en voor acc sigmoid
          tf.keras.layers.Dense(3)
        ])
        pass
  def train(self, df : pd.DataFrame, ep=128):
      # lables are first 3 columns
      train_data = df.iloc[:len(df)//2,:]
      labels = train_data[self.selectedSensors].values
      features = train_data[self.actuators].values
      
      self.mlp.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
      self.mlp.fit(labels, features, epochs=128)
      pass
  
  def predict(self, inputVector):
      # self.mlp.set
      pred = self.mlp.predict(inputVector.reshape(1,14))
      return pred