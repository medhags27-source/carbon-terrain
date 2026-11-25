from copy import deepcopy

from backend.optimizer.event_optimizer import optimize_event
from backend.calculator.carbon_calculator import calculate_event_footprint


def simulate_event(event_state, changes):
    """
    Run a temporary what-if scenario without changing
    the user's actual event state.
    """

    scenario = deepcopy(event_state)

    for key, value in changes.items():
        if key in scenario:
            scenario[key] = value

    attendees = scenario["attendees"]
    distance_km = scenario["distance_km"]
    budget = scenario["budget"]

    max_car_percent = scenario["constraints"][
        "max_car_percent"
    ]

    # -----------------------------------------------------
    # Transport optimization
    # -----------------------------------------------------

    optimization = optimize_event(
        attendees=attendees,
        distance_km=distance_km,
        budget=budget,
        max_car_percent=max_car_percent,
    )

    optimized = optimization.get(
        "optimized",
        {}
    )

    # -----------------------------------------------------
    # Full event carbon footprint
    #
    # Keep the existing event assumptions unless the
    # scenario explicitly changes them.
    # -----------------------------------------------------

    meals = scenario.get(
        "meals",
        attendees
    )

    energy_kwh = scenario.get(
        "energy_kwh",
        100
    )

    waste_kg = scenario.get(
        "waste_kg",
        10
    )

    materials_kg = scenario.get(
        "materials_kg",
        5
    )

    # Scale attendee-dependent quantities when attendance
    # changes, while preserving the original per-attendee
    # assumptions.

    original_attendees = event_state["attendees"]

    if attendees != original_attendees:

        if original_attendees > 0:

            meals_per_attendee = (
                event_state.get("meals", original_attendees)
                / original_attendees
            )

            energy_per_attendee = (
                event_state.get("energy_kwh", 100)
                / original_attendees
            )

            waste_per_attendee = (
                event_state.get("waste_kg", 10)
                / original_attendees
            )

            materials_per_attendee = (
                event_state.get("materials_kg", 5)
                / original_attendees
            )

            meals = attendees * meals_per_attendee
            energy_kwh = attendees * energy_per_attendee
            waste_kg = attendees * waste_per_attendee
            materials_kg = attendees * materials_per_attendee

    footprint = calculate_event_footprint(
        attendees=attendees,
        distance_km=distance_km,
        meals=meals,
        energy_kwh=energy_kwh,
        waste_kg=waste_kg,
        materials_kg=materials_kg,
    )

    # Replace the deterministic transport component with
    # the optimized transport result.

    optimized_transport_co2 = optimized.get(
        "co2_kg",
        footprint["transport"]
    )

    optimized_total_co2 = (
        optimized_transport_co2
        + footprint["food"]
        + footprint["energy"]
        + footprint["waste"]
        + footprint["materials"]
    )

    optimized_cost = optimized.get(
        "cost",
        0
    )

    return {
        "scenario": {
            "attendees": attendees,
            "budget": budget,
            "distance_km": distance_km,
            "carbon_limit_kg": scenario["carbon_limit_kg"],
            "meals": meals,
            "energy_kwh": energy_kwh,
            "waste_kg": waste_kg,
            "materials_kg": materials_kg,
        },

        "optimization": optimization,

        "footprint": {
            "transport_kg": round(
                optimized_transport_co2,
                2
            ),
            "food_kg": round(
                footprint["food"],
                2
            ),
            "energy_kg": round(
                footprint["energy"],
                2
            ),
            "waste_kg": round(
                footprint["waste"],
                2
            ),
            "materials_kg": round(
                footprint["materials"],
                2
            ),
            "total_co2e_kg": round(
                optimized_total_co2,
                2
            ),
        },

        "cost": {
            "transport_cost_inr": round(
                optimized_cost,
                2
            )
        }
    }


def compare_scenarios(current_state, scenario):
    """
    Compare the current event with a temporary scenario
    using full event carbon footprint and optimized
    transport cost.
    """

    current = simulate_event(
        current_state,
        {}
    )

    hypothetical = simulate_event(
        current_state,
        scenario
    )

    current_co2 = current["footprint"][
        "total_co2e_kg"
    ]

    hypothetical_co2 = hypothetical["footprint"][
        "total_co2e_kg"
    ]

    current_cost = current["cost"][
        "transport_cost_inr"
    ]

    hypothetical_cost = hypothetical["cost"][
        "transport_cost_inr"
    ]

    return {
        "current": {
            "co2_kg": round(
                current_co2,
                2
            ),
            "cost": round(
                current_cost,
                2
            ),
        },

        "scenario": {
            "co2_kg": round(
                hypothetical_co2,
                2
            ),
            "cost": round(
                hypothetical_cost,
                2
            ),
        },

        "difference": {
            "co2_change_kg": round(
                hypothetical_co2 - current_co2,
                2
            ),
            "cost_change": round(
                hypothetical_cost - current_cost,
                2
            ),
        },

        "scenario_result": hypothetical,
    }


if __name__ == "__main__":

    event = {
        "attendees": 1000,
        "budget": 300000,
        "distance_km": 10,
        "carbon_limit_kg": 2500,

        "meals": 1000,
        "energy_kwh": 1000,
        "waste_kg": 100,
        "materials_kg": 50,

        "constraints": {
            "max_car_percent": 30
        }
    }

    import json

    result = compare_scenarios(
        event,
        {
            "attendees": 1500
        }
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )
