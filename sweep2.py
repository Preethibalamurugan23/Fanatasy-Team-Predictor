import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model
import logging
import mlflow
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
from pytorch_tabnet.tab_model import TabNetRegressor  # Import TabNet
import os
import logging
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import mlflow
import mlflow.keras
import yaml
import tempfile


def load_params(params_path="params.yaml"):
    """Loads training parameters from a YAML file."""
    try:
        with open(params_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(
            f"Parameters file not found at {params_path}. Using default parameters."
        )
        return {}


def train(model_name="tabnet"):  # Changed model_name
    """
    Trains a TabNet model.
    """
    logging.info(f"Starting training function with model: {model_name}")  # Changed
    mlflow.set_experiment("Fantasy Point Prediction - Model Comparison")

    with mlflow.start_run(run_name=model_name):  # Changed
        logging.info(f"MLflow run started for model: {model_name}")  # Changed
        params = load_params()
        epochs = params.get("epochs", 100)  # TabNet often needs more epochs
        batch_size = params.get("batch_size", 64)
        test_size = params.get("test_size", 0.1)
        random_state = params.get("random_state", 42)
        player_emb_dim = params.get("player_embedding_dim", 64)
        venue_emb_dim = params.get("venue_embedding_dim", 16)
        n_d = params.get("n_d", 32)  # TabNet specific parameter
        n_a = params.get("n_a", 32)  # TabNet specific parameter
        n_steps = params.get("n_steps", 3)  # TabNet specific parameter
        gamma = params.get("gamma", 1.3)  # TabNet specific parameter

        mlflow.log_param("model_architecture", model_name)  # Changed
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("player_emb_dim", player_emb_dim)
        mlflow.log_param("venue_emb_dim", venue_emb_dim)
        mlflow.log_param("n_d", n_d)
        mlflow.log_param("n_a", n_a)
        mlflow.log_param("n_steps", n_steps)
        mlflow.log_param("gamma", gamma)

        try:
            original_df = pd.read_csv("data/Final_Fantasy_data.csv")
            context_columns = [
                "fullName",
                "venue",
                "batting_innings",
                "home_team",
                "away_team",
            ]
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

        if (
            original_context_df is not None
            and len(original_context_df) != len(player_ids)
        ):
            logging.error(
                "Mismatch in length between original context data and loaded features."
            )
            print(
                "Error: Mismatch in length between original context data and loaded features."
            )
            original_context_df = None
            logging.warning(
                "Disabling context display due to length mismatch."
            )

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

        split_args = {
            "test_size": test_size,
            "random_state": random_state,
        }
        (
            player_train,
            player_val,
            venue_train,
            venue_val,
            onehot_train,
            onehot_val,
            target_train,
            target_val,
        ) = train_test_split(
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
            logging.info(
                "Original context data was not loaded, skipping context split."
            )

        num_players = int(np.max(player_ids)) + 1
        num_venues = int(np.max(venue_ids)) + 1
        onehot_dim = onehot_inputs.shape[1]
        print(
            f"Data summary - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}"
        )
        logging.info(
            f"Data summary - Players: {num_players}, Venues: {num_venues}, Onehot feature size: {onehot_dim}"
        )

        # 1.  Embed Inputs
        player_input = Input(shape=(1,), name="player_input")
        venue_input = Input(shape=(1,), name="venue_input")

        player_embedding = Embedding(
            input_dim=num_players, output_dim=player_emb_dim
        )(player_input)
        venue_embedding = Embedding(
            input_dim=num_venues, output_dim=venue_emb_dim
        )(venue_input)

        player_vec = Flatten()(player_embedding)
        venue_vec = Flatten()(venue_embedding)

        # 2. Concatenate embeddings and one-hot features
        feature_vector = Concatenate()([player_vec, venue_vec, onehot_inputs])

        # Prepare data for TabNet
        train_data = np.concatenate(
            [player_train, venue_train, onehot_train], axis=1
        )
        valid_data = np.concatenate(
            [player_val, venue_val, onehot_val], axis=1
        )

        # Initialize and train TabNet
        tabnet_model = TabNetRegressor(
            n_d=n_d,
            n_a=n_a,
            n_steps=n_steps,
            gamma=gamma,
            optimizer_fn=tf.keras.optimizers.Adam,
            optimizer_params={},  # Removed 'learning_rate'
            scheduler_params={
                "step_size": 20,
                "gamma": 0.9,
            },  # You can adjust the scheduler parameters here
            scheduler_fn=tf.keras.optimizers.schedules.ExponentialDecay,
            mask_type="entmax",  # "entmax" or "sparsemax"
        )
        logging.info("TabNet model initialized.")

        try:  # Added a try-except block
            tabnet_model.fit(
                X_train=train_data,
                y_train=target_train,
                eval_set=[(valid_data, target_val)],
                eval_name=["val"],
                eval_metric=[
                    "mae",
                    "mse",
                ],  # You can add more metrics if needed (e.g., "rmse")
                max_epochs=epochs,
                patience=20,  # Early stopping
                batch_size=batch_size,
                virtual_batch_size=batch_size,  # Can be different from batch_size
                num_workers=0,  # Number of workers for data loading
                drop_last=False,
            )
            logging.info("TabNet model trained.")

            # Evaluate
            eval_results = tabnet_model.evaluate(valid_data, target_val)
            val_loss = eval_results[0][1]
            val_mae = eval_results[1][1]
            val_mse = eval_results[2][1]

            print(f"\nFinal Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")
            mlflow.log_metric("val_loss", val_loss)
            mlflow.log_metric("val_mae", val_mae)
            mlflow.log_metric("val_mse", val_mse)
            logging.info(f"Final Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")

            # Make predictions
            val_predictions = tabnet_model.predict(valid_data)
            logging.info("Predictions made.")

            print("\nSample Validation Predictions:")
            logging.info("Displaying sample validation predictions.")
            sample_predictions_list = []

            if context_val_df is not None:
                header = "Player Name\tVenue\tMatch Details\tActual FP\tPredicted FP\tDifference"
                print(header)
                logging.info(
                    f"Context available, printing predictions with header: {header}"
                )
                print("-" * len(header.expandtabs()))
            else:
                print("Actual FP\tPredicted FP\tDifference")
                logging.info(
                    "Context not available, printing predictions without context."
                )
                print("-------------------------------------")

            for i in range(min(10, len(target_val))):
                actual = target_val[i][0]
                predicted = val_predictions[i][0]
                diff = actual - predicted
                log_dict = {
                    "actual_fp": f"{actual:.1f}",
                    "predicted_fp": f"{predicted:.1f}",
                    "difference": f"{diff:+.1f}",
                }

                if context_val_df is not None:
                    try:
                        context_row = context_val_df.iloc[i]
                        player_name = context_row.get("fullName", "N/A")
                        venue_name = context_row.get("venue", "N/A")
                        innings = context_row.get("batting_innings", "?")
                        home_team = context_row.get("home_team", "?")
                        away_team = context_row.get("away_team", "?")
                        match_details = f"Inn:{innings} ({home_team} vs {away_team})"
                        print(
                            f"{player_name}\t{venue_name}\t{match_details}\t{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}"
                        )
                        log_dict.update(
                            {
                                "player_name": player_name,
                                "venue": venue_name,
                                "match_details": match_details,
                            }
                        )
                        logging.info(
                            f"Sample {i}: Player={player_name}, Venue={venue_name}, Match={match_details}, Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}"
                        )
                    except Exception as e:
                        logging.error(f"Error accessing context for index {i}: {e}")
                        print(f"Error accessing context for index {i}: {e}")
                        print(
                            f"N/A\tN/A\tN/A\t{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}"
                        )
                        logging.info(
                            f"Sample {i}: Error accessing context, printing with placeholders. Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}"
                        )
                else:
                    print(f"{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}")
                    logging.info(
                        f"Sample {i} (no context): Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}"
                    )
                mlflow.log_dict(log_dict, f"sample_prediction_{i}.json")
                sample_predictions_list.append(log_dict)

            logging.info("Saving validation predictions plot.")
            plt.figure(figsize=(10, 6))
            plt.scatter(target_val, val_predictions, alpha=0.3)
            plt.plot(
                [target_val.min(), target_val.max()],
                [target_val.min(), target_val.max()],
                "r--",
            )
            plt.xlabel("Actual Fantasy Points")
            plt.ylabel("Predicted Fantasy Points")
            plt.title(f"Validation Set: Actual vs Predicted ({model_name})")  # Changed
            plot_filename = f"validation_predictions_{model_name}.png"  # Changed
            plt.savefig(f"models/{plot_filename}")
            mlflow.log_artifact(f"models/{plot_filename}")
            plt.close()
            print(f"\nValidation plot saved to models/{plot_filename}")  # Changed
            logging.info("Validation predictions plot saved successfully.")

            model_save_path = f"models/fantasy_model_{model_name}.h5"  # Changed.  TabNet uses a different save format.
            logging.info(f"Saving model at {model_save_path}")
            tabnet_model.save_model(
                model_save_path
            )  # TabNet has its own save method.
            print(f"Model saved at {model_save_path}")
            print(f"Model tracked by MLflow as artifact 'model_{model_name}'.")  # Changed
            logging.info("Model saved and tracked by MLflow.")

        except TypeError as e: # Catch the TypeError
            if "Adam.__init__() got multiple values for argument 'learning_rate'" in str(e):
                logging.error("TypeError: Multiple values for learning_rate.  Please ensure only one learning rate is specified.")
                print("TypeError: Multiple values for learning_rate. Please ensure only one learning rate is specified.")
                return  # Exit the training function
            else:
                raise e # Re-raise other TypeErrors

        logging.info("MLflow run finished.")



if __name__ == "__main__":
    # Create 'data' and 'models' directories if they don't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # Create a dummy params.yaml if it doesn't exist
    if not os.path.exists("params.yaml"):
        with open("params.yaml", "w") as f:
            f.write(
                """
epochs: 100
batch_size: 64
test_size: 0.15
random_state: 123
player_embedding_dim: 64
venue_embedding_dim: 16
n_d: 32
n_a: 32
n_steps: 3
gamma: 1.3
"""
            )
        print("Created a dummy params.yaml file. Please adjust it as needed.")

    # Create dummy data files if they don't exist (for testing purposes)
    if not os.path.exists("data/Final_Fantasy_data.csv"):
        dummy_df = pd.DataFrame(
            {
                "fullName": ["PlayerA", "PlayerB", "PlayerA", "PlayerC", "PlayerB"],
                "venue": ["VenueX", "VenueY", "VenueX", "VenueZ", "VenueY"],
                "batting_innings": [1, 2, 1, 1, 2],
                "home_team": ["Team1", "Team2", "Team1", "Team3", "Team2"],
                "away_team": ["Team2", "Team1", "Team2", "Team1", "Team3"],
                "total_fantasy_points": [10.5, 15.2, 8.9, 12.1, 18.7],
            }
        )
        dummy_df.to_csv("data/Final_Fantasy_data.csv", index=False)
        print(
            "Created a dummy data/Final_Fantasy_data.csv file. Please replace with your actual data."
        )

    if not os.path.exists("data/player_ids.npy"):
        np.save("data/player_ids.npy", np.array([0, 1, 0, 2, 1]))
    if not os.path.exists("data/venue_ids.npy"):
        np.save("data/venue_ids.npy", np.array([0, 1, 0, 2, 1]))
    if not os.path.exists("data/onehot_inputs.npy"):
        np.save("data/onehot_inputs.npy", np.random.rand(5, 5))
    if not os.path.exists("data/target_fp.npy"):
        np.save("data/target_fp.npy", np.array([10.5, 15.2, 8.9, 12.1, 18.7]))
    print("Created dummy .npy data files. Please replace with your actual processed data.")

    # Run the TabNet model
    train(model_name="tabnet")  # Changed
    logging.info("All model training runs completed.")
