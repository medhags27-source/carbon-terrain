from backend.optimizer.event_optimizer import optimize_event


# =========================================================
# COUNTERFACTUAL ANALYSIS
# =========================================================

def analyze_counterfactual(
    event_state,
    target_co2_kg=None,
    target_budget=None
):
    """
    Analyze what event input would need to change
    to reach a target CO2 level or budget.

    Uses the current constraint-based event optimizer.
    """

    attendees = int(
        event_state.get("attendees", 0)
    )

    distance_km = float(
        event_state.get("distance_km", 10)
    )

    budget = float(
        event_state.get("budget", 0)
    )

    constraints = event_state.get(
        "constraints",
        {}
    )

    max_car_percent = float(
        constraints.get(
            "max_car_percent",
            30
        )
    )

    if attendees <= 0:
        return {
            "success": False,
            "status": "invalid_input",
            "message": "Attendees must be greater than zero."
        }

    # -----------------------------------------------------
    # CURRENT BASELINE / OPTIMIZED PLAN
    # -----------------------------------------------------

    current = optimize_event(
        attendees=attendees,
        distance_km=distance_km,
        budget=budget,
        max_car_percent=max_car_percent
    )

    if current.get("status") != "optimal":
        return {
            "success": False,
            "status": "current_plan_infeasible",
            "message": (
                "The current event configuration could not "
                "produce a feasible optimized transport plan."
            ),
            "current_result": current
        }

    current_optimized = current.get(
        "optimized",
        {}
    )

    current_co2 = float(
        current_optimized.get(
            "co2_kg",
            0
        )
    )

    current_cost = float(
        current_optimized.get(
            "cost",
            0
        )
    )

    current_car = int(
        current_optimized.get(
            "car_attendees",
            0
        )
    )

    current_bus = int(
        current_optimized.get(
            "bus_attendees",
            0
        )
    )

    # -----------------------------------------------------
    # TARGET VALIDATION
    # -----------------------------------------------------

    if target_co2_kg is None and target_budget is None:
        target_co2_kg = round(
            current_co2 * 0.80,
            2
        )

    if target_co2_kg is not None:
        target_co2_kg = float(
            target_co2_kg
        )

    if target_budget is not None:
        target_budget = float(
            target_budget
        )

    # -----------------------------------------------------
    # COUNTERFACTUAL SEARCH
    #
    # We vary travel distance while keeping:
    # attendees, budget and car constraint fixed.
    # -----------------------------------------------------

    distance_candidates = []

    # Search from 1 km to current distance.
    # If current distance is already very small,
    # still test 1 km.
    max_distance = max(
        1.0,
        distance_km
    )

    step = max(
        0.1,
        max_distance / 100
    )

    d = 1.0

    while d <= max_distance + 0.0001:

        result = optimize_event(
            attendees=attendees,
            distance_km=d,
            budget=budget,
            max_car_percent=max_car_percent
        )

        if result.get("status") == "optimal":

            optimized = result.get(
                "optimized",
                {}
            )

            co2 = float(
                optimized.get(
                    "co2_kg",
                    0
                )
            )

            cost = float(
                optimized.get(
                    "cost",
                    0
                )
            )

            distance_candidates.append({
                "distance_km": round(d, 2),
                "co2_kg": round(co2, 2),
                "cost_inr": round(cost, 2),
                "car_attendees": int(
                    optimized.get(
                        "car_attendees",
                        0
                    )
                ),
                "bus_attendees": int(
                    optimized.get(
                        "bus_attendees",
                        0
                    )
                )
            })

        d += step

    # -----------------------------------------------------
    # FIND COUNTERFACTUAL
    # -----------------------------------------------------

    selected = None

    if target_co2_kg is not None:

        feasible_targets = [
            item
            for item in distance_candidates
            if item["co2_kg"] <= target_co2_kg
        ]

        if feasible_targets:
            # Choose the closest distance to the
            # current planning distance.
            selected = min(
                feasible_targets,
                key=lambda x: abs(
                    x["distance_km"] - distance_km
                )
            )

    # -----------------------------------------------------
    # TARGET BUDGET ONLY
    # -----------------------------------------------------

    if (
        selected is None
        and target_budget is not None
    ):

        feasible_budget = [
            item
            for item in distance_candidates
            if item["cost_inr"] <= target_budget
        ]

        if feasible_budget:
            selected = min(
                feasible_budget,
                key=lambda x: abs(
                    x["distance_km"] - distance_km
                )
            )

    # -----------------------------------------------------
    # NO FEASIBLE COUNTERFACTUAL
    # -----------------------------------------------------

    if selected is None:

        minimum_co2_plan = None

        if distance_candidates:
            minimum_co2_plan = min(
                distance_candidates,
                key=lambda x: x["co2_kg"]
            )

        return {
            "success": True,
            "status": "infeasible",
            "target_co2_kg": target_co2_kg,
            "target_budget_inr": target_budget,
            "current": {
                "distance_km": distance_km,
                "co2_kg": round(
                    current_co2,
                    2
                ),
                "cost_inr": round(
                    current_cost,
                    2
                ),
                "car_attendees": current_car,
                "bus_attendees": current_bus
            },
            "counterfactual": None,
            "best_found": minimum_co2_plan,
            "message": (
                "The requested target could not be reached "
                "within the tested planning range while "
                "keeping the current attendance, budget "
                "and transport constraints."
            )
        }

    # -----------------------------------------------------
    # IMPACT
    # -----------------------------------------------------

    co2_change = (
        selected["co2_kg"]
        - current_co2
    )

    distance_change = (
        selected["distance_km"]
        - distance_km
    )

    cost_change = (
        selected["cost_inr"]
        - current_cost
    )

    if current_co2 > 0:
        reduction_percent = (
            (current_co2 - selected["co2_kg"])
            / current_co2
        ) * 100
    else:
        reduction_percent = 0

    # -----------------------------------------------------
    # EXPLANATION
    # -----------------------------------------------------

    if distance_change < 0:

        explanation = (
            f"To reach the target, the modeled average "
            f"travel distance would need to decrease from "
            f"{distance_km:.2f} km to "
            f"{selected['distance_km']:.2f} km. "
            f"This reduces optimized transport emissions "
            f"from {current_co2:.2f} kg CO2e to "
            f"{selected['co2_kg']:.2f} kg CO2e."
        )

    elif distance_change > 0:

        explanation = (
            f"The selected counterfactual uses an average "
            f"travel distance of "
            f"{selected['distance_km']:.2f} km. "
            f"The resulting optimized transport footprint "
            f"is {selected['co2_kg']:.2f} kg CO2e."
        )

    else:

        explanation = (
            "The current travel-distance assumption already "
            "provides the closest feasible configuration "
            "to the requested target."
        )

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "success": True,
        "status": "feasible",
        "target_co2_kg": target_co2_kg,
        "target_budget_inr": target_budget,

        "current": {
            "distance_km": round(
                distance_km,
                2
            ),
            "co2_kg": round(
                current_co2,
                2
            ),
            "cost_inr": round(
                current_cost,
                2
            ),
            "car_attendees": current_car,
            "bus_attendees": current_bus
        },

        "counterfactual": {
            "distance_km": selected[
                "distance_km"
            ],
            "co2_kg": selected[
                "co2_kg"
            ],
            "cost_inr": selected[
                "cost_inr"
            ],
            "car_attendees": selected[
                "car_attendees"
            ],
            "bus_attendees": selected[
                "bus_attendees"
            ]
        },

        "impact": {
            "distance_change_km": round(
                distance_change,
                2
            ),
            "co2_change_kg": round(
                co2_change,
                2
            ),
            "co2_reduction_kg": round(
                max(
                    0,
                    current_co2
                    - selected["co2_kg"]
                ),
                2
            ),
            "reduction_percent": round(
                max(
                    0,
                    reduction_percent
                ),
                2
            ),
            "cost_change_inr": round(
                cost_change,
                2
            )
        },

        "explanation": explanation,

        "method": (
            "Counterfactual analysis varies the modeled "
            "average travel distance while keeping "
            "attendance, event budget and maximum private-car "
            "percentage fixed. Each candidate is evaluated "
            "using the constraint-based transport optimizer."
        )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    example_event = {
        "attendees": 100,
        "distance_km": 10,
        "budget": 30000,
        "constraints": {
            "max_car_percent": 30
        }
    }

    result = analyze_counterfactual(
        example_event,
        target_co2_kg=80
    )

    print(result)