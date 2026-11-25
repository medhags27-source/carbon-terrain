from pathlib import Path
import random
import pandas as pd

from backend.calculator.carbon_calculator import calculate_event_footprint


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "ml_dataset.csv"


# Reproducibility
random.seed(42)


records = []


# Generate 2000 synthetic event scenarios
for _ in range(2000):

    attendees = random.randint(50, 1000)

    distance_km = round(
        random.uniform(2, 30),
        2
    )

    meals = attendees

    energy_kwh = round(
        random.uniform(100, 5000),
        2
    )

    waste_kg = round(
        attendees * random.uniform(0.1, 1.0),
        2
    )

    materials_kg = round(
        attendees * random.uniform(0.02, 0.3),
        2
    )


    # Calculate true carbon footprint
    result = calculate_event_footprint(
        attendees=attendees,
        distance_km=distance_km,
        meals=meals,
        energy_kwh=energy_kwh,
        waste_kg=waste_kg,
        materials_kg=materials_kg
    )


    records.append({
        "attendees": attendees,
        "distance_km": distance_km,
        "meals": meals,
        "energy_kwh": energy_kwh,
        "waste_kg": waste_kg,
        "materials_kg": materials_kg,

        "transport_co2e": result["transport"],
        "food_co2e": result["food"],
        "energy_co2e": result["energy"],
        "waste_co2e": result["waste"],
        "materials_co2e": result["materials"],

        "total_co2e": result["total_co2e"]
    })


# Convert to DataFrame
df = pd.DataFrame(records)


# Save dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nML DATASET GENERATED")
print("----------------------------")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nFirst 5 rows:")
print(df.head())

print("\nDataset statistics:")
print(df.describe())