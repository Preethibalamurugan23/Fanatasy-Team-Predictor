import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import os
import logging
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import mlflow
import mlflow.keras  # Or mlflow.tensorflow depending on your TF version
import yaml  # To load parameters if you use a params.yaml

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/train.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

def load_params(params_path="params.yaml"):
    """Loads training parameters from a YAML file."""
    try:
        with open(params_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Parameters file not found at {params_path}. Using default parameters.")
        return {}

def build_model(num_players, num_venues, onehot_dim, player_emb_dim=32, venue_emb_dim=8):
    logging.info("Building model architecture.")
    print(f"Building model with player_emb_dim={player_emb_dim}, venue_emb_dim={venue_emb_dim}, onehot_dim={onehot_dim}")
    mlflow.log_param("player_embedding_dim", player_emb_dim)
    mlflow.log_param("venue_embedding_dim", venue_emb_dim)

    # Inputs
    logging.info("Defining input layers.")
    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')
    logging.info("Input layers defined.")

    # Embeddings
    logging.info("Creating embedding layers.")
    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)
    logging.info("Embedding layers created.")

    # Flatten the embeddings
    logging.info("Flattening embedding layers.")
    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)
    logging.info("Embedding layers flattened.")

    # Concatenate all features (embeddings and one-hot)
    logging.info("Concatenating embedding and one-hot features.")
    x = Concatenate()([player_vec, venue_vec, onehot_input])
    logging.info("Features concatenated.")

    # Dense layers
    logging.info("Adding dense layers.")
    x = Dense(128, activation='relu')(x)
    x = Dense(64, activation='relu')(x)
    output = Dense(1, activation='linear')(x)  # Predict Total Fantasy Points
    logging.info("Dense layers added.")

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])  # Added MSE metric
    logging.info("Model compiled successfully.")
    return model

