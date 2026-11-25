from backend.calculator.carbon_calculator import calculate_event_footprint
from backend.optimizer.impact_optimizer import calculate_interventions


def calculate_current_footprint(event_state):

    return calculate_event_footprint(
        attendees=int(event_state.get("attendees", 0)),
        distance_km=float(event_state.get("distance_km", 0)),
        meals=int(event_state.get("meals", 0)),
        energy_kwh=float(event_state.get("energy_kwh", 0)),
        waste_kg=float(event_state.get("waste_kg", 0)),
        materials_kg=float(event_state.get("materials_kg", 0)),
    )


def find_carbon_budget_plan(
    interventions,
    required_saving
):

    """
    Find the lowest-cost combination of available interventions
    that achieves the required CO2e reduction.

    This is a small 0/1 optimization problem because each
    intervention can either be selected or not selected.
    """

    if required_saving <= 0:

        return {
            "feasible": True,
            "selected": [],
            "total_cost_inr": 0,
            "total_saving_kg": 0,
        }

    best = None

    n = len(interventions)

    # Enumerate combinations.
    # Number of interventions is small, so this is exact.
    for mask in range(1, 1 << n):

        selected = []

        total_cost = 0
        total_saving = 0

        for i in range(n):

            if mask & (1 << i):

                item = interventions[i]

                selected.append(item)

                total_cost += item["cost_inr"]
                total_saving += item["co2_saved_kg"]

        if total_saving >= required_saving:

            candidate = {
                "feasible": True,
                "selected": selected,
                "total_cost_inr": round(
                    total_cost,
                    2
                ),
                "total_saving_kg": round(
                    total_saving,
                    2
                ),
            }

            if best is None:

                best = candidate

            elif candidate["total_cost_inr"] < best[
                "total_cost_inr"
            ]:

                best = candidate

            elif (
                candidate["total_cost_inr"]
                == best["total_cost_inr"]
                and candidate["total_saving_kg"]
                < best["total_saving_kg"]
            ):

                best = candidate

    if best is not None:

        return best

    return {
        "feasible": False,
        "selected": [],
        "total_cost_inr": 0,
        "total_saving_kg": 0,
    }


def optimize_carbon_budget(
    event_state,
    carbon_limit_kg
):

    carbon_limit_kg = float(
        carbon_limit_kg
    )

    current = calculate_current_footprint(
        event_state
    )

    current_total = float(
        current["total_co2e"]
    )

    required_saving = max(
        0,
        current_total - carbon_limit_kg
    )

    # ---------------------------------------------------------
    # Already within carbon budget
    # ---------------------------------------------------------

    if required_saving <= 0:

        return {

            "status": "already_feasible",

            "carbon_limit_kg": round(
                carbon_limit_kg,
                2
            ),

            "current_footprint_kg": round(
                current_total,
                2
            ),

            "required_reduction_kg": 0,

            "optimized_footprint_kg": round(
                current_total,
                2
            ),

            "selected_interventions": [],

            "additional_cost_inr": 0,

            "remaining_carbon_budget_kg": round(
                carbon_limit_kg - current_total,
                2
            ),

            "message": (
                f"The event is already within the "
                f"{carbon_limit_kg:,.0f} kg CO2e carbon budget."
            )
        }

    # ---------------------------------------------------------
    # Generate calculated interventions
    # ---------------------------------------------------------

    interventions = calculate_interventions(
        event_state
    )

    # ---------------------------------------------------------
    # Find minimum-cost combination
    # ---------------------------------------------------------

    plan = find_carbon_budget_plan(
        interventions,
        required_saving
    )

    if plan["feasible"]:

        optimized_total = (
            current_total
            - plan["total_saving_kg"]
        )

        return {

            "status": "feasible_after_interventions",

            "carbon_limit_kg": round(
                carbon_limit_kg,
                2
            ),

            "current_footprint_kg": round(
                current_total,
                2
            ),

            "required_reduction_kg": round(
                required_saving,
                2
            ),

            "optimized_footprint_kg": round(
                optimized_total,
                2
            ),

            "co2_reduction_kg": round(
                plan["total_saving_kg"],
                2
            ),

            "selected_interventions":
                plan["selected"],

            "additional_cost_inr": round(
                plan["total_cost_inr"],
                2
            ),

            "remaining_carbon_budget_kg": round(
                carbon_limit_kg - optimized_total,
                2
            ),

            "message": (
                f"The event requires at least "
                f"{required_saving:,.2f} kg CO2e of "
                f"additional reduction. "
                f"The optimizer found a feasible "
                f"intervention combination costing "
                f"?{plan['total_cost_inr']:,.0f}, "
                f"reducing approximately "
                f"{plan['total_saving_kg']:,.2f} kg CO2e."
            )
        }

    # ---------------------------------------------------------
    # No feasible combination
    # ---------------------------------------------------------

    total_possible_saving = sum(
        item["co2_saved_kg"]
        for item in interventions
    )

    minimum_possible_footprint = (
        current_total
        - total_possible_saving
    )

    remaining_excess = max(
        0,
        minimum_possible_footprint
        - carbon_limit_kg
    )

    return {

        "status": "infeasible",

        "carbon_limit_kg": round(
            carbon_limit_kg,
            2
        ),

        "current_footprint_kg": round(
            current_total,
            2
        ),

        "required_reduction_kg": round(
            required_saving,
            2
        ),

        "maximum_calculated_reduction_kg": round(
            total_possible_saving,
            2
        ),

        "best_possible_footprint_kg": round(
            minimum_possible_footprint,
            2
        ),

        "remaining_excess_co2_kg": round(
            remaining_excess,
            2
        ),

        "selected_interventions": [],

        "additional_cost_inr": 0,

        "message": (
            f"The current event cannot meet the "
            f"{carbon_limit_kg:,.0f} kg CO2e limit "
            f"using the currently modelled interventions. "
            f"The best calculated footprint is "
            f"{minimum_possible_footprint:,.2f} kg CO2e."
        )
    }


if __name__ == "__main__":

    example_event = {

        "event_name": "College Tech Fest",

        "event_type": "College Event",

        "attendees": 1000,

        "days": 2,

        "budget": 300000,

        "carbon_limit_kg": 2000,

        "distance_km": 10,

        "meals": 2000,

        "energy_kwh": 1000,

        "waste_kg": 200,

        "materials_kg": 100
    }

    result = optimize_carbon_budget(
        example_event,
        2000
    )

    print("\n=== CARBON BUDGET OPTIMIZER ===")

    for key, value in result.items():

        print(f"{key}: {value}")
