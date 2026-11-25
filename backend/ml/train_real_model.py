from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

import joblib


# ==================================================
# PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = PROJECT_ROOT / "data" / "processed" / "agu_ml_dataset.csv"

MODEL_DIR = PROJECT_ROOT / "backend" / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# LOAD DATA
# ==================================================

df = pd.read_csv(DATA_FILE)

print("\nDATA LOADED")
print("=" * 60)
print("Rows:", len(df))


# ==================================================
# FEATURES AND TARGET
# ==================================================

features = [
    "participants",
    "distance_km",
]

target = "travel_emissions_tco2e"

X = df[features]
y = df[target]

print("\nFEATURES")
print(features)

print("\nTARGET")
print(target)


# ==================================================
# TRAIN / TEST SPLIT
# ==================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nDATA SPLIT")
print("=" * 60)
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# ==================================================
# MODELS
# ==================================================

models = {
    "Linear Regression": LinearRegression(),

    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    ),

    "XGBoost": XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="reg:squarederror"
    )
}


# ==================================================
# TRAIN + EVALUATE
# ==================================================

results = []

for name, model in models.items():

    print("\nTraining:", name)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    results.append(
        {
            "Model": name,
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2
        }
    )

    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R2:   {r2:.4f}")


# ==================================================
# MODEL COMPARISON
# ==================================================

results_df = pd.DataFrame(results)

print("\nMODEL COMPARISON")
print("=" * 60)

print(
    results_df.to_string(
        index=False
    )
)


# ==================================================
# SELECT BEST MODEL
# ==================================================

best_model_name = (
    results_df
    .sort_values("RMSE")
    .iloc[0]["Model"]
)

best_model = models[best_model_name]


# ==================================================
# SAVE BEST MODEL
# ==================================================

MODEL_FILE = (
    MODEL_DIR
    / "event_travel_carbon_model.pkl"
)

joblib.dump(
    best_model,
    MODEL_FILE
)


# ==================================================
# FINAL OUTPUT
# ==================================================

best_row = results_df[
    results_df["Model"] == best_model_name
].iloc[0]

print("\nBEST MODEL BY RMSE")
print("=" * 60)
print("Model:", best_model_name)
print(f"MAE:  {best_row['MAE']:.4f}")
print(f"RMSE: {best_row['RMSE']:.4f}")
print(f"R2:   {best_row['R2']:.4f}")

print("\nMODEL SAVED TO:")
print(MODEL_FILE)
