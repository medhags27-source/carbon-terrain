from backend.auth_api import router as auth_router

# =========================================================
# LOCAL LLM (OLLAMA)
# =========================================================

import json
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def ask_local_llm(message: str, event_state: dict) -> str:
    """Generate a concise user-facing response with local Ollama."""

    payload = {
        "model": "qwen3:4b",
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are EcoPlan AI, a helpful sustainable event planning assistant. "
                    "Answer the user directly in natural language. Never reveal internal "
                    "reasoning, repeat the question, or narrate your instructions. "
                    "Use concise, practical recommendations and short bullet points. "
                    "Treat numbers in the latest question as hypothetical scenario inputs, "
                    "and distinguish them from the saved event state. Use only facts "
                    "supported by the saved event data. Never invent numerical emissions, "
                    "savings, costs, or predictions. Do not claim a scenario was calculated "
                    "unless a calculation actually ran. If required data is missing, say so "
                    "and explain what information is needed. Discuss emission categories "
                    "only when relevant data is available."
                )
            },
            {
                "role": "user",
                "content": (
                    "Saved event state (JSON):\n"
                    + json.dumps(event_state, ensure_ascii=False, default=str)
                    + "\n\nUser's question:\n"
                    + message
                    + "\n\nAnswer the question itself. Do not narrate your reasoning."
                )
            }
        ],
        "options": {"temperature": 0.2, "num_predict": 200}
    }

    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))

        model_message = data.get("message", {})
        answer = (model_message.get("content") or "").strip()

        # Prefer the final answer if Qwen includes a </think> marker.
        if "</think>" in answer.lower():
            answer = answer[answer.lower().rfind("</think>") + len("</think>"):].strip()

        # If the model returned no visible answer, report that clearly.
        if not answer:
            return (
                "I couldn't generate a response this time. "
                "Please try again."
            )

        return answer

    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        raise RuntimeError(
            "Ollama could not answer the question. "
            "Check that Ollama is running and qwen3:4b is installed."
        ) from exc

from backend.event_estimator import estimate_event_resources

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date

from backend.agent.event_assistant import EventAssistant

from backend.optimizer.impact_optimizer import (
    analyze_event_impact,
    calculate_interventions,
    select_best_interventions,
)

from backend.optimizer.what_if_engine import compare_scenarios
from backend.optimizer.carbon_budget_optimizer import optimize_carbon_budget
from backend.calculator.carbon_calculator import calculate_event_footprint

from backend.xai.decision_explainer import explain_decision
from backend.analysis.sensitivity_analysis import analyze_sensitivity
from backend.analysis.counterfactual_analysis import analyze_counterfactual
from backend.analysis.constraint_relaxation import analyze_constraint_relaxation
from backend.optimizer.pareto_optimizer import calculate_pareto_frontier

from backend.provenance.provenance_api import router as provenance_router

from backend.ml.predict import predict_event_travel_carbon


app = FastAPI(
    title="AI Sustainable Event Planning Assistant",
    version="1.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str


class EventSetupRequest(BaseModel):
    event_name: str
    event_type: str
    event_date: str
    days: int
    attendees: int
    budget: float
    venue: str

    distance_km: float = 10.0
    meals_per_person_per_day: float = 1.0

    energy_mode: str = "estimate"
    energy_kwh: float | None = None

    waste_mode: str = "estimate"
    waste_kg: float | None = None

    materials_mode: str = "estimate"
    materials_kg: float | None = None


# =========================================================
# HELPERS
# =========================================================

def extract_number(text: str):

    import re

    match = re.search(
        r"(\d+(?:,\d+)*(?:\.\d+)?)",
        text
    )

    if not match:
        return None

    return float(
        match.group(1).replace(",", "")
    )


def extract_money(text: str):
    return extract_number(text)


def get_state():

    if "assistant" not in globals() or assistant is None:
        return {}

    return assistant.engine.get_state()


def calculate_default_values(event):

    attendees = event.attendees
    days = event.days

    meals = int(
        attendees
        * days
        * event.meals_per_person_per_day
    )

    energy_kwh = (
        event.energy_kwh
        if event.energy_kwh is not None
        else attendees * days
    )

    waste_kg = (
        event.waste_kg
        if event.waste_kg is not None
        else attendees * days * 0.1
    )

    materials_kg = (
        event.materials_kg
        if event.materials_kg is not None
        else attendees * 0.05
    )

    return {
        "meals": meals,
        "energy_kwh": energy_kwh,
        "waste_kg": waste_kg,
        "materials_kg": materials_kg,
    }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": (
            "AI Sustainable Event Planning "
            "Assistant API is running."
        )
    }


