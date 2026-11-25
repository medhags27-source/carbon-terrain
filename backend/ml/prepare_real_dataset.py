from pathlib import Path
import pandas as pd


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AGU_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "conference_travel"
    / "AGU"
    / "data"
    / "locations.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "agu_travel_clean.csv"
)


# --------------------------------------------------
# LOAD RAW AGU DATA
# --------------------------------------------------

df = pd.read_csv(AGU_FILE)

print("\nRAW AGU DATA")
print("=" * 50)
print("Rows:", len(df))
print("Columns:", len(df.columns))


# --------------------------------------------------
# SELECT RELEVANT COLUMNS
# --------------------------------------------------

df = df[
    [
        "N",
        "country",
        "state",
        "city",
        "lat",
        "lon",
        "dist",
    ]
].copy()


# --------------------------------------------------
# RENAME COLUMNS
# --------------------------------------------------

df = df.rename(
    columns={
        "N": "participants",
        "country": "country",
        "state": "state",
        "city": "city",
        "lat": "latitude",
        "lon": "longitude",
        "dist": "distance_km",
    }
)


# --------------------------------------------------
# CLEAN TEXT
# --------------------------------------------------

df["country"] = df["country"].astype(str).str.strip()
df["city"] = df["city"].astype(str).str.strip()

df["state"] = (
    df["state"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# --------------------------------------------------
# NUMERIC CLEANING
# --------------------------------------------------

numeric_columns = [
    "participants",
    "latitude",
    "longitude",
    "distance_km",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# --------------------------------------------------
# REMOVE INVALID RECORDS
# --------------------------------------------------

df = df.dropna(
    subset=[
        "participants",
        "distance_km",
        "latitude",
        "longitude",
    ]
)

df = df[df["participants"] > 0]
df = df[df["distance_km"] >= 0]


# --------------------------------------------------
# ADD DATASET METADATA
# --------------------------------------------------

df["source"] = "AGU"
df["event_year"] = 2019
df["event_name"] = "AGU Fall Meeting 2019"
df["data_type"] = "REAL_TRAVEL_DATA"


# --------------------------------------------------
# CALCULATED FEATURES
# --------------------------------------------------

# Estimated total one-way travel distance
df["total_distance_km"] = (
    df["participants"] * df["distance_km"]
)

# Round-trip distance
df["round_trip_distance_km"] = (
    df["total_distance_km"] * 2
)

# Average distance per participant
df["distance_per_participant_km"] = (
    df["distance_km"]
)


# --------------------------------------------------
# FINAL COLUMN ORDER
# --------------------------------------------------

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
        "distance_per_participant_km",
    ]
]


# --------------------------------------------------
# SAVE
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# REPORT
# --------------------------------------------------

print("\nCLEAN AGU DATA")
print("=" * 50)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print(
    "Total participants:",
    int(df["participants"].sum())
)

print(
    "Average distance:",
    round(df["distance_km"].mean(), 2),
    "km"
)

print(
    "Maximum distance:",
    round(df["distance_km"].max(), 2),
    "km"
)

print(
    "Total round-trip distance:",
    round(df["round_trip_distance_km"].sum(), 2),
    "km"
)

print("\nFIRST 10 CLEAN ROWS")
print("=" * 50)
print(df.head(10).to_string(index=False))

print("\nSaved to:")
print(OUTPUT_FILE)