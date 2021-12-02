import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing

np.set_printoptions(precision=3, suppress=True)

# Read dataset from file
raw_dataset = pd.read_csv("./data_grouped/1161114002_122.csv")
raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
dataset = raw_dataset.copy()
dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)

# Split data into training and testing
train_dataset = dataset.sample(frac=0.8, random_state=0)
test_dataset = dataset.drop(train_dataset.index)

# Split input features and lables
train_features = train_dataset.copy()
test_features = test_dataset.copy()
train_labels = train_features.pop('value')
test_labels = test_features.pop('value')

# Normalize single column in dataset
input_col = np.array(train_features['norm_time'])
input_col_normalizer = preprocessing.Normalization()
input_col_normalizer.adapt(input_col)

# Model Init fucntion
def build_and_compile_model(norm):
  model = keras.Sequential([
      norm,
      layers.Dense(64, activation='relu'),
      layers.Dense(64, activation='relu'),
      layers.Dense(1)
  ])
  # Setup optimizer, learning rate, and loss function
  model.compile(loss='mean_absolute_error',
                optimizer=tf.keras.optimizers.Adam(0.001))
  return model

DNN_single_model = build_and_compile_model(input_col_normalizer)

# Save Train loss each epochs for later analysis
history = DNN_single_model.fit(
    train_features['norm_time'], train_labels,
    epochs=100,
    # suppress logging
    verbose=0,
    # Calculate validation results on 20% of the training data
    validation_split = 0.2)

# Plot loss during training
# def plot_loss(history):
#   plt.plot(history.history['loss'], label='loss')
#   plt.plot(history.history['val_loss'], label='val_loss')
#   plt.ylim([0, 10])
#   plt.xlabel('Epoch')
#   plt.ylabel('Error [event_time]')
#   plt.legend()
#   plt.grid(True)
#   plt.show()
# plot_loss(history)

# Evaluate model in testing dataset
test_results = {}
test_results['DNN_single_var_model'] = DNN_single_model.evaluate(
    test_features['norm_time'],
    test_labels, verbose=0)
print (pd.DataFrame(test_results, index=['Mean absolute error [value]']).T)

DNN_single_model.save("../exported_models/DNN_single_regression")
converter = tf.lite.TFLiteConverter.from_saved_model("../exported_models/DNN_single_regression")
tflite_model = converter.convert()
open("../exported_models/tflite_model/DNN_single_regression.tflite", "wb").write(tflite_model)

# Ploting result
x = tf.linspace(0.0, 800, 801)
y = DNN_single_model.predict(x)
def plot_horsepower(x, y):
  plt.scatter(train_features['norm_time'], train_labels, label='Data')
  plt.plot(x, y, color='k', label='Predictions')
  plt.xlabel('norm_time')
  plt.ylabel('value')
  plt.legend()
  plt.show()
plot_horsepower(x,y)