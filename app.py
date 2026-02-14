from flask import Flask, json, request
from flask_cors import CORS
import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, GlobalAveragePooling2D, Dense
from tensorflow.keras.applications import VGG16

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# --- START: REBUILD MODEL ARCHITECTURE ---
def create_model():
    # 1. Load the VGG16 base model without its top (classification) layers
    # We set weights=None because we will load our own weights from model.h5
    base_model = VGG16(include_top=False, weights=None, 
                       input_shape=(224, 224, 3))
    
    # 2. Add the custom top layers from the repository's design
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(1024, activation='relu')(x)
    x = Dense(1024, activation='relu')(x)
    x = Dense(512, activation='relu')(x)
    
    # Output layer with 2 units (tumor/no tumor)
    predictions = Dense(2, activation='softmax')(x)
    
    # 3. Create the final model
    model = Model(inputs=base_model.input, outputs=predictions)
    return model

# Create the model structure
model = create_model()

# Now, load the weights from the .h5 file
model.load_weights("model.h5")
# --- END: MODEL LOADING ---


def get_cv2_image_from_base64_string(b64str):
    encoded_data = b64str.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@app.route('/home',methods=['GET'])
def home():
    return "Hello World"

@app.route("/", methods=['POST'])
def read_root():
    print("---------------------------------------")
    print("Request received, starting prediction...")
    data = json.loads(request.data)
    predict_img = []
    for item in data['image']:
        image = get_cv2_image_from_base64_string(item)
        image = cv2.resize(image,(224,224))
        predict_img.append(image)

    # Convert to NumPy array
    img_array = np.array(predict_img)

    # Normalize the pixel values (CRITICAL STEP)
    img_array = img_array.astype('float32') / 255.0

    # Use the global 'model' variable
    prediction = model.predict(img_array)
    print("Prediction finished, sending response.") # <-- ADD THIS
    print("---------------------------------------")
    result = np.argmax(prediction, axis=1)

    return {"result": prediction[:, 1].tolist()}


if __name__ == '__main__':
    app.run(port=5000)