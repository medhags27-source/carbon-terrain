import pandas as pd
from pathlib import Path

from backend.optimizer.event_optimizer import optimize_event


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

FACTORS_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "emission_factors.csv"
)


# =========================================================
# EMISSION FACTOR LOADER
# =========================================================

def load_factor(name: str) -> float:

    if not FACTORS_FILE.exists():
        raise FileNotFoundError(
            f"Emission factor file not found: {FACTORS_FILE}"
        )

    df = pd.read_csv(FACTORS_FILE)

    row = df[
        df["factor_id"] == name
    ]

    if row.empty:
        raise ValueError(
            f"Emission factor not found: {name}"
        )

    return float(
        row.iloc[0]["factor_value"]
    )


# =========================================================
# SOURCE-BACKED FACTORS
# =========================================================

ELECTRICITY_EF = load_factor(
    "EF_ELECTRICITY_INDIA"
)

WASTE_EF = load_factor(
    "WASTE_MIXED"
)

MATERIAL_EF = load_factor(
    "MATERIAL_REUSABLE"
)

MIXED_FOOD_EF = load_factor(
    "FOOD_MIXED_MEAL"
)

VEG_FOOD_EF = load_factor(
    "FOOD_VEG_MEAL"
)


# =========================================================
# CALCULATE INTERVENTIONS
# =========================================================

def calculate_interventions(
    event_state: dict
):

    attendees = int(
        event_state.get(
            "attendees",
            0
        )
    )

    distance_km = float(
        event_state.get(
            "distance_km",
            0
        )
    )

    energy_kwh = float(
        event_state.get(
            "energy_kwh",
            0
        )
    )

    meals = int(
        event_state.get(
            "meals",
            0
        )
    )

    waste_kg = float(
        event_state.get(
            "waste_kg",
            0
        )
    )

    materials_kg = float(
        event_state.get(
            "materials_kg",
            0
        )
    )

    interventions = []


    # =====================================================
    # TRANSPORT
    # =====================================================

    transport = optimize_event(
        attendees=attendees,
        distance_km=distance_km,
        budget=max(
            attendees * 300,
            1
        ),
        max_car_percent=30,
    )

    if transport.get("status") == "optimal":

        baseline = transport[
            "baseline"
        ]

        optimized = transport[
            "optimized"
        ]

        transport_saving = max(
            0,
            baseline["co2_kg"]
            - optimized["co2_kg"]
        )

        transport_cost_change = (
            optimized["cost"]
            - baseline["cost"]
        )

        if transport_saving > 0:

            # If transport optimization saves money,
            # represent the intervention cost as zero.
            #
            # Its actual financial impact is preserved
            # separately so that the decision engine can
            # recognize it as a cost-saving intervention.

            transport_cost = max(
                0,
                transport_cost_change
            )

            interventions.append({

                "id": "transport",

                "name": (
                    "Transport Optimization"
                ),

                "cost_inr": round(
                    transport_cost,
                    2
                ),

                "co2_saved_kg": round(
                    transport_saving,
                    2
                ),

                "basis": (
                    "Calculated by the constraint-based "
                    "transport optimizer using attendance, "
                    "travel distance, budget and configured "
                    "India-specific transport emission factors."
                ),

                "details": {

                    "baseline": baseline,

                    "optimized": optimized,

                    "cost_change_inr": round(
                        transport_cost_change,
                        2
                    ),

                    "factors": transport[
                        "transport_factors"
                    ]
                }
            })


    # =====================================================
    # ENERGY
    # =====================================================

    energy_reduction = (
        energy_kwh * 0.15
    )

    energy_saving = (
        energy_reduction
        * ELECTRICITY_EF
    )

    # Planning cost assumption.
    energy_cost = (
        energy_reduction * 12
    )

    if energy_saving > 0:

        interventions.append({

            "id": "energy",

            "name": (
                "Energy Optimization"
            ),

            "cost_inr": round(
                energy_cost,
                2
            ),

            "co2_saved_kg": round(
                energy_saving,
                2
            ),

            "basis": (
                "Estimated 15% reduction in electricity "
                "consumption through efficiency measures."
            ),

            "assumption": (
                "15% electricity reduction."
            )
        })


    # =====================================================
    # WASTE
    # =====================================================

    waste_reduction = (
        waste_kg * 0.25
    )

    waste_saving = (
        waste_reduction
        * WASTE_EF
    )

    # Planning cost assumption.
    waste_cost = (
        waste_reduction * 20
    )

    if waste_saving > 0:

        interventions.append({

            "id": "waste",

            "name": (
                "Waste Reduction"
            ),

            "cost_inr": round(
                waste_cost,
                2
            ),

            "co2_saved_kg": round(
                waste_saving,
                2
            ),

            "basis": (
                "Estimated 25% reduction in event waste "
                "through prevention and segregation."
            ),

            "assumption": (
                "25% waste reduction."
            )
        })


    # =====================================================
    # MATERIALS
    # =====================================================

    material_reduction = (
        materials_kg * 0.30
    )

    material_saving = (
        material_reduction
        * MATERIAL_EF
    )

    # Planning cost assumption.
    material_cost = (
        material_reduction * 70
    )

    if material_saving > 0:

        interventions.append({

            "id": "materials",

            "name": (
                "Reusable Materials"
            ),

            "cost_inr": round(
                material_cost,
                2
            ),

            "co2_saved_kg": round(
                material_saving,
                2
            ),

            "basis": (
                "Estimated 30% reduction in material "
                "consumption through reusable materials."
            ),

            "assumption": (
                "30% material reduction."
            )
        })


    # =====================================================
    # FOOD
    # =====================================================

    saving_per_meal = max(
        MIXED_FOOD_EF
        - VEG_FOOD_EF,
        0
    )

    shifted_meals = (
        meals * 0.30
    )

    food_saving = (
        shifted_meals
        * saving_per_meal
    )

    # Planning cost assumption.
    food_cost = (
        shifted_meals * 8
    )

    if food_saving > 0:

        interventions.append({

            "id": "food",

            "name": (
                "Lower-Carbon Food"
            ),

            "cost_inr": round(
                food_cost,
                2
            ),

            "co2_saved_kg": round(
                food_saving,
                2
            ),

            "basis": (
                "Estimated 30% of meals shifted toward "
                "the configured lower-carbon meal factor."
            ),

            "assumption": (
                "30% of meals shifted."
            )
        })


    # =====================================================
    # EFFICIENCY RANKING
    # =====================================================

    for intervention in interventions:

        cost = float(
            intervention[
                "cost_inr"
            ]
        )

        saving = float(
            intervention[
                "co2_saved_kg"
            ]
        )

        # -------------------------------------------------
        # Positive-cost intervention
        # -------------------------------------------------

        if cost > 0:

            intervention[
                "kg_saved_per_1000_inr"
            ] = round(
                (
                    saving
                    / cost
                ) * 1000,
                4
            )

            intervention[
                "financial_effect"
            ] = "additional_cost"


        # -------------------------------------------------
        # Zero-cost intervention
        # -------------------------------------------------

        else:

            # A zero-cost emission reduction is more
            # efficient than any positive-cost intervention.
            #
            # Use infinity internally so it ranks first,
            # while exposing a readable label to the API.

            intervention[
                "kg_saved_per_1000_inr"
            ] = None

            intervention[
                "financial_effect"
            ] = "cost_saving_or_zero_cost"


    # -----------------------------------------------------
    # Sort:
    #
    # 1. Cost-saving / zero-cost interventions first
    # 2. Then highest CO2 saving per ₹1000
    # -----------------------------------------------------

    interventions.sort(
        key=lambda item: (
            0
            if item["cost_inr"] <= 0
            else 1,

            -(
                item["co2_saved_kg"]
                if item["cost_inr"] <= 0
                else item["kg_saved_per_1000_inr"]
            )
        )
    )


    return interventions


