import tensorflow as tf
from tensorflow import keras # Add this line
from tensorflow.keras import layers # Add this line (optional but recommended)
from tensorflow.keras import models # Add this line (optional but recommended)
from tensorflow.keras import metrics # Add this line
from tensorflow.keras import losses # Add this line

import numpy as np
import pandas as pd # <-- Add pandas import
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import os
import logging
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import joblib # <-- Add joblib
import os
import logging
# from sklearn.preprocessing import LabelEncoder, OneHotEncoder <-- Not strictly needed if just loading

# Setup logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/model_new.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

# --- Configuration ---
ARTIFACTS_DIR = "predict_support"
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fantasy_model.h5")
# Paths to the saved sklearn encoder objects
PLAYER_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "player_encoder.pkl")
VENUE_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "venue_encoder.pkl")
ONEHOT_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "onehot_encoder.pkl")

# --- Load Artifacts ---
def load_artifacts():
    """Loads the trained model and necessary preprocessing artifacts."""
    logging.info("Loading artifacts...")
    required_files = [MODEL_PATH, PLAYER_ENCODER_PATH, VENUE_ENCODER_PATH, ONEHOT_ENCODER_PATH]
    
    if not all(os.path.exists(p) for p in required_files):
        logging.error("Error: Missing artifact files")
        return None, None, None, None

    try:
        # Register custom objects
        custom_objects = {
            'mse': tf.keras.losses.MeanSquaredError(),
            'mae': tf.keras.losses.MeanAbsoluteError()
        }
        
        # Load model with custom objects
        model = tf.keras.models.load_model(
            MODEL_PATH,
            custom_objects=custom_objects
        )
        logging.info("Model loaded successfully")

        # Load encoders
        player_encoder = joblib.load(PLAYER_ENCODER_PATH)
        venue_encoder = joblib.load(VENUE_ENCODER_PATH)
        onehot_encoder = joblib.load(ONEHOT_ENCODER_PATH)

        return model, player_encoder, venue_encoder, onehot_encoder
        
    except Exception as e:
        logging.error(f"Error loading artifacts: {e}", exc_info=True)
        return None, None, None, None

# --- Preprocess Input ---
# Modify function signature to accept encoders
def preprocess_input(input_data, player_encoder, venue_encoder, onehot_encoder):
    """Converts raw input dictionary into the format required by the model using loaded encoders."""
    logging.info(f"Preprocessing input: {input_data}")

    # 1. Get Player ID using LabelEncoder
    player_name = input_data.get('fullName')
    if player_name is None:
        raise ValueError("Missing 'fullName' in input data.")
    try:
        # LabelEncoder expects an array/list and returns an array
        player_id = player_encoder.transform([player_name])[0]
    except ValueError:
        # # Handle unseen player names during prediction
        # known_players = player_encoder.classes_[:5] # Show first few known players
        # logging.error(f"Player '{player_name}' was not seen during training.")
        # logging.error(f"Known players start with: {', '.join(known_players)}...")
        # # Option 1: Raise error (safer)
        # raise ValueError(f"Unknown player: '{player_name}'. Cannot predict.")
        # # Option 2: Assign a default ID (requires model understanding of this)
        # # player_id = -1 # Or some other indicator
        player_id=1000

    player_id_input = np.array([[player_id]], dtype=np.int32)

    # 2. Get Venue ID using LabelEncoder
    venue_name = input_data.get('venue')
    if venue_name is None:
        raise ValueError("Missing 'venue' in input data.")
    try:
        venue_id = venue_encoder.transform([venue_name])[0]
    except ValueError:
        known_venues = venue_encoder.classes_[:5]
        logging.error(f"Venue '{venue_name}' was not seen during training.")
        logging.error(f"Known venues start with: {', '.join(known_venues)}...")
        raise ValueError(f"Unknown venue: '{venue_name}'. Cannot predict.")
    venue_id_input = np.array([[venue_id]], dtype=np.int32)

    # 3. Create One-Hot Encoded Features using OneHotEncoder
    # Define the order of features expected by the onehot_encoder
    # This should match the 'feature_cols' used in preprocess.py
    feature_cols_order = ['home_team', 'away_team', 'batting_innings']
    ohe_input_list = []
    try:
        for col in feature_cols_order:
            value = input_data.get(col)
            if value is None:
                raise ValueError(f"Missing feature '{col}' needed for one-hot encoding.")

            # Apply the SAME normalization as in preprocess.py
            if col in ['home_team', 'away_team']:
                value = str(value).strip().upper() # Ensure string, strip, and uppercase
            elif col == 'batting_innings':
                value = int(value) # Ensure integer type

            ohe_input_list.append(value)

        # OneHotEncoder expects a 2D array-like structure [[feature1, feature2, ...]]
        ohe_input_array = [ohe_input_list]

        # Transform using the loaded OneHotEncoder
        onehot_input = onehot_encoder.transform(ohe_input_array)
        # If sparse=False was used in training (as in your preprocess.py), it's already a dense array
        # If sparse=True, you might need onehot_input.toarray()

    except ValueError as e:
           # This can happen if a category (e.g., team name, innings number) wasn't seen during fit
           logging.error(f"Error transforming one-hot features: {e}", exc_info=True)
           logging.error("This might be due to an unknown category (e.g., team name) in the input.")
           raise ValueError(f"Failed to one-hot encode input features: {e}") from e
    except Exception as e:
        logging.error(f"Unexpected error during one-hot encoding: {e}", exc_info=True)
        raise ValueError("Unexpected error during one-hot encoding.") from e


    onehot_input = onehot_input.astype(np.float32) # Ensure correct dtype for the model

    logging.info(f"Preprocessing successful. Shapes: PlayerID {player_id_input.shape}, VenueID {venue_id_input.shape}, OneHot {onehot_input.shape}")
    # Note: No shape check against columns needed here, as onehot_encoder handles the output dimension
    return [player_id_input, venue_id_input, onehot_input]


