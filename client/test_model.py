from tensorflow.keras.models import load_model

# Load your model
model = load_model("cnn_model.h5")

# Print architecture summary
model.summary()