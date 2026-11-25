from fastapi import FastAPI
from pydantic import BaseModel

from backend.calculator.carbon_calculator import (
    calculate_event_footprint
)

from backend.ml.predict import (
    predict_event_carbon
)

from backend.optimizer.event_optimizer import (
    optimize_event
)

from backend.agent.event_agent import (
    plan_sustainable_event
)


# ==================================================
# FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Sustainable Event Planning AI Agent",
    description=(
        "AI-assisted sustainable event planning "
        "and carbon optimization system."
    ),
    version="1.0.0"
)


# ==================================================
# EVENT INPUT MODEL
# ==================================================

class EventInput(BaseModel):

    attendees: int
    distance_km: float
    meals: int
    energy_kwh: float
    waste_kg: float
    materials_kg: float

    budget: int = 15000
    max_car_percent: int = 30


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():

    return {
        "message": (
            "Sustainable Event Planning "
            "AI Agent API is running"
        )
    }


# ==================================================
# CARBON CALCULATOR
# ==================================================

@app.post("/calculate")
def calculate_event(event: EventInput):

    result = calculate_event_footprint(
        attendees=event.attendees,
        distance_km=event.distance_km,
        meals=event.meals,
        energy_kwh=event.energy_kwh,
        waste_kg=event.waste_kg,
        materials_kg=event.materials_kg
    )

    return result


# ==================================================
# ML PREDICTION
# ==================================================

@app.post("/predict")
def predict_event(event: EventInput):

    prediction = predict_event_carbon(
        participants=event.attendees,
        distance_km=event.distance_km
    )

    return {
        "predicted_travel_co2e_tonnes": prediction
    }


# ==================================================
# OR-TOOLS OPTIMIZATION
# ==================================================

@app.post("/optimize")
def optimize_event_plan(event: EventInput):

    result = optimize_event(
        attendees=event.attendees,
        budget=event.budget,
        max_car_percent=event.max_car_percent
    )

    return result


# ==================================================
# COMPLETE AI EVENT PLAN
# ==================================================

@app.post("/plan")
def plan_event(event: EventInput):

    result = plan_sustainable_event(
        attendees=event.attendees,
        distance_km=event.distance_km,
        meals=event.meals,
        energy_kwh=event.energy_kwh,
        waste_kg=event.waste_kg,
        materials_kg=event.materials_kg,
        budget=event.budget,
        max_car_percent=event.max_car_percent
    )

    return result