# =========================================================
# EVENT SETUP
# =========================================================

@app.post("/event/setup")
def setup_event(request: EventSetupRequest):

    global assistant

    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    request.event_date = (
        date.fromisoformat(request.event_date)
        if isinstance(request.event_date, str)
        else request.event_date
    )

    if request.event_date < date.today():

        return {
            "success": False,
            "action": "invalid_event_date",
            "message": (
                "Event date cannot be in the past. "
                "Please select today or a future date."
            )
        }

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if request.days < 1:

        return {
            "success": False,
            "action": "invalid_duration",
            "message": (
                "Event duration must be at least 1 day."
            )
        }

    if request.attendees < 1:

        return {
            "success": False,
            "action": "invalid_attendees",
            "message": (
                "Expected attendees must be at least 1."
            )
        }

    if request.budget < 0:

        return {
            "success": False,
            "action": "invalid_budget",
            "message": (
                "Budget cannot be negative."
            )
        }

    # -----------------------------------------------------
    # CALCULATE PLANNING INPUTS
    # -----------------------------------------------------

    calculated = calculate_default_values(request)

    meals = calculated["meals"]
    energy_kwh = calculated["energy_kwh"]
    waste_kg = calculated["waste_kg"]
    materials_kg = calculated["materials_kg"]

    # -----------------------------------------------------
    # BASELINE CARBON
    # -----------------------------------------------------

    footprint = calculate_event_footprint(
        attendees=request.attendees,
        distance_km=request.distance_km,
        meals=meals,
        energy_kwh=energy_kwh,
        waste_kg=waste_kg,
        materials_kg=materials_kg
    )

    total_carbon = footprint["total_co2e"]

    # -----------------------------------------------------
    # ML TRAVEL CARBON PREDICTION
    # -----------------------------------------------------

    ml_prediction = predict_event_travel_carbon(
        participants=request.attendees,
        distance_km=request.distance_km
    )

    # -----------------------------------------------------
    # AI-GENERATED PLANNING TARGET
    # -----------------------------------------------------

    recommended_carbon_limit = round(
        total_carbon * 0.90,
        2
    )

    # -----------------------------------------------------
    # CREATE REAL EVENT
    # -----------------------------------------------------

    assistant = EventAssistant(
        {
            "event_name": request.event_name,
            "event_type": request.event_type,
            "event_date": request.event_date.isoformat(),
            "days": request.days,
            "attendees": request.attendees,
            "budget": request.budget,
            "venue": request.venue,

            "distance_km": request.distance_km,
            "meals": meals,
            "energy_kwh": energy_kwh,
            "waste_kg": waste_kg,
            "materials_kg": materials_kg,

            "carbon_limit_kg": recommended_carbon_limit,
        }
    )

    return {
        "success": True,
        "action": "event_created",

        "message": (
            f"Event '{request.event_name}' "
            "created successfully."
        ),

        "event": {
            "event_name": request.event_name,
            "event_type": request.event_type,
            "event_date": request.event_date.isoformat(),
            "days": request.days,
            "attendees": request.attendees,
            "budget": request.budget,
            "venue": request.venue,
        },

        "carbon": footprint,

        "ml_prediction": ml_prediction,

        "recommended_carbon_limit_kg": (
            recommended_carbon_limit
        ),

        "inputs": {
            "distance_km": request.distance_km,
            "meals": meals,
            "energy_kwh": energy_kwh,
            "waste_kg": waste_kg,
            "materials_kg": materials_kg,
        }
    }


