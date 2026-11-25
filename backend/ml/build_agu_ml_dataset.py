from pathlib import Path
import pandas as pd


# ==================================================
# PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOCATIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "agu_travel_clean.csv"
)

COUNTRY_EMISSIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "conference_travel"
    / "AGU"
    / "data"
    / "emissions_per_country.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "agu_ml_dataset.csv"
)


# ==================================================
# LOAD DATA
# ==================================================

locations = pd.read_csv(LOCATIONS_FILE)
country_emissions = pd.read_csv(COUNTRY_EMISSIONS_FILE)

print("\nLOADED DATA")
print("=" * 60)
print("Location rows:", len(locations))
print("Country rows:", len(country_emissions))


# ==================================================
# CLEAN COUNTRY NAMES
# ==================================================

locations["country"] = (
    locations["country"]
    .astype(str)
    .str.strip()
)

country_emissions["country"] = (
    country_emissions["country"]
    .astype(str)
    .str.strip()
)


# ==================================================
# SELECT COUNTRY EMISSION INFORMATION
# ==================================================

country_emissions = country_emissions[
    [
        "country",
        "N",
        "emissions [tCO2e]",
        "emissions_per_capita [tCO2e]",
    ]
].copy()

country_emissions = country_emissions.rename(
    columns={
        "N": "country_participants",
        "emissions [tCO2e]": "country_emissions_tco2e",
        "emissions_per_capita [tCO2e]":
            "country_emissions_per_participant_tco2e",
    }
)


# ==================================================
# MERGE CITY DATA WITH COUNTRY EMISSIONS
# ==================================================

df = locations.merge(
    country_emissions,
    on="country",
    how="left",
    validate="many_to_one"
)


# ==================================================
# CHECK FOR UNMATCHED COUNTRIES
# ==================================================

missing = df[
    df["country_emissions_per_participant_tco2e"].isna()
]

if len(missing) > 0:

    print("\nWARNING: UNMATCHED COUNTRIES")
    print(
        missing["country"]
        .drop_duplicates()
        .tolist()
    )

else:

    print("\nAll countries matched successfully.")


# ==================================================
# CALCULATE CITY-LEVEL TRAVEL EMISSIONS
# ==================================================

df["travel_emissions_tco2e"] = (
    df["participants"]
    * df["country_emissions_per_participant_tco2e"]
)


# Convert tonnes to kilograms
df["travel_emissions_kgco2e"] = (
    df["travel_emissions_tco2e"] * 1000
)


# ==================================================
# ADD USEFUL ML FEATURES
# ==================================================

df["log_distance_km"] = (
    df["distance_km"].clip(lower=1).apply(
        lambda x: __import__("math").log1p(x)
    )
)

df["log_participants"] = (
    df["participants"].clip(lower=1).apply(
        lambda x: __import__("math").log1p(x)
    )
)

df["event_year"] = 2019


# ==================================================
# FINAL DATASET
# ==================================================

df = df[
    [
        "source",
        "event_year",
        "event_name",
        "data_type",
        "country",
        "state",
        "city",
        "latitude",
        "longitude",
        "participants",
        "distance_km",
        "total_distance_km",
        "round_trip_distance_km",
        "country_participants",
        "country_emissions_tco2e",
        "country_emissions_per_participant_tco2e",
        "travel_emissions_tco2e",
        "travel_emissions_kgco2e",
        "log_distance_km",
        "log_participants",
    ]
]


# ==================================================
# SAVE
# ==================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==================================================
# VALIDATION REPORT
# ==================================================

print("\nAGU ML DATASET")
print("=" * 60)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print(
    "Unique countries:",
    df["country"].nunique()
)

print(
    "Total participants:",
    int(df["participants"].sum())
)

print(
    "Total reconstructed travel emissions:",
    round(df["travel_emissions_tco2e"].sum(), 2),
    "tCO2e"
)

print(
    "AGU reported total:",
    round(country_emissions["country_emissions_tco2e"].sum(), 2),
    "tCO2e"
)

print(
    "Average city travel emissions:",
    round(df["travel_emissions_tco2e"].mean(), 3),
    "tCO2e"
)

print(
    "Maximum city travel emissions:",
    round(df["travel_emissions_tco2e"].max(), 3),
    "tCO2e"
)

print("\nFIRST 10 ROWS")
print("=" * 60)
print(
    df.head(10).to_string(index=False)
)

print("\nSaved to:")
print(OUTPUT_FILE)