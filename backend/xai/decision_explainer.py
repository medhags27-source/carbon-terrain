def explain_decision(
    optimization_result,
    event_state
):
    """
    Generate a structured explanation for the
    constraint-based transport optimizer.

    This module reads the current optimizer response
    structure:
        - baseline
        - optimized
        - transport_factors
        - impact
        - constraints
    """

    # =====================================================
    # VALIDATION
    # =====================================================

    if not optimization_result:

        return {
            "success": False,
            "message": "No optimization result available."
        }

    if optimization_result.get("status") != "optimal":

        return {
            "success": False,
            "message": optimization_result.get(
                "message",
                "No feasible optimization plan was found."
            )
        }


    # =====================================================
    # READ CURRENT OPTIMIZER STRUCTURE
    # =====================================================

    baseline = optimization_result.get(
        "baseline",
        {}
    )

    optimized = optimization_result.get(
        "optimized",
        {}
    )

    impact = optimization_result.get(
        "impact",
        {}
    )

    factors = optimization_result.get(
        "transport_factors",
        {}
    )

    optimizer_constraints = optimization_result.get(
        "constraints",
        {}
    )


    # =====================================================
    # EVENT INPUTS
    # =====================================================

    attendees = int(
        event_state.get(
            "attendees",
            0
        )
    )

    budget = float(
        event_state.get(
            "budget",
            0
        )
    )

    distance_km = float(
        event_state.get(
            "distance_km",
            0
        )
    )

    max_car_percent = float(
        optimizer_constraints.get(
            "max_car_percent",
            event_state.get(
                "constraints",
                {}
            ).get(
                "max_car_percent",
                30
            )
        )
    )


    # =====================================================
    # OPTIMIZED PLAN
    # =====================================================

    optimized_car = int(
        optimized.get(
            "car_attendees",
            0
        )
    )

    optimized_bus = int(
        optimized.get(
            "bus_attendees",
            0
        )
    )

    optimized_cost = float(
        optimized.get(
            "cost",
            0
        )
    )

    optimized_co2 = float(
        optimized.get(
            "co2_kg",
            0
        )
    )


    # =====================================================
    # BASELINE PLAN
    # =====================================================

    baseline_car = int(
        baseline.get(
            "car_attendees",
            0
        )
    )

    baseline_bus = int(
        baseline.get(
            "bus_attendees",
            0
        )
    )

    baseline_cost = float(
        baseline.get(
            "cost",
            0
        )
    )

    baseline_co2 = float(
        baseline.get(
            "co2_kg",
            0
        )
    )


    # =====================================================
    # IMPACT
    # =====================================================

    co2_saved = float(
        impact.get(
            "co2_saved_kg",
            max(
                0,
                baseline_co2 - optimized_co2
            )
        )
    )

    cost_change = float(
        impact.get(
            "cost_change",
            optimized_cost - baseline_cost
        )
    )

    # Calculate reduction percentage ourselves
    # when the optimizer does not provide it.

    if baseline_co2 > 0:

        reduction_percent = (
            co2_saved
            / baseline_co2
        ) * 100

    else:

        reduction_percent = 0


    # =====================================================
    # TRANSPORT FACTORS
    # =====================================================

    private_car_data = factors.get(
        "private_car",
        {}
    )

    city_bus_data = factors.get(
        "city_bus",
        {}
    )

    car_factor = float(
        private_car_data.get(
            "factor",
            0
        )
    )

    bus_factor = float(
        city_bus_data.get(
            "factor",
            0
        )
    )

    car_factor_id = private_car_data.get(
        "factor_id",
        "TF_PRIVATE_CAR_INDIA"
    )

    bus_factor_id = city_bus_data.get(
        "factor_id",
        "TF_CITY_BUS_INDIA"
    )

    car_unit = private_car_data.get(
        "unit",
        "kgCO2e/passenger_km"
    )

    bus_unit = city_bus_data.get(
        "unit",
        "kgCO2/passenger_km"
    )


    # =====================================================
    # MAXIMUM PRIVATE-CAR ALLOCATION
    # =====================================================

    max_allowed_cars = int(
        attendees
        * max_car_percent
        / 100
    )


    # =====================================================
    # FACTOR EXPLANATION
    # =====================================================

    if car_factor < bus_factor:

        factor_effect = (
            "Under the currently configured emission "
            "factors, private cars have a lower estimated "
            "emission factor per passenger-km than buses."
        )

        factor_direction = "private_car"

    elif bus_factor < car_factor:

        factor_effect = (
            "Under the currently configured emission "
            "factors, city buses have a lower estimated "
            "emission factor per passenger-km than "
            "private cars."
        )

        factor_direction = "city_bus"

    else:

        factor_effect = (
            "The currently configured transport emission "
            "factors are equal."
        )

        factor_direction = "equal"


    # =====================================================
    # DECISION REASON
    # =====================================================

    if (
        optimized_bus == attendees
        and bus_factor < car_factor
    ):

        decision_reason = (
            f"The optimizer selected {optimized_car:,} "
            f"private-car attendees and {optimized_bus:,} "
            f"bus attendees because the configured city-bus "
            f"emission factor is lower than the private-car "
            f"factor. This configuration also satisfies "
            f"the attendance, budget and private-car "
            f"constraints."
        )

    elif optimized_car == max_allowed_cars:

        decision_reason = (
            f"The optimizer selected {optimized_car:,} "
            f"private-car attendees and {optimized_bus:,} "
            f"bus attendees. The private-car allocation "
            f"reaches the configured {max_car_percent:.0f}% "
            f"maximum while satisfying the remaining "
            f"constraints."
        )

    else:

        decision_reason = (
            f"The optimizer selected {optimized_car:,} "
            f"private-car attendees and {optimized_bus:,} "
            f"bus attendees while satisfying the configured "
            f"attendance, budget and private-car constraints."
        )


    # =====================================================
    # CONSTRAINT EXPLANATIONS
    # =====================================================

    constraints = []


    # Private-car constraint

    constraints.append({

        "constraint":
            "Maximum private-car allocation",

        "value":
            f"{max_car_percent:.0f}%",

        "effect":
            (
                f"At most {max_allowed_cars:,} attendees "
                "can be assigned to private cars."
            )
    })


    # Budget constraint

    constraints.append({

        "constraint":
            "Transport budget",

        "value":
            f"₹{budget:,.0f}",

        "effect":
            (
                f"The optimized transport configuration "
                f"costs ₹{optimized_cost:,.0f}, compared "
                f"with ₹{baseline_cost:,.0f} for the "
                "baseline configuration."
            )
    })


    # Attendance constraint

    constraints.append({

        "constraint":
            "Attendance",

        "value":
            f"{attendees:,}",

        "effect":
            (
                f"The transport plan allocates transport "
                f"for all {attendees:,} attendees."
            )
    })


    # Distance

    constraints.append({

        "constraint":
            "Average travel distance",

        "value":
            f"{distance_km:g} km",

        "effect":
            (
                "Travel distance directly affects estimated "
                "transport emissions."
            )
    })


    # =====================================================
    # IMPROVEMENTS
    # =====================================================

    improvements = []


    # If bus is currently better, suggest preserving
    # or expanding lower-carbon transport.

    if bus_factor < car_factor:

        improvements.append({

            "action":
                "Increase the share of lower-carbon transport",

            "reason":
                (
                    "The configured city-bus factor is lower "
                    "than the private-car factor, so shifting "
                    "more attendees toward bus transport can "
                    "reduce estimated transport emissions."
                )
        })


    # Travel-distance improvement

    improvements.append({

        "action":
            "Reduce average travel distance",

        "reason":
            (
                "A lower attendee travel distance directly "
                "reduces transport-related emissions."
            )
    })


    # Data quality improvement

    improvements.append({

        "action":
            "Use verified region-specific transport factors",

        "reason":
            (
                "More representative emission factors can "
                "change the optimization outcome."
            )
    })


    # =====================================================
    # COST IMPACT EXPLANATION
    # =====================================================

    if cost_change < 0:

        financial_effect = (
            f"The optimized configuration reduces transport "
            f"cost by ₹{abs(cost_change):,.0f}."
        )

    elif cost_change > 0:

        financial_effect = (
            f"The optimized configuration increases transport "
            f"cost by ₹{cost_change:,.0f}."
        )

    else:

        financial_effect = (
            "The optimized configuration has the same "
            "transport cost as the baseline."
        )


    # =====================================================
    # RETURN STRUCTURED XAI RESULT
    # =====================================================

    return {

        "success": True,

        "decision": {

            "title":
                "Why this plan?",

            "summary":
                decision_reason,

            "optimized_car_attendees":
                optimized_car,

            "optimized_bus_attendees":
                optimized_bus,

            "estimated_cost":
                round(
                    optimized_cost,
                    2
                ),

            "estimated_co2_kg":
                round(
                    optimized_co2,
                    2
                )
        },


        "reasoning": {

            "optimization_objective":
                (
                    "Minimize estimated transport CO2e "
                    "while satisfying attendance, budget "
                    "and private-car constraints."
                ),

            "factor_effect":
                factor_effect,

            "configured_car_factor":
                car_factor,

            "configured_bus_factor":
                bus_factor,

            "car_factor_id":
                car_factor_id,

            "bus_factor_id":
                bus_factor_id,

            "car_factor_unit":
                car_unit,

            "bus_factor_unit":
                bus_unit,

            "dominant_factor_direction":
                factor_direction
        },


        "constraints":
            constraints,


        "impact": {

            "baseline_car_attendees":
                baseline_car,

            "baseline_bus_attendees":
                baseline_bus,

            "baseline_cost":
                round(
                    baseline_cost,
                    2
                ),

            "baseline_co2_kg":
                round(
                    baseline_co2,
                    2
                ),

            "optimized_co2_kg":
                round(
                    optimized_co2,
                    2
                ),

            "co2_saved_kg":
                round(
                    co2_saved,
                    2
                ),

            "reduction_percent":
                round(
                    reduction_percent,
                    2
                ),

            "additional_cost":
                round(
                    cost_change,
                    2
                ),

            "financial_effect":
                financial_effect
        },


        "improvements":
            improvements
    }