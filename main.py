import numpy as np #  A library for numerical computing in Python.
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from io import BytesIO # A class for working with binary data in memory.
from PIL import Image # A library for image processing.
from typing import Tuple # A library for type hints.
import tensorflow as tf # A library for machine learning.
from fastapi.responses import HTMLResponse
from routes.videoRoutes import videos

app = FastAPI(timeout=600)

app.include_router(videos)

'''
# Load the model
MODEL = tf.keras.models.load_model('modelo_guardado.keras') # Load the model from the file
# The class names of the model
CLASS_NAMES = ['CNV', 'DME', 'DRUSEN', 'NORMAL'] 

# Function to preprocess the image
def read_file_as_image(data) -> Tuple[np.ndarray, Tuple[int, int]]: # A function to read the image file as a numpy array
    img = Image.open(BytesIO(data)).convert('RGB') # Open the image and convert it to RGB color space
    img_resized = img.resize((64, 64), resample=Image.BICUBIC) # Resize the image to 180 x 180
    image = np.array(img_resized) # Convert the image to a numpy array
    return image, img_resized.size # Return the image and its size

@app.post("/predict") # A decorator to create a route for the predict endpoint
async def predict(file: UploadFile = File(...)): # The function that will be executed when the endpoint is called
    try: # A try block to handle any errors that may occur
        image, img_size = read_file_as_image(await file.read()) # Read the image file
        img_batch = np.expand_dims(image, 0) # Add an extra dimension to the image so that it matches the input shape of the model

        predictions = MODEL.predict(img_batch) # Make a prediction
        predicted_class = CLASS_NAMES[np.argmax(predictions[0])] # Get the predicted class
        confidence = np.max(predictions[0]) # Get the confidence of the prediction

        return { # Return the prediction
            'class': predicted_class,   
            'confidence': float(confidence) 
        }
    except Exception as e: # If an error occurs
        raise HTTPException(status_code=400, detail=str(e)) # Raise an HTTPException with the error message '''