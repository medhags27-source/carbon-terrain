from pathlib import Path
import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FACTORS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "emission_factors.csv"
)


# =========================================================
# LOAD EMISSION FACTORS
# =========================================================

emission_factors = pd.read_csv(
    FACTORS_FILE
)


# =========================================================
# FACTOR LOOKUP
# =========================================================

def get_factor(
    factor_id: str
) -> float:
    """
    Return the emission factor associated
    with a factor ID.
    """

    row = emission_factors[
        emission_factors["factor_id"]
        == factor_id
    ]

    if row.empty:

        raise ValueError(
            f"Emission factor not found: "
            f"{factor_id}"
        )

    return float(
        row.iloc[0]["factor_value"]
    )


# =========================================================
# TRANSPORT
# =========================================================

def calculate_transport_emissions(
    passengers: int,
    distance_km: float,
    factor_id: str
) -> float:

    factor = get_factor(
        factor_id
    )

    return (
        passengers
        * distance_km
        * factor
    )


# =========================================================
# FOOD
# =========================================================

def calculate_food_emissions(
    meals: int,
    factor_id: str
) -> float:

    factor = get_factor(
        factor_id
    )

    return meals * factor


# =========================================================
# ENERGY
# =========================================================

def calculate_energy_emissions(
    energy_kwh: float,
    factor_id: str
) -> float:

    factor = get_factor(
        factor_id
    )

    return energy_kwh * factor


# =========================================================
# WASTE
# =========================================================

def calculate_waste_emissions(
    waste_kg: float,
    factor_id: str
) -> float:

    factor = get_factor(
        factor_id
    )

    return waste_kg * factor


# =========================================================
# MATERIALS
# =========================================================

def calculate_material_emissions(
    material_kg: float,
    factor_id: str
) -> float:

    factor = get_factor(
        factor_id
    )

    return material_kg * factor


# =========================================================
# TOTAL
# =========================================================

def calculate_total_emissions(
    transport: float,
    food: float,
    energy: float,
    waste: float,
    materials: float
) -> float:

    return (
        transport
        + food
        + energy
        + waste
        + materials
    )


# =========================================================
# EVENT FOOTPRINT
# =========================================================

def calculate_event_footprint(
    attendees: int,
    distance_km: float,
    meals: int,
    energy_kwh: float,
    waste_kg: float,
    materials_kg: float
) -> dict:

    # -----------------------------------------------------
    # TRANSPORT
    # -----------------------------------------------------
    #
    # This calculator represents the event's baseline
    # transport footprint using the private-car planning
    # factor.
    #
    # The optimizer separately evaluates alternative
    # transport allocations such as city bus.
    # -----------------------------------------------------

    transport = calculate_transport_emissions(
        passengers=attendees,
        distance_km=distance_km,
        factor_id="TF_PRIVATE_CAR_INDIA"
    )

    # -----------------------------------------------------
    # FOOD
    # -----------------------------------------------------

    food = calculate_food_emissions(
        meals=meals,
        factor_id="FOOD_VEG_MEAL"
    )

    # -----------------------------------------------------
    # ENERGY
    # -----------------------------------------------------

    energy = calculate_energy_emissions(
        energy_kwh=energy_kwh,
        factor_id="EF_ELECTRICITY_INDIA"
    )

    # -----------------------------------------------------
    # WASTE
    # -----------------------------------------------------

    waste = calculate_waste_emissions(
        waste_kg=waste_kg,
        factor_id="WASTE_MIXED"
    )

    # -----------------------------------------------------
    # MATERIALS
    # -----------------------------------------------------

    materials = calculate_material_emissions(
        material_kg=materials_kg,
        factor_id="MATERIAL_REUSABLE"
    )

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------

    total = calculate_total_emissions(
        transport=transport,
        food=food,
        energy=energy,
        waste=waste,
        materials=materials
    )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "transport": round(
            transport,
            2
        ),

        "food": round(
            food,
            2
        ),

        "energy": round(
            energy,
            2
        ),

        "waste": round(
            waste,
            2
        ),

        "materials": round(
            materials,
            2
        ),

        "total_co2e": round(
            total,
            2
        )
    }