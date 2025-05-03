# preprocess.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import joblib
import os
import logging

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/preprocess.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s"
)

def preprocess(csv_path, output_dir="processed_data"):
    logging.info(f"Starting preprocessing for {csv_path}")

    df = pd.read_csv(csv_path)
    logging.info(f"Data loaded successfully. Shape: {df.shape}")
    print(f"Data loaded. Shape: {df.shape}")

    # Sanity check
    print("Unique home teams:", df['home_team'].unique())
    print("Unique away teams:", df['away_team'].unique())
    print("Unique batting innings:", df['batting_innings'].unique())

    # Label Encode player and venue
    player_encoder = LabelEncoder()
    venue_encoder = LabelEncoder()

    df['player_id'] = player_encoder.fit_transform(df['fullName'])
    df['venue_id'] = venue_encoder.fit_transform(df['venue'])
    logging.info("Player and Venue label encoding completed.")
    print(f"Player Encoder classes: {len(player_encoder.classes_)}")
    print(f"Venue Encoder classes: {len(venue_encoder.classes_)}")

    # Save encoders
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(player_encoder, os.path.join(output_dir, 'player_encoder.pkl'))
    joblib.dump(venue_encoder, os.path.join(output_dir, 'venue_encoder.pkl'))
    logging.info("Encoders saved.")

    # Only use home_team, away_team, batting_innings
    feature_cols = ['home_team', 'away_team', 'batting_innings']

    # Normalize text columns
    for col in ['home_team', 'away_team']:
        df[col] = df[col].str.strip().str.upper()  # Uppercase for consistency

    onehot_encoder = OneHotEncoder(sparse=False)
    onehot_features = onehot_encoder.fit_transform(df[feature_cols])
    print(f"One-hot encoded feature shape: {onehot_features.shape}")
    logging.info("One-hot encoding completed.")

    # Save one-hot encoder
    joblib.dump(onehot_encoder, os.path.join(output_dir, 'onehot_encoder.pkl'))

    # Create arrays
    player_ids = df['player_id'].values
    venue_ids = df['venue_id'].values
    target_fp = df['Total_FP'].values

    
    

    # Save arrays
    np.save(os.path.join(output_dir, 'player_ids.npy'), player_ids)
    np.save(os.path.join(output_dir, 'venue_ids.npy'), venue_ids)
    np.save(os.path.join(output_dir, 'onehot_inputs.npy'), onehot_features)
    np.save(os.path.join(output_dir, 'target_fp.npy'), target_fp)
    
    logging.info("Processed arrays saved successfully.")

    print("Preprocessing complete. Files saved.")

if __name__ == "__main__":
    preprocess(r"C:/Users/Preethi/Downloads/mlops_project/data/Final_Fantasy_data.csv")
