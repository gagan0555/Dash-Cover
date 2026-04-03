import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

# Ensure models directory exists
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def generate_synthetic_data(n_samples=500):
    """
    Generates synthetic data representing delivery worker behavior during a trigger event.
    Features:
      - drift_distance (meters)
      - claims_this_week (int)
      - speed_encoded (0=Stationary, 1=Low-Speed, 2=Moving, 3=High-Speed)
    """
    np.random.seed(42)
    data = []

    # 80% Genuine behavior (Normal)
    n_genuine = int(n_samples * 0.8)
    for _ in range(n_genuine):
        drift = np.random.exponential(scale=50) # Mostly within 50-100m drift
        claims = np.random.randint(0, 3) # 0 to 2 claims
        speed = np.random.choice([0, 1], p=[0.8, 0.2]) # Mostly stationary
        data.append([drift, claims, speed])

    # 20% Anomalous behavior (Fraud / Spoofers)
    n_fraud = n_samples - n_genuine
    for _ in range(n_fraud):
        drift = np.random.uniform(5000, 20000) # High drift (5km to 20km)
        claims = np.random.randint(3, 8) # High frequency claims
        speed = np.random.choice([2, 3], p=[0.5, 0.5]) # Moving or High-Speed during a storm
        data.append([drift, claims, speed])

    df = pd.DataFrame(data, columns=["drift_distance", "claims_this_week", "speed_encoded"])
    # Shuffle dataset
    df = df.sample(frac=1).reset_index(drop=True)
    
    # Save the synthetic dataset for tracking
    csv_path = os.path.join(MODEL_DIR, "claims_training.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {n_samples} synthetic rows to {csv_path}")
    return df

def train_and_export():
    df = generate_synthetic_data(500)
    
    X = df[["drift_distance", "claims_this_week", "speed_encoded"]].values

    # Fit a standard scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    # contamination=0.2 because we generated exactly 20% fraud anomalies
    clf = IsolationForest(n_estimators=100, contamination=0.2, random_state=42)
    clf.fit(X_scaled)

    # Save models
    model_path = os.path.join(MODEL_DIR, "isolation_forest.pkl")
    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    print(f"Saved IsolationForest model to {model_path}")
    print(f"Saved StandardScaler to {scaler_path}")

if __name__ == "__main__":
    print("Starting ML Fraud Model Pipeline...")
    train_and_export()
    print("Complete.")
