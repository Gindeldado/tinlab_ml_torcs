import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
# from keras import utils

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

X = dfCollected[selectedSensors].values
Y_0 = dfCollected["ACCEL_STATE"].values
Y_1 = dfCollected["STEERING"].values


# one hot encoding for the mult class classification node
encode_Y_0 = pd.get_dummies(Y_0)

# Splitting the data into training and testing sets
X_train, X_test, y0_train, y0_test, y1_train, y1_test \
    = train_test_split(X, encode_Y_0, Y_1, test_size=0.2, random_state=42)

base_nodes = len(selectedSensors)
input_layer = tf.keras.Input(shape=(X_train.shape[1],))
x = tf.keras.layers.Dense(base_nodes * 4, activation='relu')(input_layer)
x = tf.keras.layers.Dense(base_nodes * 2, activation='relu')(x)
x = tf.keras.layers.Dense(base_nodes, activation='relu')(x)

output_layer_pedal = tf.keras.layers.Dense(y0_train.shape[1], activation='softmax', name='pedal_classification')(x)
shape_y1 = 1
output_layer_steering = tf.keras.layers.Dense(shape_y1, activation='tanh', name='steering_regression')(x)
model = tf.keras.Model(inputs=input_layer, outputs=[output_layer_pedal, output_layer_steering])

# Compile the model
model.compile(optimizer='adam', 
              loss={
                'pedal_classification':tf.keras.losses.CategoricalCrossentropy(), 
                'steering_regression':tf.keras.losses.MeanSquaredError()
                },
              metrics={
                'pedal_classification': [tf.keras.metrics.CategoricalAccuracy()], 
                'steering_regression': [tf.keras.metrics.MeanSquaredError()]})

# Display the model's architecture
model.summary()

def train_model(model):
    # history = model.fit(X_train, y0_train, epochs=50, batch_size=32, validation_data=(X_test, y0_test))
    history = model.fit(X_train, 
                {'pedal_classification': y0_train, 
                 'steering_regression': y1_train}, 
                epochs=50, 
                batch_size=32, 
                validation_data=(X_test, {'pedal_classification': y0_test, 
                                          'steering_regression': y1_test}))
    
    # Evaluate the model
    results = model.evaluate(X_test, {'pedal_classification': y0_test, 
                                    'steering_regression': y1_test})


    print("fit phase -")
    print(f"Last total loss: {history.history['loss'][-1]}")    
    print(f"Last Pedal Classification Accuracy: {history.history['pedal_classification_categorical_accuracy'][-1]}")
    print(f"Last Steering Regression mse Loss: {history.history['steering_regression_mean_squared_error'][-1]}")

    loss = results[0]
    pedal_classification_acc = results[1]
    steering_regression_loss = results[2]
    print("evaluate phase -")
    print(f"Total Loss: {loss}")
    print(f"Pedal Classification Accuracy: {pedal_classification_acc}")
    print(f"Steering Regression mse Loss: {steering_regression_loss}")

def safe_model(model):
    # save model
    model.save('model_0.keras')
    print("model has been saved!")
def load_model():
    # load model
    model = tf.keras.models.load_model("working_test_model.keras")
    return model

train_model(model=model)
safe_model(model=model)


# predict_this = [ #1,1,0,0,0.5,0.5
#     [-0.39660382148920054,124.10731612192016,-0.27645270910841735,-0.093927,42.7057,53.1032,200.0,200.0,29.1245,200.0,106.868,200.0,200.0,200.0,200.0],
#     [-0.39975414108920243,124.05056376680213,-0.2932031302490669,-0.0941101,42.159,52.384,200.0,200.0,28.8545,200.0,106.945,200.0,200.0,200.0,200.0],
#     [-0.4029037282892007,124.21609885821275,-0.33813161575425044,-0.0942932,41.5575,51.597,200.0,200.0,28.5813,200.0,107.016,200.0,200.0,200.0,200.0],
#     [-0.40666504748919036,124.49254299487819,-0.4250687938406308,-0.0944702,40.878,50.712,200.0,200.0,28.3003,200.0,107.079,200.0,200.0,200.0,200.0],
#     [0.209049614943091,56.658727470035146,3.9796387942637694,-0.126266,20.0786,16.7261,200.0,200.0,200.0,200.0,200.0,200.0,200.0,200.0,200.0], 
#     [0.22863300861588245,56.60124342142637,4.13012615915488,-0.130606,19.9229,16.5889,200.0,200.0,200.0,200.0,200.0,200.0,200.0,200.0,200.0],
# ]
# p = np.array(predict_this)
# predictions = model.predict(p)
# predicted_classes = np.argmax(predictions, axis=1)
# print(predicted_classes)
# y = tf.keras.utils.to_categorical(Y_0, num_classes=4)
# print(y)
# def model_fn():
#     input_layer = tf.keras.Input(shape=(result[selectedSensors].shape[1],))
#     x = tf.keras.layers.Dense(len(selectedSensors) * 4, activation='relu')(input_layer)  # Input layer must be provided here
#     x = tf.keras.layers.Dense(len(selectedSensors) * 2, activation='relu')(x)
#     x = tf.keras.layers.Dense(3, activation='softmax')(x)
#     model = tf.keras.Model(inputs=input_layer, outputs=[encode_Y_0])
#     # Compile model here
#     model.compile(loss = 'categorical_crossentropy', optimizer = 'adam', metrics = ['accuracy'])
#     return model

# # Create Keras Classifier and use predefined baseline model
# estimator = tf.KerasClassifier(build_fn = model_fn, epochs = 100, batch_size = 10, verbose = 0)

# # KFold Cross Validation
# seed = 10
# np.random.seed(seed)
# kfold = tf.KFold(n_splits = 5, shuffle = True, random_state = seed)

# # Object to describe the result
# results = tf.cross_val_score(estimator, dfCollected[selectedSensors].values, Y_0, cv = kfold)
# # Result
# print("Result: %.2f%% (%.2f%%)" % (results.mean()*100, results.std()*100))