def estimate_event_resources(
    attendees: int,
    days: int,
    event_type: str,
    energy_mode: str = "estimate",
    energy_kwh: float | None = None,
    waste_mode: str = "estimate",
    waste_kg: float | None = None,
    materials_mode: str = "estimate",
    materials_kg: float | None = None,
):
    """
    Planning estimates for resource quantities.

    These are NOT measured values.
    They are explicitly labelled planning estimates until the organizer
    provides actual measurements.
    """

    event_type_normalized = (event_type or "conference").strip().lower()

    # Development planning assumptions.
    # These are intentionally kept separate from emission factors.
    energy_per_attendee_day = {
        "conference": 2.0,
        "seminar": 1.5,
        "workshop": 2.0,
        "college fest": 2.5,
        "tech fest": 2.5,
        "exhibition": 3.0,
        "concert": 3.5,
        "festival": 3.0,
    }.get(event_type_normalized, 2.0)

    waste_per_attendee_day = {
        "conference": 0.20,
        "seminar": 0.15,
        "workshop": 0.20,
        "college fest": 0.25,
        "tech fest": 0.25,
        "exhibition": 0.30,
        "concert": 0.35,
        "festival": 0.30,
    }.get(event_type_normalized, 0.20)

    materials_per_attendee = {
        "conference": 0.10,
        "seminar": 0.08,
        "workshop": 0.15,
        "college fest": 0.12,
        "tech fest": 0.12,
        "exhibition": 0.20,
        "concert": 0.10,
        "festival": 0.15,
    }.get(event_type_normalized, 0.10)

    result = {}

    if energy_mode == "manual":
        if energy_kwh is None or energy_kwh < 0:
            raise ValueError("Actual energy consumption is required when energy mode is manual.")
        result["energy_kwh"] = float(energy_kwh)
        result["energy_quality"] = "user_provided"
        result["energy_note"] = "Energy consumption provided by the organizer."
    else:
        estimated = attendees * days * energy_per_attendee_day
        result["energy_kwh"] = round(estimated, 2)
        result["energy_quality"] = "estimated"
        result["energy_note"] = (
            f"Planning estimate using {energy_per_attendee_day} kWh per attendee-day "
            f"for a {event_type_normalized} event."
        )

    if waste_mode == "manual":
        if waste_kg is None or waste_kg < 0:
            raise ValueError("Actual waste quantity is required when waste mode is manual.")
        result["waste_kg"] = float(waste_kg)
        result["waste_quality"] = "user_provided"
        result["waste_note"] = "Waste quantity provided by the organizer."
    else:
        estimated = attendees * days * waste_per_attendee_day
        result["waste_kg"] = round(estimated, 2)
        result["waste_quality"] = "estimated"
        result["waste_note"] = (
            f"Planning estimate using {waste_per_attendee_day} kg per attendee-day "
            f"for a {event_type_normalized} event."
        )

    if materials_mode == "manual":
        if materials_kg is None or materials_kg < 0:
            raise ValueError("Actual materials quantity is required when materials mode is manual.")
        result["materials_kg"] = float(materials_kg)
        result["materials_quality"] = "user_provided"
        result["materials_note"] = "Material quantity provided by the organizer."
    else:
        estimated = attendees * materials_per_attendee
        result["materials_kg"] = round(estimated, 2)
        result["materials_quality"] = "estimated"
        result["materials_note"] = (
            f"Planning estimate using {materials_per_attendee} kg per attendee "
            f"for a {event_type_normalized} event."
        )

    result["assumptions"] = {
        "energy_kwh_per_attendee_day": energy_per_attendee_day,
        "waste_kg_per_attendee_day": waste_per_attendee_day,
        "materials_kg_per_attendee": materials_per_attendee,
        "status": "planning_assumptions",
    }

    return result
