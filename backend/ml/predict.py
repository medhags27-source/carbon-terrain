from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "models"
    / "event_travel_carbon_model.pkl"
)


model = joblib.load(MODEL_FILE)


def predict_event_carbon(
    participants: int,
    distance_km: float
) -> float:

    input_data = pd.DataFrame(
        [
            {
                "participants": participants,
                "distance_km": distance_km
            }
        ]
    )

    prediction = model.predict(input_data)[0]

    return round(float(prediction), 2)


def predict_event_travel_carbon(
    participants: int,
    distance_km: float
) -> dict:

    prediction_tco2e = predict_event_carbon(
        participants,
        distance_km
    )

    return {
        "prediction_tco2e": prediction_tco2e,
        "prediction_kgco2e": round(
            prediction_tco2e * 1000,
            2
        ),
        "unit": "tCO2e",
        "participants": participants,
        "distance_km": distance_km,
        "model": "Random Forest",
        "scope": "travel-related emissions",
        "dataset": "AGU conference travel dataset"
    }


if __name__ == "__main__":

    result = predict_event_travel_carbon(
        participants=100,
        distance_km=10
    )

    print(result)