# =========================================================
# STATE
# =========================================================

@app.get("/assistant/state")
def assistant_state():

    if "assistant" not in globals() or assistant is None:

        return {
            "success": False,
            "action": "no_event",
            "message": (
                "Please create an event first."
            )
        }

    return {
        "success": True,
        "state": get_state()
    }


# =========================================================
# CARBON BUDGET
# =========================================================

@app.post("/optimize/carbon-budget")
def optimize_carbon_budget_endpoint(
    carbon_limit_kg: float
):

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "carbon budget optimization."
            )
        )

    if carbon_limit_kg <= 0:

        raise HTTPException(
            status_code=400,
            detail="Carbon limit must be greater than zero."
        )

    current_state = assistant.engine.get_state()

    return optimize_carbon_budget(
        current_state,
        carbon_limit_kg
    )


# =========================================================
# ASSISTANT
# =========================================================

@app.post("/assistant")
def chat(request: ChatRequest):

    if "assistant" not in globals() or assistant is None:

        return {
            "success": False,
            "action": "no_event",
            "message": (
                "Please create your event first "
                "before using the assistant."
            )
        }

    message = request.message.strip()
    lower = message.lower()

    if not message:

        return {
            "success": False,
            "action": "empty_message",
            "message": "Please enter a request."
        }

    # =====================================================
    # CARBON BUDGET
    # =====================================================

    carbon_keywords = [
        "carbon budget",
        "carbon limit",
        "co2 limit",
        "co2e limit",
        "carbon below",
        "carbon under",
        "stay below",
        "keep my event below",
        "keep the event below",
    ]

    if any(
        keyword in lower
        for keyword in carbon_keywords
    ):

        limit = extract_number(message)

        if limit is None:

            return {
                "success": False,
                "action": "carbon_budget",
                "message": (
                    "Please specify the carbon limit "
                    "in kg CO2e."
                )
            }

        result = optimize_carbon_budget(
            get_state(),
            limit
        )

        return {
            "success": True,
            "action": "carbon_budget_optimization",
            "message": result["message"],
            "result": result
        }

    # =====================================================
    # EXTRA BUDGET
    # =====================================================

    if (
        "extra" in lower
        and "budget" in lower
    ):

        amount = extract_money(message)

        if amount is None:

            return {
                "success": False,
                "action": "impact_optimization",
                "message": (
                    "Please specify the extra budget."
                )
            }

        result = analyze_event_impact(
            get_state(),
            amount
        )

        return {
            "success": True,
            "action": "impact_optimization",
            "message": result["recommendation"],
            "result": result
        }

    # =====================================================
    # WHAT-IF ATTENDANCE
    # =====================================================

    if (
        "what if" in lower
        and (
            "people" in lower
            or "students" in lower
            or "attendees" in lower
            or "attendance" in lower
        )
    ):

        attendees = extract_number(message)

        if attendees is None:

            return {
                "success": False,
                "action": "what_if_attendance",
                "message": (
                    "Please specify the expected attendance."
                )
            }

        current_state = get_state()

        result = compare_scenarios(
            current_state,
            {
                "attendees": int(attendees)
            }
        )

        scenario_plan = result.get(
            "scenario_result",
            {}
        )

        scenario_data = scenario_plan.get(
            "scenario",
            {}
        )

        scenario_optimization = scenario_plan.get(
            "optimization",
            {}
        )

        # Use the actual event footprint for the
        # current/before value instead of the old
        # compare_scenarios placeholder values.
        current_footprint = calculate_event_footprint(
            attendees=current_state["attendees"],
            distance_km=current_state["distance_km"],
            meals=current_state["meals"],
            energy_kwh=current_state["energy_kwh"],
            waste_kg=current_state["waste_kg"],
            materials_kg=current_state["materials_kg"]
        )

        current_co2 = current_footprint["total_co2e"]

        current_cost = current_state.get(
            "budget",
            0
        )

        scenario_co2 = scenario_optimization.get(
            "optimized",
            {}
        ).get(
            "co2_kg",
            0
        )

        scenario_cost = scenario_optimization.get(
            "optimized",
            {}
        ).get(
            "cost",
            0
        )

        current_result = result.get("current", {})
        scenario_result = result.get("scenario", {})

        comparison = {
            "mode": "what_if",

            "before": {
                "attendees": current_state.get("attendees"),
                "budget": current_state.get("budget"),
                "co2_kg": current_result.get(
                    "co2_kg",
                    current_co2
                ),
                "transport_cost_inr": current_result.get(
                    "cost",
                    0
                ),
            },

            "after": {
                "attendees": scenario_data.get(
                    "attendees",
                    int(attendees)
                ),
                "budget": scenario_data.get(
                    "budget",
                    current_state.get("budget")
                ),
                "co2_kg": scenario_result.get(
                    "co2_kg",
                    0
                ),
                "transport_cost_inr": scenario_result.get(
                    "cost",
                    0
                ),
            },

            "change": {
                "co2_kg": round(
                    scenario_result.get("co2_kg", 0)
                    - current_result.get("co2_kg", 0),
                    2
                ),
                "transport_cost_inr": round(
                    scenario_result.get("cost", 0)
                    - current_result.get("cost", 0),
                    2
                ),
            },
        }

        return {
            "success": True,
            "action": "what_if_attendance",
            "message": (
                f"I simulated the event with "
                f"{int(attendees):,} attendees."
            ),
            "result": result,
            "comparison": comparison
        }

    # =====================================================
    # WHAT-IF BUDGET
    # =====================================================

    if (
        "what if" in lower
        and "budget" in lower
    ):

        budget = extract_money(message)

        if budget is None:

            return {
                "success": False,
                "action": "what_if_budget",
                "message": (
                    "Please specify the hypothetical budget."
                )
            }

        result = compare_scenarios(
            get_state(),
            {
                "budget": budget
            }
        )

        return {
            "success": True,
            "action": "what_if_budget",
            "message": (
                f"I simulated the event with "
                f"a ?{budget:,.0f} budget."
            ),
            "result": result
        }

    # =====================================================
    # ML TRAVEL PREDICTION
    # =====================================================

    ml_keywords = [
        "predict travel emissions",
        "predict travel carbon",
        "predict travel co2",
        "ml prediction",
        "machine learning prediction",
        "travel emission prediction",
    ]

    if any(
        keyword in lower
        for keyword in ml_keywords
    ):

        import re

        matches = re.findall(
            r"(\d+(?:,\d+)*(?:\.\d+)?)",
            message
        )

        numbers = [
            float(value.replace(",", ""))
            for value in matches
        ]

        if len(numbers) < 2:

            return {
                "success": False,
                "action": "ml_travel_prediction",
                "message": (
                    "Please provide participants and "
                    "travel distance. Example: "
                    "'Predict travel emissions for "
                    "500 people travelling 20 km.'"
                )
            }

        participants = int(numbers[0])
        distance_km = numbers[1]

        if participants < 1:

            return {
                "success": False,
                "action": "ml_travel_prediction",
                "message": "Participants must be at least 1."
            }

        if distance_km < 0:

            return {
                "success": False,
                "action": "ml_travel_prediction",
                "message": "Travel distance cannot be negative."
            }

        prediction = predict_event_travel_carbon(
            participants=participants,
            distance_km=distance_km
        )

        return {
            "success": True,
            "action": "ml_travel_prediction",
            "message": (
                f"The Random Forest model predicts "
                f"{prediction['prediction_tco2e']} tCO2e "
                f"of travel-related emissions for "
                f"{participants:,} participants travelling "
                f"{distance_km:g} km."
            ),
            "result": prediction
        }

    # =====================================================
    # NORMAL ASSISTANT
    # =====================================================

    result = assistant.process(message)

    # Keep existing deterministic actions working.
    # Use Ollama for general natural-language questions.
    if result.get("action") == "event_aware_response":
        try:
            answer = ask_local_llm(message, get_state())
            return {
                "success": True,
                "action": "local_llm",
                "message": answer,
                "state": get_state()
            }
        except RuntimeError as exc:
            return {
                "success": False,
                "action": "local_llm_error",
                "message": str(exc)
            }

    return {
        "success": result.get(
            "success",
            True
        ),

        "action": result.get(
            "action",
            "assistant"
        ),

        "message": result.get(
            "message",
            "Request processed."
        ),

        "result": result,

        "comparison": result.get(
            "comparison"
        ),

        "state": result.get(
            "state"
        )
    }


