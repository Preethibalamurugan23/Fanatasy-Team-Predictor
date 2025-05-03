import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten, Dropout, BatchNormalization, Activation
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import os
import logging
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import mlflow
import mlflow.keras
import yaml
import tempfile

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
def build_model_with_interactions(num_players, num_venues, onehot_dim,
                                  player_emb_dim=64, venue_emb_dim=16):
    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    # Example of a simple interaction (dot product)
    interaction_vec = tf.keras.layers.Dot(axes=1)([player_vec, venue_vec])
    interaction_expanded = tf.expand_dims(interaction_vec, axis=-1) # Reshape for concatenation

    x = Concatenate()([player_vec, venue_vec, interaction_expanded, onehot_input])

    x = Dense(256, activation='relu')(x)
    x = Dense(128, activation='relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    return model

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten, Dropout, BatchNormalization
from tensorflow.keras.models import Model
import logging
import mlflow

def build_model_dual_path(num_players, num_venues, onehot_dim,
                        player_emb_dim=64, venue_emb_dim=16,
                        dense_units1=256, dense_units2=128,
                        dropout_rate=0.2):
    """
    Builds a dual-path neural network model.

    This model has two separate paths: one for player and venue embeddings,
    and another for the one-hot encoded features.  The outputs of these paths
    are then combined.  This allows for different processing of the different
    types of input data.

    Args:
        num_players: Number of unique players.
        num_venues: Number of unique venues.
        onehot_dim: Dimension of the one-hot encoded input.
        player_emb_dim: Dimension of the player embedding.
        venue_emb_dim: Dimension of the venue embedding.
        dense_units1: Number of units in the first dense layer after concatenation.
        dense_units2: Number of units in the second dense layer.
        dropout_rate: Dropout rate for regularization.

    Returns:
        A compiled TensorFlow Keras model.
    """
    logging.info("Building dual-path neural network model.")
    mlflow.log_param("model_architecture", "dual_path")
    mlflow.log_param("player_emb_dim", player_emb_dim)
    mlflow.log_param("venue_emb_dim", venue_emb_dim)
    mlflow.log_param("dense_units1", dense_units1)
    mlflow.log_param("dense_units2", dense_units2)
    mlflow.log_param("dropout_rate", dropout_rate)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    # Path 1: Player and Venue Embeddings
    embed_path = Concatenate()([player_vec, venue_vec])
    embed_path = Dense(dense_units1, activation='relu')(embed_path)
    embed_path = Dropout(dropout_rate)(embed_path)

    # Path 2: One-Hot Encoded Features
    onehot_path = Dense(dense_units1, activation='relu')(onehot_input)
    onehot_path = Dropout(dropout_rate)(onehot_path)

    # Combine the two paths
    combined = Concatenate()([embed_path, onehot_path])
    x = Dense(dense_units2, activation='relu')(combined)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Dual-path model compiled.")
    return model


def build_model_feature_fusion(num_players, num_venues, onehot_dim,
                              player_emb_dim=64, venue_emb_dim=16,
                              fusion_type='concat', dense_units1=256,
                              dense_units2=128, dropout_rate=0.2):
    """
    Builds a model with different feature fusion methods.

    This model explores different ways to combine the player/venue embeddings
    with the one-hot encoded features: concatenation, element-wise multiplication,
    or element-wise addition.

    Args:
        num_players: Number of unique players.
        num_venues: Number of unique venues.
        onehot_dim: Dimension of the one-hot encoded input.
        player_emb_dim: Dimension of the player embedding.
        venue_emb_dim: Dimension of the venue embedding.
        fusion_type:  'concat', 'multiply', or 'add'.
        dense_units1: Number of units in the first dense layer after fusion.
        dense_units2: Number of units in the second dense layer.
        dropout_rate: Dropout rate.

    Returns:
        A compiled TensorFlow Keras model.
    """
    logging.info(f"Building model with feature fusion: {fusion_type}")
    mlflow.log_param("model_architecture", "feature_fusion")
    mlflow.log_param("player_emb_dim", player_emb_dim)
    mlflow.log_param("venue_emb_dim", venue_emb_dim)
    mlflow.log_param("fusion_type", fusion_type)
    mlflow.log_param("dense_units1", dense_units1)
    mlflow.log_param("dense_units2", dense_units2)
    mlflow.log_param("dropout_rate", dropout_rate)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    if fusion_type == 'concat':
        x = Concatenate()([player_vec, venue_vec, onehot_input])
    elif fusion_type == 'multiply':
        x = player_vec * venue_vec * onehot_input  # Element-wise multiplication
    elif fusion_type == 'add':
        x = player_vec + venue_vec + onehot_input  # Element-wise addition
    else:
        raise ValueError(f"Invalid fusion_type: {fusion_type}.  Must be 'concat', 'multiply', or 'add'.")

    x = Dense(dense_units1, activation='relu')(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(dense_units2, activation='relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info(f"{fusion_type} fusion model compiled.")
    return model


def build_model_residual(num_players, num_venues, onehot_dim,
                         player_emb_dim=64, venue_emb_dim=16,
                         dense_units1=256, dense_units2=128,
                         dropout_rate=0.2):
    """
    Builds a neural network model with a residual connection.

    Residual connections can help with training deeper networks by allowing the
    gradient to flow more easily.

    Args:
        num_players: Number of unique players.
        num_venues: Number of unique venues.
        onehot_dim: Dimension of the one-hot encoded input.
        player_emb_dim: Dimension of the player embedding.
        venue_emb_dim: Dimension of the venue embedding.
        dense_units1: Number of units in the first dense layer.
        dense_units2: Number of units in the second dense layer.
        dropout_rate: Dropout rate.

    Returns:
        A compiled TensorFlow Keras model.
    """
    logging.info("Building model with residual connection.")
    mlflow.log_param("model_architecture", "residual")
    mlflow.log_param("player_emb_dim", player_emb_dim)
    mlflow.log_param("venue_emb_dim", venue_emb_dim)
    mlflow.log_param("dense_units1", dense_units1)
    mlflow.log_param("dense_units2", dense_units2)
    mlflow.log_param("dropout_rate", dropout_rate)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    x = Concatenate()([player_vec, venue_vec, onehot_input])

    # First dense layer
    x1 = Dense(dense_units1, activation='relu')(x)
    x1 = Dropout(dropout_rate)(x1)

    # Second dense layer with residual connection
    x2 = Dense(dense_units2, activation='relu')(x1)
    x2 = Dropout(dropout_rate)(x2)
    x = Concatenate()([x1, x2]) # Residual connection

    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Residual model compiled.")
    return model


def build_model_simple(num_players, num_venues, onehot_dim, player_emb_dim=32, venue_emb_dim=8):
    logging.info("Building simple model architecture.")
    print(f"Building simple model with player_emb_dim={player_emb_dim}, venue_emb_dim={venue_emb_dim}, onehot_dim={onehot_dim}")
    mlflow.log_param("player_embedding_dim", player_emb_dim)
    mlflow.log_param("venue_embedding_dim", venue_emb_dim)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    x = Concatenate()([player_vec, venue_vec, onehot_input])

    x = Dense(128, activation='relu')(x)
    x = Dense(64, activation='relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Simple model compiled successfully.")
    return model

def build_model_deep_fc(num_players, num_venues, onehot_dim, player_emb_dim=32, venue_emb_dim=8, dropout_rate=0.2):
    logging.info("Building deep fully connected model architecture.")
    print(f"Building deep FC model with player_emb_dim={player_emb_dim}, venue_emb_dim={venue_emb_dim}, onehot_dim={onehot_dim}, dropout={dropout_rate}")
    mlflow.log_param("player_embedding_dim", player_emb_dim)
    mlflow.log_param("venue_embedding_dim", venue_emb_dim)
    mlflow.log_param("dropout_rate", dropout_rate)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    x = Concatenate()([player_vec, venue_vec, onehot_input])

    x = Dense(256, activation='relu')(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(64, activation='relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Deep FC model compiled successfully.")
    return model

def build_model_wide_fc(num_players, num_venues, onehot_dim, player_emb_dim=64, venue_emb_dim=16):
    logging.info("Building wide fully connected model architecture.")
    print(f"Building wide FC model with player_emb_dim={player_emb_dim}, venue_emb_dim={venue_emb_dim}, onehot_dim={onehot_dim}")
    mlflow.log_param("player_embedding_dim", player_emb_dim)
    mlflow.log_param("venue_embedding_dim", venue_emb_dim)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    x = Concatenate()([player_vec, venue_vec, onehot_input])

    x = Dense(512, activation='relu')(x)
    x = Dense(256, activation='relu')(x)
    x = Dense(128, activation='relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Wide FC model compiled successfully.")
    return model

def build_model_with_bn(num_players, num_venues, onehot_dim, player_emb_dim=32, venue_emb_dim=8):
    logging.info("Building model with batch normalization.")
    print(f"Building BN model with player_emb_dim={player_emb_dim}, venue_emb_dim={venue_emb_dim}, onehot_dim={onehot_dim}")
    mlflow.log_param("player_embedding_dim", player_emb_dim)
    mlflow.log_param("venue_embedding_dim", venue_emb_dim)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    player_embedded = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedded = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedded)
    venue_vec = Flatten()(venue_embedded)

    x = Concatenate()([player_vec, venue_vec, onehot_input])

    x = Dense(128)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = Dense(64)(x)
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    output = Dense(1, activation='linear')(x)

    model = Model(inputs=[player_input, venue_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("BN model compiled successfully.")
    return model

def train(model_name="model_simple"):
    logging.info(f"Starting training function with model: {model_name}")
    mlflow.set_experiment("Fantasy Point Prediction - Model Comparison")

    with mlflow.start_run(run_name=model_name):
        logging.info(f"MLflow run started for model: {model_name}")
        params = load_params()
        epochs = params.get("epochs", 50)
        batch_size = params.get("batch_size", 32)
        test_size = params.get("test_size", 0.1)
        random_state = params.get("random_state", 42)
        player_emb_dim = params.get("player_embedding_dim", 32)
        venue_emb_dim = params.get("venue_embedding_dim", 8)
        dropout_rate = params.get("dropout_rate", 0.2) # For deep model

        mlflow.log_param("model_architecture", model_name)
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        # mlflow.log_param("player_embedding_dim", player_emb_dim)
        # mlflow.log_param("venue_embedding_dim", venue_emb_dim)
        # if model_name == "model_deep_fc":
        #     mlflow.log_param("dropout_rate", dropout_rate)

        try:
            original_df = pd.read_csv("data/Final_Fantasy_data.csv")
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

        if original_context_df is not None and len(original_context_df) != len(player_ids):
            logging.error(f"Mismatch in length between original context data and loaded features.")
            print("Error: Mismatch in length between original context data and loaded features.")
            original_context_df = None
            logging.warning("Disabling context display due to length mismatch.")

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

        if model_name == "model_simple":
            model = build_model_simple(num_players, num_venues, onehot_dim, player_emb_dim, venue_emb_dim)
        elif model_name == "model_deep_fc":
            model = build_model_deep_fc(num_players, num_venues, onehot_dim, player_emb_dim, venue_emb_dim, dropout_rate)
        elif model_name == "model_wide_fc":
            model = build_model_wide_fc(num_players, num_venues, onehot_dim, player_emb_dim=64, venue_emb_dim=16)
        elif model_name == "model_with_bn":
            model = build_model_with_bn(num_players, num_venues, onehot_dim, player_emb_dim, venue_emb_dim)
        else:
            logging.error(f"Unknown model architecture: {model_name}. Using default (simple).")
            model = build_model_simple(num_players, num_venues, onehot_dim, player_emb_dim, venue_emb_dim)

        logging.info("Model built.")
        mlflow.keras.log_model(model, f"model_{model_name}")

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

        logging.info("Saving validation predictions plot.")
        plt.figure(figsize=(10, 6))
        plt.scatter(target_val, val_predictions, alpha=0.3)
        plt.plot([target_val.min(), target_val.max()],
                 [target_val.min(), target_val.max()], 'r--')
        plt.xlabel('Actual Fantasy Points')
        plt.ylabel('Predicted Fantasy Points')
        plt.title(f'Validation Set: Actual vs Predicted ({model_name})')
        plot_filename = f'validation_predictions_{model_name}.png'
        plt.savefig(f'models/{plot_filename}')
        mlflow.log_artifact(f'models/{plot_filename}')
        plt.close()
        print(f"\nValidation plot saved to models/{plot_filename}")
        logging.info("Validation predictions plot saved successfully.")

        model_save_path = f"models/fantasy_model_{model_name}.h5"
        logging.info(f"Saving model at {model_save_path}")
        model.save(model_save_path,
                   save_format='h5',
                   include_optimizer=True)
        print(f"Model saved at {model_save_path}")
        print(f"Model tracked by MLflow as artifact 'model_{model_name}'.")
        logging.info("Model saved and tracked by MLflow.")

        logging.info("MLflow run finished.")

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model
import logging
import mlflow

def build_stage1_model(num_players, num_venues, player_emb_dim=128, venue_emb_dim=32, stage1_units=64):
    """
    Builds the first stage of the two-stage model, focusing on player and venue embeddings.
    """
    logging.info("Building Stage 1 model: Player/Venue Embeddings")
    mlflow.log_param("stage1_model_architecture", "embedding_model")
    mlflow.log_param("player_emb_dim", player_emb_dim)
    mlflow.log_param("venue_emb_dim", venue_emb_dim)
    mlflow.log_param("stage1_units", stage1_units)

    player_input = Input(shape=(1,), name='player_input')
    venue_input = Input(shape=(1,), name='venue_input')

    player_embedding = Embedding(input_dim=num_players, output_dim=player_emb_dim)(player_input)
    venue_embedding = Embedding(input_dim=num_venues, output_dim=venue_emb_dim)(venue_input)

    player_vec = Flatten()(player_embedding)
    venue_vec = Flatten()(venue_embedding)
    combined_embedding = Concatenate()([player_vec, venue_vec])
    x = Dense(stage1_units, activation='relu')(combined_embedding)  # Process combined embedding
    output = Dense(stage1_units, activation='linear', name='embedding_output')(x) # Output the embedding
    model = Model(inputs=[player_input, venue_input], outputs=output)
    logging.info("Stage 1 model compiled.")
    return model

def build_stage2_model(onehot_dim, embedding_dim, dense_units1=256, dense_units2=128):
    """
    Builds the second stage of the two-stage model, using pre-trained embeddings and one-hot inputs.

    Args:
        onehot_dim: Dimension of the one-hot encoded input.
        embedding_dim:  The dimension of the combined player/venue embedding (output from Stage 1).
        dense_units1: Number of units in the first dense layer.
        dense_units2: Number of units in the second dense layer.
    """
    logging.info("Building Stage 2 model: Contextual Prediction")
    mlflow.log_param("stage2_model_architecture", "context_model")
    mlflow.log_param("embedding_dim", embedding_dim)
    mlflow.log_param("dense_units1", dense_units1)
    mlflow.log_param("dense_units2", dense_units2)


    embedding_input = Input(shape=(embedding_dim,), name='embedding_input')  # Input for pre-trained embeddings
    onehot_input = Input(shape=(onehot_dim,), name='onehot_input')

    x = Concatenate()([embedding_input, onehot_input])
    x = Dense(dense_units1, activation='relu')(x)
    x = Dense(dense_units2, activation='relu')(x)
    output = Dense(1, activation='linear')(x)
    model = Model(inputs=[embedding_input, onehot_input], outputs=output)
    model.compile(optimizer='adam', loss='mse', metrics=['mae', 'mse'])
    logging.info("Stage 2 model compiled.")
    return model

def train(model_name="two_stage"):
    """
    Trains the two-stage model.
    """
    logging.info(f"Starting training function with model: {model_name}")
    mlflow.set_experiment("Fantasy Point Prediction - Model Comparison")

    with mlflow.start_run(run_name=model_name):
        logging.info(f"MLflow run started for model: {model_name}")
        params = load_params()
        epochs = params.get("epochs", 50)
        batch_size = params.get("batch_size", 32)
        test_size = params.get("test_size", 0.1)
        random_state = params.get("random_state", 42)
        player_emb_dim = params.get("player_embedding_dim", 128)  # Stage 1
        venue_emb_dim = params.get("venue_embedding_dim", 32)    # Stage 1
        stage1_units = params.get("stage1_units", 64) #stage 1
        dense_units1 = params.get("dense_units1", 256)  # Stage 2
        dense_units2 = params.get("dense_units2", 128)  # Stage 2

        mlflow.log_param("model_architecture", model_name)
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("player_emb_dim", player_emb_dim)  # Stage 1
        mlflow.log_param("venue_emb_dim", venue_emb_dim)    # Stage 1
        mlflow.log_param("stage1_units", stage1_units)
        mlflow.log_param("dense_units1", dense_units1)  # Stage 2
        mlflow.log_param("dense_units2", dense_units2)  # Stage 2

        try:
            original_df = pd.read_csv("data/Final_Fantasy_data.csv")
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

        if original_context_df is not None and len(original_context_df) != len(player_ids):
            logging.error(f"Mismatch in length between original context data and loaded features.")
            print("Error: Mismatch in length between original context data and loaded features.")
            original_context_df = None
            logging.warning("Disabling context display due to length mismatch.")

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

        # Build and train Stage 1:
        stage1_model = build_stage1_model(num_players, num_venues, player_emb_dim, venue_emb_dim, stage1_units)
        logging.info("Stage 1 model built.")
        stage1_model.fit(
            x=[player_train, venue_train],
            y=np.zeros((len(player_train), stage1_units)),  # Dummy target, we are learning representations
            epochs=epochs,  # Can be tuned separately
            batch_size=batch_size,
            verbose=0
        )
        logging.info("Stage 1 model trained.")

        # Get the embeddings for the training and validation sets
        embedding_train = stage1_model.predict([player_train, venue_train])
        embedding_val = stage1_model.predict([player_val, venue_val])
        logging.info("Embeddings from Stage 1 model obtained.")


        # Build and train Stage 2:
        stage2_model = build_stage2_model(onehot_dim, stage1_units, dense_units1, dense_units2) # stage1_units is the embedding dim
        logging.info("Stage 2 model built.")
        history = stage2_model.fit(
            x=[embedding_train, onehot_train],
            y=target_train,
            validation_data=([embedding_val, onehot_val], target_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)],
            verbose=2
        )
        logging.info("Stage 2 model trained.")

        logging.info("Evaluating model on the validation set.")
        val_loss, val_mae, val_mse = stage2_model.evaluate(
            [embedding_val, onehot_val],
            target_val,
            verbose=0
        )
        print(f"\nFinal Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")
        mlflow.log_metric("val_loss", val_loss)
        mlflow.log_metric("val_mae", val_mae)
        mlflow.log_metric("val_mse", val_mse)
        logging.info(f"Final Validation MSE: {val_mse:.4f}, MAE: {val_mae:.4f}")

        logging.info("Making predictions on the validation set.")
        val_predictions = stage2_model.predict([embedding_val, onehot_val])
        logging.info("Predictions made.")

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
            else:
                print(f"{actual:.1f}\t\t{predicted:.1f}\t\t{diff:+.1f}")
                logging.info(f"Sample {i} (no context): Actual={actual:.1f}, Predicted={predicted:.1f}, Difference={diff:+.1f}")
            mlflow.log_dict(log_dict, f"sample_prediction_{i}.json")
            sample_predictions_list.append(log_dict)

        logging.info("Saving validation predictions plot.")
        plt.figure(figsize=(10, 6))
        plt.scatter(target_val, val_predictions, alpha=0.3)
        plt.plot([target_val.min(), target_val.max()],
                 [target_val.min(), target_val.max()], 'r--')
        plt.xlabel('Actual Fantasy Points')
        plt.ylabel('Predicted Fantasy Points')
        plt.title(f'Validation Set: Actual vs Predicted ({model_name})')
        plot_filename = f'validation_predictions_{model_name}.png'
        plt.savefig(f'models/{plot_filename}')
        mlflow.log_artifact(f'models/{plot_filename}')
        plt.close()
        print(f"\nValidation plot saved to models/{plot_filename}")
        logging.info("Validation predictions plot saved successfully.")

        model_save_path = f"models/fantasy_model_{model_name}.h5"
        logging.info(f"Saving model at {model_save_path}")
        stage2_model.save(model_save_path, # Save stage 2
                   save_format='h5',
                   include_optimizer=True)
        print(f"Model saved at {model_save_path}")
        print(f"Model tracked by MLflow as artifact 'model_{model_name}'.")
        logging.info("Model saved and tracked by MLflow.")

        logging.info("MLflow run finished.")


if __name__ == "__main__":
    # Create 'data' and 'models' directories if they don't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    if not os.path.exists("data/player_ids.npy"):
        np.save("data/player_ids.npy", np.array([0, 1, 0, 2, 1]))
    if not os.path.exists("data/venue_ids.npy"):
        np.save("data/venue_ids.npy", np.array([0, 1, 0, 2, 1]))
    if not os.path.exists("data/onehot_inputs.npy"):
        np.save("data/onehot_inputs.npy", np.random.rand(5, 5))
    if not os.path.exists("data/target_fp.npy"):
        np.save("data/target_fp.npy", np.array([10.5, 15.2, 8.9, 12.1, 18.7]))
    print("Created dummy .npy data files. Please replace with your actual processed data.")

    # Run the two-stage model
    train(model_name="two_stage")
    logging.info("All model training runs completed.")


# if __name__ == "__main__":
#     # train()
#     # logging.info("Training script finished.")
#     # Run different model architectures
#     # train(model_name="model_simple")
#     # train(model_name="model_deep_fc")
#     # train(model_name="model_wide_fc")
#     # train(model_name="model_with_bn")
#     train(model_name="model_dual_path")
#     train(model_name="model_feature_fusion")
#     train(model_name="model_residual")
#     logging.info("All model training runs completed.")