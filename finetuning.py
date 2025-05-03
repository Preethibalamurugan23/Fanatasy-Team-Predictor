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
import mlflow.keras
import yaml
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/finetune.log",  # Separate log file for fine-tuning
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
    """
    Builds the Keras model.  This is the same as in train.py.
    """
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

def load_latest_match_date(csv_file="batting_Fantasy.csv"):
    """
    Loads the latest match date from the existing CSV file.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        datetime: The latest match date, or None if the file is empty or an error occurs.
    """
    try:
        df = pd.read_csv(csv_file)
        if 'date' not in df.columns:
            logging.error(f"Column 'date' not found in CSV file: {csv_file}")
            return None
        if df.empty:
            logging.info(f"CSV file is empty: {csv_file}")
            return None
        latest_date_str = df['date'].max()
        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')  # Assuming date format is %Y-%m-%d
        logging.info(f"Loaded latest match date: {latest_date} from {csv_file}")
        return latest_date
    except FileNotFoundError:
        logging.warning(f"CSV file not found: {csv_file}.  Returning None.")
        return None
    except Exception as e:
        logging.error(f"Error loading latest match date from CSV: {e}")
        return None

def load_new_data(csv_file="webscrapper/batting_stats.csv"):
    """
    Loads new data from the provided CSV file.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Returns a dataframe.
    """
    try:
        new_df = pd.read_csv(csv_file)
        logging.info(f"Loaded new data from {csv_file}")
        return new_df
    except FileNotFoundError:
        logging.error(f"File not found: {csv_file}")
        return None
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}")
        return None
    
def preprocess_new_data(new_df, latest_match_date):
    """
    Preprocesses the new data, filters for new matches, and prepares it for fine-tuning.

    Args:
        new_df (pd.DataFrame): The new data as a Pandas DataFrame.
        latest_match_date (datetime): The latest match date from the existing data.

    Returns:
        tuple: (player_ids, venue_ids, onehot_inputs, target_fp, new_context_df) or (None, None, None, None, None) if no new data.
    """
    if new_df is None:
        return None, None, None, None, None

    # Convert 'date' column to datetime objects
    new_df['date'] = pd.to_datetime(new_df['date'], format='%Y-%m-%d')  # Ensure correct format

    # Filter out data points that are not from a later date.
    new_df = new_df[new_df['date'] > latest_match_date]
    logging.info(f"Filtered new data to include only matches after {latest_match_date}")

    if new_df.empty:
        logging.info("No new data points found after the latest date.")
        return None, None, None, None, None

    # --- Load Original Context Data ---
    logging.info("Attempting to load original context data.")
    try:
        original_df = pd.read_csv(r"data/Final_Fantasy_data.csv")
        context_columns = ['fullName', 'venue', 'batting_innings', 'home_team', 'away_team']
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

    # Merge new_df with original_context_df to get context data
    new_context_df = None
    if original_context_df is not None:
        new_context_df = new_df.merge(original_context_df, left_on=['batter_name', 'venue', 'date'], right_on=['fullName', 'venue'], how='left')
        if len(new_context_df) != len(new_df):
            logging.warning("Length mismatch after merging with original context data.  Some context data may be missing.")
            print("Warning: Length mismatch after merging with original context data. Some context data may be missing.")
        else:
            logging.info("Successfully merged new data with original context data.")
            print("Successfully merged new data with original context data.")


    # Load mappings from the original training data
    try:
        player_mapping_df = np.load("data/player_name_id.npy")
        venue_mapping_df = np.load("data/venue_name_id.npy")
        logging.info("Loaded player and venue mappings.")
    except FileNotFoundError as e:
        logging.error(f"Error loading mapping files: {e}.  Cannot process new data.")
        print(f"Error loading mapping files: {e}.  Cannot process new data.")
        return None, None, None, None, None

    # Map player names to IDs, handle unknown players
    player_name_to_id_map = dict(zip(player_mapping_df['name'], player_mapping_df['player_id']))
    player_ids = new_df['batter_name'].map(player_name_to_id_map).fillna(-1).astype(int).values  # -1 for unknown
    logging.info("Mapped player names to IDs.")

    # Map venue names to IDs, handle unknown venues
    venue_name_to_id_map = dict(zip(venue_mapping_df['venue'], venue_mapping_df['venue_id']))
    venue_ids = new_df['venue'].map(venue_name_to_id_map).fillna(-1).astype(int).values  # -1 for unknown
    logging.info("Mapped venue names to IDs.")
    
    # Create one-hot encoding for match details
    onehot_inputs = pd.get_dummies(new_df[['home_team', 'away_team', 'batting_innings']]).values
    logging.info("Created one-hot encoding for match details.")

    # Extract target variable
    target_fp = new_df['fantasy_score'].values
    logging.info("Extracted target variable (fantasy points).")
    
    return player_ids, venue_ids, onehot_inputs, target_fp, new_context_df

