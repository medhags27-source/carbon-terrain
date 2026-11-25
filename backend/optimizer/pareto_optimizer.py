from typing import List, Dict, Any
from backend.optimizer.event_optimizer import optimize_event


def calculate_pareto_frontier(
    attendees: int,
    distance_km: float,
    budget: float,
    max_car_percent: float = 30,
) -> Dict[str, Any]:
    """
    Generate non-dominated event configurations by varying
    the maximum allowed private-car percentage.

    Objectives:
    1. Minimize CO2 emissions
    2. Minimize transportation cost
    """

    scenarios: List[Dict[str, Any]] = []

    # Evaluate different feasible car-usage limits.
    car_percentages = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    # Respect the event's configured maximum constraint.
    car_percentages = [
        p for p in car_percentages
        if p <= max_car_percent
    ]

    # Always include the configured maximum.
    if max_car_percent not in car_percentages:
        car_percentages.append(max_car_percent)

    car_percentages = sorted(set(car_percentages))

    for car_percent in car_percentages:
        try:
            result = optimize_event(
                attendees=attendees,
                distance_km=distance_km,
                budget=budget,
                max_car_percent=car_percent,
            )
        except Exception as exc:
            scenarios.append({
                "max_car_percent": car_percent,
                "status": "error",
                "error": str(exc),
            })
            continue

        if result.get("status") != "optimal":
            scenarios.append({
                "max_car_percent": car_percent,
                "status": result.get("status", "infeasible"),
            })
            continue

        optimized = result.get("optimized", {})

        scenarios.append({
            "max_car_percent": car_percent,
            "status": "optimal",
            "car_attendees": optimized.get("car_attendees", 0),
            "bus_attendees": optimized.get("bus_attendees", 0),
            "cost_inr": optimized.get("cost", 0),
            "co2_kg": optimized.get("co2_kg", 0),
        })

    # Keep only valid solutions.
    feasible = [
        s for s in scenarios
        if s.get("status") == "optimal"
    ]

    # A solution is Pareto-dominated if another solution is
    # no worse on both objectives and strictly better on at least one.
    pareto_frontier = []

    for candidate in feasible:
        candidate_cost = candidate["cost_inr"]
        candidate_co2 = candidate["co2_kg"]

        dominated = False

        for other in feasible:
            if other is candidate:
                continue

            other_cost = other["cost_inr"]
            other_co2 = other["co2_kg"]

            no_worse = (
                other_cost <= candidate_cost
                and other_co2 <= candidate_co2
            )

            strictly_better = (
                other_cost < candidate_cost
                or other_co2 < candidate_co2
            )

            if no_worse and strictly_better:
                dominated = True
                break

        if not dominated:
            pareto_frontier.append(candidate)

    # Sort from lowest cost to highest cost.
    pareto_frontier.sort(
        key=lambda x: (
            x.get("cost_inr", float("inf")),
            x.get("co2_kg", float("inf")),
        )
    )

    # Identify the lowest-carbon feasible configuration.
    lowest_carbon = None
    if feasible:
        lowest_carbon = min(
            feasible,
            key=lambda x: x["co2_kg"]
        )

    # Identify the lowest-cost feasible configuration.
    lowest_cost = None
    if feasible:
        lowest_cost = min(
            feasible,
            key=lambda x: x["cost_inr"]
        )

    return {
        "success": True,
        "status": "feasible" if feasible else "infeasible",
        "objectives": [
            "minimize_co2",
            "minimize_cost",
        ],
        "base_constraints": {
            "attendees": attendees,
            "distance_km": distance_km,
            "budget_inr": budget,
            "max_car_percent": max_car_percent,
        },
        "scenarios_evaluated": len(scenarios),
        "feasible_scenarios": len(feasible),
        "pareto_solutions": len(pareto_frontier),
        "pareto_frontier": pareto_frontier,
        "lowest_carbon_solution": lowest_carbon,
        "lowest_cost_solution": lowest_cost,
        "explanation": (
            "The Pareto frontier contains event configurations for which "
            "no other feasible configuration simultaneously provides lower "
            "cost and lower carbon emissions. These solutions expose the "
            "trade-off between transportation cost and emissions."
        ),
        "method": (
            "Constraint-based enumeration followed by Pareto dominance "
            "filtering over cost and travel-related CO2 emissions."
        ),
    }
