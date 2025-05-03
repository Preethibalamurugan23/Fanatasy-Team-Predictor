import mlflow
import mlflow.keras
import tensorflow as tf
import numpy as np
import os
from mlflow.models.signature import infer_signature
from tensorflow import keras # Import keras directly for the decorator


# Constants
ARTIFACTS_DIR = "processed_data"
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fantasy_model.h5")

@keras.saving.register_keras_serializable(package="CustomLosses")
def mse(y_true, y_pred):
    """Wrapper for Mean Squared Error."""
    return tf.keras.losses.MeanSquaredError()(y_true, y_pred)

@keras.saving.register_keras_serializable(package="CustomLosses")
def mae(y_true, y_pred):
    """Wrapper for Mean Absolute Error."""
    return tf.keras.losses.MeanAbsoluteError()(y_true, y_pred)


if __name__ == "__main__":
    # Load your Keras model
    model = tf.keras.models.load_model(
        MODEL_PATH,
        custom_objects={
            'mse': mse, # Use the registered function objects here
            'mae': mae
        }
    )
    # Set or create MLflow experiment
    mlflow.set_experiment("fantasy-ipl-prediction")

    # Prepare proper example input
    input_example = {
        "player_input": np.random.randint(0, 32, size=(1, 1), dtype=np.int32),
        "venue_input": np.random.randint(0, 8, size=(1, 1), dtype=np.int32),
        "onehot_input": np.random.rand(1, 30).astype(np.float32)
    }

    model_inputs_in_order = [
        input_example['player_input'],
        input_example['venue_input'],
        input_example['onehot_input']
    ]

    # Infer signature
    example_output = model.predict(model_inputs_in_order)
    signature = infer_signature(input_example, example_output)

    # Start MLflow run and log model
    with mlflow.start_run(run_name="fantasy_model_saving"):
        # Save model to a temporary directory
        temp_dir = "temp_saved_model"
        os.makedirs(temp_dir, exist_ok=True)

        mlflow.keras.save_model(
            model,
            path=temp_dir,
            input_example=input_example,
            signature=signature
        )

        # Log the entire temp folder manually
        mlflow.log_artifacts(temp_dir, artifact_path="model")

        print("✅ Model logged successfully with MLflow.")
