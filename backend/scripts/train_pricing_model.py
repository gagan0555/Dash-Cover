import os
import numpy as np
import pandas as pd
import xgboost as xgb
import pickle

# Ensure models directory exists
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def generate_pricing_data(n_samples=5000):
    """
    Generate synthetic training data for the pricing model.
    Features:
        - zone_type (categorical: 0=low, 1=medium, 2=high)
        - historical_disruptions (int)
        - avg_disruption_duration (float, hours)
        - month (1-12)
    Target:
        - risk_multiplier (float, 0.8 - 1.5)
    """
    np.random.seed(42)
    
    # 0 = Low Risk (e.g. South Delhi), 1 = Medium Risk (e.g. Gurugram), 2 = High Risk (e.g. Ghaziabad)
    zone_types = np.random.choice([0, 1, 2], size=n_samples, p=[0.4, 0.4, 0.2])
    
    historical_disruptions = []
    avg_durations = []
    months = np.random.randint(1, 13, size=n_samples)
    risk_multipliers = []
    
    for i in range(n_samples):
        zt = zone_types[i]
        m = months[i]
        
        # Base multiplier based on zone type
        base_mult = 0.8 if zt == 0 else 1.0 if zt == 1 else 1.2
        
        # Simulate disruptions based on zone
        if zt == 0:
            hist_d = np.random.randint(0, 5)
            dur = np.random.uniform(1.0, 3.0)
        elif zt == 1:
            hist_d = np.random.randint(2, 10)
            dur = np.random.uniform(2.0, 5.0)
        else:
            hist_d = np.random.randint(5, 20)
            dur = np.random.uniform(4.0, 10.0)
            
        # Summer (heat) and Monsoon (rain) increase risk
        if m in [5, 6, 7, 8]:
            hist_d += np.random.randint(2, 6)
            base_mult += 0.15
            
        # Calculate target multiplier (with some noise)
        mult = base_mult + (hist_d * 0.01) + (dur * 0.01)
        # Cap between 0.8 and 1.5
        mult = max(0.8, min(1.5, mult))
        
        historical_disruptions.append(hist_d)
        avg_durations.append(dur)
        risk_multipliers.append(mult)
        
    df = pd.DataFrame({
        "zone_type": zone_types,
        "historical_disruptions": historical_disruptions,
        "avg_duration": avg_durations,
        "month": months,
        "risk_multiplier": risk_multipliers
    })
    
    csv_path = os.path.join(MODEL_DIR, "pricing_training.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved {n_samples} pricing training rows to {csv_path}")
    return df

def train_pricing_model():
    df = generate_pricing_data()
    
    X = df[["zone_type", "historical_disruptions", "avg_duration", "month"]]
    y = df["risk_multiplier"]
    
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    
    model.fit(X, y)
    
    # Save model
    model_path = os.path.join(MODEL_DIR, "xgboost_pricing.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Saved XGBoost pricing model to {model_path}")
    
    # Feature importance
    importance = model.feature_importances_
    features = X.columns
    print("\nFeature Importances:")
    for feat, imp in zip(features, importance):
        print(f"  - {feat}: {imp:.4f}")

if __name__ == "__main__":
    print("Starting ML Pricing Model Training Pipeline...")
    train_pricing_model()
    print("Complete.")
