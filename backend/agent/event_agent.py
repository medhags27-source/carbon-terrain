from backend.calculator.carbon_calculator import (
    calculate_event_footprint
)

from backend.ml.predict import (
    predict_event_carbon
)

from backend.optimizer.event_optimizer import (
    optimize_event
)


def plan_sustainable_event(
    attendees: int,
    distance_km: float,
    meals: int,
    energy_kwh: float,
    waste_kg: float,
    materials_kg: float,
    budget: int = 15000,
    max_car_percent: int = 30
):

    # ----------------------------------------------
    # 1. CALCULATE BASELINE
    # ----------------------------------------------

    baseline = calculate_event_footprint(
        attendees=attendees,
        distance_km=distance_km,
        meals=meals,
        energy_kwh=energy_kwh,
        waste_kg=waste_kg,
        materials_kg=materials_kg
    )


    # ----------------------------------------------
    # 2. ML PREDICTION
    # ----------------------------------------------

    prediction = predict_event_carbon(
        participants=attendees,
        distance_km=distance_km
    )


    # ----------------------------------------------
    # 3. OPTIMIZE EVENT
    # ----------------------------------------------

    optimization = optimize_event(
        attendees=attendees,
        budget=budget,
        max_car_percent=max_car_percent
    )


    # ----------------------------------------------
    # 4. RETURN COMPLETE PLAN
    # ----------------------------------------------

    return {
        "baseline": baseline,

        "ml_prediction_tco2e": prediction,

        "optimization": optimization,

        "recommendations": [
            "Increase public transport usage.",
            "Reduce private car usage.",
            "Prefer vegetarian meals.",
            "Use reusable event materials.",
            "Monitor energy consumption."
        ]
    }


if __name__ == "__main__":

    result = plan_sustainable_event(
        attendees=100,
        distance_km=10,
        meals=100,
        energy_kwh=500,
        waste_kg=50,
        materials_kg=20
    )

    print("\nAI EVENT AGENT")
    print("=" * 60)

    print("\nBASELINE:")
    print(result["baseline"])

    print("\nML PREDICTION:")
    print(
        result["ml_prediction_tco2e"],
        "tCO2e"
    )

    print("\nOPTIMIZATION:")
    print(result["optimization"])

    print("\nRECOMMENDATIONS:")

    for recommendation in result["recommendations"]:
        print("-", recommendation)