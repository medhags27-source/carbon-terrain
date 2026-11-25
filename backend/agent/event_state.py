from copy import deepcopy


DEFAULT_EVENT_STATE = {
    "event_name": "Untitled Event",
    "event_type": "College Event",

    "attendees": 500,
    "days": 1,
    "budget": 150000,
    "carbon_limit_kg": 2500,

    "distance_km": 10,
    "meals": 500,
    "energy_kwh": 500,
    "waste_kg": 100,
    "materials_kg": 50,

    "constraints": {
        "max_car_percent": 30,
        "venue_locked": False,
        "transport_locked": False,
        "food_locked": False,
        "energy_locked": False,
        "waste_locked": False,
        "materials_locked": False,
    },

    "current_plan": None,
    "previous_plan": None,

    "history": []
}


class EventState:
    """
    Stores the current event configuration and keeps
    track of changes made through the AI assistant.
    """

    def __init__(self, initial_data=None):
        self.state = deepcopy(DEFAULT_EVENT_STATE)

        if initial_data:
            self.update(initial_data)

    def get(self, key, default=None):
        return self.state.get(key, default)

    def get_all(self):
        return deepcopy(self.state)

    def update(self, updates):
        """
        Update one or more event parameters.
        """

        changes = {}

        for key, new_value in updates.items():

            if key not in self.state:
                continue

            old_value = self.state[key]

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }

                self.state[key] = new_value

        if changes:
            self.state["history"].append({
                "type": "event_update",
                "changes": changes
            })

        return changes

    def update_constraint(self, constraint, value):
        """
        Update a planning constraint.
        """

        if constraint not in self.state["constraints"]:
            raise ValueError(
                f"Unknown constraint: {constraint}"
            )

        old_value = self.state["constraints"][constraint]

        self.state["constraints"][constraint] = value

        change = {
            "constraint": constraint,
            "old": old_value,
            "new": value
        }

        self.state["history"].append({
            "type": "constraint_update",
            "change": change
        })

        return change

    def set_plan(self, plan):
        """
        Store the latest optimized plan while preserving
        the previous plan for comparison.
        """

        if self.state["current_plan"] is not None:
            self.state["previous_plan"] = deepcopy(
                self.state["current_plan"]
            )

        self.state["current_plan"] = deepcopy(plan)

    def get_current_plan(self):
        return deepcopy(self.state["current_plan"])

    def get_previous_plan(self):
        return deepcopy(self.state["previous_plan"])

    def lock(self, constraint):
        """
        Lock a planning constraint so the optimizer
        cannot modify it.
        """

        return self.update_constraint(
            constraint,
            True
        )

    def unlock(self, constraint):
        """
        Unlock a planning constraint.
        """

        return self.update_constraint(
            constraint,
            False
        )

    def add_history(self, entry):
        self.state["history"].append(
            deepcopy(entry)
        )

    def get_history(self):
        return deepcopy(self.state["history"])

    def reset(self):
        """
        Reset the event to its default configuration.
        """

        self.state = deepcopy(DEFAULT_EVENT_STATE)

    def summary(self):
        """
        Return the important event information
        for the assistant.
        """

        return {
            "event_name": self.state["event_name"],
            "event_type": self.state["event_type"],
            "attendees": self.state["attendees"],
            "days": self.state["days"],
            "budget": self.state["budget"],
            "carbon_limit_kg": self.state["carbon_limit_kg"],
            "distance_km": self.state["distance_km"],
            "meals": self.state["meals"],
            "energy_kwh": self.state["energy_kwh"],
            "waste_kg": self.state["waste_kg"],
            "materials_kg": self.state["materials_kg"],
            "constraints": deepcopy(
                self.state["constraints"]
            )
        }