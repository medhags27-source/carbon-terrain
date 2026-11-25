from backend.optimizer.event_optimizer import optimize_event


def analyze_constraint_relaxation(
    attendees,
    distance_km,
    budget,
    max_car_percent=30,
    target_co2_kg=None,
    target_budget=None,
):
    """
    Constraint-relaxation analysis using the current event optimizer.

    Tests progressively relaxed private-car constraints while keeping
    attendance, travel distance and event budget fixed.
    """

    attendees = int(attendees)
    distance_km = float(distance_km)
    budget = float(budget)
    max_car_percent = float(max_car_percent)

    current = optimize_event(
        attendees=attendees,
        distance_km=distance_km,
        budget=budget,
        max_car_percent=max_car_percent,
    )

    if current.get("status") != "optimal":
        return {
            "success": False,
            "status": "infeasible",
            "message": "Current event configuration is infeasible.",
            "current": current,
        }

    current_plan = current["optimized"]

    current_co2 = float(current_plan["co2_kg"])
    current_cost = float(current_plan["cost"])
    current_car = int(current_plan["car_attendees"])
    current_bus = int(current_plan["bus_attendees"])

    relaxation_values = sorted(
        set([
            max_car_percent,
            min(100.0, max_car_percent + 10),
            min(100.0, max_car_percent + 20),
            min(100.0, max_car_percent + 30),
            100.0,
        ])
    )

    scenarios = []

    for relaxed_car_percent in relaxation_values:

        result = optimize_event(
            attendees=attendees,
            distance_km=distance_km,
            budget=budget,
            max_car_percent=relaxed_car_percent,
        )

        if result.get("status") != "optimal":
            scenarios.append({
                "max_car_percent": relaxed_car_percent,
                "status": result.get("status"),
                "co2_kg": None,
                "cost_inr": None,
                "car_attendees": None,
                "bus_attendees": None,
                "co2_change_kg": None,
                "cost_change_inr": None,
            })
            continue

        plan = result["optimized"]

        scenario_co2 = float(plan["co2_kg"])
        scenario_cost = float(plan["cost"])
        scenario_car = int(plan["car_attendees"])
        scenario_bus = int(plan["bus_attendees"])

        scenarios.append({
            "max_car_percent": relaxed_car_percent,
            "status": "optimal",
            "co2_kg": round(scenario_co2, 2),
            "cost_inr": round(scenario_cost, 2),
            "car_attendees": scenario_car,
            "bus_attendees": scenario_bus,
            "co2_change_kg": round(scenario_co2 - current_co2, 2),
            "cost_change_inr": round(scenario_cost - current_cost, 2),
        })

    optimal_scenarios = [
        s for s in scenarios
        if s["status"] == "optimal"
    ]

    best_co2 = (
        min(optimal_scenarios, key=lambda x: x["co2_kg"])
        if optimal_scenarios
        else None
    )

    target_analysis = None

    if target_co2_kg is not None:
        target_co2_kg = float(target_co2_kg)

        feasible = [
            s for s in optimal_scenarios
            if s["co2_kg"] <= target_co2_kg
        ]

        if feasible:
            target_analysis = {
                "status": "feasible",
                "target_co2_kg": target_co2_kg,
                "configuration": min(
                    feasible,
                    key=lambda x: x["max_car_percent"]
                ),
            }
        else:
            target_analysis = {
                "status": "infeasible",
                "target_co2_kg": target_co2_kg,
                "message": (
                    "Target CO2 cannot be achieved within the "
                    "tested constraint-relaxation range."
                ),
            }

    if target_budget is not None:
        target_budget = float(target_budget)

        budget_feasible = [
            s for s in optimal_scenarios
            if s["cost_inr"] <= target_budget
        ]

        if budget_feasible:
            budget_analysis = {
                "status": "feasible",
                "target_budget_inr": target_budget,
                "configuration": min(
                    budget_feasible,
                    key=lambda x: x["co2_kg"]
                ),
            }
        else:
            budget_analysis = {
                "status": "infeasible",
                "target_budget_inr": target_budget,
                "message": (
                    "Target budget cannot be satisfied by the "
                    "tested configurations."
                ),
            }
    else:
        budget_analysis = None

    return {
        "success": True,
        "status": "analyzed",

        "current": {
            "max_car_percent": max_car_percent,
            "co2_kg": round(current_co2, 2),
            "cost_inr": round(current_cost, 2),
            "car_attendees": current_car,
            "bus_attendees": current_bus,
        },

        "scenarios": scenarios,

        "best_co2_configuration": best_co2,

        "target_analysis": target_analysis,

        "budget_analysis": budget_analysis,

        "impact_of_relaxation": {
            "maximum_co2_reduction_kg": (
                round(current_co2 - best_co2["co2_kg"], 2)
                if best_co2
                else None
            ),
            "best_max_car_percent": (
                best_co2["max_car_percent"]
                if best_co2
                else None
            ),
        },

        "explanation": (
            "The analysis progressively relaxes the maximum private-car "
            "constraint and re-runs the constraint-based optimizer. "
            "Each scenario is compared using optimized CO2 emissions, "
            "cost and transport allocation."
        ),

        "method": (
            "Constraint-relaxation analysis evaluates multiple feasible "
            "constraint levels while keeping attendance, distance and "
            "event budget fixed."
        ),
    }


if __name__ == "__main__":
    import json

    result = analyze_constraint_relaxation(
        attendees=100,
        distance_km=10,
        budget=30000,
        max_car_percent=30,
    )

    print(json.dumps(result, indent=2))