# --- Make Prediction ---
# (This function remains the same as before)
def predict_fantasy_points(model, processed_input):
    """Makes a prediction using the loaded model and preprocessed input."""
    logging.info("Making prediction...")
    try:
        prediction = model.predict(processed_input)
        predicted_value = prediction[0][0]
        logging.info(f"Prediction successful: {predicted_value}")
        return predicted_value
    except Exception as e:
        logging.error(f"Error during model prediction: {e}", exc_info=True)
        raise


# --- Main Execution ---
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fantasy Points Predictor")
    parser.add_argument("--fullName", type=str, required=True, help="Player's full name")
    parser.add_argument("--venue", type=str, required=True, help="Venue name")
    parser.add_argument("--batting_innings", type=int, required=True, help="Batting innings (1 or 2)")
    parser.add_argument("--home_team", type=str, required=True, help="Home team")
    parser.add_argument("--away_team", type=str, required=True, help="Away team")

    args = parser.parse_args()

    model, player_encoder, venue_encoder, onehot_encoder = load_artifacts()

    if model is None:
        print("\nExiting due to failure loading artifacts. Please check logs and file paths.")
    else:
        input_data = {
            "fullName": args.fullName,
            "venue": args.venue,
            "batting_innings": args.batting_innings,
            "home_team": args.home_team,
            "away_team": args.away_team
        }

        print("\n--- Using Input Data ---")
        for key, value in input_data.items():
            print(f"- {key}: {value}")

        model_input = preprocess_input(
            input_data,
            player_encoder,
            venue_encoder,
            onehot_encoder
        )

        predicted_fp = predict_fantasy_points(model, model_input)

        print("\n--- Prediction Result ---")
        print(f"Predicted Fantasy Points for {input_data['fullName']} at {input_data['venue']}: {predicted_fp:.2f}")
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import numpy as np
# import tensorflow as tf
# import joblib
# import os
# import logging

# # Load artifacts (model, encoders)
# ARTIFACTS_DIR = "processed_data"
# MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fantasy_model.h5")
# PLAYER_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "player_encoder.pkl")
# VENUE_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "venue_encoder.pkl")
# ONEHOT_ENCODER_PATH = os.path.join(ARTIFACTS_DIR, "onehot_encoder.pkl")

# # --- FastAPI Setup ---
# app = FastAPI()

# # --- Model and Encoder Loading ---
# def load_artifacts():
#     try:
#         custom_objects = {
#             'mse': tf.keras.losses.MeanSquaredError(),
#             'mae': tf.keras.losses.MeanAbsoluteError()
#         }
#         model = tf.keras.models.load_model(MODEL_PATH, custom_objects=custom_objects)
#         player_encoder = joblib.load(PLAYER_ENCODER_PATH)
#         venue_encoder = joblib.load(VENUE_ENCODER_PATH)
#         onehot_encoder = joblib.load(ONEHOT_ENCODER_PATH)
#         return model, player_encoder, venue_encoder, onehot_encoder
#     except Exception as e:
#         logging.error(f"Error loading artifacts: {e}")
#         return None, None, None, None

# # --- Input Data Model ---
# class InputData(BaseModel):
#     fullName: str
#     venue: str
#     batting_innings: int
#     home_team: str
#     away_team: str

# # --- Prediction Logic ---
# def preprocess_input(input_data, player_encoder, venue_encoder, onehot_encoder):
#     """Converts raw input dictionary into the format required by the model using loaded encoders."""
#     logging.info(f"Preprocessing input: {input_data}")

#     # 1. Get Player ID using LabelEncoder
#     player_name = input_data.get('fullName')
#     if player_name is None:
#         raise ValueError("Missing 'fullName' in input data.")
#     try:
#         # LabelEncoder expects an array/list and returns an array
#         player_id = player_encoder.transform([player_name])[0]
#     except ValueError:
#         # Handle unseen player names during prediction
#         known_players = player_encoder.classes_[:5] # Show first few known players
#         logging.error(f"Player '{player_name}' was not seen during training.")
#         logging.error(f"Known players start with: {', '.join(known_players)}...")
#         # Option 1: Raise error (safer)
#         raise ValueError(f"Unknown player: '{player_name}'. Cannot predict.")
#         # Option 2: Assign a default ID (requires model understanding of this)
#         # player_id = -1 # Or some other indicator
#     player_id_input = np.array([[player_id]], dtype=np.int32)

#     # 2. Get Venue ID using LabelEncoder
#     venue_name = input_data.get('venue')
#     if venue_name is None:
#         raise ValueError("Missing 'venue' in input data.")
#     try:
#         venue_id = venue_encoder.transform([venue_name])[0]
#     except ValueError:
#         known_venues = venue_encoder.classes_[:5]
#         logging.error(f"Venue '{venue_name}' was not seen during training.")
#         logging.error(f"Known venues start with: {', '.join(known_venues)}...")
#         raise ValueError(f"Unknown venue: '{venue_name}'. Cannot predict.")
#     venue_id_input = np.array([[venue_id]], dtype=np.int32)

#     # 3. Create One-Hot Encoded Features using OneHotEncoder
#     # Define the order of features expected by the onehot_encoder
#     # This should match the 'feature_cols' used in preprocess.py
#     feature_cols_order = ['home_team', 'away_team', 'batting_innings']
#     ohe_input_list = []
#     try:
#         for col in feature_cols_order:
#             value = input_data.get(col)
#             if value is None:
#                 raise ValueError(f"Missing feature '{col}' needed for one-hot encoding.")

#             # Apply the SAME normalization as in preprocess.py
#             if col in ['home_team', 'away_team']:
#                 value = str(value).strip().upper() # Ensure string, strip, and uppercase
#             elif col == 'batting_innings':
#                 value = int(value) # Ensure integer type

#             ohe_input_list.append(value)

#         # OneHotEncoder expects a 2D array-like structure [[feature1, feature2, ...]]
#         ohe_input_array = [ohe_input_list]

#         # Transform using the loaded OneHotEncoder
#         onehot_input = onehot_encoder.transform(ohe_input_array)
#         # If sparse=False was used in training (as in your preprocess.py), it's already a dense array
#         # If sparse=True, you might need onehot_input.toarray()

#     except ValueError as e:
#            # This can happen if a category (e.g., team name, innings number) wasn't seen during fit
#            logging.error(f"Error transforming one-hot features: {e}", exc_info=True)
#            logging.error("This might be due to an unknown category (e.g., team name) in the input.")
#            raise ValueError(f"Failed to one-hot encode input features: {e}") from e
#     except Exception as e:
#         logging.error(f"Unexpected error during one-hot encoding: {e}", exc_info=True)
#         raise ValueError("Unexpected error during one-hot encoding.") from e


#     onehot_input = onehot_input.astype(np.float32) # Ensure correct dtype for the model

#     logging.info(f"Preprocessing successful. Shapes: PlayerID {player_id_input.shape}, VenueID {venue_id_input.shape}, OneHot {onehot_input.shape}")
#     # Note: No shape check against columns needed here, as onehot_encoder handles the output dimension
#     return [player_id_input, venue_id_input, onehot_input]


# # --- Make Prediction ---
# # (This function remains the same as before)
# def predict_fantasy_points(model, processed_input):
#     """Makes a prediction using the loaded model and preprocessed input."""
#     logging.info("Making prediction...")
#     try:
#         prediction = model.predict(processed_input)
#         predicted_value = prediction[0][0]
#         logging.info(f"Prediction successful: {predicted_value}")
#         return predicted_value
#     except Exception as e:
#         logging.error(f"Error during model prediction: {e}", exc_info=True)
#         raise

# # --- API Endpoint ---
# @app.post("/predict")
# async def make_prediction(input_data: InputData):
#     model, player_encoder, venue_encoder, onehot_encoder = load_artifacts()

#     if model is None:
#         raise HTTPException(status_code=500, detail="Model loading failed")

#     # Preprocess input data
#     model_input = preprocess_input(input_data, player_encoder, venue_encoder, onehot_encoder)
    
#     # Make prediction
#     prediction = predict_fantasy_points(model, model_input)
    
#     return {"predicted_fantasy_points": prediction}