# =========================================================
# SELECT BEST INTERVENTIONS
# =========================================================

def select_best_interventions(
    interventions,
    extra_budget
):

    remaining_budget = float(
        extra_budget
    )

    selected = []

    total_cost = 0.0

    total_saving = 0.0


    for intervention in interventions:

        cost = float(
            intervention[
                "cost_inr"
            ]
        )

        # -------------------------------------------------
        # Cost-saving / zero-cost intervention
        # -------------------------------------------------

        if cost <= 0:

            selected.append(
                intervention
            )

            total_saving += (
                intervention[
                    "co2_saved_kg"
                ]
            )

            continue


        # -------------------------------------------------
        # Positive-cost intervention
        # -------------------------------------------------

        if cost <= remaining_budget:

            selected.append(
                intervention
            )

            remaining_budget -= cost

            total_cost += cost

            total_saving += (
                intervention[
                    "co2_saved_kg"
                ]
            )


    return {

        "selected": selected,

        "total_cost_inr": round(
            total_cost,
            2
        ),

        "total_co2_saved_kg": round(
            total_saving,
            2
        ),

        "remaining_budget_inr": round(
            remaining_budget,
            2
        )
    }


# =========================================================
# ANALYZE EVENT IMPACT
# =========================================================

def analyze_event_impact(
    event_state,
    extra_budget
):

    extra_budget = float(
        extra_budget
    )

    interventions = (
        calculate_interventions(
            event_state
        )
    )

    optimization = (
        select_best_interventions(
            interventions,
            extra_budget
        )
    )

    total_saving = optimization[
        "total_co2_saved_kg"
    ]


    if optimization[
        "selected"
    ]:

        names = [
            item["name"]
            for item
            in optimization[
                "selected"
            ]
        ]

        recommendation = (
            f"With ₹{extra_budget:,.0f} "
            f"extra budget, the best "
            f"combination is: "
            f"{', '.join(names)}. "
            f"Estimated CO2e reduction: "
            f"{total_saving:,.2f} kg."
        )

    else:

        recommendation = (
            f"No calculated intervention "
            f"fits within the extra budget "
            f"of ₹{extra_budget:,.0f}."
        )


    return {

        "extra_budget_inr": round(
            extra_budget,
            2
        ),

        "interventions_ranked":
            interventions,

        "optimization":
            optimization,

        "recommendation":
            recommendation,

        "method": (
            "Interventions are ranked by "
            "estimated marginal CO2e reduction "
            "per ₹1,000 of additional budget, "
            "with cost-saving or zero-cost "
            "interventions prioritized first."
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    example_event = {

        "attendees": 1000,

        "distance_km": 10,

        "energy_kwh": 1000,

        "meals": 2000,

        "waste_kg": 200,

        "materials_kg": 100
    }


    result = analyze_event_impact(
        example_event,
        50000
    )


    print(
        "\n=== IMPACT OPTIMIZER ==="
    )


    for item in result[
        "interventions_ranked"
    ]:

        efficiency = (
            "Cost-saving / zero-cost"
            if item["kg_saved_per_1000_inr"] is None
            else f'{item["kg_saved_per_1000_inr"]:.4f}'
        )

        print(
            f'{item["name"]} | '
            f'Cost: ₹'
            f'{item["cost_inr"]:.2f} | '
            f'Saving: '
            f'{item["co2_saved_kg"]:.2f} kg | '
            f'kg/₹1000: '
            f'{efficiency}'
        )


    print(
        "\nRecommendation:"
    )

    print(
        result[
            "recommendation"
        ]
    )