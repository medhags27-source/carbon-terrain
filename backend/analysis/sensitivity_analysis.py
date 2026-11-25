from backend.optimizer.event_optimizer import optimize_event


def analyze_sensitivity(event_state):
    """
    Analyze how the optimized transport plan changes when
    key planning inputs are varied.
    """

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

    budget = float(
        event_state.get(
            "budget",
            0
        )
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
            "message": "Attendees must be greater than zero."
        }


    results = []


    # ==================================================
    # HELPER
    # ==================================================

    def extract_result(
        result,
        parameter,
        value
    ):
        """
        Convert the current optimizer response structure
        into a consistent sensitivity-analysis result.
        """

        optimized = result.get(
            "optimized",
            {}
        )

        return {
            "parameter": parameter,
            "value": value,
            "status": result.get(
                "status"
            ),
            "co2_kg": optimized.get(
                "co2_kg"
            ),
            "cost": optimized.get(
                "cost"
            ),
            "car_attendees": optimized.get(
                "car_attendees"
            ),
            "bus_attendees": optimized.get(
                "bus_attendees"
            ),
        }


    # ==================================================
    # ATTENDANCE SENSITIVITY
    # ==================================================

    attendance_values = sorted(
        set([
            max(
                1,
                int(attendees * 0.75)
            ),

            max(
                1,
                int(attendees * 0.90)
            ),

            attendees,

            max(
                1,
                int(attendees * 1.10)
            ),

            max(
                1,
                int(attendees * 1.25)
            ),
        ])
    )


    for value in attendance_values:

        result = optimize_event(
            attendees=value,
            distance_km=distance_km,
            budget=budget,
            max_car_percent=max_car_percent
        )

        results.append(
            extract_result(
                result,
                "attendees",
                value
            )
        )


    # ==================================================
    # DISTANCE SENSITIVITY
    # ==================================================

    distance_values = sorted(
        set([
            max(
                0,
                round(
                    distance_km * 0.50,
                    2
                )
            ),

            max(
                0,
                round(
                    distance_km * 0.75,
                    2
                )
            ),

            round(
                distance_km,
                2
            ),

            round(
                distance_km * 1.25,
                2
            ),

            round(
                distance_km * 1.50,
                2
            ),
        ])
    )


    for value in distance_values:

        result = optimize_event(
            attendees=attendees,
            distance_km=value,
            budget=budget,
            max_car_percent=max_car_percent
        )

        results.append(
            extract_result(
                result,
                "distance_km",
                value
            )
        )


    # ==================================================
    # BUDGET SENSITIVITY
    # ==================================================

    budget_values = sorted(
        set([
            max(
                0,
                round(
                    budget * 0.50,
                    2
                )
            ),

            max(
                0,
                round(
                    budget * 0.75,
                    2
                )
            ),

            round(
                budget,
                2
            ),

            round(
                budget * 1.25,
                2
            ),

            round(
                budget * 1.50,
                2
            ),
        ])
    )


    for value in budget_values:

        result = optimize_event(
            attendees=attendees,
            distance_km=distance_km,
            budget=value,
            max_car_percent=max_car_percent
        )

        results.append(
            extract_result(
                result,
                "budget",
                value
            )
        )


    # ==================================================
    # MAX CAR PERCENTAGE SENSITIVITY
    # ==================================================

    car_limit_values = [
        10,
        20,
        30,
        40,
        50,
    ]


    for value in car_limit_values:

        result = optimize_event(
            attendees=attendees,
            distance_km=distance_km,
            budget=budget,
            max_car_percent=value
        )

        results.append(
            extract_result(
                result,
                "max_car_percent",
                value
            )
        )


    # ==================================================
    # THRESHOLD DETECTION
    # ==================================================

    thresholds = []


    for parameter in [
        "attendees",
        "distance_km",
        "budget",
        "max_car_percent"
    ]:

        parameter_results = [
            item
            for item in results
            if item["parameter"] == parameter
        ]


        previous_status = None
        previous_value = None


        for item in parameter_results:

            current_status = item[
                "status"
            ]

            if (
                previous_status is not None
                and current_status != previous_status
            ):

                thresholds.append({

                    "parameter":
                        parameter,

                    "from_value":
                        previous_value,

                    "to_value":
                        item["value"],

                    "from_status":
                        previous_status,

                    "to_status":
                        current_status
                })


            previous_status = current_status

            previous_value = item[
                "value"
            ]


    # ==================================================
    # SUMMARY
    # ==================================================

    valid_results = [
        item
        for item in results
        if item["status"] == "optimal"
        and item["co2_kg"] is not None
    ]


    return {

        "success": True,

        "base_case": {

            "attendees":
                attendees,

            "distance_km":
                distance_km,

            "budget":
                budget,

            "max_car_percent":
                max_car_percent,
        },

        "results":
            results,

        "thresholds":
            thresholds,

        "summary": {

            "total_scenarios":
                len(results),

            "optimal_scenarios":
                len(valid_results),

            "infeasible_scenarios":
                len(results)
                - len(valid_results)
        }
    }