# =========================================================
# IMPACT OPTIMIZER API
# =========================================================

@app.post("/optimize/impact")
def optimize_impact(
    extra_budget: float = 50000
):

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "the optimizer."
            )
        )

    current_state = assistant.engine.get_state()

    interventions = calculate_interventions(
        current_state
    )

    selected = select_best_interventions(
        interventions,
        extra_budget
    )

    return {
        "extra_budget": extra_budget,
        "interventions": interventions,
        "recommendation": selected,
    }


# =========================================================
# XAI / WHY THIS PLAN
# =========================================================

@app.get("/optimize/explanation")
def optimize_explanation():

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before requesting "
                "an explanation."
            )
        )

    current_state = assistant.engine.get_state()

    optimization = assistant.engine.state.get_current_plan()

    if optimization is None:
        optimization = assistant.engine.optimize()

    explanation = explain_decision(
        optimization,
        current_state
    )

    return explanation


# =========================================================
# SENSITIVITY / THRESHOLD ANALYSIS
# =========================================================

@app.get("/optimize/sensitivity")
def optimize_sensitivity():

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "sensitivity analysis."
            )
        )

    current_state = assistant.engine.get_state()

    return analyze_sensitivity(
        current_state
    )


# =========================================================
# COUNTERFACTUAL ANALYSIS
# =========================================================

