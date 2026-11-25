from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
FACTOR_FILE = BASE_DIR / "data" / "raw" / "emission_factors.csv"


def load_provenance():

    if not FACTOR_FILE.exists():
        raise FileNotFoundError(
            f"Emission factor file not found: {FACTOR_FILE}"
        )

    df = pd.read_csv(FACTOR_FILE)

    records = []

    for _, row in df.iterrows():

        source = str(row["source"]).strip()

        records.append({
            "factor_id": str(row["factor_id"]),
            "category": str(row["category"]),
            "subcategory": str(row["subcategory"]),
            "factor_value": float(row["factor_value"]),
            "unit": str(row["unit"]),
            "region": str(row["region"]),
            "source": source,
            "source_year": str(row["source_year"]).strip(),
            "data_status": (
                "assumption"
                if "placeholder" in source.lower()
                else "source-derived"
            )
        })

    return records


def get_factor_provenance(factor_id):

    for record in load_provenance():

        if record["factor_id"] == factor_id:
            return record

    return None


def build_event_provenance(event_state):

    provenance = {
        "event_inputs": [],
        "emission_factors": [],
        "data_quality": {
            "user_provided": [],
            "estimated": [],
            "source_derived": []
        }
    }

    input_fields = [
        "event_name",
        "event_type",
        "event_date",
        "days",
        "attendees",
        "budget",
        "venue",
        "distance_km",
        "meals",
        "energy_kwh",
        "waste_kg",
        "materials_kg"
    ]

    estimated_fields = {
        "distance_km",
        "meals",
        "energy_kwh",
        "waste_kg",
        "materials_kg"
    }

    for field in input_fields:

        if field not in event_state:
            continue

        value = event_state[field]

        if value is None:
            continue

        if field in estimated_fields:

            data_status = "estimated"
            provenance["data_quality"]["estimated"].append(field)

        else:

            data_status = "user-provided"
            provenance["data_quality"]["user_provided"].append(field)

        provenance["event_inputs"].append({
            "field": field,
            "value": value,
            "data_status": data_status
        })

    factor_ids = [
        "TF_BANGALORE_CAR_2W_AVG",
        "TF_BUS_AVG",
        "EF_ELECTRICITY_INDIA",
        "FOOD_VEG_MEAL",
        "FOOD_MIXED_MEAL",
        "WASTE_MIXED",
        "MATERIAL_REUSABLE"
    ]

    for factor_id in factor_ids:

        factor = get_factor_provenance(factor_id)

        if factor is None:
            continue

        provenance["emission_factors"].append(factor)

        if factor["data_status"] == "source-derived":
            provenance["data_quality"]["source_derived"].append(
                factor_id
            )
        else:
            provenance["data_quality"]["estimated"].append(
                factor_id
            )

    return provenance