def finetune_model(run_id, new_player_ids, new_venue_ids, new_onehot_inputs, new_target_fp,
                   epochs=10, batch_size=32, test_size=0.1, random_state=42):
    """
    Fine-tunes the model with new data.

    Args:
        run_id (str): The MLflow run ID of the trained model to fine-tune.
        new_player_ids (np.ndarray):  Player IDs for the new data.
        new_venue_ids (np.ndarray): Venue IDs for the new data.
        new_onehot_inputs (np.ndarray): One-hot encoded features for the new data.
        new_target_fp (np.ndarray): Target fantasy points for the new data.
        epochs (int): Number of epochs for fine-tuning.
        batch_size (int): Batch size for fine-tuning.
    """
    logging.info(f"Starting fine-tuning process with run_id: {run_id}")
    mlflow.set_experiment("Fantasy Point Prediction")  # Set the experiment

    with mlflow.start_run(run_name="model_finetune", nested=True):  # Start a nested run
        mlflow.log_param("finetune_epochs", epochs)
        mlflow.log_param("finetune_batch_size", batch_size)
        mlflow.log_param("finetune_test_size", test_size)
        mlflow.log_param("finetune_random_state", random_state)
        
        # Load the model from the specified run
        logging.info(f"Loading model from MLflow run: {run_id}")
        try:
            model = mlflow.keras.load_model(f"runs:/{run_id}/keras_model")
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading model from MLflow: {e}")
            print(f"Error: {e}")
            return

        # Prepare data for fine-tuning
        num_players = int(np.max(np.concatenate([new_player_ids])) + 1)
        num_venues = int(np.max(np.concatenate([new_venue_ids])) + 1)
        onehot_dim = new_onehot_inputs.shape[1]
        
        logging.info(f"Data summary for fine-tuning - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}")
        print(f"Data summary for fine-tuning - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}")

        # Split new data
        (player_train, player_val,
         venue_train, venue_val,
         onehot_train, onehot_val,
         target_train, target_val) = train_test_split(
            new_player_ids, new_venue_ids, new_onehot_inputs, new_target_fp,
            test_size=test_size, random_state=random_state
        )
        logging.info("New data split into training and validation sets.")

        # Fine-tune the model
        logging.info("Starting model fine-tuning.")
        history = model.fit(
            x=[player_train, venue_train, onehot_train],
            y=target_train,
            validation_data=([player_val, venue_val, onehot_val], target_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)], # reduced patience
            verbose=2,
        )
        logging.info("Model fine-tuning finished.")

        # Evaluate on the new validation set
        logging.info("Evaluating model on the new validation set.")
        val_loss, val_mae, val_mse = model.evaluate(
            [player_val, venue_val, onehot_val],
            target_val,
            verbose=0
        )
        print(f"\nFine-tuned Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")
        mlflow.log_metric("finetune_val_loss", val_loss)
        mlflow.log_metric("finetune_val_mae", val_mae)
        mlflow.log_metric("finetune_val_mse", val_mse)
        logging.info(f"Fine-tuned Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")
        
        # Save the fine-tuned model
        model_save_path = "models/fantasy_model.h5"
        logging.info(f"Saving fine-tuned model to {model_save_path}")
        model.save(model_save_path, save_format='h5', include_optimizer=True)
        print(f"Fine-tuned model saved to {model_save_path}")
        mlflow.keras.log_model(model, artifact_path="keras_model")
        logging.info("Fine-tuned model saved and tracked with MLflow.")
        
        logging.info("Fine-tuning process completed.")
    return model  # Return the fine-tuned model

def main(run_id):
    """
    Main function to orchestrate the fine-tuning process.

    Args:
        run_id (str): The MLflow run ID of the trained model to fine-tune.
    """
    logging.info("Starting main function.")
    latest_match_date = load_latest_match_date()
    if latest_match_date is None:
        logging.warning("Could not load latest match date. Exiting.")
        print("Error: Could not load latest match date.  Please ensure batting_Fantasy.csv is available and has a valid 'date' column.")
        return

    new_data_df = load_new_data()
    if new_data_df is None:
        logging.warning("Could not load new data. Exiting.")
        print("Error: Could not load new data.  Please ensure the new data CSV is available.")
        return

    new_player_ids, new_venue_ids, new_onehot_inputs, new_target_fp, new_context_df = preprocess_new_data(new_data_df, latest_match_date)
    if new_player_ids is None:
        logging.info("No new data to process. Exiting.")
        print("No new data to process.")
        return

    # Fine-tune the model
    finetuned_model = finetune_model(run_id, new_player_ids, new_venue_ids, new_onehot_inputs, new_target_fp)
    if finetuned_model is None:
        logging.error("Fine-tuning failed. Exiting.")
        print("Fine-tuning failed.")
        return
    
    logging.info("Fine-tuning process complete.")
    print("Fine-tuning complete.")

if __name__ == "__main__":
    # Replace with the actual run ID of the model you want to fine-tune
    run_id = "34261a26df834786a4a84f7ad61a8a3d"  # e.g., "e5e9b5f42c03495989c10b8b184d412b"
    main(run_id)
    logging.info("Script finished.")
