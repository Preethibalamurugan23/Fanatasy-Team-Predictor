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
from players import team_players


# Initialize FastAPI app
app = FastAPI()

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

# # Define the request body using Pydantic for validation
# class InputData(BaseModel):
#     fullName: str
#     venue: str
#     batting_innings: int
#     home_team: str
#     away_team: str

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
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for all origins (or specify the exact origin of your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with the specific frontend URL like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

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
        
#         # Ensure prediction is a native Python float
#         predicted_fp = float(predicted_fp)

#         # Return the prediction result as a JSON response
#         return {"predicted_fantasy_points": round(predicted_fp, 2)}

#     except ValueError as e:
#         logging.error(f"Input error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal Server Error")

class InputData(BaseModel):
    home_team: str
    away_team: str
    venue: str
    inning: int

# @app.post("/predict_fantasy_points/")
# async def predict_top_players(input_data: InputData):
#     """Handles the prediction request for all players of two teams."""
#     try:
#         logging.info(f"Received input data: {input_data}")

#         home_team = input_data.home_team
#         away_team = input_data.away_team

#         if home_team not in team_players or away_team not in team_players:
#             raise ValueError(f"Invalid team names: {home_team}, {away_team}")

#         # Get all players from both teams
#         players = team_players[home_team] + team_players[away_team]

#         player_scores = []

#         for player in players:
#             player_input = {
#                 "fullName": player,
#                 "home_team": home_team,
#                 "away_team": away_team,
#                 "venue": input_data.venue,
#                 "inning": input_data.inning,
#                 "batting_innings": input_data.inning  # 🔥 add this line

#             }

#             # preprocess and predict
#             processed_input = preprocess_input(player_input, player_encoder, venue_encoder, onehot_encoder)
#             if processed_input[0] == 1000:
#                 predicted_fp=25
#             else:
#                 predicted_fp = predict_fantasy_points(model, processed_input)

#             # ensure float
#             predicted_fp = float(predicted_fp)

#             player_scores.append((player, predicted_fp))

#         # Sort by fantasy points
#         sorted_players = sorted(player_scores, key=lambda x: x[1], reverse=True)

#         # Top 10 players
#         top_players = [player for player, _ in sorted_players[:11]]

#         return {"predicted_players": top_players}

#     except ValueError as e:
#         logging.error(f"Input error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Internal Server Error")

from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import Gauge
from fastapi import FastAPI, HTTPException, Request
from starlette.responses import Response


# Prometheus metrics
# REQUEST_COUNT = Counter('api_requests_total', 'Total number of API requests', ['method', 'endpoint'])
# EXCEPTION_COUNT = Counter('api_exceptions_total', 'Total number of exceptions', ['endpoint', 'exception_type'])
# REQUEST_LATENCY = Summary('api_request_latency_seconds', 'API request latency', ['endpoint'])
# FAILED_PREDICTIONS = Gauge('api_failed_predictions_total', 'Current number of failed predictions')

# @app.middleware("http")
# async def prometheus_middleware(request: Request, call_next):
#     """Middleware to collect request metrics"""
#     method = request.method
#     endpoint = request.url.path

#     with REQUEST_LATENCY.labels(endpoint=endpoint).time():
#         try:
#             response = await call_next(request)
#             REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
#             return response
#         except Exception as e:
#             EXCEPTION_COUNT.labels(endpoint=endpoint, exception_type=type(e).__name__).inc()
#             raise e

import time
from prometheus_client import Counter, Summary, Gauge

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total number of API requests', ['method', 'endpoint'])
EXCEPTION_COUNT = Counter('api_exceptions_total', 'Total number of exceptions', ['endpoint', 'exception_type'])
REQUEST_LATENCY = Summary('api_request_latency_seconds', 'API request latency', ['endpoint'])
FAILED_PREDICTIONS = Gauge('api_failed_predictions_total', 'Current number of failed predictions')

# @app.post("/reset_failed_predictions/")
# async def reset_failed_predictions():
#     FAILED_PREDICTIONS.set(0)
#     return {"message": "FAILED_PREDICTIONS reset to 0"}

@app.post("/predict_fantasy_points/")
async def predict_top_players(input_data: InputData):
    endpoint = "/predict_fantasy_points"
    method = "POST"
    print("Incrementing REQUEST_COUNT")
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    FAILED_PREDICTIONS.set(0)  # reset at the start


    start_time = time.time()

    try:
        logging.info(f"Received input data: {input_data}")

        home_team = input_data.home_team
        away_team = input_data.away_team

        if home_team not in team_players or away_team not in team_players:
            EXCEPTION_COUNT.labels(endpoint=endpoint, exception_type="ValueError").inc()
            # FAILED_PREDICTIONS.inc()
            raise ValueError(f"Invalid team names: {home_team}, {away_team}")

        players = team_players[home_team] + team_players[away_team]
        player_scores = []

        for player in players:
            player_input = {
                "fullName": player,
                "home_team": home_team,
                "away_team": away_team,
                "venue": input_data.venue,
                "inning": input_data.inning,
                "batting_innings": input_data.inning
            }

            processed_input = preprocess_input(player_input, player_encoder, venue_encoder, onehot_encoder)

            if processed_input[0] == 1000:
                # FAILED_PREDICTIONS.inc()
                predicted_fp = 25
            else:
                predicted_fp = predict_fantasy_points(model, processed_input)

            player_scores.append((player, float(predicted_fp)))

        sorted_players = sorted(player_scores, key=lambda x: x[1], reverse=True)
        top_players = [player for player, _ in sorted_players[:11]]

        return {"predicted_players": top_players}

    except ValueError as e:
        logging.error(f"Input error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        EXCEPTION_COUNT.labels(endpoint=endpoint, exception_type="Exception").inc()
        # FAILED_PREDICTIONS.inc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

@app.get("/")
async def root():
    REQUEST_COUNT.inc()
    return {"message": "Hello World"}
            
@app.get("/metrics")
async def metrics():
    # """Expose Prometheus metrics"""
    # return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    data = generate_latest()
    return Response(content=data, media_type="text/plain")


# Run the app using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