@app.get("/optimize/counterfactual")
def optimize_counterfactual(
    target_co2_kg: float | None = None,
    target_budget: float | None = None
):

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "counterfactual analysis."
            )
        )

    current_state = assistant.engine.get_state()

    return analyze_counterfactual(
        current_state,
        target_co2_kg=target_co2_kg,
        target_budget=target_budget
    )


# =========================================================
# CONSTRAINT RELAXATION
# =========================================================

@app.get("/optimize/constraint-relaxation")
def optimize_constraint_relaxation(
    target_co2_kg: float | None = None,
    target_budget: float | None = None
):

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "constraint relaxation."
            )
        )

    current_state = assistant.engine.get_state()

    return analyze_constraint_relaxation(
        attendees=current_state["attendees"],
        distance_km=current_state["distance_km"],
        budget=current_state["budget"],
        max_car_percent=current_state.get(
            "constraints", {}
        ).get("max_car_percent", 30),
        target_co2_kg=target_co2_kg,
        target_budget=target_budget
    )


# =========================================================
# PARETO / TRADE-OFF ANALYSIS
# =========================================================

@app.get("/optimize/pareto")
def optimize_pareto():

    if "assistant" not in globals() or assistant is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Create an event before running "
                "Pareto analysis."
            )
        )

    current_state = assistant.engine.get_state()

    return calculate_pareto_frontier(
        attendees=current_state["attendees"],
        distance_km=current_state["distance_km"],
        budget=current_state["budget"],
        max_car_percent=current_state.get(
            "constraints", {}
        ).get("max_car_percent", 30)
    )


# =========================================================
# ML / TRAVEL CARBON PREDICTION API
# =========================================================

@app.get("/ml/travel-prediction")
def ml_travel_prediction(
    participants: int,
    distance_km: float
):

    if participants < 1:

        raise HTTPException(
            status_code=400,
            detail="Participants must be at least 1."
        )

    if distance_km < 0:

        raise HTTPException(
            status_code=400,
            detail="Distance cannot be negative."
        )

    prediction = predict_event_travel_carbon(
        participants=participants,
        distance_km=distance_km
    )

    return {
        "success": True,
        "prediction": prediction
    }


# =========================================================
# PROVENANCE
# =========================================================

app.include_router(
    provenance_router
)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.assistant_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )










