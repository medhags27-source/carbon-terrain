from pathlib import Path

import pandas as pd
from ortools.linear_solver import pywraplp


# =========================================================
# EMISSION FACTOR LOADER
# =========================================================

FACTOR_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "emission_factors.csv"
)


def load_factor(factor_id: str) -> float:
    """
    Load an emission factor directly from the project's
    emission_factors.csv file.
    """

    if not FACTOR_FILE.exists():
        raise FileNotFoundError(
            f"Emission factor file not found: {FACTOR_FILE}"
        )

    factors = pd.read_csv(FACTOR_FILE)

    match = factors[
        factors["factor_id"] == factor_id
    ]

    if match.empty:
        raise ValueError(
            f"Emission factor '{factor_id}' "
            "was not found in emission_factors.csv."
        )

    return float(
        match.iloc[0]["factor_value"]
    )


# =========================================================
# EVENT OPTIMIZER
# =========================================================

def optimize_event(
    attendees: int,
    distance_km: float,
    budget: float,
    max_car_percent: float = 30,
):
    """
    Multi-constraint transportation optimizer.

    Objective:
        Minimize estimated transportation CO2e.

    Constraints:
        1. All attendees must be assigned.
        2. Private-car usage cannot exceed the configured
           maximum percentage.
        3. Transportation cost cannot exceed the budget.
    """

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if attendees < 1:
        return {
            "status": "infeasible",
            "message": "Attendees must be at least 1."
        }

    if distance_km < 0:
        return {
            "status": "infeasible",
            "message": "Distance cannot be negative."
        }

    if budget < 0:
        return {
            "status": "infeasible",
            "message": "Budget cannot be negative."
        }

    if not 0 <= max_car_percent <= 100:
        return {
            "status": "infeasible",
            "message": (
                "Maximum private-car percentage "
                "must be between 0 and 100."
            )
        }

    # -----------------------------------------------------
    # LOAD INDIA-SPECIFIC TRANSPORT FACTORS
    # -----------------------------------------------------

    car_factor = load_factor(
        "TF_PRIVATE_CAR_INDIA"
    )

    bus_factor = load_factor(
        "TF_CITY_BUS_INDIA"
    )

    # -----------------------------------------------------
    # TRANSPORT COST ASSUMPTIONS
    # -----------------------------------------------------
    #
    # These are operational planning assumptions.
    # They are NOT emission factors.
    #
    # Later these can be replaced by actual organizer
    # transport costs.
    # -----------------------------------------------------

    car_cost_per_person = 300.0
    bus_cost_per_person = 80.0

    # -----------------------------------------------------
    # MAXIMUM PRIVATE-CAR ATTENDEES
    # -----------------------------------------------------

    max_car_attendees = int(
        attendees
        * max_car_percent
        / 100
    )

    # -----------------------------------------------------
    # MINIMUM POSSIBLE TRANSPORT COST
    #
    # All attendees use bus.
    # -----------------------------------------------------

    minimum_transport_cost = (
        attendees
        * bus_cost_per_person
    )

    if budget < minimum_transport_cost:

        return {
            "status": "infeasible",

            "message": (
                "The available budget is too low "
                "to transport all attendees under "
                "the current planning assumptions."
            ),

            "minimum_required_budget": (
                minimum_transport_cost
            ),

            "available_budget": budget,
        }

    # -----------------------------------------------------
    # BASELINE
    # -----------------------------------------------------
    #
    # Baseline = highest feasible private-car allocation
    # under the current percentage and budget constraints.
    # -----------------------------------------------------

    if car_cost_per_person == bus_cost_per_person:

        baseline_car_attendees = max_car_attendees

    else:

        baseline_car_attendees = int(
            (
                budget
                - attendees * bus_cost_per_person
            )
            /
            (
                car_cost_per_person
                - bus_cost_per_person
            )
        )

        baseline_car_attendees = min(
            baseline_car_attendees,
            max_car_attendees
        )

    baseline_car_attendees = max(
        0,
        min(
            baseline_car_attendees,
            attendees
        )
    )

    baseline_bus_attendees = (
        attendees
        - baseline_car_attendees
    )

    baseline_cost = (
        baseline_car_attendees
        * car_cost_per_person
        +
        baseline_bus_attendees
        * bus_cost_per_person
    )

    baseline_co2 = (
        baseline_car_attendees
        * distance_km
        * car_factor
        +
        baseline_bus_attendees
        * distance_km
        * bus_factor
    )

    # -----------------------------------------------------
    # CREATE OR-TOOLS SOLVER
    # -----------------------------------------------------

    solver = pywraplp.Solver.CreateSolver(
        "SCIP"
    )

    if solver is None:

        return {
            "status": "error",
            "message": (
                "OR-Tools SCIP solver is unavailable."
            )
        }

    # -----------------------------------------------------
    # DECISION VARIABLES
    # -----------------------------------------------------

    car_attendees = solver.IntVar(
        0,
        max_car_attendees,
        "car_attendees"
    )

    bus_attendees = solver.IntVar(
        0,
        attendees,
        "bus_attendees"
    )

    # -----------------------------------------------------
    # CONSTRAINT 1
    # ALL ATTENDEES MUST BE ASSIGNED
    # -----------------------------------------------------

    solver.Add(
        car_attendees
        + bus_attendees
        == attendees
    )

    # -----------------------------------------------------
    # CONSTRAINT 2
    # TOTAL TRANSPORT COST <= BUDGET
    # -----------------------------------------------------

    total_cost = (
        car_attendees
        * car_cost_per_person
        +
        bus_attendees
        * bus_cost_per_person
    )

    solver.Add(
        total_cost <= budget
    )

    # -----------------------------------------------------
    # OBJECTIVE
    # MINIMIZE TRANSPORT CO2E
    # -----------------------------------------------------

    total_co2 = (
        car_attendees
        * distance_km
        * car_factor
        +
        bus_attendees
        * distance_km
        * bus_factor
    )

    solver.Minimize(
        total_co2
    )

    # -----------------------------------------------------
    # SOLVE
    # -----------------------------------------------------

    status = solver.Solve()

    if status != pywraplp.Solver.OPTIMAL:

        return {
            "status": "infeasible",

            "message": (
                "No feasible transportation plan "
                "was found under the current constraints."
            ),

            "baseline": {
                "car_attendees": (
                    baseline_car_attendees
                ),

                "bus_attendees": (
                    baseline_bus_attendees
                ),

                "cost": round(
                    baseline_cost,
                    2
                ),

                "co2_kg": round(
                    baseline_co2,
                    2
                ),
            }
        }

    # -----------------------------------------------------
    # OPTIMIZED PLAN
    # -----------------------------------------------------

    optimized_car_attendees = int(
        round(
            car_attendees.solution_value()
        )
    )

    optimized_bus_attendees = int(
        round(
            bus_attendees.solution_value()
        )
    )

    optimized_cost = (
        optimized_car_attendees
        * car_cost_per_person
        +
        optimized_bus_attendees
        * bus_cost_per_person
    )

    optimized_co2 = (
        optimized_car_attendees
        * distance_km
        * car_factor
        +
        optimized_bus_attendees
        * distance_km
        * bus_factor
    )

    # -----------------------------------------------------
    # IMPACT
    # -----------------------------------------------------

    carbon_saved = max(
        0.0,
        baseline_co2
        - optimized_co2
    )

    cost_change = (
        optimized_cost
        - baseline_cost
    )

    # -----------------------------------------------------
    # EXPLANATION
    # -----------------------------------------------------

    if optimized_car_attendees < baseline_car_attendees:

        explanation = (
            "The optimizer reduced private-car usage "
            "because the configured city-bus emission "
            "factor is lower than the private-car factor."
        )

    elif optimized_car_attendees > baseline_car_attendees:

        explanation = (
            "The optimizer increased private-car usage "
            "because the configured private-car emission "
            "factor is lower than the city-bus factor."
        )

    else:

        explanation = (
            "The optimizer selected the lowest-carbon "
            "feasible allocation under the current "
            "attendance, budget and private-car constraints."
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "status": "optimal",

        "objective": (
            "Minimize transportation CO2e"
        ),

        "constraints": {
            "attendees": attendees,
            "budget": budget,
            "max_car_percent": (
                max_car_percent
            ),
        },

        "transport_factors": {

            "private_car": {
                "factor": car_factor,
                "unit": (
                    "kgCO2e/passenger_km"
                ),
                "factor_id": (
                    "TF_PRIVATE_CAR_INDIA"
                ),
            },

            "city_bus": {
                "factor": bus_factor,
                "unit": (
                    "kgCO2/passenger_km"
                ),
                "factor_id": (
                    "TF_CITY_BUS_INDIA"
                ),
            },
        },

        "baseline": {

            "car_attendees": (
                baseline_car_attendees
            ),

            "bus_attendees": (
                baseline_bus_attendees
            ),

            "cost": round(
                baseline_cost,
                2
            ),

            "co2_kg": round(
                baseline_co2,
                2
            ),
        },

        "optimized": {

            "car_attendees": (
                optimized_car_attendees
            ),

            "bus_attendees": (
                optimized_bus_attendees
            ),

            "cost": round(
                optimized_cost,
                2
            ),

            "co2_kg": round(
                optimized_co2,
                2
            ),
        },

        "impact": {

            "co2_saved_kg": round(
                carbon_saved,
                2
            ),

            "cost_change": round(
                cost_change,
                2
            ),
        },

        "explanation": explanation,

        "planning_assumptions": {

            "private_car_cost_per_person": (
                car_cost_per_person
            ),

            "city_bus_cost_per_person": (
                bus_cost_per_person
            ),
        }
    }