def train():
    logging.info("Starting training function.")
    mlflow.set_experiment("Fantasy Point Prediction")  # Set your experiment name

    with mlflow.start_run(run_name="model_simple"):
        logging.info("MLflow run started.")

        # Load parameters from params.yaml (if it exists)
        params = load_params()
        epochs = params.get("epochs", 50)
        batch_size = params.get("batch_size", 32)
        test_size = params.get("test_size", 0.1)
        random_state = params.get("random_state", 42)
        player_emb_dim = params.get("player_embedding_dim", 32)
        venue_emb_dim = params.get("venue_embedding_dim", 8)

        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)

        # --- Load Original Context Data ---
        logging.info("Attempting to load original context data.")
        try:
            original_df = pd.read_csv(r"data/Final_Fantasy_data.csv")
            context_columns = ['fullName','venue','batting_innings','home_team', 'away_team']
            original_context_df = original_df[context_columns]
            logging.info("Original context data loaded successfully.")
            print("Loaded original context data.")
        except FileNotFoundError:
            logging.error("Error: Original context data file not found.")
            print("Error: Original context data file not found. Cannot display names.")
            print("Please provide the correct path to the original data CSV.")
            original_context_df = None
        except KeyError as e:
            logging.error(f"Error: Column {e} not found in the original data CSV.")
            print(f"Error: Column {e} not found in the original data CSV.")
            print("Please ensure the CSV contains the required context columns.")
            original_context_df = None

        # Load processed data
        logging.info("Loading processed data (.npy files).")
        try:
            player_ids = np.load("data/player_ids.npy")
            venue_ids = np.load("data/venue_ids.npy")
            onehot_inputs = np.load("data/onehot_inputs.npy")
            target_fp = np.load("data/target_fp.npy")
            logging.info("Processed data loaded successfully.")
            print("Loaded processed data.")
        except FileNotFoundError as e:
            logging.error(f"Error loading processed data file: {e}")
            print(f"Error loading processed data file: {e}")
            return

        # --- Data Shape Validation ---
        logging.info("Validating shape of loaded data.")
        if original_context_df is not None and len(original_context_df) != len(player_ids):
            logging.error(f"Mismatch in length between original context data and loaded features.")
            print("Error: Mismatch in length between original context data and loaded features.")
            original_context_df = None
            logging.warning("Disabling context display due to length mismatch.")

        # Fix shape mismatch for model input
        logging.info("Reshaping data for model input.")
        player_ids = player_ids.reshape(-1, 1)
        venue_ids = venue_ids.reshape(-1, 1)
        target_fp = target_fp.reshape(-1, 1)
        logging.info("Data reshaped.")

        print(f"player_ids shape: {player_ids.shape}")
        logging.info(f"player_ids shape: {player_ids.shape}")
        print(f"venue_ids shape: {venue_ids.shape}")
        logging.info(f"venue_ids shape: {venue_ids.shape}")
        print(f"onehot_inputs shape: {onehot_inputs.shape}")
        logging.info(f"onehot_inputs shape: {onehot_inputs.shape}")
        print(f"target_fp shape: {target_fp.shape}")
        logging.info(f"target_fp shape: {target_fp.shape}")
        print(f"player_ids dtype: {player_ids.dtype}")
        logging.info(f"player_ids dtype: {player_ids.dtype}")
        print(f"venue_ids dtype: {venue_ids.dtype}")
        logging.info(f"venue_ids dtype: {venue_ids.dtype}")
        print(f"onehot_inputs dtype: {onehot_inputs.dtype}")
        logging.info(f"onehot_inputs dtype: {onehot_inputs.dtype}")

        # --- Split Data (Features and Context) ---
        logging.info("Splitting data into training and validation sets.")
        split_args = {
            'test_size': test_size,
            'random_state': random_state
        }

        (player_train, player_val,
         venue_train, venue_val,
         onehot_train, onehot_val,
         target_train, target_val) = train_test_split(
            player_ids, venue_ids, onehot_inputs, target_fp, **split_args
        )
        logging.info("Features split successfully.")

        context_train_df, context_val_df = (None, None)
        if original_context_df is not None:
            context_train_df, context_val_df = train_test_split(
                original_context_df, **split_args
            )
            logging.info("Context data split successfully.")
            print("Context data split successfully.")
        else:
            logging.info("Original context data was not loaded, skipping context split.")

        num_players = int(np.max(player_ids)) + 1
        num_venues = int(np.max(venue_ids)) + 1
        onehot_dim = onehot_inputs.shape[1]
        print(f"Data summary - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}")
        logging.info(f"Data summary - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}")

        # Build model
        logging.info("Building the model.")
        model = build_model(num_players, num_venues, onehot_dim, player_emb_dim, venue_emb_dim)
        logging.info("Model built.")
        mlflow.keras.log_model(model, "model") # Log the trained Keras model

        # Train model
        logging.info("Starting model training.")
        history = model.fit(
            x=[player_train, venue_train, onehot_train],
            y=target_train,
            validation_data=([player_val, venue_val, onehot_val], target_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)],
            verbose=2
        )
        logging.info("Model training finished.")

        # Evaluate on validation set
        logging.info("Evaluating model on the validation set.")
        val_loss, val_mae, val_mse = model.evaluate(
            [player_val, venue_val, onehot_val],
            target_val,
            verbose=0
        )
        print(f"\nFinal Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")
        mlflow.log_metric("val_loss", val_loss)
        mlflow.log_metric("val_mae", val_mae)
        mlflow.log_metric("val_mse", val_mse)
        logging.info(f"Final Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")

        # Make predictions on validation set
        logging.info("Making predictions on the validation set.")
        val_predictions = model.predict([player_val, venue_val, onehot_val])
        logging.info("Predictions made.")

        # --- Display sample predictions vs actual with context ---
        print("\nSample Validation Predictions:")
        logging.info("Displaying sample validation predictions.")
        sample_predictions_list = []

        if context_val_df is not None:
            header = "Player Name\tVenue\tMatch Details\tActual FP\tPredicted FP\tDifference"
            print(header)
            logging.info(f"Context available, printing predictions with header: {header}")
            print("-" * len(header.expandtabs()))
        else:
            print("Actual FP\tPredicted FP\tDifference")
            logging.info("Context not available, printing predictions without context.")
            print("-------------------------------------")

        for i in range(min(10, len(target_val))):
            actual = target_val[i][0]
            predicted = val_predictions[i][0]
            diff = actual - predicted
            log_dict = {"actual_fp": f"{actual:.1f}", "predicted_fp": f"{predicted:.1f}", "difference": f"{diff:+.1f}"}


            if context_val_df is not None:
                try:
                    context_row = context_val_df.iloc[i]
                    player_name = context_row.get('fullName', 'N/A')
                    venue_name = context_row.get('venue', 'N/A')
                    innings = context_row.get('batting_innings', '?')
                    home_team = context_row.get('home_team', '?')
                    away_team = context_row.get('away_team', '?')
                    match_details = f"Inn:{innings} ({home_team} vs {away_team})"
                    print(f"{player_name}\t{venue_name}\t{match_details}\t{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}")
                    log_dict.update({"player_name": player_name, "venue": venue_name, "match_details": match_details})
                    logging.info(f"Sample {i}: Player={player_name}, Venue={venue_name}, Match={match_details}, Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}")
                except Exception as e:
                    logging.error(f"Error accessing context for index {i}: {e}")
                    print(f"Error accessing context for index {i}: {e}")
                    print(f"N/A\tN/A\tN/A\t{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}")
                    logging.info(f"Sample {i}: Error accessing context, printing with placeholders. Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}")
                mlflow.log_dict(log_dict, f"sample_prediction_{i}.json")
                sample_predictions_list.append(log_dict)
            else:
                print(f"{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}")
                logging.info(f"Sample {i} (no context): Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}")

        # Plot predictions vs actual
        logging.info("Saving validation predictions plot.")
        plt.figure(figsize=(10, 6))
        plt.scatter(target_val, val_predictions, alpha=0.3)
        plt.plot([target_val.min(), target_val.max()],
                 [target_val.min(), target_val.max()], 'r--')
        plt.xlabel('Actual Fantasy Points')
        plt.ylabel('Predicted Fantasy Points')
        plt.title('Validation Set: Actual vs Predicted')
        plt.savefig('models/validation_predictions.png')
        mlflow.log_artifact('models/validation_predictions.png') # Log the plot as an artifact
        plt.close()
        print("\nValidation plot saved to validation_predictions.png")
        logging.info("Validation predictions plot saved successfully.")

        # Save model (MLflow takes care of this with mlflow.keras.log_model)
        model_save_path = "models/fantasy_model3.h5"
        logging.info(f"Saving model at {model_save_path}")
        model.save(model_save_path, 
            save_format='h5',
            include_optimizer=True)
        print(f"Model saved at {model_save_path}")
        # We don't need to manually save with Keras anymore as MLflow is tracking it
        # model.save(model_save_path)
        mlflow.keras.log_model(model, artifact_path="keras_model")
        print(f"Model saved (tracked by MLflow).")
        logging.info("Model saved (tracked by MLflow).")
        
        logging.info("MLflow run finished.")

if __name__ == "__main__":
    train()
    logging.info("Training script finished.")