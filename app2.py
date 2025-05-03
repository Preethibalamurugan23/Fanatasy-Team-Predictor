# import os
# import logging
# import numpy as np
# import joblib
# import mlflow
# import mlflow.pyfunc
# from flask import Flask, request, jsonify

# # --- Configuration ---
# MODEL_URI = "http://localhost:5001/models/fantasy_model/1"  # Adjust based on your model URI and version
# ARTIFACTS_DIR = "predict_support"
# PLAYER_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "player_encoder.pkl")
# VENUE_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "venue_encoder.pkl")
# ONEHOT_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "onehot_encoder.pkl")

# # Load encoders
# def load_encoders():
#     """Load the player, venue, and onehot encoders."""
#     try:
#         player_encoder = joblib.load(PLAYER_ENCODER_PATH)
#         venue_encoder = joblib.load(VENUE_ENCODER_PATH)
#         onehot_encoder = joblib.load(ONEHOT_ENCODER_PATH)
#         return player_encoder, venue_encoder, onehot_encoder
#     except Exception as e:
#         logging.error(f"Error loading encoders: {e}", exc_info=True)
#         return None, None, None

# # --- Preprocess Input ---
# def preprocess_input(input_data, player_encoder, venue_encoder, onehot_encoder):
#     """Converts raw input dictionary into the format required by the model using loaded encoders."""
#     logging.info(f"Preprocessing input: {input_data}")

#     # 1. Get Player ID using LabelEncoder
#     player_name = input_data.get('fullName')
#     if player_name is None:
#         raise ValueError("Missing 'fullName' in input data.")
#     try:
#         player_id = player_encoder.transform([player_name])[0]
#     except ValueError:
#         raise ValueError(f"Unknown player: '{player_name}'. Cannot predict.")
#     player_id_input = np.array([[player_id]], dtype=np.int32)

#     # 2. Get Venue ID using LabelEncoder
#     venue_name = input_data.get('venue')
#     if venue_name is None:
#         raise ValueError("Missing 'venue' in input data.")
#     try:
#         venue_id = venue_encoder.transform([venue_name])[0]
#     except ValueError:
#         raise ValueError(f"Unknown venue: '{venue_name}'. Cannot predict.")
#     venue_id_input = np.array([[venue_id]], dtype=np.int32)

#     # 3. One-Hot Encode Features
#     feature_cols_order = ['home_team', 'away_team', 'batting_innings']
#     ohe_input_list = []
#     for col in feature_cols_order:
#         value = input_data.get(col)
#         if value is None:
#             raise ValueError(f"Missing feature '{col}' needed for one-hot encoding.")
#         if col in ['home_team', 'away_team']:
#             value = str(value).strip().upper()
#         elif col == 'batting_innings':
#             value = int(value)
#         ohe_input_list.append(value)
#     ohe_input_array = [ohe_input_list]
#     onehot_input = onehot_encoder.transform(ohe_input_array).astype(np.float32)

#     return [player_id_input, venue_id_input, onehot_input]

# # --- Prediction Function ---
# def predict(model, processed_input):
#     """Makes a prediction using the loaded model and preprocessed input."""
#     try:
#         prediction = model.predict(processed_input)
#         return prediction[0][0]
#     except Exception as e:
#         logging.error(f"Error during model prediction: {e}", exc_info=True)
#         raise

# # --- Set Up Flask App ---
# app = Flask(__name__)

# @app.route('/predict', methods=['POST'])
# def predict_fantasy_points():
#     try:
#         # Get input data from the request
#         input_data = request.get_json()
#         logging.info(f"Received input data: {input_data}")

#         # Load encoders
#         player_encoder, venue_encoder, onehot_encoder = load_encoders()
#         if not all([player_encoder, venue_encoder, onehot_encoder]):
#             return jsonify({"error": "Error loading encoders"}), 500

#         # Load the model using MLflow
#         model = mlflow.pyfunc.load_model(MODEL_URI)
#         if model is None:
#             return jsonify({"error": "Error loading the model"}), 500

#         # Preprocess the input data
#         processed_input = preprocess_input(input_data, player_encoder, venue_encoder, onehot_encoder)

#         # Make a prediction
#         predicted_fp = predict(model, processed_input)

#         # Return the prediction as a JSON response
#         return jsonify({"predicted_fantasy_points": round(predicted_fp, 2)})

#     except Exception as e:
#         logging.error(f"Error in prediction: {e}", exc_info=True)
#         return jsonify({"error": str(e)}), 400

# # --- Run Flask App ---
# if __name__ == "__main__":
#     app.run(debug=True, host='0.0.0.0', port=8000)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
import joblib
import numpy as np
import tensorflow as tf
from predict import load_artifacts, preprocess_input, predict_fantasy_points
from prometheus_client import start_http_server, Summary, Counter, Histogram, Gauge
from prometheus_client import generate_latest
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware


# start_http_server(8001)
# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with the specific frontend URL like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Create Prometheus metrics to track
REQUEST_COUNT = Counter('app_request_count', 'Total number of requests')
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency in seconds')

# Initialize logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/fastapi_model.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

# Load the model and encoders
model, player_encoder, venue_encoder, onehot_encoder = load_artifacts()
if model is None:
    logging.error("Failed to load model and artifacts.")
else:
    logging.info("Model and artifacts loaded successfully.")


# Define the request body using Pydantic for validation
class InputData(BaseModel):
    fullName: str
    venue: str
    batting_innings: int
    home_team: str
    away_team: str

# API endpoint to predict fantasy points
# @app.post("/predict_fantasy_points/")
# async def predict_fantasy_points_endpoint(input_data: InputData):
#     """Handles the prediction request."""
#     try:
#         logging.info(f"Received input data: {input_data}")

#         # Prepare the input data for prediction
#         input_data_dict = input_data.dict()
#         processed_input = preprocess_input(
#             input_data_dict,
#             player_encoder,
#             venue_encoder,
#             onehot_encoder
#         )

#         # Make prediction
#         predicted_fp = predict_fantasy_points(model, processed_input)
        
#         # Return the prediction result as a JSON response
#         return {"predicted_fantasy_points": round(predicted_fp, 2)}

#     except ValueError as e:
#         logging.error(f"Input error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal Server Error")

from fastapi import HTTPException
import logging

@app.post("/predict_fantasy_points/")
async def predict_fantasy_points_endpoint(input_data: InputData):
    """Handles the prediction request."""
    try:
        logging.info(f"Received input data: {input_data}")

        # Prepare the input data for prediction
        input_data_dict = input_data.dict()
        processed_input = preprocess_input(
            input_data_dict,
            player_encoder,
            venue_encoder,
            onehot_encoder
        )

        # Make prediction
        predicted_fp = predict_fantasy_points(model, processed_input)
        
        # Ensure prediction is a native Python float
        predicted_fp = float(predicted_fp)

        # Return the prediction result as a JSON response
        return {"predicted_fantasy_points": round(predicted_fp, 2)}

    except ValueError as e:
        logging.error(f"Input error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Metrics endpoint for Prometheus
@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type="text/plain")

# Run the app using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
