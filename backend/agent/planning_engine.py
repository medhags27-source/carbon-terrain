from copy import deepcopy

from backend.agent.event_state import EventState
from backend.optimizer.event_optimizer import optimize_event


class EventPlanningEngine:

    def __init__(self, initial_state):
        self.state = EventState(initial_state)

    def optimize(self):
        current = self.state.get_all()

        result = optimize_event(
            attendees=current["attendees"],
            distance_km=current["distance_km"],
            budget=current["budget"],
            max_car_percent=current["constraints"]["max_car_percent"]
        )

        self.state.set_plan(result)

        return result

    def update_event(self, updates):
        """
        Apply an event change while preserving the previous
        event plan for before-vs-after comparison.
        """

        # Snapshot the current plan BEFORE changing the event.
        old_plan = self.state.get_current_plan()

        # Apply the event changes.
        changes = self.state.update(updates)

        # Re-optimize using the new event configuration.
        new_plan = self.optimize()

        # If there was an existing plan, explicitly preserve it
        # as the comparison baseline.
        if old_plan is not None:
            self.state.state["previous_plan"] = deepcopy(old_plan)

        return {
            "changes": changes,
            "previous_plan": old_plan,
            "current_plan": deepcopy(new_plan)
        }

    def update_constraint(self, name, value):
        """
        Apply a constraint change while preserving the previous
        event plan for before-vs-after comparison.
        """

        old_plan = self.state.get_current_plan()

        change = self.state.update_constraint(name, value)

        new_plan = self.optimize()

        if old_plan is not None:
            self.state.state["previous_plan"] = deepcopy(old_plan)

        return {
            "change": change,
            "previous_plan": old_plan,
            "current_plan": deepcopy(new_plan)
        }

    def get_comparison(self):
        return {
            "previous_plan": self.state.get_previous_plan(),
            "current_plan": self.state.get_current_plan()
        }

    def get_state(self):
        return self.state.get_all()


if __name__ == "__main__":

    engine = EventPlanningEngine({
        "event_name": "Test Event",
        "event_type": "College Event",
        "attendees": 1000,
        "days": 2,
        "budget": 300000,
        "carbon_limit_kg": 2500,
        "distance_km": 10,
        "meals": 2000,
        "energy_kwh": 1000,
        "waste_kg": 200,
        "materials_kg": 100
    })

    print("INITIAL STATE")
    print(engine.get_state())

    print("\nINITIAL OPTIMIZATION")
    print(engine.optimize())

    print("\nUPDATE EVENT")
    result = engine.update_event({
        "attendees": 1500
    })

    print(result)

    print("\nCOMPARISON")
    print(engine.get_comparison())
